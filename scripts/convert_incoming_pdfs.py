#!/usr/bin/env python3
"""
Process files dropped into incoming/<book>/:

  - *.pdf / *.PDF  → convert with PyMuPDF + layout cleanup → content/PT/<book>/
  - *.md           → move as-is to content/PT/<book>/

Book folders (matching major works):
  - Parallel-Lives
  - Moralia

Design goals (shared with optimize_formatting.py):
  - drop obvious PDF TOC (leader dots, pure page-number lines)
  - join mid-sentence lines across page breaks
  - balance paragraph length for mobile (~420 chars, split only at sentence ends)
  - never invent mid-sentence headings
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF

INCOMING_ROOT = Path("incoming")
CONTENT_ROOT = Path("content") / "PT"

SUBFOLDERS = [
    "Parallel-Lives",
    "Moralia",
]

# Keep CJK pattern for mixed-language PDFs; harmless for pure Latin text
CJK = r"[\u2e80-\u2eff\u2f00-\u2fdf\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]"

HAS_LEADER_DOTS = re.compile(r"[.…·•]{4,}")
JUNK = re.compile(r"^(\d{1,4}|[·•—–\-…]{1,8})$")
PAGE_GLUE = re.compile(r"^\d{1,3}[A-Za-z\u4e00-\u9fff“\"「]")
EXISTING_HEADING = re.compile(r"^#{1,6}\s+")


def safe_name(name: str) -> str:
    name = name or "untitled"
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\-\.]+", "_", name, flags=re.UNICODE)
    return cleaned.strip("_ ")[:120] or "untitled"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def extract_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    parts: list[str] = []
    for page in doc:
        t = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_DEHYPHENATE)
        parts.append(t)
    doc.close()
    return "\n".join(parts)


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
        if is_toc_line(ln.strip()):
            continue
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
        if p:
            paras.append(p)
        buf.clear()

    for ln in filtered:
        ln = ln.strip()
        if EXISTING_HEADING.match(ln):
            ln = EXISTING_HEADING.sub("", ln).strip()
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


def convert_one(pdf_path: Path, out_dir: Path) -> bool:
    try:
        raw = extract_text(pdf_path)
        text = clean_layout(raw)
    except Exception as e:
        print(f"  CONVERT FAIL {pdf_path.name}: {e}")
        return False

    if not text or len(text) < 20:
        print(f"  EMPTY RESULT {pdf_path.name}")
        return False

    base = safe_name(pdf_path.stem)
    out_path = out_dir / f"{base}.md"

    header = (
        f"# {pdf_path.stem}\n\n"
        f"> original PDF: `{pdf_path.name}`  \n"
        f"> folder: `PT/{out_dir.name}`  \n"
        f"> converted with PyMuPDF + layout reflow + mobile balancing\n\n"
    )
    full = header + text

    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        if content_hash(existing) == content_hash(full):
            print(f"  SKIP (unchanged) {out_path.relative_to(CONTENT_ROOT.parent)}")
            pdf_path.unlink(missing_ok=True)
            return False

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full, encoding="utf-8")
    print(f"  WROTE     {out_path.relative_to(CONTENT_ROOT.parent)}")
    pdf_path.unlink(missing_ok=True)
    print(f"  DELETED   {pdf_path}")
    return True


def move_md_one(md_path: Path, out_dir: Path) -> bool:
    """Move an already-prepared .md from incoming/ to content/PT/..."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / md_path.name

    if out_path.exists():
        try:
            existing = out_path.read_text(encoding="utf-8")
            incoming = md_path.read_text(encoding="utf-8")
            if content_hash(existing) == content_hash(incoming):
                print(f"  SKIP (unchanged) {out_path.relative_to(CONTENT_ROOT.parent)}")
                md_path.unlink(missing_ok=True)
                return False
        except Exception:
            pass

    shutil.move(str(md_path), str(out_path))
    print(f"  MOVED     {out_path.relative_to(CONTENT_ROOT.parent)}")
    return True


def main() -> int:
    changed = 0
    total_files = 0

    for sub in SUBFOLDERS:
        src_dir = INCOMING_ROOT / sub
        if not src_dir.is_dir():
            print(f"(no folder) {src_dir}")
            continue

        out_dir = CONTENT_ROOT / sub

        # 1. PDFs → convert
        pdfs = sorted(src_dir.glob("*.pdf")) + sorted(src_dir.glob("*.PDF"))
        if pdfs:
            print(f"\n=== {sub} PDFs ({len(pdfs)}) ===")
            for pdf in pdfs:
                total_files += 1
                if convert_one(pdf, out_dir):
                    changed += 1

        # 2. Markdown → move as-is
        mds = sorted(src_dir.glob("*.md"))
        if mds:
            print(f"\n=== {sub} Markdown ({len(mds)}) ===")
            for md in mds:
                total_files += 1
                if move_md_one(md, out_dir):
                    changed += 1

        if not pdfs and not mds:
            print(f"(empty)    {src_dir}")

    print(f"\nDone. scanned={total_files}  written/moved={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
