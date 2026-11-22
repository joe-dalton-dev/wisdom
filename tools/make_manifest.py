"""Build or check the corpus manifest: one row per file with its size and SHA-256.

Runners use the manifest to confirm they have exactly the right copy of a book.
Standard library only, so it runs with any Python 3.9+ on Windows, macOS or Linux.

Build (maintainer, once per corpus change):
    python tools/make_manifest.py build "C:/Users/joseph dalton/Documents/ClaudeMemory/SacredTexts/corpus-books" books_manifest.csv

Check a downloaded copy against a manifest (anyone):
    python tools/make_manifest.py check "D:/downloads/corpus-books" books_manifest.csv
"""
import csv
import hashlib
import pathlib
import sys

FIELDS = ["path", "bytes", "sha256"]
SKIP = {"desktop.ini", "thumbs.db", ".ds_store"}


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files(root: pathlib.Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name.lower() not in SKIP:
            yield p


def build(root: pathlib.Path, out: pathlib.Path) -> None:
    rows = []
    for i, p in enumerate(files(root), 1):
        rows.append({"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)})
        if i % 200 == 0:
            print(f"  hashed {i} files...")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    total = sum(r["bytes"] for r in rows)
    print(f"wrote {out}: {len(rows)} files, {total / 1e6:.1f} MB")


def check(root: pathlib.Path, manifest: pathlib.Path) -> int:
    with manifest.open(newline="", encoding="utf-8") as f:
        expected = {r["path"]: r for r in csv.DictReader(f)}
    seen, bad = set(), []
    for p in files(root):
        rel = p.relative_to(root).as_posix()
        seen.add(rel)
        exp = expected.get(rel)
        if exp is None:
            bad.append(f"extra file (not in manifest): {rel}")
        elif int(exp["bytes"]) != p.stat().st_size or exp["sha256"] != sha256(p):
            bad.append(f"changed: {rel}")
    bad += [f"missing: {rel}" for rel in sorted(set(expected) - seen)]
    for line in bad:
        print(line)
    print(f"{len(seen)} files checked against {len(expected)} in manifest; {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in {"build", "check"}:
        print(__doc__)
        sys.exit(2)
    mode, root, manifest = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    if not root.is_dir():
        sys.exit(f"not a folder: {root}")
    if mode == "build":
        build(root, manifest)
    else:
        sys.exit(check(root, manifest))
