"""Join sentences with the latest accepted S1-S4 records into one CSV per book, for browsing in Excel."""
from __future__ import annotations

import collections
import csv
import json
import pathlib

from .assemble import Codebook


def _latest(path: pathlib.Path) -> dict:
    """Latest accepted record per unit_id (later lines win, so reruns replace earlier answers)."""
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            out[r["unit_id"]] = r
    return out


SPEECH_ACTS = {"law", "teaching", "command", "prophecy", "prayer_hymn"}


def carry_speakers(s1: dict, paragraphs: list[dict]) -> None:
    """Fill a blank speaker from the last named one, in code, across chapter breaks.

    A speech often runs on past a chapter heading (Leviticus 2 continues the LORD's speech from 1), and
    S1 only sees its window. A narration paragraph ends the carry-over. Filled values are marked."""
    last = None
    for para in paragraphs:
        r = s1.get(para["id"])
        if not r:
            continue
        if r.get("speech_act") == "narration":
            last = None
        elif r.get("speaker"):
            last = (r["speaker"], r.get("addressee", ""))
        elif last and r.get("speech_act") in SPEECH_ACTS:
            r["speaker"], r["addressee"] = last[0] + " *", r.get("addressee") or last[1]


def build(out_dir: pathlib.Path, book: str) -> dict:
    d = out_dir / book
    cb = Codebook()
    tl = {t["id"]: t["label"] for t in cb.themes["themes"]} | {t["id"]: t["label"] for t in cb.topics["topics"]}
    sents = [json.loads(line) for line in (d / "sentences.jsonl").read_text(encoding="utf-8").splitlines()]
    s1, s2, s3, s4 = (_latest(d / f"out_S{i}.jsonl") for i in range(1, 5))
    carry_speakers(s1, [json.loads(line) for line in (d / "paragraphs.jsonl").read_text(encoding="utf-8").splitlines()])
    theme_count, topic_count, norm_count, cat_count = (collections.Counter() for _ in range(4))
    rows = []
    for s in sents:
        p = s1.get(s["para"], {})
        r2, r3, r4 = s2.get(s["id"], {}), s3.get(s["id"], {}), s4.get(s["id"], {})
        for t in r2.get("themes", []):
            theme_count[t["id"]] += 1
        for t in r2.get("topics", []):
            topic_count[t["id"]] += 1
        for n in r3.get("norms", []):
            norm_count[n["modality"]] += 1
        for m in r4.get("mentions", []):
            if m.get("social_category", "none") != "none":
                cat_count[m["social_category"]] += 1
        rows.append({
            "sentence_id": s["id"], "ref": s["ref"], "text": s["text"],
            "speech_act": p.get("speech_act", ""), "force": p.get("force", ""),
            "speaker": p.get("speaker", ""), "addressee": p.get("addressee", ""),
            "themes": "; ".join(f"{t['id']} {tl.get(t['id'], '')} ({t['salience']})" for t in r2.get("themes", [])),
            "topics": "; ".join(f"{t['id']} {tl.get(t['id'], '')} ({t['salience']})" for t in r2.get("topics", [])),
            "proposal": (r2.get("proposal") or {}).get("label", ""),
            "norms": "; ".join(f"{n['modality']}: {n['action']}" + (f" [if {n['condition']}]" if n.get("condition") else "")
                               for n in r3.get("norms", [])),
            "mentions": "; ".join(f"{m['span']}={m.get('referent') or '?'}"
                                  + (f" <{m['social_category']}/{m['role']}>" if m.get("social_category", "none") != "none" else "")
                                  for m in r4.get("mentions", [])),
            "s2_confidence": r2.get("confidence", ""),
        })
    path = d / "report.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig so Excel shows accents
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["sentence_id"])
        w.writeheader()
        w.writerows(rows)
    covered = {k: sum(1 for s in sents if s["id"] in src) for k, src in (("S2", s2), ("S3", s3), ("S4", s4))}
    covered["S1"] = sum(1 for s in sents if s["para"] in s1)
    return {"path": str(path), "sentences": len(sents), "covered": covered,
            "top_themes": [(k, tl.get(k, ""), n) for k, n in theme_count.most_common(8)],
            "top_topics": [(k, tl.get(k, ""), n) for k, n in topic_count.most_common(5)],
            "norms": dict(norm_count), "social_categories": dict(cat_count)}
