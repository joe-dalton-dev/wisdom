"""Command line: python -m pipeline <command> [options]

  split     cut the books in the config into sentences, paragraphs and windows (no API calls)
  estimate  show how many calls a run would make and what it should cost
  run       send pending windows to Claude, check the replies and save them
  collect   fetch finished batches (only needed after `run --mode batch` without --wait)
  status    jobs and spend so far, per book and agent
  report    write report.csv per book: each sentence with its labels

Examples (smoke test: one book, themes only, first 10 windows, results in a minute):
  python -m pipeline split
  python -m pipeline estimate --book daodejing --agent S2 --limit 10 --mode sync
  python -m pipeline run --book daodejing --agent S2 --limit 10 --mode sync
  python -m pipeline report --book daodejing
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

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
    ap.add_argument("command", choices=["split", "estimate", "run", "collect", "status", "report"])
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
    a = ap.parse_args(argv)

    cfg = load_cfg(a.config)
    books = book_ids(cfg, a.book)
    agents = a.agent or list(AGENTS)

    if a.command == "split":
        cfg_one = {**cfg, "books": [b for b in cfg["books"] if b["id"] in books]}
        for m in run_split(cfg_one):
            warn = f"  MISSING: {m['missing_files']}" if m["missing_files"] else ""
            print(f"{m['book']:<18} {m['chapters']:>3} chapters {m['paragraphs']:>5} paragraphs "
                  f"{m['sentences']:>5} sentences {m['words']:>6} words  (notes removed: {m['note_lines']} lines){warn}")
        return

    runner = Runner(cfg)
    if a.command == "status":
        print(f"{'book':<18} {'agent':<5} {'status':<9} {'windows':>7} {'accepted':>8} {'rejected':>8} {'missing':>7} {'USD':>8}")
        for r in runner.ledger.summary():
            print(f"{r['book']:<18} {r['agent']:<5} {r['status']:<9} {r['n']:>7} {r['acc'] or 0:>8} "
                  f"{r['rej'] or 0:>8} {r['miss'] or 0:>7} {r['usd'] or 0:>8.4f}")
        print(f"\nTotal spent: ${runner.ledger.spent():.4f}   Open batches: {len(runner.ledger.open_batches())}")
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
    est = runner.estimate(jobs, a.mode)
    spent = runner.ledger.spent()
    print(f"{est['calls']} calls pending ({a.mode} mode). Estimated cost ${est['usd']:.3f} "
          + "(" + ", ".join(f"{k} ${v:.3f}" for k, v in sorted(est["by_agent"].items())) + ")")
    print(f"Spent so far: ${spent:.4f}. Cap for this run: ${a.max_usd:.2f}.")
    if a.command == "estimate" or not jobs:
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
            print(runner.collect(wait=True))
        else:
            print("Run `python -m pipeline collect` later (or now with --wait) to fetch results.")
    print(f"Spent so far: ${runner.ledger.spent():.4f}")


if __name__ == "__main__":
    main()
