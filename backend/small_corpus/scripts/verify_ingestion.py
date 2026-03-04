#!/usr/bin/env python3
"""Quick verification script to check if ingestion completed."""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent

_env_path = BACKEND_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

try:
    from supabase import create_client
except ImportError:
    print("Install supabase: pip install supabase")
    sys.exit(1)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    print("Set SUPABASE_URL and SUPABASE_KEY in .env")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# VERIFICATION
print("Checking ingestion status...\n")

# Check paragraphs
try:
    result = supabase.table("corpus_documents_mini_paragraphs").select("id", count="exact").execute()
    para_count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
    print(f"[OK] Paragraphs in database: {para_count}")
except Exception as e:
    print(f"[ERROR] Error checking paragraphs: {e}")

# Check sentences (individual classifications)
try:
    result = supabase.table("corpus_documents_mini_sentences_indiv_class").select("id", count="exact").execute()
    sent_count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
    print(f"[OK] Sentences (indiv class) in database: {sent_count}")
except Exception as e:
    print(f"[ERROR] Error checking sentences: {e}")

# Check if classifications are present
try:
    result = supabase.table("corpus_documents_mini_paragraphs").select("classification").limit(5).execute()
    if result.data:
        print(f"\n[OK] Sample classifications found: {[r.get('classification') for r in result.data[:3]]}")
    else:
        print("\n[WARNING] No data found in paragraphs table")
except Exception as e:
    print(f"\n[ERROR] Error checking classifications: {e}")

print("\nDone!")
