#!/usr/bin/env python3
"""
Generate baseline output for the 5 test files using the MINI corpus (paragraph-level).

Reads curated rows from Test_Files_Baseline_Input.tsv, queries the mini corpus
(corpus_documents_mini_paragraphs via match_corpus_mini_paragraphs_knn RPC), and
outputs a full TSV with all columns for Google Sheets.

Usage:
  python run_baseline_mini_corpus.py

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY.
Output: backend/Mini_Corpus_Baseline_Output.tsv
"""

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

INPUT_TSV = SCRIPT_DIR / "Test_Files_Baseline_Input.tsv"
OUTPUT_TSV = SCRIPT_DIR / "Mini_Corpus_Baseline_Output.tsv"
TEST_XML_DIR = SCRIPT_DIR / "Test Files" / "xml docs"
FINAL_DATASET_DIR = SCRIPT_DIR.parent / "Final Dataset"
RAW_XML_DIR = SCRIPT_DIR.parent / "data" / "raw_xml"

RPC_BY_CORPUS = {
    "mini_paragraphs": "match_corpus_mini_paragraphs_knn",
    "mini_sentences": "match_corpus_mini_sentences_knn",
}


def load_input_rows() -> list[list]:
    rows = []
    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            co = row.get("Court/Opinion Type", "").strip().split(None, 1)
            court = co[0] if co else "UKSC"
            opinion = co[1] if len(co) >= 2 else "Majority"
            rows.append([
                court, opinion,
                row.get("File Name", ""),
                row.get("Test Position", ""),
                row.get("Context: Previous", ""),
                row.get("Test Paragraph (To Paste)", ""),
                row.get("Context: Next", ""),
            ])
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


def main():
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
    corpus = os.environ.get("RAG_CORPUS", "mini_paragraphs")
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

    def get_top_10_mini(test_paragraph: str, source_file: str, retries: int = 3):
        """
        Return up to 10 suggestions for the test paragraph,
        excluding hits that come from the same file as the test paragraph.
        """
        if not (test_paragraph or test_paragraph.strip()):
            return []
        embs = embed_batch([test_paragraph.strip()[:8000]])
        if not embs:
            return []
        import time

        # Normalized name for the source file (e.g. xml file for the test paragraph)
        source_norm = ""
        if source_file:
            # File name column already looks like "Case Name ... .xml"
            cleaned = source_file.replace(".xml", "")
            source_norm = normalize_case_name(cleaned)

        for attempt in range(retries):
            try:
                r = supabase.rpc(
                    rpc_name,
                    {
                        "query_embedding": embs[0].tolist(),
                        "similarity_threshold": -2.0,
                        # Ask for effectively all rows in the
                        # mini sentence corpus so that even after
                        # filtering same-file hits we still have
                        # cross-case suggestions.
                        "max_results": 2000,
                    },
                ).execute()
                hits = r.data or []

                # Prefer suggestions from different files; if all hits
                # come from the same file, return an empty list so we
                # do *not* fall back to same-file matches.
                hits_filtered = []
                if source_norm:
                    filtered = []
                    for hit in hits:
                        doc_id = (hit.get("doc_id") or "").strip()
                        if not doc_id:
                            filtered.append(hit)
                            continue
                        doc_norm = normalize_case_name(doc_id)
                        if doc_norm != source_norm:
                            filtered.append(hit)
                    if filtered:
                        hits_filtered = filtered
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

    suggestion_cols = []
    for i in range(1, 11):
        suggestion_cols.append(f"Suggestion {i} Text")
        suggestion_cols.append(f"Suggestion {i} Citation")

    first_7_header = [
        "Court/Opinion Type",
        "File Name",
        "Test Position",
        "Context: Previous",
        "Test Paragraph (To Paste)",
        "Context: Next",
    ]
    out_header = first_7_header + [
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores",
        "Top Suggestion",
        *suggestion_cols,
    ]

    output_rows = []
    for idx, row in enumerate(rows):
        court, opinion, file_name, position, ctx_prev, test_para, ctx_next = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        first_7 = [f"{court} {opinion}", file_name, position, ctx_prev, test_para, ctx_next]

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

        top10 = get_top_10_mini(test_para, file_name)
        if len(top10) >= 1:
            first_sim = _float_sim(top10[0])
            if first_sim is not None:
                para_sim = round(first_sim, 4)

        for i, hit in enumerate(top10[:10]):
            suggestion_texts[i] = (hit.get("text") or "").strip()
            suggestion_citations[i] = (hit.get("doc_id") or "").strip()
            sim = _float_sim(hit)
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

        suggestion_pairs = []
        for i in range(10):
            suggestion_pairs.append(suggestion_texts[i])
            suggestion_pairs.append(suggestion_citations[i])

        output_rows.append(
            first_7
            + [str(para_sim) if para_sim != "" else "", str(full_doc_sim) if full_doc_sim != "" else ""]
            + [semantic_scores_col, top_suggestion_col]
            + suggestion_pairs
        )
        print(f"Row {idx+1}/{len(rows)}: {file_name} {position} - para_sim={para_sim}, full_doc={full_doc_sim}")

    def sanitize_cell(s) -> str:
        if s is None:
            return ""
        if not isinstance(s, str):
            s = str(s)
        return s.replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()

    n_cols = len(out_header)
    with open(OUTPUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerow(out_header)
        for r in output_rows:
            cells = [sanitize_cell(c) for c in r]
            while len(cells) < n_cols:
                cells.append("")
            w.writerow(cells[:n_cols])
    print(f"\nSaved: {OUTPUT_TSV.resolve()}")
    print("Import in Google Sheets: File > Import > Upload, choose Tab as separator.")


if __name__ == "__main__":
    main()
