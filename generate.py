from pathlib import Path
import subprocess
import re


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
    """Fix non-standard LaTeX command names."""
    text = text.replace(r'\argmin', r'\arg\min')
    text = text.replace(r'\argmax', r'\arg\max')
    return text


# ============================================================
# Configuration
# ============================================================

SRC = Path("/home/alex/Downloads/temp/Masters/S2 - Deep Learning/revision")
OUT_MD = Path("./output/deep-learning.md")
OUT_PDF = Path("./output/deep-learning.pdf")

OUT_MD.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. Combine Markdown files
# ============================================================

files = sorted(SRC.glob("*.md"))

combined = []

for f in files:
    combined.append(f.read_text(encoding="utf-8"))
    combined.append("\n\\newpage\n")

combined_text = "\n".join(combined)

# ============================================================
# 2. Sanitize
# ============================================================

sanitized = fix_unicode_corruption(combined_text)
sanitized = fix_latex_commands(sanitized)

OUT_MD.with_suffix(".md.bak").write_text(combined_text, encoding="utf-8")
OUT_MD.write_text(sanitized, encoding="utf-8")

# ============================================================
# 3. Run Pandoc
# ============================================================

subprocess.run(
    [
        "pandoc",
        str(OUT_MD),
        "--toc",
        "--toc-depth=2",
        "--number-sections",
        "--pdf-engine=xelatex",
        "--from", "markdown+tex_math_dollars",
        "-V", "geometry:margin=1in",
        "-o",
        str(OUT_PDF),
    ],
    check=True,
)

print("PDF generated successfully:", OUT_PDF)
