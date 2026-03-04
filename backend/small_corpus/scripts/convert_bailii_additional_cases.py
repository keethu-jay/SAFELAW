#!/usr/bin/env python3
"""
Convert BAILII HTML files in Additional Cases to the extracted_html format
used by the classification workflow. Skips McLoughlin v O'Brian (duplicate).
"""

import re
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install beautifulsoup4: pip install beautifulsoup4")
    exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
ADDITIONAL_CASES_DIR = BACKEND_DIR / "small_corpus" / "Additional Cases"
EXTRACTED_DIR = BACKEND_DIR / "small_corpus" / "extracted_html"

# Skip McLoughlin - already in main corpus
SKIP_PATTERNS = [
    r"McLoughlin\s+v\.?\s*O['']?Brian",
    r"McLoughlin\s+ v \s+O['']?Brian",
]


def sanitize_filename(name: str) -> str:
    """Convert case filename to underscore format (e.g. Alcock_v_Chief_Constable_...)."""
    # Remove .html
    stem = name.replace(".html", "").replace(".htm", "")
    # Replace spaces, colons, slashes with underscores
    stem = re.sub(r"[\s:/\–—-]+", "_", stem)
    # Remove or replace characters unsafe for filenames
    stem = re.sub(r'["\'<>|?*]', "", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem + ".html"


def filename_to_doc_id(filename: str) -> str:
    """Derive doc_id (display name) from filename."""
    stem = filename.replace(".html", "").replace(".htm", "")
    return stem


# Patterns that indicate nav/header boilerplate - skip paragraphs containing these
NAV_SKIP_PATTERNS = [
    r"\[\s*Home\s*\]",
    r"\[\s*Databases\s*\]",
    r"You are here:",
    r"Cite as:",
    r"URL:\s*https?://",
    r"United Kingdom House of Lords Decisions",
    r"Printable PDF",
    r"\[ New search \]",
    r"\[Buy ICLR report",
    r"View without highlighting",
    r"JISCBAILII_",
    r"Parliamentary Archives,?\s*HL/",
    r"DONATE\s*\]",
]


def is_nav_boilerplate(text: str) -> bool:
    """Return True if paragraph looks like nav/header content."""
    if not text or len(text) < 20:
        return True
    t = text[:500]  # Check start of long paragraphs
    for pat in NAV_SKIP_PATTERNS:
        if re.search(pat, t, re.I):
            return True
    return False


# EXTRACTION: BAILII PARAGRAPHS
def extract_paragraphs_from_bailii(html_content: str) -> list[str]:
    """
    Extract judgment paragraphs from BAILII HTML, matching ideal case structure
    (Ann Kelly, McGee, Norris, Donoghue, McLoughlin): one unit per numbered legal paragraph.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove navigation, scripts, styles
    for tag in soup.find_all(["script", "style", "nav", "noscript"]):
        tag.decompose()
    # Remove first table if it looks like nav (contains Home/Databases) - keeps IESC table layouts
    tables = soup.find_all("table")
    if tables and re.search(r"\[.*Home.*\]|You are here", tables[0].get_text()[:500]):
        tables[0].decompose()

    # Collect blocks from p and blockquote
    blocks = []
    for tag in soup.find_all(["p", "blockquote"]):
        text = tag.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if text and len(text) >= 15 and not is_nav_boilerplate(text):
            blocks.append(text)

    # UKHL/ICLR format: fallback to div/td when p/blockquote yields little
    if len(blocks) < 5 or sum(len(b) for b in blocks) < 3000:
        blocks = []
        for tag in soup.find_all(["p", "blockquote", "div", "td"]):
            text = tag.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if text and len(text) >= 50 and not is_nav_boilerplate(text):
                blocks.append(text)

    if not blocks:
        return []

    # Ideal structure (Ann Kelly, McGee, Norris, Donoghue, McLoughlin): one unit per legal paragraph.
    # Split on " N. " (space + number + period + space) when followed by capital, excluding citations.
    # Exclude "2. I.R." (I.R. = Irish Reports), "2. A.C." (Appeal Cases), "2. All" (All ER).
    full_text = " ".join(blocks)
    # Match \s+(\d{1,3}\.\s) when followed by [A-Z] but not citation abbrevs
    parts = re.split(
        r"\s+(\d{1,3}\.\s)(?=[A-Z](?!\.?R\.|\.?C\.|ll\s))",
        full_text,
    )
    legal_paragraphs = []
    if len(parts) == 1:
        if parts[0].strip() and re.match(r"^\d{1,3}\.\s", parts[0].strip()[:15]):
            legal_paragraphs.append(parts[0].strip())
    else:
        # First para if starts with "1. "
        if parts[0].strip() and re.match(r"^\d{1,3}\.\s", parts[0].strip()[:15]):
            legal_paragraphs.append(parts[0].strip())
        for i in range(1, len(parts) - 1, 2):
            num, content = parts[i], parts[i + 1].strip()
            para = (num + content).strip()
            if len(para) >= 50:
                legal_paragraphs.append(para)

    # Fallback: use blocks when extraction yields too few (Caparo-style HTML) or too many
    if not legal_paragraphs or (len(legal_paragraphs) < 5 and len(blocks) > 5):
        return blocks
    if len(legal_paragraphs) > 600:  # Single judgment rarely exceeds ~300 paras
        return blocks

    return legal_paragraphs


MIN_PARA_CHARS = 300
MAX_PARA_CHARS = 1200
TARGET_PARA_CHARS = 600


# Placeholder to protect abbreviations from sentence-splitting
_ABBR_PLACEHOLDER = "\x00"
_ABBREVIATIONS = [
    " pp. ", " I.L.R.M. ", " A.L.R. ", " W.L.R. ", " et al. ", " e.g. ", " i.e. ",
    " v. ", " p. ", " Ltd. ", " Co. ", " Inc. ", " No. ", " Vol. ", " U.S. ",
    " A.C. ", " K.B. ", " Q.B. ", " I.R. ", " S.C. ", " E.R. ", " App. ", " L.R. ",
    " etc. ", " cf. ", " para. ", " art. ", " Dr. ", " Mr. ", " Mrs. ", " Prof. ",
]


def split_into_sentences(text: str) -> list[str]:
    """Split text at sentence boundaries. Avoids splitting on legal abbreviations (v., p., Ltd., etc.)."""
    protected = text
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr, abbr[:-2] + _ABBR_PLACEHOLDER + abbr[-1])
    sentences = re.split(r'(?<=[.!?])\s+', protected)
    return [s.replace(_ABBR_PLACEHOLDER, ".").strip() for s in sentences if s.strip()]


def split_into_phrases(text: str) -> list[str]:
    """Split long text at sentence or clause boundaries (semicolon) when no sentence end. Use for runs > MAX."""
    parts = re.split(r'(?<=[.!?;])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def rechunk_paragraphs(paragraphs: list[str]) -> list[str]:
    """
    Resize paragraphs to 300-1200 chars (target ~600). Never split sentences.
    - Long paragraphs: split at sentence boundaries
    - Short paragraphs: merge with adjacent until in range
    """
    if not paragraphs:
        return []

    # First: split any paragraph > MAX at sentence boundaries (never split mid-sentence)
    expanded = []
    for para in paragraphs:
        if len(para) > MAX_PARA_CHARS:
            sentences = split_into_sentences(para)
            # If one "sentence" is > MAX (e.g. header run-on), try splitting at semicolons
            if len(sentences) == 1 and len(sentences[0]) > MAX_PARA_CHARS:
                sentences = split_into_phrases(para)
            chunk = []
            chunk_len = 0
            for sent in sentences:
                sent_len = len(sent) + 1
                if chunk and chunk_len + sent_len > MAX_PARA_CHARS:
                    expanded.append(" ".join(chunk))
                    chunk = []
                    chunk_len = 0
                chunk.append(sent)
                chunk_len += sent_len
            if chunk:
                expanded.append(" ".join(chunk))
        else:
            expanded.append(para)

    # Second: merge short paragraphs (< MIN), split if merged exceeds MAX
    def flush_buffer(buf: list[str]) -> tuple[list[str], str | None]:
        """Returns (chunks to append, leftover if < MIN and could prepend)."""
        if not buf:
            return [], None
        merged = " ".join(buf)
        if len(merged) < MIN_PARA_CHARS:
            return [], merged
        if len(merged) <= MAX_PARA_CHARS:
            return [merged], None
        sents = split_into_sentences(merged)
        chunks, chunk, chunk_len = [], [], 0
        for s in sents:
            sl = len(s) + 1
            if chunk and chunk_len + sl > MAX_PARA_CHARS:
                chunks.append(" ".join(chunk))
                chunk, chunk_len = [], 0
            chunk.append(s)
            chunk_len += sl
        if chunk:
            chunks.append(" ".join(chunk))
        return chunks, None

    result = []
    buffer = []
    for para in expanded:
        if len(para) < MIN_PARA_CHARS:
            buffer.append(para)
        else:
            if buffer:
                chunks, leftover = flush_buffer(buffer)
                buffer = []
                result.extend(chunks)
                if leftover:
                    para = leftover + " " + para
            if len(para) > MAX_PARA_CHARS:
                chunks, _ = flush_buffer([para])
                result.extend(chunks)
            else:
                result.append(para)
    if buffer:
        chunks, leftover = flush_buffer(buffer)
        result.extend(chunks)
        if leftover and result:
            result[-1] = result[-1] + " " + leftover
        elif leftover:
            result.append(leftover)

    # Final pass: merge short paras with adjacent (previous or next) when combined <= MAX
    # Allow slight overage (up to 1250) when short para < 250 and merge-with-next is the only fix
    MERGE_OVERRIDE_MAX = 1250
    final = []
    i = 0
    while i < len(result):
        para = result[i]
        if not para:
            i += 1
            continue
        if len(para) < MIN_PARA_CHARS:
            combined_with_prev = len(final[-1]) + 1 + len(para) if final else 0
            combined_with_next = len(para) + 1 + len(result[i + 1]) if i + 1 < len(result) else 0
            merged = False
            # Try merging with previous (allow override when short < MIN and combined <= 1250)
            if final and (combined_with_prev <= MAX_PARA_CHARS or (len(para) < MIN_PARA_CHARS and combined_with_prev <= MERGE_OVERRIDE_MAX)):
                final[-1] = final[-1] + " " + para
                merged = True
            # Else try merging with next (allow override when short < MIN and combined <= 1250)
            elif i + 1 < len(result):
                if combined_with_next <= MAX_PARA_CHARS or (len(para) < MIN_PARA_CHARS and combined_with_next <= MERGE_OVERRIDE_MAX):
                    final.append(para + " " + result[i + 1])
                    i += 1
                    merged = True
            if not merged:
                final.append(para)
        else:
            final.append(para)
        i += 1
    return final


# OUTPUT: EXTRACTED HTML
def convert_file(src_path: Path, out_path: Path) -> bool:
    """Convert one BAILII file to extracted_html format."""
    try:
        raw = src_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  Error reading {src_path.name}: {e}")
        return False

    paragraphs = extract_paragraphs_from_bailii(raw)
    if not paragraphs:
        print(f"  No paragraphs extracted from {src_path.name}")
        return False

    paragraphs = rechunk_paragraphs(paragraphs)
    # Cap at 600 to avoid 14k+ paragraphs (wastes API calls)
    if len(paragraphs) > 600:
        paragraphs = paragraphs[:600]

    doc_id = filename_to_doc_id(src_path.stem)

    # Match Ann Kelly format: minimal head, no style/nav, simple p structure
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{doc_id}</title>",
        "</head>",
        "<body>",
    ]
    for i, para in enumerate(paragraphs, 1):
        escaped = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(f'<p id="p{i}" data-content-type="">[{i}] {escaped}</p>')
    parts.append("</body>")
    parts.append("</html>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return True


def should_skip(filename: str) -> bool:
    """Return True if this file should be skipped (e.g. duplicate McLoughlin)."""
    name_lower = filename.lower()
    for pat in SKIP_PATTERNS:
        if re.search(pat, filename, re.I):
            return True
    if "mcloughlin" in name_lower and "o" in name_lower and "brian" in name_lower:
        return True
    return False


# MAIN
def main():
    if not ADDITIONAL_CASES_DIR.exists():
        print(f"Additional Cases dir not found: {ADDITIONAL_CASES_DIR}")
        return

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    html_files = list(ADDITIONAL_CASES_DIR.glob("*.html")) + list(
        ADDITIONAL_CASES_DIR.glob("*.htm")
    )

    converted = 0
    skipped = 0
    for src in html_files:
        if should_skip(src.name):
            print(f"Skipping (duplicate): {src.name}")
            skipped += 1
            continue

        safe_name = sanitize_filename(src.name)
        out_path = EXTRACTED_DIR / safe_name
        print(f"Converting: {src.name} -> {safe_name} ...", end=" ")
        if convert_file(src, out_path):
            print("OK")
            converted += 1
        else:
            print("FAILED")

    print(f"\nConverted {converted} files. Skipped {skipped} duplicate(s).")
    print(f"Output: {EXTRACTED_DIR}")


if __name__ == "__main__":
    main()
