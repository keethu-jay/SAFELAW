#!/usr/bin/env python3
# v3: case summary (first ~500 chars of judgment). No role filter.
# Uses corpus_documents_mini_sentences_case_summary.
# Out: testing_scripts/output/Classification_Comparison_sentences_v3_case_summary.tsv

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

_env_path = BACKEND_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from supabase import create_client
from openai import OpenAI

sys.path.insert(0, str(SCRIPT_DIR))
from _runner import run
import tsv_utils as U


def get_text_v3(idx, court_opinion, file_name, test_para, test_label, case_metadata, get_case_summary):
    doc_id = U.file_name_to_doc_id(file_name)
    case_summary = get_case_summary(doc_id)
    if case_summary:
        return f"[{test_label}] {case_summary} {test_para.strip()}"
    return f"[{test_label}] {test_para.strip()}"


def main():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)
    if not openai_key:
        print("Set OPENAI_API_KEY in .env")
        sys.exit(1)

    sys.path.insert(0, str(BACKEND_DIR / "src"))
    from embedding_helper import EmbeddingModel

    openai_client = OpenAI(api_key=openai_key)
    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Set ISAACUS_API_KEY in .env")
        sys.exit(1)
    supabase = create_client(supabase_url, supabase_key)
    case_metadata = U.load_case_metadata()
    rows = U.load_input_rows()

    print("=== v3: case summary ===")
    run(
        rpc_name="match_corpus_mini_sentences_case_summary_knn",
        table="corpus_documents_mini_sentences_case_summary",
        extra_col="case_summary",
        filter_by_label=False,
        add_role_columns=True,
        out_suffix="v3_case_summary",
        get_text_to_embed=get_text_v3,
        supabase=supabase,
        model=model,
        openai_client=openai_client,
        case_metadata=case_metadata,
        rows=rows,
    )
    print("Done.")


if __name__ == "__main__":
    main()
