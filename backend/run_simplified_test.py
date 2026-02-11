#!/usr/bin/env python3
"""
Generate simplified test output for the mini corpus.

Reads Simplified_Test_Input.tsv, queries the mini corpus (paragraphs or sentences
per RAG_CORPUS), filters out same-case suggestions, and outputs a TSV in the
simplified format for both paragraph and sentence retrieval.

Usage:
  # For paragraphs (set RAG_CORPUS=mini_paragraphs in .env, or pass --corpus)
  python run_simplified_test.py --corpus mini_paragraphs

  # For sentences
  python run_simplified_test.py --corpus mini_sentences

  # Run both and produce two output files
  python run_simplified_test.py --both

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY.
"""

import argparse
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_env_path = SCRIPT_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

INPUT_TSV = SCRIPT_DIR / "Simplified_Test_Input.tsv"
TEST_XML_DIR = SCRIPT_DIR / "Test Files" / "xml docs"
FINAL_DATASET_DIR = SCRIPT_DIR.parent / "Final Dataset"
RAW_XML_DIR = SCRIPT_DIR.parent / "data" / "raw_xml"

RPC_BY_CORPUS = {
    "mini_paragraphs": "match_corpus_mini_paragraphs_knn",
    "mini_sentences": "match_corpus_mini_sentences_knn",
}


def load_input_rows() -> list[list]:
    """Load rows by splitting on first two tabs so Test Paragraph can contain quotes."""
    rows = []
    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return rows
    # Skip header
    for line in lines[1:]:
        line = line.rstrip("\n\r")
        parts = line.split("\t", 2)
        court_opinion = (parts[0] if len(parts) > 0 else "").strip()
        file_name = (parts[1] if len(parts) > 1 else "").strip()
        test_para = (parts[2] if len(parts) > 2 else "").strip()
        if court_opinion or file_name or test_para:
            rows.append([court_opinion, file_name, test_para])
    return rows


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def find_xml_file(case_name: str, search_dirs: list) -> Path | None:
    raw = (case_name or "").strip().strip("()").replace(".xml", "")
    if not raw:
        return None
    targets = [normalize_case_name(raw)]
    no_cite = re.sub(r"\s*\[\d{4}\][^\]]*\]?\s*", " ", raw).strip()
    if no_cite and no_cite != raw:
        targets.append(normalize_case_name(no_cite))
    for target_norm in targets:
        target_prefix = target_norm.replace("...", "").strip()
        if len(target_prefix) > 50:
            target_prefix = target_prefix[:50]
        for base_dir in search_dirs:
            base = Path(base_dir)
            if not base.exists():
                continue
            for xml_path in base.rglob("*.xml"):
                stem_norm = normalize_case_name(xml_path.stem)
                if stem_norm == target_norm:
                    return xml_path
                if target_prefix and len(target_prefix) >= 8 and stem_norm.startswith(target_prefix[:30]):
                    return xml_path
                if target_prefix and stem_norm.startswith(target_prefix.split()[0]) and len(stem_norm) > 10:
                    if sum(1 for w in target_prefix.split()[:5] if w in stem_norm) >= 2:
                        return xml_path
    return None


def extract_full_text(file_path: Path) -> str:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        parts = [t.strip() for t in root.itertext() if t and t.strip()]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception:
        return ""


