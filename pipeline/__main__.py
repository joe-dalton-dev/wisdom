"""Command line: python -m pipeline <command> [options]

  split     cut the books in the config into sentences, paragraphs and windows (no API calls)
  estimate  show how many calls a run would make and what it should cost
  run       send pending windows to Claude, check the replies and save them
  collect   fetch finished batches (only needed after `run --mode batch` without --wait)
  status    jobs and spend so far, per book and agent
  report    write report.csv per book: each sentence with its labels

Gold set (silver standard: Opus + Sonnet label, Opus adjudicates; see pipeline/gold.py):
  gold-select      pick 50 windows per book
  gold-label       S2 + S3 on them with Opus 5.5 and Sonnet 5.5
  gold-adjudicate  send disagreements to the A1 adjudicator (Opus 5.5)
  gold-collect     fetch finished gold batches (if you ran without --wait)
  gold-finalize    write gold_S2 / gold_S3 per book
  gold-sample      50 gold items as a CSV for a quick human sanity check
  gold-split       freeze a dev/test split of the gold windows (once; IDs go in project/gold_split.json)
  gold-haiku       run the current S2/S3 cards (Haiku) on the gold test windows
  score            score Haiku against the gold set: --agent S2|S3, --split dev|test, --source pilot|gold

Examples (smoke test: one book, themes only, first 10 windows, results in a minute):
  python -m pipeline split
  python -m pipeline estimate --book daodejing --agent S2 --limit 10 --mode sync
  python -m pipeline run --book daodejing --agent S2 --limit 10 --mode sync
  python -m pipeline report --book daodejing
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

from . import gold
from . import report as report_mod
from .assemble import AGENTS
from .runner import Runner, book_ids
from .split import run_split


def load_cfg(path: str) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        sys.exit(f"{p} not found. Copy config/pilot.example.yaml to config/pilot.yaml and set corpus_root.")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["split", "estimate", "run", "collect", "status", "report", "gold-select",
                                        "gold-label", "gold-adjudicate", "gold-collect", "gold-finalize",
                                        "gold-sample", "gold-split", "gold-haiku", "score"])
    ap.add_argument("--config", default="config/pilot.yaml")
    ap.add_argument("--book", action="append", help="book id; repeat for several; default all")
    ap.add_argument("--agent", action="append", choices=list(AGENTS), help="S1-S4; repeat; default all four")
    ap.add_argument("--mode", choices=["batch", "sync"], default="batch",
                    help="batch = half price, results within hours; sync = full price, results in minutes")
    ap.add_argument("--limit", type=int, help="only the first N windows per book (smoke tests)")
    ap.add_argument("--max-usd", type=float, default=2.0,
                    help="hard stop: total spend recorded in the ledger may not pass this (default 2.00)")
    ap.add_argument("--wait", action="store_true", help="batch mode: wait for batches to finish and collect")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--split", choices=["dev", "test"], default="", help="score: only this half of the gold set")
    ap.add_argument("--source", choices=["pilot", "gold"], default="pilot",
                    help="score: pilot = Haiku outputs from the pilot run; gold = outputs of gold-haiku")
    ap.add_argument("--force", action="store_true", help="gold-split: rebuild an existing split")
    a = ap.parse_args(argv)

    cfg = load_cfg(a.config)
    cfg.setdefault("spend_ledgers", [str(gold.gold_dir(cfg) / "ledger.sqlite")])
    books = book_ids(cfg, a.book)
    agents = a.agent or list(AGENTS)

    if a.command == "split":
        cfg_one = {**cfg, "books": [b for b in cfg["books"] if b["id"] in books]}
        for m in run_split(cfg_one):
            warn = f"  MISSING: {m['missing_files']}" if m["missing_files"] else ""
            print(f"{m['book']:<18} {m['chapters']:>3} chapters {m['paragraphs']:>5} paragraphs "
                  f"{m['sentences']:>5} sentences {m['words']:>6} words  (notes removed: {m['note_lines']} lines){warn}")
        return

    if a.command.startswith("gold-") or a.command == "score":
        return gold_command(a, cfg, books)

    runner = Runner(cfg)
    if a.command == "status":
        print(f"{'book':<18} {'agent':<5} {'status':<9} {'windows':>7} {'accepted':>8} {'rejected':>8} {'missing':>7} {'USD':>8}")
        for r in runner.ledger.summary():
            print(f"{r['book']:<18} {r['agent']:<5} {r['status']:<9} {r['n']:>7} {r['acc'] or 0:>8} "
                  f"{r['rej'] or 0:>8} {r['miss'] or 0:>7} {r['usd'] or 0:>8.4f}")
        print(f"\nTotal spent: ${runner.spent():.4f}   Open batches: {len(runner.ledger.open_batches())}")
        return

    if a.command == "report":
        for b in books:
            r = report_mod.build(pathlib.Path(cfg["out_dir"]), b)
            print(f"\n{b}: {r['path']}")
            print(f"  sentences labelled: " + ", ".join(f"{k} {v}/{r['sentences']}" for k, v in sorted(r["covered"].items())))
            if r["top_themes"]:
                print("  top themes: " + ", ".join(f"{lbl} {n}" for _, lbl, n in r["top_themes"]))
            if r["top_topics"]:
                print("  top topics: " + ", ".join(f"{lbl} {n}" for _, lbl, n in r["top_topics"]))
            if r["norms"]:
                print(f"  norms: {r['norms']}")
            if r["social_categories"]:
                print(f"  social categories: {r['social_categories']}")
        return

    if a.command == "collect":
        print(runner.collect(wait=a.wait))
        return

    jobs = runner.plan(agents, books, a.limit)
    send(runner, jobs, a)


def send(runner, jobs, a, windows_for=None):
    """Estimate, check the cap, confirm, then run sync or batch."""
    est = runner.estimate(jobs, a.mode)
    spent = runner.spent()
    print(f"{est['calls']} calls pending ({a.mode} mode). Estimated cost ${est['usd']:.3f} "
          + "(" + ", ".join(f"{k} ${v:.3f}" for k, v in sorted(est["by_agent"].items())) + ")")
    print(f"Spent so far: ${spent:.4f}. Cap for this run: ${a.max_usd:.2f}.")
    if a.command in ("estimate",) or not jobs:
        return
    if spent + est["usd"] > a.max_usd:
        sys.exit(f"Stopped: spent + estimate (${spent + est['usd']:.3f}) is over --max-usd ${a.max_usd:.2f}. "
                 "Raise --max-usd or use --limit.")
    if not a.yes and input("Send them? [y/N] ").strip().lower() != "y":
        return
    if a.mode == "sync":
        res = runner.run_sync(jobs, a.max_usd)
        print(res)
    else:
        ids = runner.submit_batches(jobs)
        print(f"Submitted {len(ids)} batch(es): {', '.join(ids)}")
        if a.wait:
            print(runner.collect(wait=True, windows_for=windows_for))
        else:
            cmd = "gold-collect" if windows_for else "collect"
            print(f"Run `python -m pipeline {cmd} --wait` later to fetch results.")
    print(f"Spent so far: ${runner.spent():.4f}")


def gold_command(a, cfg, books):
    gcfg = gold.gold_cfg(cfg)
    if a.command == "gold-select":
        for b, m in gold.select(cfg).items():
            print(f"{b:<18} {m['windows']:>3} windows {m['sentences']:>4} sentences")
        return
    if a.command == "gold-finalize":
        for b, m in gold.finalize(cfg).items():
            print(f"{b:<18} " + "   ".join(f"{k}: {v['agreed']} agreed, {v['adjudicated']} adjudicated, "
                                          f"{v['unresolved']} unresolved" for k, v in m.items()))
        return
    if a.command == "gold-sample":
        print("Wrote", gold.sample(cfg), "- mark anything that looks wrong and send it back.")
        return
    if a.command == "gold-split":
        for b, m in gold.make_split(cfg, force=a.force).items():
            print(f"{b:<18} dev {m['dev']:>3}   test {m['test']:>3}")
        print(f"Wrote {gold.SPLIT_FILE} - commit it; don't rebuild it.")
        return
    if a.command == "score":
        for ag in (a.agent or ["S2", "S3"]):
            if ag not in ("S2", "S3"):
                continue
            r = gold.score(cfg, ag, split=a.split, source=a.source)
            print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    runner = Runner(gcfg)
    if a.command == "gold-collect":
        print(runner.collect(wait=a.wait, windows_for=gold.windows_for(cfg)))
        return
    if a.command == "gold-label":
        jobs = []
        for model, effort in gold.REF_MODELS:
            jobs += runner.plan(gold.GOLD_AGENTS, books, None, model=model, effort=effort)
        send(runner, jobs, a, gold.windows_for(cfg))
        return
    if a.command == "gold-haiku":
        ags = [x for x in (a.agent or gold.GOLD_AGENTS) if x in gold.GOLD_AGENTS]
        items = [(ag, b, w) for ag in ags for b in books for w in gold.test_windows(cfg, b)]
        send(runner, runner.plan_windows(items), a, gold.windows_for(cfg))
        return
    if a.command == "gold-adjudicate":
        for b, s in gold.disputes(cfg).items():
            print(f"{b:<18} {s}")
        wf = gold.windows_for(cfg)
        items = [(adj, b, w) for adj in gold.DISPUTE_FILES for b in books for w in wf(adj, b).values()]
        send(runner, runner.plan_windows(items), a, wf)
        return


if __name__ == "__main__":
    main()
