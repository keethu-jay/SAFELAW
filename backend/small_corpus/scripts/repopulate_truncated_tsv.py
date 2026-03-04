#!/usr/bin/env python3
"""
Repopulate truncated suggestion cells in sentence comparison TSVs.

Reads source HTML (sentences_indiv_class) to find full text for cells that end with
truncation patterns (e.g. "v.", "at p.", "p."). Replaces truncated text in place.
"""

import csv
import re
from pathlib import Path
from html.parser import HTMLParser

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
SENT_DIR = BACKEND_DIR / "small_corpus" / "sentences_indiv_class"
REF_DIR = BACKEND_DIR / "testing_scripts" / "output"

DOC_ID_MAP = {
    "Ann_Kelly_(Plaintiff)_v_Fergus_Hennessy_(Defendant)": "Ann Kelly v Fergus Hennessy [1995] 3 IR 253",
    "Donoghue_v_Stevenson_[1932]_UKHL_100_(26_May_1932)": "Donoghue v Stevenson [1932] UKHL 100",
    "McGee_v._Attorney_General": "McGee v A.G. and Anor [1973] IESC 2",
    "McLoughlin_v_O'Brian": "McLoughlin v O'Brian [1982] UKHL 3",
    "Norris_v._Ireland": "Norris v A.G. [1983] IESC 3",
}

# Patterns that indicate truncation (text ends with these)
TRUNCATION_PATTERNS = [
    re.compile(r"\s+[A-Za-z][a-zA-Z']*\s+v\.\s*$"),  # "Donoghue v.", "McLoughlin v."
    re.compile(r",?\s+at\s+p\.\s*$"),                 # "at p.", ", at p."
    re.compile(r"\s+\(at\s+p\.\s*$"),                 # "(at p."
    re.compile(r"\s+\(ibid\.\s*,\s*p\.\s*$"),         # "(ibid., p."
    re.compile(r"\s+\([A-Za-z]+\s+v\.\s*$"),         # "(Chadwick v."
    re.compile(r"\.\s*381\s+U\.S\.\s*$"),             # "381 U.S." at end (incomplete)
]


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _doc_ids_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    # Match if one contains the other (handles citation variants)
    if len(na) >= 15 and len(nb) >= 15:
        return na[:40] in nb or nb[:40] in na
    return False


def is_truncated(text: str) -> bool:
    if not text or len(text) < 20:
        return False
    t = text.strip()
    for pat in TRUNCATION_PATTERNS:
        if pat.search(t):
            return True
    return False


# PARSING: HTML TO SENTENCES
class SentenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sentences = []
        self.current = ""
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
            self.current = ""

    def handle_endtag(self, tag):
        if tag == "p" and self.in_p:
            s = self.current.strip()
            if s:
                self.sentences.append(s)
            self.in_p = False

    def handle_data(self, data):
        if self.in_p:
            self.current += data.strip() + " "


def load_doc_sentences() -> dict[str, list[str]]:
    """Build doc_id -> [full sentences] from HTML files."""
    doc_sentences = {}
    for html_path in sorted(SENT_DIR.glob("*_sentences_indiv_class.html")):
        stem = html_path.stem.replace("_sentences_indiv_class", "")
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        parser = SentenceParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        doc_sentences[doc_id] = parser.sentences
    return doc_sentences


def find_full_text(truncated: str, doc_id: str, doc_sentences: dict) -> str | None:
    """Find full sentence that contains or starts with the truncated text."""
    sentences = None
    for did, sents in doc_sentences.items():
        if _doc_ids_match(did, doc_id):
            sentences = sents
            break
    if not sentences:
        return None
    t = truncated.strip()
    # Prefer: sentence that starts with truncated text
    for s in sentences:
        if s.startswith(t) or (t in s and s.startswith(t[:min(50, len(t))])):
            return s
    # Fallback: sentence that contains truncated text (for mid-sentence truncation)
    for s in sentences:
        if t in s:
            return s
    # Try prefix match (truncated might have minor differences)
    t_norm = _normalize(t)
    for s in sentences:
        if _normalize(s).startswith(t_norm[:80]):
            return s
    return None


# TSV REPOPULATION
def repopulate_tsv(tsv_path: Path, doc_sentences: dict) -> int:
    """Repopulate truncated cells. Returns count of replacements."""
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        rows = list(reader)
    if not rows:
        return 0

    header = rows[0]
    replacements = 0

    # Find column indices: Top Suggestion (7), then Suggestion N Text (pairs of 3: Text, Citation, Role)
    # Header: Court, File, Test Para, Role, para_sim, file_sim, Scores, Top Suggestion, S1 Citation, S1 Role, S2 Text, S2 Citation, S2 Role, ...
    try:
        top_col = header.index("Top Suggestion")
    except ValueError:
        top_col = 7
    # Suggestion N Text columns
    text_cols = []
    for i in range(2, 11):
        try:
            idx = header.index(f"Suggestion {i} Text")
            text_cols.append((idx, i))
        except ValueError:
            pass
    # Citation is always text_col - 1 for S2+ (S2 Text, S2 Citation, S2 Role)
    # Top Suggestion format: "text (Citation)" - citation is in same row, Suggestion 1 Citation col
    try:
        s1_citation_col = header.index("Suggestion 1 Citation")
    except ValueError:
        s1_citation_col = 8

    for row_idx in range(1, len(rows)):
        row = rows[row_idx]
        while len(row) < len(header):
            row.append("")

        # Top Suggestion: "full text (Citation)" - if truncated, extract citation from S1 Citation
        if top_col < len(row):
            top_val = row[top_col] or ""
            if top_val and is_truncated(top_val):
                # Extract citation from "text (Citation)" or use S1 Citation
                m = re.search(r"\s*\(([^)]+)\)\s*$", top_val)
                cite = m.group(1).strip() if m else (row[s1_citation_col] if s1_citation_col < len(row) else "")
                if cite:
                    full = find_full_text(
                        re.sub(r"\s*\([^)]+\)\s*$", "", top_val).strip(),
                        cite,
                        doc_sentences,
                    )
                    if full:
                        row[top_col] = f"{full} ({cite})"
                        replacements += 1

        # Suggestion 2-10: order is Text, Citation, Role - so Citation is text_col + 1
        for text_col, _ in text_cols:
            if text_col >= len(row):
                continue
            text_val = row[text_col] or ""
            if not text_val or not is_truncated(text_val):
                continue
            cite_col = text_col + 1
            if cite_col >= len(row):
                continue
            cite = row[cite_col] if cite_col < len(row) else ""
            if not cite:
                continue
            full = find_full_text(text_val, cite, doc_sentences)
            if full:
                row[text_col] = full
                replacements += 1

    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
    return replacements


# MAIN
def main():
    doc_sentences = load_doc_sentences()
    print(f"Loaded {len(doc_sentences)} documents from {SENT_DIR}")

    patterns = [
        "Classification_Comparison_sentences_v1_label_filtered.tsv",
        "Classification_Comparison_sentences_v2_context_tag.tsv",
        "Classification_Comparison_sentences_v3_label_filtered.tsv",
        "Classification_Comparison_sentences_v4_label_filtered_context_tag.tsv",
    ]
    total = 0
    for name in patterns:
        path = REF_DIR / name
        if not path.exists():
            print(f"  Skip {name} (not found)")
            continue
        n = repopulate_tsv(path, doc_sentences)
        total += n
        print(f"  {name}: {n} replacements")
    print(f"\nTotal: {total} truncated cells repopulated")


if __name__ == "__main__":
    main()
