#!/usr/bin/env python3
"""
Extract case metadata (date, judges, short name) from extracted HTML files.
Used by the context-tag and case-summary ingestion pipeline.
Outputs a JSON file: case_metadata.json
"""

import json
import re
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install beautifulsoup4: pip install beautifulsoup4")
    exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
EXTRACTED_DIR = BACKEND_DIR / "small_corpus" / "extracted_html"
OUTPUT_PATH = BACKEND_DIR / "case_metadata.json"

# PATTERNS: JUDGES & CITATIONS
# Patterns for judge names in UK/Irish judgments
JUDGE_PATTERNS = [
    # UK: LORD ATKINSON:, LADY HALE:, LORD REID, Lord Reid
    r"(?:^|\n)\s*(?:LORD|LADY)\s+([A-Z][A-Za-z\-]+)(?:\s*:)?",
    # Irish/UK: Walsh J., Fennelly J., Kearns J.
    r"(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+J\.(?:\s*:)?",
    # Mr Justice X, Mrs Justice Y
    r"(?:Mr|Mrs|Ms)\s+Justice\s+([A-Z][a-z]+)",
    # LORD WILBERFORCE said, Lord Reid said
    r"(?:LORD|LADY|Lord|Lady)\s+([A-Z][A-Za-z\-]+)\s+(?:said|observed|pointed out|held)",
    # Viscount X, Baroness Y
    r"(?:Viscount|Baroness)\s+([A-Z][A-Za-z\-]+)",
]


def extract_year_from_filename(stem: str) -> str:
    """Extract year from filename like [1990] or [1932]_UKHL."""
    m = re.search(r"\[(\d{4})\]", stem)
    return m.group(1) if m else ""


def extract_year_from_title(title: str) -> str:
    """Extract year from title like [2006] IESC 19 (22 March 2006)."""
    m = re.search(r"\[(\d{4})\]", title)
    return m.group(1) if m else ""


def extract_judges(text: str, max_chars: int = 4000) -> list[str]:
    """Extract judge names from judgment text (first N chars)."""
    sample = (text or "")[:max_chars]
    judges = set()
    for pat in JUDGE_PATTERNS:
        for m in re.finditer(pat, sample, re.MULTILINE):
            name = m.group(1).strip()
            if len(name) >= 3 and name.lower() not in ("the", "and", "for", "not"):
                judges.add(name)
    return sorted(judges)


def extract_short_case_name(stem: str, title: str) -> str:
    """Derive short case name, e.g. 'Donoghue v Stevenson' or 'McGee v A.G.'."""
    # Try title first (before citation)
    if title:
        # "Donoghue v Stevenson [1932] UKHL 100" -> "Donoghue v Stevenson"
        before_cite = re.split(r"\s*\[\d{4}\]", title)[0].strip()
        if len(before_cite) > 5:
            return before_cite
    # From stem: Donoghue_v_Stevenson_[1932]_... -> Donoghue v Stevenson
    core = re.sub(r"_\s*\[\d{4}\][^_]*", "", stem)
    core = re.sub(r"_\s*\(\d+[^)]*\)", "", core)
    return core.replace("_", " ").strip()


# EXTRACTION LOGIC
def process_file(html_path: Path) -> dict:
    """Extract metadata from one HTML file."""
    content = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    body_text = soup.get_text(separator=" ", strip=True) if soup.body else ""

    stem = html_path.stem
    year = extract_year_from_filename(stem) or extract_year_from_title(title)
    judges = extract_judges(body_text)
    short_name = extract_short_case_name(stem, title)

    return {
        "short_name": short_name,
        "year": year,
        "judges": judges,
        "title": title[:200] if title else "",
    }


# MAIN
def main():
    extracted_dir = EXTRACTED_DIR
    if not extracted_dir.exists():
        print(f"Extracted dir not found: {extracted_dir}")
        return

    metadata = {}
    for html_path in sorted(extracted_dir.glob("*.html")):
        stem = html_path.stem
        doc_id = stem.replace("_", " ")
        try:
            meta = process_file(html_path)
            metadata[doc_id] = meta
            metadata[stem] = meta  # Also key by stem for lookup
            judges_str = ", ".join(meta["judges"][:8]) if meta["judges"] else "Various"
            print(f"  {stem[:50]}: year={meta['year']}, judges={judges_str[:60]}")
        except Exception as e:
            print(f"  Error {html_path.name}: {e}")

    OUTPUT_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
