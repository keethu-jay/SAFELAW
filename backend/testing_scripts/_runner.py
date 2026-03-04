# Shared runner for v1–v4. Each script calls run() with different rpc/table/filter settings.

import sys
import time
from pathlib import Path
from typing import List, Dict, Callable, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

import tsv_utils as U

MAX_RES = 300
RPC_ATTEMPTS = 5


def run(
    rpc_name: str,
    table: str,
    extra_col: str,
    filter_by_label: bool,
    add_role_columns: bool,
    out_suffix: str,
    get_text_to_embed: Callable,
    supabase,
    model,
    openai_client,
    case_metadata: Dict,
    rows: Optional[List[List[str]]] = None,
) -> Path:
    # get_text_to_embed(idx, court_opinion, file_name, test_para, test_label, case_metadata, get_case_summary) -> str
    import numpy as np
    from embedding_helper import EmbeddingModel

    if model is None:
        model = EmbeddingModel(model_name="kanon-2-embedder")
    if rows is None:
        rows = U.load_input_rows()

    def embed_batch(texts, max_chars=8000):
        if not texts:
            return []
        truncated = [t[:max_chars] + ("..." if len(t) > max_chars else "") for t in texts if t and str(t).strip()]
        if not truncated:
            return [np.zeros(1792) for _ in texts]
        try:
            resp = model.client.embeddings.create(model=model.model_name, texts=truncated, task="retrieval/document")
            return [np.array(e.embedding) for e in resp.embeddings]
        except Exception as e:
            print(f"  Embed failed: {e}")
            return []

    def get_case_summary(doc_id: str) -> str:
        try:
            r = supabase.table("corpus_documents_mini_sentences_case_summary").select("case_summary").eq("doc_id", doc_id).limit(1).execute()
            if r.data and len(r.data) > 0:
                return (r.data[0].get("case_summary") or "").strip()
        except Exception:
            pass
        return ""

    out_header = [
        "Court/Opinion Type", "File Name", "Test Paragraph (To Paste)", "Test Text Role",
        "Semantic Score Comparison of paragraphs", "Semantic Score Comparison of the whole file", "Semantic Scores",
        "Top Suggestion", "Suggestion 1 Citation",
    ]
    if add_role_columns:
        out_header.append("Suggestion 1 Role")
    for i in range(2, 11):
        out_header.append(f"Suggestion {i} Text")
        out_header.append(f"Suggestion {i} Citation")
        if add_role_columns:
            out_header.append(f"Suggestion {i} Role")

    output_rows = []
    for idx, (court_opinion, file_name, test_para) in enumerate(rows):
        test_label = U.classify_paragraph(test_para, openai_client)
        text_to_embed = get_text_to_embed(idx, court_opinion, file_name, test_para, test_label, case_metadata, get_case_summary)
        if not text_to_embed:
            text_to_embed = f"[{test_label}] {test_para.strip()}"

        embs = embed_batch([text_to_embed[:8000]])
        if not embs:
            output_rows.append([court_opinion or "N/A", file_name or "N/A", test_para or "N/A", test_label or "N/A", "0.0", "0.0", "0.0", "N/A", "N/A"] + [""] * (30 if add_role_columns else 20))
            continue

        hits = []
        for attempt in range(RPC_ATTEMPTS):
            try:
                r = supabase.rpc(rpc_name, {
                    "query_embedding": embs[0].tolist(),
                    "similarity_threshold": -2.0,
                    "max_results": MAX_RES,
                }).execute()
                hits = r.data or []
                break
            except Exception as e:
                print(f"  RPC error (attempt {attempt + 1}/{RPC_ATTEMPTS}): {e}")
                time.sleep(5)

        used_fallback = False
        if not hits and table:
            hits = U.run_direct_db_knn(table, extra_col, embs[0].tolist(), MAX_RES, U.file_name_to_doc_id(file_name) or "")
            if hits:
                used_fallback = True
                print(f"  Row {idx + 1}: used direct DB fallback ({len(hits)} hits)")

        filtered = U.filter_hits(hits, file_name, test_label, filter_by_label, 10)

        if not filtered and hits and table and not used_fallback:
            hits = U.run_direct_db_knn(table, extra_col, embs[0].tolist(), MAX_RES, U.file_name_to_doc_id(file_name) or "")
            if hits:
                print(f"  Row {idx + 1}: retry with direct DB (exclude same-case, {len(hits)} hits)")
                filtered = U.filter_hits(hits, file_name, test_label, filter_by_label, 10)

        para_sim = str(round(filtered[0].get("similarity", 0) or 0, 4)) if filtered else "0.0"
        scores = [h.get("similarity") or 0 for h in filtered[:10]]
        semantic_scores_col = ", ".join(f"{s:.4f}" for s in scores) if scores else "0.0"
        suggestion_texts = [(h.get("text") or "").strip() for h in filtered[:10]]
        suggestion_citations = [(h.get("doc_id") or "").strip() for h in filtered[:10]]
        suggestion_roles = [(h.get("classification") or "").strip() for h in filtered[:10]]
        while len(suggestion_texts) < 10:
            suggestion_texts.append("")
            suggestion_citations.append("")
            suggestion_roles.append("")
        top_suggestion_col = f"{suggestion_texts[0]} ({suggestion_citations[0]})" if filtered and suggestion_citations[0] else (suggestion_texts[0] if filtered else "")

        empty = "N/A"
        cells = [
            court_opinion or empty, file_name or empty, test_para or empty, test_label or empty,
            para_sim, "0.0", semantic_scores_col, top_suggestion_col or empty,
            suggestion_citations[0] if suggestion_citations[0] else empty,
        ]
        if add_role_columns:
            cells.append(suggestion_roles[0] if suggestion_roles[0] else empty)
        for i in range(1, 10):
            cells.append(suggestion_texts[i] if suggestion_texts[i] else empty)
            cells.append(suggestion_citations[i] if suggestion_citations[i] else empty)
            if add_role_columns:
                cells.append(suggestion_roles[i] if suggestion_roles[i] else empty)
        output_rows.append(cells)
        print(f"  Row {idx + 1}/{len(rows)}: {file_name} - test_role={test_label}, suggestions={len(filtered)}")

    output_path = U.REFERENCE_OUTPUT_DIR / f"Classification_Comparison_sentences_{out_suffix}.tsv"
    U.ensure_reference_output_dir()
    U.write_tsv(output_path, out_header, output_rows, len(out_header))
    print(f"\nSaved: {output_path}")
    return output_path
