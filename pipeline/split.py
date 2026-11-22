"""Deterministic splitting: book files -> chapters -> paragraphs -> sentences -> windows.

No model touches the text here. Every sentence gets a stable ID: <book>.<chapter:03>.<sentence:04>.
Editorial notes in [square brackets], page markers and running heads are removed and counted,
never analysed.
"""
from __future__ import annotations

import json
import pathlib
import re
from dataclasses import asdict, dataclass, field

SPLIT_VERSION = "0.1.0"
TARGETS_PER_WINDOW = 5
CONTEXT_BEFORE = 4
CONTEXT_AFTER = 2
PARAS_PER_WINDOW = 5
MAX_SENTENCE_WORDS = 80

_PAGE = re.compile(r"^p\. [0-9ivxlc]+$", re.I)
_INLINE_PAGE = re.compile(r"\[fp\. [0-9ivxlc]+\]\s*", re.I)
_NUMBER_LINE = re.compile(r"^(\d+)$")
_NUMBERED = re.compile(r"^(\d+)(?:\.,?|,)\s+(?:(\d+)\.\s+)?(.*)$")  # "256., 257. text" -> ref 256-257
_FRAGMENT = re.compile(r"^[a-zâêîôûāīū]{1,2}$")  # 1-2 lowercase letters split off by the cleaner
_ABBREV = {"mr", "mrs", "dr", "st", "cf", "v", "vv", "p", "pp", "ch", "no", "viz", "i.e", "e.g", "vol", "ed", "tr"}
_SENT_END = re.compile(r"""([.!?]["'”’)\]]*)\s+(?=["'“‘(]?[A-Z0-9])""")


@dataclass
class Sentence:
    id: str
    book: str
    chapter: int
    para: str
    ref: str
    text: str


@dataclass
class Paragraph:
    id: str
    book: str
    chapter: int
    ref: str
    text: str
    sentence_ids: list = field(default_factory=list)


@dataclass
class Chapter:
    id: str
    book: str
    number: int
    title: str
    source_file: str
    sentence_count: int = 0


def expand(pattern: str) -> list[str]:
    """Expand one {03..28} range in a path pattern, keeping zero padding."""
    m = re.search(r"\{(\d+)\.\.(\d+)\}", pattern)
    if not m:
        return [pattern]
    a, b = m.group(1), m.group(2)
    width = len(a)
    return [pattern[: m.start()] + str(i).zfill(width) + pattern[m.end():] for i in range(int(a), int(b) + 1)]


def header_title(path: pathlib.Path) -> str:
    """Title from the '# Collection: Title' line at the top of a corpus-clean file."""
    first = path.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0].strip()
    first = re.sub(r"\s*\|.*$", "", first.lstrip("# "))
    title = first.rsplit(": ", 1)[-1].strip()
    return "" if title.endswith("...") else title


def read_body(path: pathlib.Path) -> list[str]:
    """Return the file's lines after the '=====' header, with Windows line endings removed."""
    lines = path.read_text(encoding="utf-8", errors="replace").replace("\r", "").split("\n")
    for i, line in enumerate(lines[:12]):
        if line.startswith("=" * 20):
            return lines[i + 1:]
    return lines