def run_for_corpus(corpus: str) -> Path:
    sys.path.insert(0, str(SCRIPT_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

    if not INPUT_TSV.exists():
        print(f"Input not found: {INPUT_TSV}")
        sys.exit(1)

    rows = load_input_rows()
    print(f"Loaded {len(rows)} rows from {INPUT_TSV}")

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Set ISAACUS_API_KEY in .env")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)
    rpc_name = RPC_BY_CORPUS.get(corpus, RPC_BY_CORPUS["mini_paragraphs"])
    print(f"Using corpus: {corpus} -> {rpc_name}")
    search_dirs = [d for d in [FINAL_DATASET_DIR, RAW_XML_DIR, TEST_XML_DIR] if d.exists()]

    def embed_batch(texts, max_chars=8000):
        if not texts:
            return []
        truncated = [t[:max_chars] + ("..." if len(t) > max_chars else "") for t in texts if t and str(t).strip()]
        if not truncated:
            import numpy as np
            return [np.zeros(1792) for _ in texts]
        try:
            resp = model.client.embeddings.create(
                model=model.model_name, texts=truncated, task="retrieval/document"
            )
            import numpy as np
            return [np.array(e.embedding) for e in resp.embeddings]
        except Exception as e:
            print(f"  Embed failed: {e}")
            return []

    def get_top_10(test_paragraph: str, source_file: str, retries: int = 3):
        if not (test_paragraph or test_paragraph.strip()):
            return []
        embs = embed_batch([test_paragraph.strip()[:8000]])
        if not embs:
            return []
        import time
        source_norm = ""
        if source_file:
            source_norm = normalize_case_name(source_file.replace(".xml", ""))
        for attempt in range(retries):
            try:
                r = supabase.rpc(
                    rpc_name,
                    {
                        "query_embedding": embs[0].tolist(),
                        "similarity_threshold": -2.0,
                        "max_results": 2000,
                    },
                ).execute()
                hits = r.data or []
                hits_filtered = []
                if source_norm:
                    for hit in hits:
                        doc_id = (hit.get("doc_id") or "").strip()
                        if not doc_id:
                            hits_filtered.append(hit)
                            continue
                        if normalize_case_name(doc_id) != source_norm:
                            hits_filtered.append(hit)
                else:
                    hits_filtered = hits
                return hits_filtered
            except Exception as e:
                print(f"  RPC error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        return []

    def cosine_sim(a, b):
        import numpy as np
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    def compute_full_doc(path1: Path, path2: Path) -> float:
        t1, t2 = extract_full_text(path1), extract_full_text(path2)
        if not t1 or not t2:
            return 0.0
        embs = embed_batch([t1[:8000], t2[:8000]])
        if len(embs) < 2:
            return 0.0
        return round(cosine_sim(embs[0], embs[1]), 4)

    out_header = [
        "Court/Opinion Type",
        "File Name",
        "Test Paragraph (To Paste)",
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores",
        "Top Suggestion",
        "Suggestion 1 Citation",
    ]
    for i in range(2, 11):
        out_header.append(f"Suggestion {i} Text")
        out_header.append(f"Suggestion {i} Citation")

    output_rows = []
    for idx, (court_opinion, file_name, test_para) in enumerate(rows):
        para_sim = ""
        full_doc_sim = ""
        semantic_scores_col = ""
        top_suggestion_col = ""
        suggestion_texts = [""] * 10
        suggestion_citations = [""] * 10

        def _float_sim(hit):
            v = hit.get("similarity")
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            return None

        top10 = get_top_10(test_para, file_name)
        if len(top10) >= 1:
            first_sim = _float_sim(top10[0])
            if first_sim is not None:
                para_sim = round(first_sim, 4)

        for i, hit in enumerate(top10[:10]):
            suggestion_texts[i] = (hit.get("text") or "").strip()
            suggestion_citations[i] = (hit.get("doc_id") or "").strip()
        scores = [_float_sim(h) or 0.0 for h in top10[:10]]
        if scores:
            semantic_scores_col = ", ".join(f"{s:.4f}" for s in scores)
            first_text = (top10[0].get("text") or "").strip()
            doc_id = (top10[0].get("doc_id") or "").strip()
            top_suggestion_col = f"{first_text} ({doc_id})" if doc_id else first_text
            path_source = find_xml_file(file_name.replace(".xml", ""), search_dirs) or find_xml_file(file_name, search_dirs)
            path_sugg = find_xml_file(doc_id, search_dirs)
            if path_source and path_sugg:
                full_doc_sim = compute_full_doc(path_source, path_sugg)

        cells = [court_opinion, file_name, test_para]
        cells += [str(para_sim) if para_sim != "" else "", str(full_doc_sim) if full_doc_sim != "" else ""]
        cells += [semantic_scores_col, top_suggestion_col, suggestion_citations[0]]
        for i in range(1, 10):
            cells.append(suggestion_texts[i])
            cells.append(suggestion_citations[i])
        output_rows.append(cells)
        print(f"Row {idx + 1}/{len(rows)}: {file_name} - para_sim={para_sim}, full_doc={full_doc_sim}")

    def sanitize_cell(s) -> str:
        if s is None:
            return ""
        if not isinstance(s, str):
            s = str(s)
        return s.replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()

    output_path = SCRIPT_DIR / f"Simplified_Test_Output_{corpus}.tsv"
    n_cols = len(out_header)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerow(out_header)
        for r in output_rows:
            cells = [sanitize_cell(c) for c in r]
            while len(cells) < n_cols:
                cells.append("")
            w.writerow(cells[:n_cols])
    print(f"\nSaved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Run simplified test for mini corpus")
    parser.add_argument("--corpus", choices=["mini_paragraphs", "mini_sentences"],
                        default=None, help="Corpus to use (default: from RAG_CORPUS env)")
    parser.add_argument("--both", action="store_true", help="Run for both paragraph and sentence corpus")
    args = parser.parse_args()

    if args.both:
        for c in ["mini_paragraphs", "mini_sentences"]:
            print(f"\n--- {c} ---")
            run_for_corpus(c)
        return

    corpus = args.corpus or os.environ.get("RAG_CORPUS", "mini_paragraphs")
    run_for_corpus(corpus)


if __name__ == "__main__":
    main()
