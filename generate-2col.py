#!/usr/bin/env python3
"""
Usage:
    python generate.py <input_dir> <output_name>

Example:
    python generate.py ~/notes/deep-learning deep-learning
    → produces ./output/deep-learning.md and ./output/deep-learning.pdf
"""

import argparse
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Convert a folder of Markdown files to a PDF.")
    parser.add_argument("input_dir", help="Directory containing .md files")
    parser.add_argument("output_name", help="Output filename stem (e.g. 'deep-learning')")
    args = parser.parse_args()

    src = Path(args.input_dir).expanduser().resolve()
    if not src.is_dir():
        raise SystemExit(f"Error: input directory not found: {src}")

    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_md = out_dir / f"{args.output_name}.md"
    out_pdf = out_dir / f"{args.output_name}.pdf"


    # ============================================================
    # 1. Combine Markdown files
    # ============================================================

    files = sorted(src.glob("*.md"))
    if not files:
        raise SystemExit(f"Error: no .md files found in {src}")

    print(f"Found {len(files)} file(s) in {src}")

    combined = []
    for f in files:
        combined.append("\n\\newpage\n")
        combined.append(f.read_text(encoding="utf-8"))

    combined_text = "\n".join(combined)

    # ============================================================
    # 2. Sanitize
    # ============================================================

    out_md.write_text(combined_text, encoding="utf-8")

    # ============================================================
    # 3. Run Pandoc
    # ============================================================

    subprocess.run(
        [
            "pandoc",
            str(out_md),
            "-V", "geometry:margin=0.75in",
            "-V", "mainfont=DejaVu Serif",
            "-V", "monofont=DejaVu Sans Mono",
            "-V", "documentclass=extarticle",
            "-V", "fontsize=8pt",

       "-o", str(out_pdf),
        ],
        check=True,
    )

    print(f"PDF generated successfully: {out_pdf}")


if __name__ == "__main__":
    main()
