"""V1 verifier: plain code, no model. Checks every reply before anything is stored.

A window's reply is split into accepted records and problems. Records for missing targets are
reported so the runner can retry them; records that break a rule are rejected with the reason.
"""
from __future__ import annotations

import json
import re

MAX_LABELS = 3


_QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "—": "-", "–": "-"})


def _norm(s: str) -> str:
    """Lower case, no punctuation, single spaces. Also drops the '|' caesura marks of the Edda
    translation, which the model leaves out of spans (171 of 250 Edda span rejections in the pilot)."""
    s = s.translate(_QUOTES).replace("|", " ").lower()
    s = re.sub(r"[^\w' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def span_ok(span: str, text: str) -> bool:
    """The span's words, in order, appear in the target. Punctuation, case and spacing are ignored."""
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
    context_ids = {c["id"] for c in window["context_before"] + window["context_after"]
                   + window.get("chapter_opening", [])}
    lower = {k: {v.lower(): v for v in vals} for k, vals in enums.items()}
    seen = set()
    target_order = [t["id"] for t in window["targets"]]
    for pos, rec in enumerate(records):
        # A blank unit_id in an otherwise complete reply is matched by position (seen once in the smoke test).
        if not rec.get("unit_id") and len(records) == len(target_order):
            rec["unit_id"] = target_order[pos]
            rec["_unit_id_from_position"] = True
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

        kind = {"A1T": "S2", "A1N": "S3"}.get(agent_short, agent_short)
        if kind == "S1":
            rec["speech_act"] = check_enum(rec.get("speech_act"), "$SPEECH_ACT", "speech_act")
            rec["force"] = check_enum(rec.get("force"), "$FORCE", "force")
        elif kind == "S2":
            for kind, key in (("themes", "$THEME_IDS"), ("topics", "$TOPIC_IDS")):
                labels = rec.get(kind, [])
                # Salience 0 ("in passing") proved to be noise in the first review; drop those labels.
                dropped = [lab for lab in labels if lab.get("salience") == 0]
                if dropped:
                    labels = [lab for lab in labels if lab.get("salience") != 0]
                    rec[kind] = labels
                    rec.setdefault("_dropped_salience0", []).extend(lab.get("id") for lab in dropped)
                if len(labels) > MAX_LABELS:  # keep the most salient three rather than reject the record
                    labels = sorted(labels, key=lambda lab: -(lab.get("salience") or 0))[:MAX_LABELS]
                    rec[kind] = labels
                    rec["_trimmed"] = True
                best: dict = {}
                for lab in labels:
                    lab["id"] = check_enum(lab.get("id"), key, kind[:-1])
                    # The same label listed twice: keep the higher salience rather than reject the record.
                    if lab["id"] not in best or (lab.get("salience") or 0) > (best[lab["id"]].get("salience") or 0):
                        best[lab["id"]] = lab
                if len(best) < len(labels):
                    labels = list(best.values())
                    rec[kind] = labels
                for lab in labels:
                    if not isinstance(lab.get("salience"), int) or not 1 <= lab["salience"] <= 3:
                        problems.append(f"salience out of range: {lab.get('salience')!r}")
                    check_span(lab.get("span"), kind[:-1])
            prop = rec.get("proposal") or {}
            if prop.get("label"):
                check_span(prop.get("span"), "proposal")
        elif kind == "S3":
            # The same norm listed twice (same modality and action): keep one rather than count it twice.
            uniq, seen_norms = [], set()
            for n in rec.get("norms", []):
                k = (str(n.get("modality")).lower(), _norm(n.get("action") or ""))
                if k not in seen_norms:
                    seen_norms.add(k)
                    uniq.append(n)
            if len(uniq) < len(rec.get("norms", [])):
                rec["norms"] = uniq
                rec["_deduped"] = True
            for n in rec.get("norms", []):
                n["modality"] = check_enum(n.get("modality"), "$NORM_MODALITY", "modality")
                n["topic"] = check_enum(n.get("topic"), "$TOPIC_IDS_OR_NONE", "topic")
                check_span(n.get("span"), "norm")
                for f in ("condition", "sanction"):
                    check_span(n.get(f), f)
        elif kind == "S4":
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
