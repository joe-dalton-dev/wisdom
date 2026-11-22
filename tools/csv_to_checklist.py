"""Render project/checklist.csv as CHECKLIST.md (GitHub task-list format).

Usage: python tools/csv_to_checklist.py project/checklist.csv CHECKLIST.md
"""
import csv
import sys
from itertools import groupby

src, dst = sys.argv[1], sys.argv[2]
with open(src, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

lines = [
    "# Project checklist",
    "",
    "The live copy is the Claude sheet [Wisdom Graph — Phase 0 status](https://claude.ai/artifact/9JucZmoVQVncnq38Y65Grv). "
    "This file is regenerated from `project/checklist.csv`; edit the CSV, not this file.",
    "",
]
for phase, items in groupby(rows, key=lambda r: r["Phase"]):
    lines += [f"## {phase}", ""]
    for r in items:
        box = "x" if r["Status"] == "Done" else " "
        extra = f" *({r['Status']})*" if r["Status"] not in ("Done", "Not started", "Ongoing") else ""
        lines.append(f"- [{box}] **{r['ID']}** {r['Task']} · {r['Owner']}{extra}")
        lines.append(f"    - Done when: {r['Done when']}" + (f" · {r['Notes']}" if r["Notes"] else ""))
    lines.append("")

with open(dst, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"wrote {dst}: {len(rows)} tasks")