def clean_lines(lines: list[str], drop: list[re.Pattern], stats: dict) -> list[str]:
    """Remove notes in [brackets], page markers and dropped lines. Glue 1-2 letter fragments."""
    out: list[str] = []
    in_note = False
    glue_next = False
    for raw in lines:
        line = _INLINE_PAGE.sub("", raw).strip()
        if not line:
            continue
        if in_note:
            stats["note_lines"] += 1
            if line.endswith("]"):
                in_note = False
            continue
        if line.startswith("["):
            stats["note_lines"] += 1
            in_note = not line.endswith("]")
            continue
        if _PAGE.match(line) or any(p.search(line) for p in drop):
            stats["dropped_lines"] += 1
            continue
        if _FRAGMENT.match(line) and out:
            out[-1] += line
            glue_next = True
            stats["glued_fragments"] += 1
            continue
        if glue_next and out and line[:1].islower():
            out[-1] += line
            glue_next = False
            continue
        glue_next = False
        out.append(line)
    return out


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts, start = [], 0
    for m in _SENT_END.finditer(text):
        end = m.end(1)
        word = re.findall(r"([A-Za-z.]+)\.$", text[start:m.start(1) + 1])
        if word and word[-1].lower().rstrip(".") in _ABBREV:
            continue
        parts.append(text[start:end].strip())
        start = m.end()
    parts.append(text[start:].strip())
    merged: list[str] = []
    for p in parts:
        if merged and len(p) < 4:
            merged[-1] += " " + p
        elif p:
            merged.append(p)
    return [piece for s in merged for piece in _split_long(s)]


def _split_long(s: str, limit: int = MAX_SENTENCE_WORDS) -> list[str]:
    """Verse and law texts can run 200+ words without a full stop; cut those at semicolons."""
    if len(s.split()) <= limit:
        return [s]
    out, cur = [], ""
    for piece in re.split(r"(?<=;)\s+", s):
        if cur and len((cur + " " + piece).split()) > limit:
            out.append(cur)
            cur = piece
        else:
            cur = (cur + " " + piece).strip()
    if cur:
        out.append(cur)
    return out


def _paragraphs_by_shape(lines: list[str]) -> list[str]:
    """Group hard-wrapped lines into paragraphs: a short line ending a sentence closes a paragraph."""
    paras, cur = [], []
    for line in lines:
        cur.append(line)
        if len(line) < 60 and re.search(r"""[.!?:]["'”’)]*$""", line):
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def _units(lines: list[str], mode: str) -> list[tuple[str, str]]:
    """Return (ref, text) units. ref is the verse/stanza number where the text gives one."""
    if mode == "none":
        return [("", p) for p in _paragraphs_by_shape(lines)]
    units: list[tuple[str, list[str]]] = []
    for line in lines:
        if mode == "number_line" and _NUMBER_LINE.match(line):
            units.append((line, []))
            continue
        m = _NUMBERED.match(line) if mode == "numbered" else None
        if m:
            ref = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
            units.append((ref, [m.group(3)]))
            continue
        if not units:
            units.append(("", []))
        units[-1][1].append(line)
    return [(ref, " ".join(ls)) for ref, ls in units if ls]


