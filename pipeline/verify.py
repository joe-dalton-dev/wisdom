"""V1 verifier: plain code, no model. Checks every reply before anything is stored.

A window's reply is split into accepted records and problems. Records for missing targets are
reported so the runner can retry them; records that break a rule are rejected with the reason.
"""
from __future__ import annotations

import json
import re

MAX_LABELS = 3


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def span_ok(span: str, text: str) -> bool:
    """Exact substring, or the same after collapsing whitespace and case (models sometimes re-space)."""
    return not span or span in text or _norm(span) in _norm(text)


def parse_reply(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def verify(agent_short: str, window: dict, reply_text: str, enums: dict) -> dict:
    """Return {"accepted": [...], "rejected": [...], "missing": [...], "fatal": str|None}."""
    out = {"accepted": [], "rejected": [], "missing": [], "fatal": None}
    try:
        data = parse_reply(reply_text)
        records = data["records"]
        assert isinstance(records, list)
    except Exception as e:  # noqa: BLE001 - any parse failure makes the whole reply unusable
        out["fatal"] = f"unparseable reply: {type(e).__name__}: {e}"[:300]
        out["missing"] = [t["id"] for t in window["targets"]]
        return out

    texts = {t["id"]: t["text"] for t in window["targets"]}
    context_ids = {c["id"] for c in window["context_before"] + window["context_after"]}
    lower = {k: {v.lower(): v for v in vals} for k, vals in enums.items()}
    seen = set()
    for rec in records:
        problems = []
        uid = rec.get("unit_id")
        if uid in context_ids:
            problems.append("record for a context item")
        elif uid not in texts:
            problems.append(f"unknown unit_id {uid!r}")
        elif uid in seen:
            problems.append("duplicate record")
        text = texts.get(uid, "")
        conf = rec.get("confidence")
        if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
            problems.append(f"confidence out of range: {conf!r}")

        def check_enum(value, key, field):
            if value is None:
                problems.append(f"{field} missing")
                return value
            canon = lower[key].get(str(value).lower())
            if canon is None:
                problems.append(f"{field} {value!r} not allowed")
            return canon or value

        def check_span(span, field):
            if not span_ok(span or "", text):
                problems.append(f"{field} span not in text: {span!r}"[:200])

        if agent_short == "S1":
            rec["speech_act"] = check_enum(rec.get("speech_act"), "$SPEECH_ACT", "speech_act")
            rec["force"] = check_enum(rec.get("force"), "$FORCE", "force")
        elif agent_short == "S2":
            for kind, key in (("themes", "$THEME_IDS"), ("topics", "$TOPIC_IDS")):
                labels = rec.get(kind, [])
                if len(labels) > MAX_LABELS:
                    problems.append(f"{len(labels)} {kind}, max {MAX_LABELS}")
                ids = []
                for lab in labels:
                    lab["id"] = check_enum(lab.get("id"), key, kind[:-1])
                    if lab["id"] in ids:
                        problems.append(f"repeated {kind[:-1]} {lab['id']}")
                    ids.append(lab["id"])
                    if not isinstance(lab.get("salience"), int) or not 0 <= lab["salience"] <= 3:
                        problems.append(f"salience out of range: {lab.get('salience')!r}")
                    check_span(lab.get("span"), kind[:-1])
            prop = rec.get("proposal") or {}
            if prop.get("label"):
                check_span(prop.get("span"), "proposal")
        elif agent_short == "S3":
            for n in rec.get("norms", []):
                n["modality"] = check_enum(n.get("modality"), "$NORM_MODALITY", "modality")
                n["topic"] = check_enum(n.get("topic"), "$TOPIC_IDS_OR_NONE", "topic")
                check_span(n.get("span"), "norm")
                for f in ("condition", "sanction"):
                    check_span(n.get(f), f)
        elif agent_short == "S4":
            for m in rec.get("mentions", []):
                m["social_category"] = check_enum(m.get("social_category"), "$SOCIAL_CATEGORY_OR_NONE",
                                                  "social_category")
                m["role"] = check_enum(m.get("role"), "$ROLE_OR_NONE", "role")
                check_span(m.get("span"), "mention")

        if problems:
            out["rejected"].append({"record": rec, "problems": problems})
        else:
            seen.add(uid)
            out["accepted"].append(rec)
    out["missing"] = [t for t in texts if t not in seen]
    return out
