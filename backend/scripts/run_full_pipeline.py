#!/usr/bin/env python3
"""
Run the full classification + ingestion + sentence comparison pipeline.

Order:
1. classify_and_ingest_mini_corpus.py --force
2. ingest_classified_mini_corpus.py --full
3. ingest_context_enriched_sentences.py --full
4. run_sentence_context_comparison.py (v1-v4)

Usage:
  python scripts/run_full_pipeline.py [--skip-classify]
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
SMALL_CORPUS_SCRIPTS = BACKEND_DIR / "small_corpus" / "scripts"
TESTING = BACKEND_DIR / "testing_scripts"


# PIPELINE RUNNER
def run(cmd: list[str], desc: str) -> bool:
    print(f"\n{'='*60}")
    print(f">>> {desc}")
    print(f"{'='*60}")
    rc = subprocess.call(cmd, cwd=str(BACKEND_DIR))
    if rc != 0:
        print(f"FAILED: {desc} (exit {rc})")
        return False
    return True


# MAIN
def main():
    ap = argparse.ArgumentParser(description="Run full classification + ingest + comparison pipeline")
    ap.add_argument("--skip-classify", action="store_true", help="Skip classification (use existing HTML)")
    args = ap.parse_args()

    if not args.skip_classify:
        if not run(
            [sys.executable, str(SMALL_CORPUS_SCRIPTS / "classify_and_ingest_mini_corpus.py"), "--force"],
            "1. Classify paragraphs and sentences (--force)",
        ):
            sys.exit(1)

    if not run(
        [sys.executable, str(SMALL_CORPUS_SCRIPTS / "ingest_classified_mini_corpus.py"), "--full"],
        "2. Ingest classified corpus to Supabase (--full)",
    ):
        sys.exit(1)

    if not run(
        [sys.executable, str(SMALL_CORPUS_SCRIPTS / "ingest_context_enriched_sentences.py"), "--full"],
        "3. Ingest context_tag and case_summary tables (--full)",
    ):
        sys.exit(1)

    if not run(
        [sys.executable, str(SMALL_CORPUS_SCRIPTS / "run_sentence_context_comparison.py")],
        "4. Run sentence comparison v1-v4",
    ):
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Pipeline complete. TSV files in testing_scripts/output/")
    print("=" * 60)


if __name__ == "__main__":
    main()
