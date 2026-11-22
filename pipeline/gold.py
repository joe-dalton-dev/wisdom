"""Silver-standard gold set: two strong models label the same windows, Opus adjudicates disagreements.

Steps (each is a CLI command, see __main__.py):
  gold-select      pick 50 sentence windows per pilot book (deterministic)
  gold-label       S2 and S3 on those windows with Claude Opus 5.5 and Claude Sonnet 5.5
  gold-adjudicate  find disagreements, send them to A1 (Opus), blind to which model said what
  gold-finalize    agreed + adjudicated labels -> gold_S2.jsonl, gold_S3.jsonl per book
  gold-sample      50 random gold items as a CSV for a human sanity check
  score            Haiku's labels against the gold set
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import pathlib
import random

from .assemble import Codebook

REF_MODELS = [("claude-opus-5-5", "medium"), ("claude-sonnet-5-5", "medium")]
GOLD_AGENTS = ["S2", "S3"]
DISPUTE_FILES = {"A1T": "disputes_A1T.jsonl", "A1N": "disputes_A1N.jsonl"}
SEED = 7


def _jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def _write(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def _latest(path: pathlib.Path) -> dict:
    return {r["unit_id"]: r for r in _jsonl(path)}


def gold_dir(cfg: dict) -> pathlib.Path:
    return pathlib.Path(cfg["out_dir"]) / "gold"


def gold_cfg(cfg: dict) -> dict:
    """Runner config for gold work: own folder and ledger; spend still counts against the main cap."""
    g = gold_dir(cfg)
    return {**cfg, "out_dir": str(g), "ledger": str(g / "ledger.sqlite"),
            "spend_ledgers": [str(pathlib.Path(cfg["out_dir"]) / "ledger.sqlite")]}


# ---------- select ----------
def select(cfg: dict, per_book: int = 50) -> dict:
    """Systematic sample over each book's windows (spreads across chapters), fixed seed."""
    out, g = {}, gold_dir(cfg)
    for book in cfg["books"]:
        b = book["id"]
        src = pathlib.Path(cfg["out_dir"]) / b
        wins = _jsonl(src / "windows_sentence.jsonl")
        if not wins:
            raise SystemExit(f"No windows for {b}; run `python -m pipeline split` first.")
        step = max(1, len(wins) / per_book)
        start = random.Random(f"{SEED}-{b}").random() * step
        picked = sorted({int(start + i * step) for i in range(min(per_book, len(wins)))})
        _write(g / b / "windows_sentence.jsonl", [wins[i] for i in picked])
        (g / b / "sentences.jsonl").write_text((src / "sentences.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
        out[b] = {"windows": len(picked), "sentences": sum(len(wins[i]["targets"]) for i in picked)}
    (g / "selection.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


# ---------- compare and build disputes ----------
def _s2_ids(r: dict) -> set:
    return {t["id"] for t in r.get("themes", [])} | {t["id"] for t in r.get("topics", [])}


def _s3_key(r: dict) -> list:
    return sorted(n["modality"] for n in r.get("norms", []))


def _fmt_s2(r: dict, labels: dict) -> str:
    th = "; ".join(f"{t['id']} {labels.get(t['id'], '')} ({t['salience']}) '{t['span']}'" for t in r.get("themes", []))
    tp = "; ".join(f"{t['id']} {labels.get(t['id'], '')} ({t['salience']}) '{t['span']}'" for t in r.get("topics", []))
    return f"themes: {th or 'none'} | topics: {tp or 'none'}"


def _fmt_s3(r: dict) -> str:
    if not r.get("norms"):
        return "no norms"
    return "; ".join(f"{n['modality']}: {n['action']} (addressee: {n['addressee'] or '-'}; target: {n['target'] or '-'};"
                     f" condition: {n['condition'] or '-'}; sanction: {n['sanction'] or '-'}; topic: {n['topic']})"
                     for n in r["norms"])


def disputes(cfg: dict) -> dict:
    g, cb = gold_dir(cfg), Codebook()
    labels = {t["id"]: t["label"] for t in cb.themes["themes"]} | {t["id"]: t["label"] for t in cb.topics["topics"]}
    (m_a, _), (m_b, _) = REF_MODELS
    summary = {}
    for book in cfg["books"]:
        b = book["id"]
        d = g / b
        wins = _jsonl(d / "windows_sentence.jsonl")
        stats = collections.Counter()
        for agent, adj, same, fmt in (("S2", "A1T", lambda x, y: _s2_ids(x) == _s2_ids(y), lambda r: _fmt_s2(r, labels)),
                                      ("S3", "A1N", lambda x, y: _s3_key(x) == _s3_key(y), _fmt_s3)):
            ra, rb = _latest(d / f"out_{agent}@{m_a}.jsonl"), _latest(d / f"out_{agent}@{m_b}.jsonl")
            agreed, dispute_windows = [], []
            for w in wins:
                ids = [t["id"] for t in w["targets"]]
                disputed = []
                for uid in ids:
                    if uid not in ra or uid not in rb:
                        stats[f"{agent}_missing"] += 1
                    elif same(ra[uid], rb[uid]):
                        agreed.append({**ra[uid], "_gold": "agreed"})
                        stats[f"{agent}_agreed"] += 1
                    else:
                        disputed.append(uid)
                        stats[f"{agent}_disputed"] += 1
                if not disputed:
                    continue
                texts = {t["id"]: t for t in w["targets"]}
                # The window's other (agreed) targets become context, so the adjudicator reads the same passage.
                before = list(w["context_before"]) + [texts[i] for i in ids if i not in disputed]
                after = list(w["context_after"])
                cands = []
                for uid in disputed:
                    pair = [fmt(ra[uid]), fmt(rb[uid])]
                    if int(hashlib.sha256(uid.encode()).hexdigest(), 16) % 2:  # blind and order-balanced
                        pair.reverse()
                    cands.append({"unit_id": uid, "text": f"Annotator 1: {pair[0]}\nAnnotator 2: {pair[1]}"})
                dispute_windows.append({"id": f"{w['id']}.{adj}", "book": b, "chapter": w["chapter"], "kind": adj,
                                        "targets": [texts[i] for i in disputed], "context_before": before,
                                        "context_after": after, "candidates": cands})
            _write(d / f"agreed_{agent}.jsonl", agreed)
            _write(d / DISPUTE_FILES[adj], dispute_windows)
        summary[b] = dict(stats)
    return summary


def windows_for(cfg: dict):
    g = gold_dir(cfg)

    def get(agent: str, book: str) -> dict:
        path = g / book / (DISPUTE_FILES[agent] if agent in DISPUTE_FILES else "windows_sentence.jsonl")
        return {w["id"]: w for w in _jsonl(path)}
    return get


# ---------- finalize ----------
def finalize(cfg: dict) -> dict:
    g = gold_dir(cfg)
    (m_a, _), (m_b, _) = REF_MODELS
    summary = {}
    for book in cfg["books"]:
        b = book["id"]
        d = g / b
        st = {}
        for agent, adj in (("S2", "A1T"), ("S3", "A1N")):
            rows = _jsonl(d / f"agreed_{agent}.jsonl")
            ra, rb = _latest(d / f"out_{agent}@{m_a}.jsonl"), _latest(d / f"out_{agent}@{m_b}.jsonl")
            decided = _latest(d / f"out_{adj}.jsonl")
            disputed = [t["id"] for w in _jsonl(d / DISPUTE_FILES[adj]) for t in w["targets"]]
            unresolved = 0
            for uid in disputed:
                r = decided.get(uid)
                if r is None:
                    unresolved += 1
                    continue
                if agent == "S2":  # adjudicator may only choose among the two annotators' labels
                    allowed = _s2_ids(ra.get(uid, {})) | _s2_ids(rb.get(uid, {}))
                    r["themes"] = [t for t in r["themes"] if t["id"] in allowed]
                    r["topics"] = [t for t in r["topics"] if t["id"] in allowed]
                rows.append({**r, "_gold": "adjudicated"})
            _write(d / f"gold_{agent}.jsonl", rows)
            st[agent] = {"agreed": sum(1 for r in rows if r["_gold"] == "agreed"),
                         "adjudicated": sum(1 for r in rows if r["_gold"] == "adjudicated"),
                         "unresolved": unresolved}
        summary[b] = st
    return summary


# ---------- human sanity sample ----------
def sample(cfg: dict, n: int = 50) -> str:
    g, cb = gold_dir(cfg), Codebook()
    labels = {t["id"]: t["label"] for t in cb.themes["themes"]} | {t["id"]: t["label"] for t in cb.topics["topics"]}
    items = []
    for book in cfg["books"]:
        b = book["id"]
        sents = {s["id"]: s["text"] for s in _jsonl(g / b / "sentences.jsonl")}
        s3 = _latest(g / b / "gold_S3.jsonl")
        for r in _jsonl(g / b / "gold_S2.jsonl"):
            items.append((b, r, s3.get(r["unit_id"], {}), sents.get(r["unit_id"], "")))
    random.Random(SEED).shuffle(items)
    path = g / "sanity_sample.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["book", "sentence_id", "text", "themes", "topics", "norms", "how decided", "adjudicator reason",
                    "Looks wrong? (x)", "Comment"])
        for b, r, n3, text in items[:n]:
            w.writerow([b, r["unit_id"], text,
                        "; ".join(f"{labels.get(t['id'], t['id'])} ({t['salience']})" for t in r.get("themes", [])),
                        "; ".join(labels.get(t["id"], t["id"]) for t in r.get("topics", [])),
                        "; ".join(f"{x['modality']}: {x['action']}" for x in n3.get("norms", [])),
                        r["_gold"] + (f" / norms {n3.get('_gold', '')}" if n3 else ""),
                        r.get("reason", "") or n3.get("reason", ""), "", ""])
    return str(path)


# ---------- scoring ----------
def _prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
            "tp": tp, "fp": fp, "fn": fn}


