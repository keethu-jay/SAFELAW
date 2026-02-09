#!/usr/bin/env python3
"""
Compute two cosine similarities for each of the 18 rows in the CSV:
  1. Paragraph similarity: target paragraph vs best-matching paragraph in top suggestion case
  2. Full-doc similarity: full text of source case vs full text of top suggestion case

Uses Isaacus kanon-2-embedder. Output is copy-paste ready for two columns.

Usage:
    python compare_case_similarity.py [csv_path]

    Requires ISAACUS_API_KEY in backend/.env
"""

import csv
import os
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Load .env from backend directory
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from embedding_helper import EmbeddingModel

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
FINAL_DATASET_DIR = BASE_DIR / "Final Dataset"
RAW_XML_DIR = BASE_DIR / "data" / "raw_xml"
DEFAULT_CSV = SCRIPT_DIR / "semantic_comparison_input.csv"
SOURCE_SEARCH_DIRS = [FINAL_DATASET_DIR, RAW_XML_DIR]
SUGGESTION_SEARCH_DIRS = [FINAL_DATASET_DIR]

# CSV column indices
COL_FILE = 2
COL_TEST_PARAGRAPH = 5
COL_TOP_SUGGESTION = 8


def extract_text_from_element(element: ET.Element) -> str:
    """Recursively extract text from XML element."""
    parts = []
    if element.text:
        parts.append(element.text.strip())
    for child in element:
        parts.append(extract_text_from_element(child))
        if child.tail:
            parts.append(child.tail.strip())
    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def parse_xml_paragraphs(file_path: Path) -> list[str]:
    """Extract paragraph texts from AkomaNtoso XML."""
    ns = {"ns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
    paragraphs = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for para_elem in root.findall(".//ns:paragraph", ns):
            text = extract_text_from_element(para_elem)
            if text:
                paragraphs.append(text)
        if not paragraphs:
            for elem in root.findall(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}p"):
                text = extract_text_from_element(elem)
                if text and len(text) > 50:
                    paragraphs.append(text)
    except Exception as e:
        print(f"  Error parsing paragraphs from {file_path}: {e}")
    return paragraphs


def extract_full_text(file_path: Path) -> str:
    """Extract all text from XML."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        parts = [t.strip() for t in root.itertext() if t and t.strip()]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception as e:
        print(f"  Error parsing {file_path}: {e}")
        return ""


def normalize_case_name(s: str) -> str:
    s = s.strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def find_xml_file(case_name: str, search_dirs: list | None = None) -> Path | None:
    raw = case_name.strip().strip("()")
    if not raw:
        return None
    target_norm = normalize_case_name(raw)
    if not target_norm:
        return None
    target_prefix = target_norm.replace("...", "").strip()
    dirs = [d for d in (search_dirs or [FINAL_DATASET_DIR]) if d and Path(d).exists()]
    for base_dir in dirs:
        base = Path(base_dir)
        for xml_path in base.rglob("*.xml"):
            stem_norm = normalize_case_name(xml_path.stem)
            if stem_norm == target_norm:
                return xml_path
            if target_prefix and stem_norm.startswith(target_prefix):
                return xml_path
    return None


def get_suggestion(row: list) -> str:
    for i in range(COL_TOP_SUGGESTION, min(len(row), COL_TOP_SUGGESTION + 5)):
        cell = row[i].strip()
        if " v " in cell and len(cell) < 200:
            return cell
    return row[COL_TOP_SUGGESTION].strip() if len(row) > COL_TOP_SUGGESTION else ""


def cosine_sim(emb1, emb2):
    import numpy as np
    a, b = np.array(emb1), np.array(emb2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def embed_batch(model: EmbeddingModel, texts: list[str], max_chars: int = 8000) -> list:
    """Embed multiple texts in one API call where possible."""
    import numpy as np
    if not texts:
        return []
    truncated = [t[:max_chars] + ("..." if len(t) > max_chars else "") for t in texts if t and t.strip()]
    if not truncated:
        return [np.zeros(1792) for _ in texts]
    try:
        resp = model.client.embeddings.create(
            model=model.model_name,
            texts=truncated,
            task="retrieval/document",
        )
        return [np.array(e.embedding) for e in resp.embeddings]
    except Exception as e:
        print(f"  Batch embed failed: {e}, falling back to one-by-one")
        return [np.array(model.embed(t)) for t in truncated]


def compute_paragraph_similarity(
    target_para: str, suggestion_path: Path, model: EmbeddingModel, max_chars: int = 8000
) -> float:
    """Target paragraph vs best-matching paragraph in suggestion case."""
    if not target_para or not target_para.strip():
        return 0.0
    paragraphs = [p for p in parse_xml_paragraphs(suggestion_path) if p.strip()]
    if not paragraphs:
        return 0.0
    emb_t = embed_batch(model, [target_para], max_chars)[0]
    BATCH = 32  # Isaacus batch limit
    best = 0.0
    for i in range(0, len(paragraphs), BATCH):
        chunk = paragraphs[i : i + BATCH]
        embs = embed_batch(model, chunk, max_chars)
        for ep in embs:
            sim = cosine_sim(emb_t, ep)
            if sim > best:
                best = sim
    return round(float(best), 4)


def compute_full_doc_similarity(
    path1: Path, path2: Path, model: EmbeddingModel, max_chars: int = 8000
) -> float:
    t1 = extract_full_text(path1)
    t2 = extract_full_text(path2)
    if not t1 or not t2:
        return 0.0
    embs = embed_batch(model, [t1, t2], max_chars)
    if len(embs) < 2:
        return 0.0
    return round(float(cosine_sim(embs[0], embs[1])), 4)


def parse_csv_rows(csv_path: Path) -> list[list]:
    """Parse CSV; split by row boundaries (UKSC|Tribunal at start) to handle embedded newlines."""
    import re
    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Split at newlines that start a new data row
    parts = re.split(r"\n(?=UKSC\t|Tribunal\t)", content)
    # parts[0] = header (Court\t...), parts[1:] = data rows
    data_parts = parts[1:] if parts[0].strip().startswith("Court") else parts
    rows = []
    for part in data_parts:
        part = part.strip()
        if not part or not (part.startswith("UKSC") or part.startswith("Tribunal")):
            continue
        row = part.split("\t")
        if len(row) >= 6:
            while len(row) < 10:
                row.append("")
            rows.append(row)
    return rows


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    if not FINAL_DATASET_DIR.exists():
        print(f"Final Dataset not found: {FINAL_DATASET_DIR}")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Error: Isaacus client not initialized. Check ISAACUS_API_KEY in .env")
        sys.exit(1)

    rows = parse_csv_rows(csv_path)
    n_expected = 18
    if len(rows) != n_expected:
        print(f"Note: Found {len(rows)} rows (expected {n_expected}). Processing all.\n")
    print(f"Processing {len(rows)} rows from {csv_path}\n")

    results = []
    for i, row in enumerate(rows):
        file_name = row[COL_FILE].strip()
        test_para = row[COL_TEST_PARAGRAPH].strip() if len(row) > COL_TEST_PARAGRAPH else ""
        suggestion = get_suggestion(row)
        suggestion_clean = suggestion.strip("()").strip()

        path_source = find_xml_file(file_name, SOURCE_SEARCH_DIRS) or find_xml_file(
            file_name.replace(".xml", ""), SOURCE_SEARCH_DIRS
        )
        path_sugg = find_xml_file(suggestion_clean, SUGGESTION_SEARCH_DIRS) or find_xml_file(
            f"({suggestion_clean})", SUGGESTION_SEARCH_DIRS
        )

        if not path_source:
            print(f"Row {i+1}: Source not found: {file_name}")
            results.append((i + 1, "N/A", "N/A"))
            continue
        if not path_sugg:
            print(f"Row {i+1}: Suggestion not found: {suggestion_clean}")
            results.append((i + 1, "N/A", "N/A"))
            continue

        para_sim = compute_paragraph_similarity(test_para, path_sugg, model)
        full_sim = compute_full_doc_similarity(path_source, path_sugg, model)
        results.append((i + 1, para_sim, full_sim))
        print(f"Row {i+1}: paragraph={para_sim}, full-doc={full_sim}")

    # Copy-paste block: two columns, tab-separated
    print("\n" + "=" * 60)
    print("COPY-PASTE BLOCK (tab-separated: Paragraph Sim | Full-Doc Sim)")
    print("=" * 60)
    block_lines = []
    for r in results:
        _, ps, fs = r
        block_lines.append(f"{ps}\t{fs}")
    print("\n".join(block_lines))

    # Save complete Excel-ready CSV: original columns + Paragraph_Sim + FullDoc_Sim
    out_csv = SCRIPT_DIR / "semantic_comparison_results.csv"
    with open(csv_path, "r", encoding="utf-8") as fin:
        reader = csv.reader(fin, delimiter="\t")
        orig_header = next(reader)
        orig_rows = []
        for r in reader:
            if len(r) >= 6:
                while len(r) < 10:
                    r.append("")
                orig_rows.append(r)

    # Pad header if needed, add our two columns
    while len(orig_header) < 10:
        orig_header.append("")
    out_header = orig_header[:10] + ["Paragraph_Sim", "FullDoc_Sim"]
    out_rows = []
    for i in range(len(results)):
        orig = orig_rows[i][:10] if i < len(orig_rows) else [""] * 10
        ps, fs = results[i][1], results[i][2]
        out_rows.append(orig + [str(ps), str(fs)])

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(out_header)
        for r in out_rows:
            w.writerow(r)
    print(f"\nSaved complete sheet to {out_csv}")


if __name__ == "__main__":
    main()
