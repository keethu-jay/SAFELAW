    #!/usr/bin/env python3

'''
WHAT DOES THIS DO???
- Walks an input directory for .html files (skips PDFs by default).
- Targets the real content under <div id="content_document">.
- Pulls core metadata (case_name, court, date, citations, doc_id).
- Extracts BNA headnotes.
- Splits the opinion into labeled sections (FACTS AND PROCEEDINGS, DISCUSSION, CONCLUSION, etc.)
- Writes JSON Lines to output file; optional per-case .md files for human inspection.
'''
import argparse
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

SECTION_SELECTOR = "h1.organization"  # Bloomberg uses this for major section headers

def norm(s: str) -> str:
    if not s:
        return ""
    # normalize whitespace & strip artifacts
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def text_of(el) -> str:
    return norm(el.get_text(separator="\n")) if el else ""

def parse_headnotes(content_root):
    headnotes = []
    hn_container = content_root.select_one(".headnotesContainer")
    if not hn_container:
        return headnotes
    for hn in hn_container.select(".headnote"):
        # headline slug + body text are useful
        slug = hn.select_one(".headnoteSlug")
        # some pages use .headnoteDescriptor + following .headnote_text
        descriptor = hn.select_one(".headnoteDescriptor")
        body = hn.select_one(".headnote_text") or hn.select_one(".headnoteToggle .headnoteText")
        headnotes.append({
            "slug": text_of(slug) or text_of(descriptor),
            "text": text_of(body)
        })
    # fallback: single block headnote_texts
    if not headnotes:
        for body in hn_container.select(".headnote_text"):
            headnotes.append({"slug": "", "text": text_of(body)})
    return [hn for hn in headnotes if (hn["slug"] or hn["text"])]

def parse_citations(soup):
    cites = set()
    # Primary citations block
    for c in soup.select(".citation-group .cite"):
        cites.add(norm(c.get_text()))
    # Page-number “[*822]” style markers aren’t citations; skip .page_no
    return sorted(c for c in cites if c)

def parse_doc_meta(soup):
    meta = {}
    # Bloomberg embeds an invisible "metadata" block and inputs with ids
    meta["doc_id"] = (soup.select_one("#doc_id") or soup.select_one("input#doc_id"))
    meta["doc_id"] = meta["doc_id"]["value"] if meta["doc_id"] and meta["doc_id"].has_attr("value") else None

    meta["case_name"] = None
    m_case = soup.select_one("input#hidden_case_name")
    if m_case and m_case.has_attr("value"):
        meta["case_name"] = m_case["value"]
    if not meta["case_name"]:
        title = soup.select_one("div.breadCrumbTitleRow .title") or soup.select_one("title")
        if title:
            t = title.get_text()
            meta["case_name"] = t.split(", Court Opinion")[0].strip()

    # Court + Date appear as centered lines just above headnotes
    content = soup.select_one("#content_document")
    court, date = None, None
    if content:
        # Heuristic: first <center> near top with 'U.S. ' likely the court
        centers = content.find_all(["center"], recursive=True)
        for c in centers[:6]:  # only early centers
            txt = norm(c.get_text())
            if not court and ("U.S." in txt or "Court" in txt):
                court = txt
            # dates like "January 3, 2013"
            if not date:
                m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}", txt)
                if m:
                    date = m.group(0)

    meta["court"] = court
    meta["date"] = date
    meta["citations"] = parse_citations(soup)
    return meta

def parse_sections(content_root):
    """
    Splits major sections by <h1 class="organization"> headers and captures the text
    until the next header.
    """
    sections = []
    if not content_root:
        return sections

    # Collect all direct descendants starting from the first header
    headers = content_root.select(SECTION_SELECTOR)
    if not headers:
        # If no headers, fallback: dump everything as "Opinion"
        return [{"title": "Opinion", "text": text_of(content_root)}]

    # Iterate headers and slice content between them
    for i, h in enumerate(headers):
        title = norm(h.get_text())
        # capture all siblings until next h1.organization
        texts = []
        node = h.next_sibling
        while node:
            if getattr(node, "name", None) == "h1" and "organization" in node.get("class", []):
                break
            if hasattr(node, "get_text"):
                texts.append(node)
            node = node.next_sibling
        body = norm("\n".join(text_of(el) for el in texts if el))
        if body:
            sections.append({"title": title, "text": body})
    return sections

def parse_case_html(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    content_root = soup.select_one("#content_document")
    if not content_root:
        # fallback to whole body
        content_root = soup.body or soup

    meta = parse_doc_meta(soup)
    headnotes = parse_headnotes(content_root)
    sections = parse_sections(content_root)

    # Try to isolate “Majority Opinion” text if present by anchor
    maj_anchor = content_root.find(id="contentMajOp")
    majority_text = text_of(maj_anchor) if maj_anchor else ""

    record = {
        "source_path": str(path),
        "doc_type": "OPINION",
        **meta,
        "headnotes": headnotes,
        "sections": sections,
        "majority_opinion": majority_text or None,
    }
    return record

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True, help="Input directory containing .html files")
    ap.add_argument("--out", dest="outfile", required=True, help="Output JSONL path")
    ap.add_argument("--write-md", action="store_true", help="Also write a .md per case (for human review)")
    args = ap.parse_args()

    indir = Path(args.indir)
    out = Path(args.outfile)
    out.parent.mkdir(parents=True, exist_ok=True)

    html_files = sorted([p for p in indir.rglob("*") if p.suffix.lower() == ".html"])
    if not html_files:
        print(f"[warn] No .html files found under {indir}")
        return

    written = 0
    with out.open("w", encoding="utf-8") as f:
        for p in html_files:
            try:
                rec = parse_case_html(p)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                written += 1

                if args.write_md:
                    # Make a compact reviewer-friendly MD
                    name = (rec.get("case_name") or Path(p).stem)
                    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:120]
                    md_path = out.parent / f"{safe}.md"
                    with md_path.open("w", encoding="utf-8") as md:
                        md.write(f"# {rec.get('case_name','')}\n\n")
                        meta_lines = []
                        if rec.get("court"): meta_lines.append(f"**Court:** {rec['court']}")
                        if rec.get("date"): meta_lines.append(f"**Date:** {rec['date']}")
                        if rec.get("citations"): meta_lines.append(f"**Citations:** {', '.join(rec['citations'])}")
                        if rec.get("doc_id"): meta_lines.append(f"**Doc ID:** {rec['doc_id']}")
                        if meta_lines:
                            md.write("\n".join(meta_lines) + "\n\n")

                        if rec.get("headnotes"):
                            md.write("## Headnotes\n")
                            for i, hn in enumerate(rec["headnotes"], 1):
                                if hn.get("slug"):
                                    md.write(f"**[{i}] {hn['slug']}**\n\n")
                                if hn.get("text"):
                                    md.write(hn["text"] + "\n\n")

                        if rec.get("sections"):
                            md.write("## Sections\n")
                            for s in rec["sections"]:
                                md.write(f"### {s['title']}\n\n{s['text'][:4000]}\n\n")

            except Exception as e:
                print(f"[error] {p}: {e}")

    print(f"[ok] Wrote {written} JSONL records to {out}")

if __name__ == "__main__":
    main()