def score(cfg: dict, agent: str, against: str = "") -> dict:
    """Score a model's labels on the gold sentences. against='' -> the pilot (Haiku) outputs."""
    g, main = gold_dir(cfg), pathlib.Path(cfg["out_dir"])
    cb = Codebook()
    labels = {t["id"]: t["label"] for t in cb.themes["themes"]} | {t["id"]: t["label"] for t in cb.topics["topics"]}
    tot = collections.Counter()
    per_label = collections.defaultdict(collections.Counter)
    by_book = {}
    for book in cfg["books"]:
        b = book["id"]
        gold = _latest(g / b / f"gold_{agent}.jsonl")
        pred_path = (g / b / f"out_{agent}@{against}.jsonl") if against else (main / b / f"out_{agent}.jsonl")
        pred = _latest(pred_path)
        bc = collections.Counter()
        for uid, gr in gold.items():
            pr = pred.get(uid)
            if pr is None:
                bc["unlabelled"] += 1
                continue
            bc["sentences"] += 1
            if agent == "S2":
                for kind in ("themes", "topics"):
                    G, P = {t["id"] for t in gr.get(kind, [])}, {t["id"] for t in pr.get(kind, [])}
                    bc[f"{kind}_tp"] += len(G & P)
                    bc[f"{kind}_fp"] += len(P - G)
                    bc[f"{kind}_fn"] += len(G - P)
                    for i in G | P:
                        per_label[i]["tp"] += i in G and i in P
                        per_label[i]["fp"] += i in P and i not in G
                        per_label[i]["fn"] += i in G and i not in P
            else:
                G, P = collections.Counter(_s3_key(gr)), collections.Counter(_s3_key(pr))
                bc["norm_tp"] += sum((G & P).values())
                bc["norm_fp"] += sum((P - G).values())
                bc["norm_fn"] += sum((G - P).values())
                has_g, has_p = bool(gr.get("norms")), bool(pr.get("norms"))
                bc["has_tp"] += has_g and has_p
                bc["has_fp"] += has_p and not has_g
                bc["has_fn"] += has_g and not has_p
                bc["count_exact"] += len(gr.get("norms", [])) == len(pr.get("norms", []))
        by_book[b] = bc
        tot += bc
    res = {"agent": agent, "model": against or "pilot (card model)", "sentences": tot["sentences"],
           "unlabelled": tot["unlabelled"]}
    if agent == "S2":
        res["themes"] = _prf(tot["themes_tp"], tot["themes_fp"], tot["themes_fn"])
        res["topics"] = _prf(tot["topics_tp"], tot["topics_fp"], tot["topics_fn"])
        res["by_book_theme_f1"] = {b: _prf(c["themes_tp"], c["themes_fp"], c["themes_fn"])["f1"] for b, c in by_book.items()}
        rows = [(i, labels.get(i, i), _prf(c["tp"], c["fp"], c["fn"])) for i, c in per_label.items()
                if c["tp"] + c["fn"] >= 5]
        res["worst_labels"] = [(i, lbl, m["f1"], m["tp"] + m["fn"]) for i, lbl, m in sorted(rows, key=lambda x: x[2]["f1"])[:10]]
    else:
        res["norm_modalities"] = _prf(tot["norm_tp"], tot["norm_fp"], tot["norm_fn"])
        res["has_norm"] = _prf(tot["has_tp"], tot["has_fp"], tot["has_fn"])
        res["norm_count_exact"] = round(tot["count_exact"] / tot["sentences"], 3) if tot["sentences"] else 0
        res["by_book_norm_f1"] = {b: _prf(c["norm_tp"], c["norm_fp"], c["norm_fn"])["f1"] for b, c in by_book.items()}
    (g / f"score_{agent}{'@' + against if against else ''}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res
