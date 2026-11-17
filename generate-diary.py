#!/usr/bin/env python3
"""
Build one annual diary as a print-ready A4 booklet (A5 pages, 2-up, saddle-stitch).

Usage:
    python generate-diary.py <year> [--input input/Diaries]

Example:
    python generate-diary.py 2003
    -> ./output/diary-2003.md
       ./output/diary-2003-a5.pdf       (reading copy, A5 pages in order)
       ./output/diary-2003-booklet.pdf  (A4 landscape, print double-sided
                                         see README note, fold & staple)

Any .md file under the input dir whose name contains <year> (e.g. 2003-03.md,
"TODO 2002-06.md", "2009 Ethiopia.md") is included, sorted by filename.
"""

import argparse
import calendar
import re
import subprocess
from pathlib import Path


def collect_files(root: Path, year: str) -> list[Path]:
    files = [p for p in root.rglob("*.md") if year in p.stem]
    # monthly files (YYYY-MM) first in order, then anything else
    def key(p: Path):
        m = re.search(rf"{year}-(\d\d)", p.stem)
        return (0, int(m.group(1)), p.name) if m else (1, 0, p.name)
    return sorted(files, key=key)


def title_for(p: Path, year: str) -> str:
    m = re.search(rf"{year}-(\d\d)", p.stem)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{calendar.month_name[int(m.group(1))]} {year}"
    return p.stem


def clean(text: str) -> str:
    # drop empty bullets directly after a day header
    text = re.sub(r"(## .+\n)-\s*(\n|$)", r"\1\n", text)
    # strip emoji variation selectors / non-BMP chars xelatex can't render
    text = re.sub(r"[\ufe0f\u20e3]", "", text)
    text = re.sub(r"[\U0001F000-\U0001FFFF]", "", text)
    # Joplin week separators ("* * *") -> a plain rule
    text = re.sub(r"^\s*\* \* \*\s*$", "\n---\n", text, flags=re.MULTILINE)
    # explicit gap before every day heading (titlesec's own spacing collapses
    # between consecutive headings, so empty days would otherwise bunch up)
    text = re.sub(r"^(## .+)$", r"\\vspace{7pt}\n\n\1", text, flags=re.MULTILINE)
    return text


def main():
    ap = argparse.ArgumentParser(description="Annual diary -> A4 booklet PDF")
    ap.add_argument("year")
    ap.add_argument("--input", default="input/Diaries")
    ap.add_argument("--font", default="Faculty Glyphic")
    ap.add_argument("--size", default="10pt", help="extarticle sizes: 8,9,10,11,12,14pt")
    args = ap.parse_args()

    root = Path(args.input).expanduser().resolve()
    files = collect_files(root, args.year)
    if not files:
        raise SystemExit(f"No .md files for {args.year} under {root}")
    print(f"Found {len(files)} file(s) for {args.year}")

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    stem = f"diary-{args.year}"
    out_md, a5, booklet = (out_dir / f"{stem}.md", out_dir / f"{stem}-a5.pdf",
                           out_dir / f"{stem}-booklet.pdf")

    parts = [f"\\thispagestyle{{empty}}\n\n\\vspace*{{\\fill}}\n\n"
             f"\\begin{{center}}{{\\fontsize{{40}}{{48}}\\selectfont {args.year}}}\\\\[1em]"
             f"{{\\Large Diary}}\\end{{center}}\n\n\\vspace*{{\\fill}}\n\n\\newpage\n"]
    for f in files:
        parts.append(f"\n# {title_for(f, args.year)}\n\n" + clean(f.read_text(encoding="utf-8")))
    out_md.write_text("\n".join(parts), encoding="utf-8")

    # day headings are "##" -> demote via titlesec config in header (section=#, subsection=##)
    subprocess.run([
        "pandoc", str(out_md),
        "--pdf-engine=xelatex",
        "--from", "markdown+raw_tex-implicit_figures-yaml_metadata_block",
        "--include-in-header=diary-header.tex",
        "-V", "documentclass=extarticle",
        "-V", f"fontsize={args.size}",
        "-V", "papersize=a5",
        "-V", "geometry:paperwidth=148mm,paperheight=210mm,top=14mm,bottom=16mm,inner=16mm,outer=11mm",
        "-V", f"mainfont={args.font}", "-V", "mainfontoptions=AutoFakeBold=2",
        "-V", "monofont=DejaVu Sans Mono",
        "-o", str(a5),
    ], check=True)

    # Impose: pads to a multiple of 4, reorders, puts 2 A5 pages per A4 sheet
    subprocess.run(["pdfbook2", "--paper=a4paper", "--no-crop",
                    "-o", "0", "-i", "0", "-t", "0", str(a5)], check=True)
    produced = a5.with_name(a5.stem + "-book.pdf")
    produced.replace(booklet)
    print(f"Reading copy: {a5}\nBooklet:      {booklet}")


if __name__ == "__main__":
    main()
