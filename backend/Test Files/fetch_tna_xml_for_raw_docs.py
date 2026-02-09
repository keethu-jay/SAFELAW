#!/usr/bin/env python3
"""
Fetch XML from the National Archives (TNA) Case Law API for each document in
backend/Test Files/raw docs (PDFs / Word-like filenames). Saves XML to
backend/Test Files/xml docs.

Uses the Atom feed search (query=) to find matching cases, then downloads
the first result's Akoma Ntoso XML. Skips files that don't yield a search
query (e.g. 2.rtf) or when TNA has no match (e.g. Irish citations).
"""

import os
import re
import time
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

# Paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DOCS_DIR = SCRIPT_DIR / "raw docs"
XML_DOCS_DIR = SCRIPT_DIR / "xml docs"

BASE_URL = "https://caselaw.nationalarchives.gov.uk"
ATOM_ENDPOINT = f"{BASE_URL}/atom.xml"
USER_AGENT = "SafeLaw-WPI/1.0 (Research Project; mailto:kjayamoorthy@wpi.edu)"
RATE_LIMIT_DELAY = 0.6

# Optional: explicit search query per filename (overrides heuristic)
FILENAME_TO_QUERY = {
    "Donoghue_v_Stevenson__1932__UKHL_100__26_May_1932_.pdf": "Donoghue Stevenson",
    "mcloughlin-v-obrian.pdf": "McLoughlin O'Brian",
    "Ann Kelly, Plaintiff, v Fergus Hennessy, Defendant [1995] 3 IR 253.pdf": "Kelly Hennessy",
}

# Optional: direct document URI when neutral citation is known (avoids search order issues)
FILENAME_TO_URI = {
    "Donoghue_v_Stevenson__1932__UKHL_100__26_May_1932_.pdf": "ukhl/1932/100",
    "mcloughlin-v-obrian.pdf": "ukhl/1982/3",  # McLoughlin v O'Brian [1982] UKHL 3
}


def fetch_url(url: str, params: dict | None = None, retry: int = 0) -> bytes | None:
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            return r.content
        if r.status_code == 429:
            print("  Rate limit (429); waiting 60s...")
            time.sleep(60)
            return fetch_url(url, params, retry)
        if r.status_code in (500, 502, 503) and retry < 3:
            print(f"  Server error {r.status_code}; retry in 15s ({retry + 1}/3)")
            time.sleep(15)
            return fetch_url(url, params, retry + 1)
        print(f"  HTTP {r.status_code}: {r.text[:200] if r.text else 'no body'}")
        return None
    except Exception as e:
        print(f"  Request error: {e}")
        return None


