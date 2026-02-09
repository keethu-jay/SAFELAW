#!/usr/bin/env python3
"""
Corpus Studio Baseline: recalculate paragraph scores, swap columns, add top-10 suggestion text.

Reads your baseline CSV, calls Supabase match_corpus_documents with the TEST PARAGRAPH
(to fix the mistake of comparing "next content" to top suggestion). Output:
- First 7 columns unchanged.
- Semantic Score Comparison of paragraphs (recalculated).
- Semantic Score Comparison of the whole file (when XMLs available).
- Semantic Scores then Top Suggestion (swapped).
- Suggestion 1 Text, Suggestion 1 Citation … Suggestion 10 Text, Suggestion 10 Citation (only filled when all 10 results are non-blank).

Output is tab-separated (.tsv) so commas inside paragraphs do not break columns when you paste into Google Sheets. Use File > Import > Upload and choose Tab as separator, or paste and use Split by tab.

Usage:
  python run_baseline_corpus_studio.py [path_to_baseline.csv]

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY.
Input CSV: comma-delimited, quoted (e.g. "Testing Corpus Studio - Baseline (Right Comparison).csv").
"""

import csv
import os
import re
import sys
from pathlib import Path

# Load .env from backend directory
SCRIPT_DIR = Path(__file__).resolve().parent
_env_path = SCRIPT_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

BASE_DIR = SCRIPT_DIR.parent
FINAL_DATASET_DIR = BASE_DIR / "Final Dataset"
RAW_XML_DIR = BASE_DIR / "data" / "raw_xml"
TEST_XML_DIR = SCRIPT_DIR / "Test Files" / "xml docs"
DEFAULT_INPUT_CSV = Path(os.path.expanduser("~/Downloads/Testing Corpus Studio - Baseline (Right Comparison).csv"))
OUTPUT_TSV = SCRIPT_DIR / "Corpus_Studio_Baseline_Output.tsv"


def read_baseline_csv(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        header = next(reader)
        rows = list(reader)
    return header, rows


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def find_xml_file(case_name: str, search_dirs: list) -> Path | None:
    raw = (case_name or "").strip().strip("()")
    if not raw:
        return None
    target_norm = normalize_case_name(raw)
    target_prefix = target_norm.replace("...", "").strip()
    for base_dir in search_dirs:
        base = Path(base_dir)
        if not base.exists():
            continue
        for xml_path in base.rglob("*.xml"):
            stem_norm = normalize_case_name(xml_path.stem)
            if stem_norm == target_norm or (target_prefix and stem_norm.startswith(target_prefix)):
                return xml_path
    return None


def extract_full_text(file_path: Path) -> str:
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        parts = [t.strip() for t in root.itertext() if t and t.strip()]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception:
        return ""


def cosine_sim(a, b):
    import numpy as np
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def main():
    sys.path.insert(0, str(SCRIPT_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

    input_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_CSV
    if not input_csv.exists():
        print(f"CSV not found: {input_csv}")
        sys.exit(1)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Isaacus client not initialized. Set ISAACUS_API_KEY in .env")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)
    header, rows = read_baseline_csv(input_csv)
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

    def get_top_10(supabase_client, test_paragraph: str, match_threshold=0.0):
        if not (test_paragraph or test_paragraph.strip()):
            return []
        embs = embed_batch([test_paragraph.strip()[:8000]])
        if not embs:
            return []
        try:
            r = supabase_client.rpc(
                "match_corpus_documents",
                {
                    "query_embedding": embs[0].tolist(),
                    "similarity_threshold": match_threshold,
                    "max_results": 10,
                },
            ).execute()
            return r.data or []
        except Exception as e:
            print(f"  RPC error: {e}")
            return []

    def compute_full_doc(path1: Path, path2: Path) -> float:
        t1, t2 = extract_full_text(path1), extract_full_text(path2)
        if not t1 or not t2:
            return 0.0
        embs = embed_batch([t1[:8000], t2[:8000]])
        if len(embs) < 2:
            return 0.0
        return round(cosine_sim(embs[0], embs[1]), 4)

    # Suggestion 1 Text, Suggestion 1 Citation, Suggestion 2 Text, Suggestion 2 Citation, ...
    suggestion_cols = []
    for i in range(1, 11):
        suggestion_cols.append(f"Suggestion {i} Text")
        suggestion_cols.append(f"Suggestion {i} Citation")
    out_header = [
        header[0], header[1], header[2], header[3], header[4], header[5], header[6],
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores",
        "Top Suggestion",
        *suggestion_cols,
    ]

    output_rows = []
    for idx, row in enumerate(rows):
        while len(row) < 11:
            row.append("")
        court, opinion, file_name, position, ctx_prev, test_para, ctx_next = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        first_7 = [court, opinion, file_name, position, ctx_prev, test_para, ctx_next]

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

        top10 = get_top_10(supabase, test_para)
        if len(top10) >= 1:
            first_sim = _float_sim(top10[0])
            if first_sim is not None:
                para_sim = round(first_sim, 4)

        if len(top10) >= 10:
            scores = []
            for i, hit in enumerate(top10[:10]):
                sim = _float_sim(hit)
                if sim is None:
                    scores = []
                    break
                scores.append(sim)
                suggestion_texts[i] = (hit.get("text") or "").strip()
                suggestion_citations[i] = (hit.get("doc_id") or "").strip()
            if len(scores) == 10:
                semantic_scores_col = ", ".join(f"{s:.4f}" for s in scores)
                first_text = (top10[0].get("text") or "").strip()
                doc_id = (top10[0].get("doc_id") or "").strip()
                top_suggestion_col = f"{first_text} ({doc_id})" if doc_id else first_text
                path_source = find_xml_file(file_name.replace(".xml", ""), search_dirs) or find_xml_file(file_name, search_dirs)
                path_sugg = find_xml_file(doc_id, search_dirs)
                if path_source and path_sugg:
                    full_doc_sim = compute_full_doc(path_source, path_sugg)

        # Interleave text and citation for each suggestion (S1 Text, S1 Citation, S2 Text, S2 Citation, ...)
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
        print(f"Row {idx+1}/{len(rows)}: para_sim={para_sim}, full_doc={full_doc_sim}, top10_filled={bool(semantic_scores_col)}")

    # Tab-separated so commas in paragraphs don't split columns in Google Sheets
    with open(OUTPUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(out_header)
        for r in output_rows:
            w.writerow(r)
    print(f"\nSaved: {OUTPUT_TSV}")
    print("Import in Google Sheets: File > Import > Upload, choose Tab as separator.")


if __name__ == "__main__":
    main()
