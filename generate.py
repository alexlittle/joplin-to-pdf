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


def fix_unicode_corruption(text: str) -> str:
    # Remove keycap emoji sequences (e.g. 4️⃣ → 4)
    text = re.sub(r'\ufe0f\u20e3', '', text)
    text = re.sub(r'\ufe0f', '', text)

    # Replace known symbols with LaTeX equivalents BEFORE stripping
    text = text.replace('\u2705', r'\checkmark{}')  # ✅
    text = text.replace('\u2713', r'\checkmark{}')  # ✓
    text = text.replace('\u274c', r'$\times$')      # ❌
    text = text.replace('\u2248', r'$\approx$')     # ≈
    text = text.replace('\u2260', r'$\neq$')        # ≠
    text = text.replace('\u2264', r'$\leq$')        # ≤
    text = text.replace('\u2261', r'$\equiv$')      # ≡
    text = text.replace('\u2194', r'$\leftrightarrow$')  # ↔
    text = text.replace('\u2192', r'$\rightarrow$') # →

    # Replace emoji at start of line with markdown bullet
    text = re.sub(r'^[\U0001F000-\U0001FFFF\u2600-\u26FF\u2700-\u27BF]+\s+', '- ', text, flags=re.MULTILINE)

    # Strip any remaining non-BMP characters xelatex can't handle
    text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)

    return text


def fix_latex_commands(text: str) -> str:
    """Fix non-standard LaTeX command names and spacing commands."""
    text = text.replace(r'\argmin', r'\arg\min')
    text = text.replace(r'\argmax', r'\arg\max')
    return text


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

    sanitized = fix_unicode_corruption(combined_text)
    sanitized = fix_latex_commands(sanitized)

    #out_md.with_suffix(".md.bak").write_text(combined_text, encoding="utf-8")
    out_md.write_text(sanitized, encoding="utf-8")

    # ============================================================
    # 3. Run Pandoc
    # ============================================================

    subprocess.run(
        [
            "pandoc",
            str(out_md),
            "--toc",
            "--toc-depth=2",
            "--number-sections",
            "--pdf-engine=xelatex",
            "--from", "markdown+tex_math_dollars",
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