def split_book(book: dict, corpus_root: pathlib.Path) -> dict:
    """Split one book into chapters, paragraphs, sentences. Returns dicts ready for JSONL."""
    bid = book["id"]
    drop = [re.compile(p) for p in book.get("drop", [])]
    start_at = re.compile(book["start_at"]) if book.get("start_at") else None
    stats = {"files": 0, "missing_files": [], "note_lines": 0, "dropped_lines": 0, "glued_fragments": 0,
             "skipped_intro_lines": 0}
    files = [f for pat in book["files"] for f in expand(pat)]

    # 1. Collect (chapter_title, source_file, lines) blocks.
    blocks: list[tuple[str, str, list[str]]] = []
    for rel in files:
        path = corpus_root / rel
        if not path.exists():
            stats["missing_files"].append(rel)
            continue
        stats["files"] += 1
        lines = read_body(path)
        if start_at:
            idx = next((i for i, l in enumerate(lines) if start_at.search(l.strip())), None)
            if idx is None:
                stats["missing_files"].append(rel + " (start_at not found)")
                continue
            stats["skipped_intro_lines"] += sum(1 for l in lines[:idx] if l.strip())
            lines = lines[idx:]
        lines = clean_lines(lines, drop, stats)
        if book.get("chapters", "file") == "number_line":
            cur_title, cur = None, []
            for line in lines:
                if _NUMBER_LINE.match(line):
                    if cur_title is not None and cur:
                        blocks.append((cur_title, rel, cur))
                    cur_title, cur = line, []
                elif cur_title is not None:
                    cur.append(line)
            if cur_title is not None and cur:
                blocks.append((cur_title, rel, cur))
        else:
            title = ""
            if book.get("title_line") and lines:
                title, lines = lines[0], lines[1:]
            blocks.append((title or header_title(path) or pathlib.Path(rel).stem, rel, lines))

    # 2. Paragraphs and sentences with stable IDs.
    chapters, paragraphs, sentences = [], [], []
    for cnum, (title, rel, lines) in enumerate(blocks, start=1):
        ch = Chapter(id=f"{bid}.{cnum:03d}", book=bid, number=cnum, title=title, source_file=rel)
        s_no = 0
        for p_no, (ref, text) in enumerate(_units(lines, book.get("units", "none")), start=1):
            para = Paragraph(id=f"{bid}.{cnum:03d}.p{p_no:04d}", book=bid, chapter=cnum,
                             ref=ref, text=re.sub(r"\s+", " ", text).strip())
            for st in split_sentences(text):
                s_no += 1
                s = Sentence(id=f"{bid}.{cnum:03d}.{s_no:04d}", book=bid, chapter=cnum,
                             para=para.id, ref=ref, text=st)
                sentences.append(s)
                para.sentence_ids.append(s.id)
            if para.sentence_ids:
                paragraphs.append(para)
        ch.sentence_count = s_no
        if s_no:
            chapters.append(ch)
    return {"chapters": [asdict(c) for c in chapters], "paragraphs": [asdict(p) for p in paragraphs],
            "sentences": [asdict(s) for s in sentences], "stats": stats}


def windows(units: list[dict], per: int, before: int, after: int, kind: str) -> list[dict]:
    """Cut units (sentences or paragraphs) into windows of `per` targets, never crossing a chapter."""
    out = []
    by_ch: dict[int, list[dict]] = {}
    for u in units:
        by_ch.setdefault(u["chapter"], []).append(u)
    for ch, us in by_ch.items():
        for w_no, i in enumerate(range(0, len(us), per), start=1):
            tg = us[i:i + per]
            out.append({
                "id": f"{tg[0]['book']}.{ch:03d}.{kind}{w_no:03d}",
                "book": tg[0]["book"], "chapter": ch, "kind": kind,
                "targets": [{"id": u["id"], "text": u["text"]} for u in tg],
                "context_before": [{"id": u["id"], "text": u["text"]} for u in us[max(0, i - before):i]],
                "context_after": [{"id": u["id"], "text": u["text"]} for u in us[i + per:i + per + after]],
            })
    return out


def write_jsonl(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_split(cfg: dict, only: str | None = None) -> list[dict]:
    root = pathlib.Path(cfg["corpus_root"])
    out = pathlib.Path(cfg["out_dir"])
    summary = []
    for book in cfg["books"]:
        if only and book["id"] != only:
            continue
        res = split_book(book, root)
        d = out / book["id"]
        write_jsonl(d / "chapters.jsonl", res["chapters"])
        write_jsonl(d / "paragraphs.jsonl", res["paragraphs"])
        write_jsonl(d / "sentences.jsonl", res["sentences"])
        write_jsonl(d / "windows_sentence.jsonl",
                    windows(res["sentences"], TARGETS_PER_WINDOW, CONTEXT_BEFORE, CONTEXT_AFTER, "w"))
        write_jsonl(d / "windows_paragraph.jsonl",
                    windows(res["paragraphs"], PARAS_PER_WINDOW, 1, 0, "pw"))
        meta = {"book": book["id"], "title": book["title"], "tradition": book["tradition"],
                "split_version": SPLIT_VERSION, "chapters": len(res["chapters"]),
                "paragraphs": len(res["paragraphs"]), "sentences": len(res["sentences"]),
                "words": sum(len(s["text"].split()) for s in res["sentences"]), **res["stats"]}
        (d / "book.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        summary.append(meta)
    return summary
