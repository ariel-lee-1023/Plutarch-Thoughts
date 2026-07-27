#!/usr/bin/env python3
"""
Optimize formatting of existing Markdown under content/PT/.

Rules:
  - drop obvious PDF TOC leftovers (leader dots, pure page numbers)
  - join / reflow paragraphs
  - balance length for mobile (~420 chars, split only at sentence ends)
  - never invent mid-sentence headings
"""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

CONTENT_ROOT = Path("content") / "PT"

SUBFOLDERS = [
    "Works",
]

CJK = r"[\u2e80-\u2eff\u2f00-\u2fdf\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]"

HAS_LEADER_DOTS = re.compile(r"[.…·•]{4,}")
JUNK = re.compile(r"^(\d{1,4}|[·•—–\-…]{1,8}|#{1,6})$")
PAGE_GLUE = re.compile(r"^\d{1,3}[A-Za-z\u4e00-\u9fff“\"「]")
EXISTING_HEADING = re.compile(r"^#{1,6}\s+")
TRAILING_HASH = re.compile(r"#{1,6}\s*$")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fix_spacing(text: str) -> str:
    text = re.sub(rf"({CJK})[ \t]+(?={CJK})", r"\1", text)
    punct = r"[，。！？；：、“”‘’（）【】《》〈〉「」『』、,.!?;:]"
    text = re.sub(rf"({CJK})[ \t]+({punct})", r"\1\2", text)
    text = re.sub(rf"({punct})[ \t]+({CJK})", r"\1\2", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def is_toc_line(ln: str) -> bool:
    if not ln:
        return False
    if JUNK.match(ln):
        return True
    if HAS_LEADER_DOTS.search(ln):
        return True
    if PAGE_GLUE.match(ln):
        return True
    return False


def reflow_paragraphs(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    raw_lines = [ln.rstrip() for ln in text.split("\n")]

    filtered: list[str] = []
    for ln in raw_lines:
        s = ln.strip()
        s = TRAILING_HASH.sub("", s).strip()
        if is_toc_line(s):
            continue
        if TRAILING_HASH.search(ln.strip()):
            filtered.append(TRAILING_HASH.sub("", ln.strip()).rstrip())
        else:
            filtered.append(ln)

    terminal = re.compile(r"[.。！？；…」』”’]$")
    force_start = re.compile(
        r"^(Chapter\s+[IVXLC\d]+|CHAPTER\s+[IVXLC\d]+|"
        r"Book\s+[IVXLC\d]+|BOOK\s+[IVXLC\d]+|"
        r"Life of |The Life of |"
        r"[0-9]+\.\s|[IVX]+\.\s)"
    )

    paras: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        p = " ".join(buf)
        p = re.sub(r" {2,}", " ", p).strip()
        p = TRAILING_HASH.sub("", p).strip()
        if p:
            paras.append(p)
        buf.clear()

    for ln in filtered:
        ln = ln.strip()
        if EXISTING_HEADING.match(ln):
            ln = EXISTING_HEADING.sub("", ln).strip()
        ln = TRAILING_HASH.sub("", ln).strip()
        if not ln:
            if buf and terminal.search(buf[-1]):
                flush()
            continue
        if is_toc_line(ln):
            continue

        is_force = bool(force_start.match(ln))
        if buf and (is_force or terminal.search(buf[-1])):
            flush()
        if is_force and len(ln) < 80:
            if buf:
                flush()
            paras.append(ln)
            continue
        buf.append(ln)
    flush()

    balanced: list[str] = []
    max_len = 420
    for p in paras:
        if len(p) <= max_len:
            balanced.append(p)
            continue
        parts = re.split(r"(?<=[.。！？；…])", p)
        current = ""
        for part in parts:
            if not part.strip():
                continue
            if current and len(current) + len(part) > max_len:
                balanced.append(current.strip())
                current = part
            else:
                current += part
        if current.strip():
            balanced.append(current.strip())

    final: list[str] = []
    for p in balanced:
        if force_start.match(p) and len(p) < 80:
            if final and final[-1] != "":
                final.append("")
            final.append(f"## {p}")
            final.append("")
            continue
        final.append(p)

    text = "\n\n".join(x for x in final if x is not None)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_layout(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = fix_spacing(text)
    text = reflow_paragraphs(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_header_body(full: str) -> tuple[str, str]:
    lines = full.splitlines(keepends=True)
    if not lines:
        return "", full
    header_end = 0
    in_meta = False
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("#") and not stripped.startswith("## "):
            header_end = i + 1
            continue
        if stripped.startswith(">"):
            in_meta = True
            header_end = i + 1
            continue
        if in_meta and not stripped:
            header_end = i + 1
            continue
        if in_meta and stripped:
            break
        if not stripped:
            header_end = i + 1
            continue
        break
    header = "".join(lines[:header_end]).rstrip() + "\n\n"
    body = "".join(lines[header_end:]).strip()
    return header, body


def optimize_one(md_path: Path) -> bool:
    try:
        original = md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  READ FAIL {md_path}: {e}")
        return False
    header, body = split_header_body(original)
    if not body or len(body) < 20:
        return False
    cleaned_body = clean_layout(body)
    new_full = header + cleaned_body + "\n"
    if content_hash(original) == content_hash(new_full):
        return False
    md_path.write_text(new_full, encoding="utf-8")
    print(f"  OPTIMIZED {md_path.relative_to(CONTENT_ROOT.parent)}")
    return True


def main() -> int:
    changed = 0
    total = 0
    for sub in SUBFOLDERS:
        src_dir = CONTENT_ROOT / sub
        if not src_dir.is_dir():
            print(f"(no folder) {src_dir}")
            continue
        mds = sorted(src_dir.glob("*.md"))
        if not mds:
            print(f"(empty)    {src_dir}")
            continue
        print(f"\n=== {sub} ({len(mds)} file(s)) ===")
        for md in mds:
            total += 1
            if optimize_one(md):
                changed += 1
    print(f"\nDone. scanned={total}  optimized={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