def query_to_search(query: str) -> str:
    """Normalise a case-name query for TNA full-text search (keep key words)."""
    # Remove citation-like bits and extra punctuation
    s = re.sub(r"\[\d{4}\].*$", "", query, flags=re.IGNORECASE)
    s = re.sub(r"\s+v\s+", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"[\s_,\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80] if s else ""


def search_tna(query: str, per_page: int = 30) -> list[dict]:
    """Search TNA Atom feed by query; return list of entry dicts with title, xml_href."""
    params = {"query": query, "per_page": per_page}
    content = fetch_url(ATOM_ENDPOINT, params=params)
    if not content:
        return []
    time.sleep(RATE_LIMIT_DELAY)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  Atom parse error: {e}")
        return []
    entries = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        xml_link = entry.find("atom:link[@type='application/akn+xml']", ns)
        if xml_link is None:
            xml_link = entry.find("atom:link[@type='application/xml']", ns)
        href = xml_link.get("href") if xml_link is not None else None
        if href and title:
            entries.append({"title": title, "xml_href": href})
    return entries


def pick_best_match(entries: list[dict], query: str) -> tuple[dict | None, int]:
    """Choose the entry whose title best matches the search query (most query words present).
    Returns (entry, count of query words in title). Returns (None, 0) if no entry has any match."""
    if not entries:
        return None, 0
    q_lower = query.lower()
    words = [w for w in re.split(r"\W+", q_lower) if len(w) > 1]
    if not words:
        return entries[0], 0
    best = None
    best_count = -1
    for e in entries:
        t = (e["title"] or "").lower()
        count = sum(1 for w in words if w in t)
        if count > best_count:
            best_count = count
            best = e
    if best_count <= 0:
        return None, 0
    return best, best_count


def safe_filename_from_title(title: str) -> str:
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    safe = re.sub(r"\s+", " ", safe)[:120]
    return f"{safe}.xml" if safe else "document.xml"


def get_document_uri_for_file(file_path: Path) -> str | None:
    """Return TNA document URI (court/year/seq) if known for this file."""
    if file_path.name in FILENAME_TO_URI:
        return FILENAME_TO_URI[file_path.name]
    # Try to parse from filename e.g. ...__1932__UKHL_100__...
    m = re.search(r"__(\d{4})__(UKHL|UKSC|EWCA|EWHC|UKPC)(?:_(\d+))?", file_path.name, re.IGNORECASE)
    if m:
        year, court, seq = m.group(1), m.group(2).lower(), m.group(3) or "1"
        return f"{court}/{year}/{seq}"
    return None


def get_search_query_for_file(file_path: Path) -> str | None:
    name = file_path.name
    if name in FILENAME_TO_QUERY:
        return FILENAME_TO_QUERY[name]
    # Only try heuristic for PDF
    if file_path.suffix.lower() != ".pdf":
        return None
    stem = file_path.stem
    # "Donoghue_v_Stevenson__1932__..." -> "Donoghue Stevenson"
    stem = re.sub(r"\s*\[\d{4}\].*$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"\s*v\s+", " ", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[\s_,\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    if len(stem) < 4:
        return None
    return stem[:80]


def main():
    RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    XML_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    files = list(RAW_DOCS_DIR.iterdir())
    if not files:
        print(f"No files in {RAW_DOCS_DIR}")
        return

    print(f"Raw docs: {RAW_DOCS_DIR}")
    print(f"XML out:  {XML_DOCS_DIR}\n")

    for file_path in sorted(files):
        if file_path.is_dir():
            continue
        query = get_search_query_for_file(file_path)
        if not query:
            print(f"Skip (no query): {file_path.name}")
            continue

        # 1) Try direct document URI first (avoids search order issues for known citations)
        uri = get_document_uri_for_file(file_path)
        if uri:
            data_url = f"{BASE_URL}/{uri}/data.xml"
            out_name = safe_filename_from_title(query)
            out_path = XML_DOCS_DIR / out_name
            if out_path.exists():
                print(f"Already have (URI): {out_name} <- {file_path.name}")
                continue
            print(f"Fetch by URI: {uri} <- {file_path.name}")
            xml_content = fetch_url(data_url)
            time.sleep(RATE_LIMIT_DELAY)
            if xml_content:
                out_path.write_bytes(xml_content)
                print(f"  Saved: {out_name}")
            else:
                print(f"  URI fetch failed (document may predate TNA coverage from ~2001), trying search...")
                uri = None  # fall through to search

        # 2) Search Atom feed if no URI or direct fetch failed
        if not uri:
            print(f"Search TNA: '{query}' <- {file_path.name}")
            results = search_tna(query, per_page=50)
            if not results:
                print(f"  No TNA results for: {query}")
                continue
            first, match_count = pick_best_match(results, query)
            if first is None or match_count == 0:
                print(f"  No result title matched query words; skip to avoid wrong document.")
                continue
            xml_href = first["xml_href"]
            title = first["title"]
            out_name = safe_filename_from_title(title)
            out_path = XML_DOCS_DIR / out_name
            if out_path.exists():
                print(f"  Already have: {out_name}")
                continue
            print(f"  Download: {title[:60]}...")
            xml_content = fetch_url(xml_href)
            time.sleep(RATE_LIMIT_DELAY)
            if xml_content:
                out_path.write_bytes(xml_content)
                print(f"  Saved: {out_name}")
            else:
                print(f"  Failed to download XML")

    print("\nDone.")


if __name__ == "__main__":
    main()
