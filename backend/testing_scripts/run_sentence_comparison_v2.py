#!/usr/bin/env python3
# v2: context tag (case date, judges, para preview). No role filter.
# Uses corpus_documents_mini_sentences_context_tag.
# Out: testing_scripts/output/Classification_Comparison_sentences_v2_context_tag.tsv

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


def get_text_v2(idx, court_opinion, file_name, test_para, test_label, case_metadata, get_case_summary):
    doc_id = U.file_name_to_doc_id(file_name)
    context_tag = U.get_context_tag(doc_id, case_metadata, test_para)
    return f"[{test_label}] {context_tag} {test_para.strip()}"


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

    print("=== v2: context tag ===")
    run(
        rpc_name="match_corpus_mini_sentences_context_tag_knn",
        table="corpus_documents_mini_sentences_context_tag",
        extra_col="context_tag",
        filter_by_label=False,
        add_role_columns=True,
        out_suffix="v2_context_tag",
        get_text_to_embed=get_text_v2,
        supabase=supabase,
        model=model,
        openai_client=openai_client,
        case_metadata=case_metadata,
        rows=rows,
    )
    print("Done.")


if __name__ == "__main__":
    main()
