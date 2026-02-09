#!/usr/bin/env python3
"""
Read a TSV with Context/Test Paragraph columns filled, and fill the semantic columns
(Semantic Score, Top Suggestion, Suggestion 1-10 Text/Citation) using Supabase pgvector.

Usage:
  python fill_semantic_columns.py [input.tsv] [output.tsv]

  Default: reads Test_Files_Baseline_Input.tsv, writes Test_Files_Baseline_Semantic_Only.tsv

Input TSV must have columns (tab-separated):
  Court/Opinion Type, File Name, Test Position, Context: Previous, Test Paragraph (To Paste), Context: Next
  (+ optional empty columns for semantic data which will be overwritten)

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY.
"""

import csv
import os
import sys
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
OUTPUT_TSV = SCRIPT_DIR / "Test_Files_Baseline_Semantic_Only.tsv"


def parse_court_opinion(val: str) -> tuple[str, str]:
    """Split 'Tribunal Majority' -> (Tribunal, Majority), 'UKSC Majority' -> (UKSC, Majority)."""
    parts = (val or "").strip().split(None, 1)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0] if parts else "UKSC", "Majority"


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_TSV
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_TSV

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Create Test_Files_Baseline_Input.tsv with your 7 columns, or pass path as first arg.")
        sys.exit(1)

    sys.path.insert(0, str(SCRIPT_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

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

    def get_top_10(test_paragraph: str, match_threshold=0.0):
        if not (test_paragraph or str(test_paragraph).strip()):
            return []
        embs = embed_batch([str(test_paragraph).strip()[:8000]])
        if not embs:
            return []
        try:
            r = supabase.rpc(
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

    # Read input
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    # Determine column indices/names
    test_para_col = "Test Paragraph (To Paste)"
    ctx_prev_col = "Context: Previous"
    ctx_next_col = "Context: Next"
    court_col = "Court/Opinion Type"
    file_col = "File Name"
    pos_col = "Test Position"

    if not rows:
        print("No data rows found.")
        sys.exit(1)

    # Build output header
    suggestion_cols = []
    for i in range(1, 11):
        suggestion_cols.append(f"Suggestion {i} Text")
        suggestion_cols.append(f"Suggestion {i} Citation")
    out_header = [
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores", "Top Suggestion",
        *suggestion_cols,
    ]

    output_rows = []
    for idx, row in enumerate(rows):
        court_opinion = row.get(court_col, row.get("Court/Opinion Type", ""))
        court, opinion = parse_court_opinion(court_opinion)
        file_name = row.get(file_col, row.get("File Name", ""))
        position = row.get(pos_col, row.get("Test Position", ""))
        ctx_prev = row.get(ctx_prev_col, "")
        test_para = row.get(test_para_col, "")
        ctx_next = row.get(ctx_next_col, "")

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

        top10 = get_top_10(test_para)
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

        suggestion_pairs = []
        for i in range(10):
            suggestion_pairs.append(suggestion_texts[i])
            suggestion_pairs.append(suggestion_citations[i])

        output_rows.append(
            [str(para_sim) if para_sim != "" else "", full_doc_sim]
            + [semantic_scores_col, top_suggestion_col]
            + suggestion_pairs
        )
        print(f"Row {idx + 1}/{len(rows)}: {file_name} {position} - para_sim={para_sim}")

    def sanitize(s):
        if s is None:
            return ""
        s = str(s).replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
        return s

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(out_header)
        for r in output_rows:
            w.writerow([sanitize(c) for c in r])

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
