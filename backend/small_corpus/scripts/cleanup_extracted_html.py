#!/usr/bin/env python3
"""
Cleanup script for the 14 extracted HTML files from Additional Cases.
- Standardize paragraph numbering: remove leading "N. " from content (we already have [1], [2] in tags)
- Remove orphan paragraph/page numbers in the middle (e.g. " 39. " or " 237. " when they're stray markers)
- Fix common typos
- Does NOT split sentences or paragraphs
"""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
ADDITIONAL_CASES_DIR = BACKEND_DIR / "small_corpus" / "Additional Cases"
EXTRACTED_DIR = BACKEND_DIR / "small_corpus" / "extracted_html"


# SANITIZATION
def sanitize_filename(name: str) -> str:
    stem = name.replace(".html", "").replace(".htm", "")
    stem = re.sub(r"[\s:/\–—-]+", "_", stem)
    stem = re.sub(r'["\'<>|?*]', "", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem + ".html"


# PARAGRAPH CLEANUP
def clean_paragraph_content(text: str) -> str:
    """Clean paragraph text: remove stray numbers, standardize. Never splits."""
    if not text:
        return text

    # 1. Strip leading "N. " at start - source para/page numbers (e.g. "39. In Candler" -> "In Candler")
    text = re.sub(r"^\d{1,4}\.\s+", "", text)

    # 2. Remove orphan " N. " in middle - paragraph markers from quoted judgment text
    # e.g. " . 12. He continued at p. 90" -> " . He continued at p. 90"
    # Only 1-2 digit numbers (para numbers), not page refs like p. 42 or section 237
    # Avoid: p. 42, pp. 42, s. 42 - use negative lookbehind for "p. " "pp. " "s. "
    text = re.sub(
        r"(?<!p\. )(?<!pp\. )(?<!s\. )(?<=[.!?\"'])\s+\d{1,2}\.\s+(?=[A-Z][a-z])",
        " ",
        text,
    )

    # 3. Fix typos
    text = re.sub(r'Reporter"s\s', "Reporter's ", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def process_file(path: Path) -> bool:
    """Process one HTML file. Returns True if changed."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  Error: {e}")
        return False

    # Match <p id="pN" ...>[N] content</p>
    def replace_p(m):
        full = m.group(0)
        prefix = m.group(1)
        num = m.group(2)
        content = m.group(3)
        cleaned = clean_paragraph_content(content)
        return f'{prefix}[{num}] {cleaned}</p>'

    pattern = re.compile(r'(<p id="p(\d+)"[^>]*>)\[\d+\]\s*(.*?)</p>', re.DOTALL)
    new_raw = pattern.sub(replace_p, raw)

    if new_raw != raw:
        path.write_text(new_raw, encoding="utf-8")
        return True
    return False


# MAIN
def main():
    if not ADDITIONAL_CASES_DIR.exists():
        print(f"Additional Cases dir not found: {ADDITIONAL_CASES_DIR}")
        return

    html_files = list(ADDITIONAL_CASES_DIR.glob("*.html")) + list(
        ADDITIONAL_CASES_DIR.glob("*.htm")
    )

    changed = 0
    for src in html_files:
        safe_name = sanitize_filename(src.name)
        out_path = EXTRACTED_DIR / safe_name
        if not out_path.exists():
            print(f"Skipping (no extracted file): {src.name}")
            continue
        print(f"Cleaning: {safe_name} ...", end=" ")
        if process_file(out_path):
            print("OK (updated)")
            changed += 1
        else:
            print("OK (no changes)")

    print(f"\nCleaned {changed} files.")


if __name__ == "__main__":
    main()
