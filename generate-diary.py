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

Only files named exactly YYYY-MM.md (e.g. 2003-03.md) under the input dir are used.
Other names (e.g. "TODO 2002-06.md", "2009 Ethiopia.md") are ignored, and the script
stops if any of the 12 months is missing.
"""

import argparse
import calendar
import re
import subprocess
from pathlib import Path


def collect_files(root: Path, year: str) -> list[Path]:
    """Only files named exactly YYYY-MM.md (MM = 01-12), in month order.

    Exits if any of the 12 months is missing or duplicated.
    """
    pattern = re.compile(rf"{re.escape(year)}-(0[1-9]|1[0-2])")
    by_month: dict[int, list[Path]] = {}
    for p in root.rglob("*.md"):
        m = pattern.fullmatch(p.stem)
        if m:
            by_month.setdefault(int(m.group(1)), []).append(p)

    missing = [calendar.month_name[m] for m in range(1, 13) if m not in by_month]
    if missing:
        raise SystemExit(f"Error: {year} is incomplete - missing {len(missing)} month(s): "
                         + ", ".join(missing))
    dupes = {m: ps for m, ps in by_month.items() if len(ps) > 1}
    if dupes:
        lines = [f"  {calendar.month_name[m]}: " + ", ".join(map(str, ps)) for m, ps in dupes.items()]
        raise SystemExit(f"Error: duplicate files for {year}:\n" + "\n".join(lines))
    return [by_month[m][0] for m in range(1, 13)]


def title_for(p: Path, year: str) -> str:
    return f"{calendar.month_name[int(p.stem.split('-')[1])]} {year}"


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
        # month title spans the page; the days flow in 2 columns beneath it
        parts.append(f"\n# {title_for(f, args.year)}\n\n`\\startcols`{{=latex}}\n\n"
                     + clean(f.read_text(encoding="utf-8"))
                     + "\n\n`\\stopcols`{=latex}\n")
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
    print_sequence(booklet)


def page_count(pdf: Path) -> int:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, flags=re.MULTILINE).group(1))


def print_sequence(booklet: Path):
    """Manual duplex: each PDF page is one A4 side; odd = front, even = back of the same sheet."""
    n = page_count(booklet)
    odd = list(range(1, n + 1, 2))
    even = list(range(2, n + 1, 2))
    fmt = lambda pages: ",".join(map(str, pages))
    print(f"\nPrinting ({n} sides = {n // 2} sheets, A4 landscape):")
    print(f"  1. Print fronts (odd pages):   {fmt(odd)}")
    print( "  2. Put the printed stack back in the tray, blank side to be printed")
    print(f"  3. Print backs (even pages):   {fmt(even)}")
    print(f"     If the sheets come out in the wrong order, use: {fmt(even[::-1])}")
    print( "  4. Fold the stack in half and staple the spine.")
    print( "  Tip: test with sheet 1 first (pages 1 then 2) to check back-side orientation.")


if __name__ == "__main__":
    main()
