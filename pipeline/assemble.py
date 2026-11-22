"""Prompt assembly from agent cards. Same card + same window -> byte-identical request and hash.

Layout, for prompt caching: the system prompt (base rules + role card + label lists) is identical for
every call of an agent and is cached; only the user message (the window) changes per call.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS = {"S1": "S1_discourse", "S2": "S2_theme_tagger", "S3": "S3_norm_extractor", "S4": "S4_entities"}
ADJUDICATORS = {"A1T": "A1_themes", "A1N": "A1_norms"}
ALL_CARDS = {**AGENTS, **ADJUDICATORS}


def sha256(obj) -> str:
    data = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class Codebook:
    def __init__(self, root: pathlib.Path = ROOT):
        self.themes = yaml.safe_load((root / "codebook/themes.yaml").read_text(encoding="utf-8"))
        self.topics = yaml.safe_load((root / "codebook/topics.yaml").read_text(encoding="utf-8"))
        self.facets = yaml.safe_load((root / "codebook/facets.yaml").read_text(encoding="utf-8"))["facets"]
        self.theme_ids = [t["id"] for t in self.themes["themes"]]
        self.topic_ids = [t["id"] for t in self.topics["topics"]]
        self.version = f"themes@{self.themes['version']}+topics@{self.topics['version']}"

    def enums(self) -> dict:
        f = self.facets
        return {
            "$THEME_IDS": self.theme_ids,
            "$TOPIC_IDS": self.topic_ids,
            "$TOPIC_IDS_OR_NONE": self.topic_ids + ["none"],
            "$SPEECH_ACT": f["speech_act"]["values"],
            "$FORCE": f["force"]["values"],
            "$NORM_MODALITY": f["norm_modality"]["values"],
            "$SOCIAL_CATEGORY_OR_NONE": f["social_category"]["values"] + ["none"],
            "$ROLE_OR_NONE": f["social_category"]["roles"] + ["none"],
        }

    def render(self, which: str) -> str:
        """Human-readable label list for the system prompt."""
        if which == "themes":
            dom = {d["id"]: d["label"] for d in self.themes["domains"]}
            lines, cur = ["THEMES (id - label: definition | include | exclude)"], None
            for t in self.themes["themes"]:
                if t["domain"] != cur:
                    cur = t["domain"]
                    lines.append(f"\n{dom[cur]}")
                terms = f" Terms: {', '.join(t['terms'])}." if t.get("terms") else ""
                lines.append(f"- {t['id']} - {t['label']}: {t['definition']} | Include: {t['include']} | "
                             f"Exclude: {t['exclude']}{terms}")
            return "\n".join(lines)
        if which == "topics":
            lines, cur = ["TOPICS (id - label: definition | include | exclude)"], None
            for t in self.topics["topics"]:
                if t["group"] != cur:
                    cur = t["group"]
                    lines.append(f"\n{cur}")
                lines.append(f"- {t['id']} - {t['label']}: {t['definition']} | Include: {t['include']} | "
                             f"Exclude: {t['exclude']}")
            return "\n".join(lines)
        f = self.facets[which]
        vals = f["values"]
        vals = ", ".join(f"{k} = {v}" for k, v in vals.items()) if isinstance(vals, dict) else ", ".join(vals)
        extra = f" Roles: {', '.join(f['roles'])}." if "roles" in f else ""
        return f"{which.upper()} values: {vals}.{extra}"


def _fill(node, enums: dict):
    if isinstance(node, dict):
        return {k: (enums[v] if k == "enum" and isinstance(v, str) else _fill(v, enums)) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill(v, enums) for v in node]
    return node


class Agent:
    def __init__(self, short: str, codebook: Codebook | None = None, root: pathlib.Path = ROOT,
                 model: str | None = None, effort: str | None = None):
        self.short = short
        self.card = yaml.safe_load((root / "agents" / f"{ALL_CARDS[short]}.yaml").read_text(encoding="utf-8"))
        self.default_model = self.card["model"]
        if model:  # gold-set runs use the same card on a stronger model
            self.card["model"] = model
        if effort:
            self.card["effort"] = effort
        self.codebook = codebook or Codebook(root)
        base = (root / "agents/_base.md").read_text(encoding="utf-8")
        self.base_text = base.split("-->", 1)[-1].strip()
        raw = json.loads((root / self.card["output_schema"]).read_text(encoding="utf-8"))
        schema = _fill(raw, self.codebook.enums())
        for k in ("$schema", "$id", "title", "description"):
            schema.pop(k, None)
        self.schema = schema
        self.system = self._system_prompt()
        self.fixed_hash = sha256({"system": self.system, "schema": self.schema, "model": self.card["model"],
                                  "max_tokens": self.card["max_tokens"], "effort": self.card.get("effort")})

    @property
    def model(self) -> str:
        return self.card["model"]

    @property
    def version_tag(self) -> str:
        tag = f"{self.card['id']}@{self.card['version']}"
        return tag if self.model == self.default_model else f"{tag}+{self.model}"

    @property
    def variant(self) -> str:
        """'' for the card's own model; the model ID when overridden (used in file names)."""
        return "" if self.model == self.default_model else self.model

    def _system_prompt(self) -> str:
        parts = [self.base_text, f"## Your role: {self.card['id']} (card {self.card['version']})",
                 self.card["task"].strip()]
        parts += [self.codebook.render(lbl) for lbl in self.card["labels"]]
        if self.card.get("examples"):
            parts.append("EXAMPLES\n" + "\n\n".join(self.card["examples"]))
        return "\n\n".join(parts)

    @staticmethod
    def user_message(window: dict) -> str:
        def block(title, items):
            return f"{title}:\n" + ("\n".join(f"[{i['id']}] {i['text']}" for i in items) if items else "(none)")
        opening = [block("CHAPTER OPENING (context)", window["chapter_opening"])] if window.get("chapter_opening") else []
        parts = opening + [block("CONTEXT BEFORE", window["context_before"]),
                           block("TARGETS", window["targets"]),
                           block("CONTEXT AFTER", window["context_after"])]
        if window.get("candidates"):  # adjudication: what the two reference models proposed
            parts.append("CANDIDATES:\n" + "\n".join(
                f"[{c['unit_id']}]\n{c['text']}" for c in window["candidates"]))
        return "\n\n".join(parts)

    def request(self, window: dict) -> dict:
        """Messages API parameters for one window. Deterministic for a given card and window."""
        return {
            "model": self.model,
            "max_tokens": self.card["max_tokens"],
            "system": [{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": self.user_message(window)}],
            "output_config": {"format": {"type": "json_schema", "schema": copy.deepcopy(self.schema)},
                              **({"effort": self.card["effort"]} if self.card.get("effort") else {})},
        }

    def job_key(self, window: dict) -> str:
        """Identity of a job: card, base, codebook, model and the exact window text. Same key -> skip."""
        return sha256({"fixed": self.fixed_hash, "window": self.user_message(window)})

    def prompt_hash(self, window: dict) -> str:
        return sha256(self.request(window))
