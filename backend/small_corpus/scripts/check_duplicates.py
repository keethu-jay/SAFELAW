#!/usr/bin/env python3
"""Check for duplicates in mini corpus tables."""
import os
from pathlib import Path
from collections import defaultdict

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

from supabase import create_client
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def check_table(table, cols):
    all_rows = []
    offset = 0
    while True:
        r = sb.table(table).select(cols).range(offset, offset + 999).execute()
        rows = r.data or []
        all_rows.extend(rows)
        if len(rows) < 1000:
            break
        offset += 1000

    by_key = defaultdict(list)
    for row in all_rows:
        text = (row.get("text") or "")[:500]
        key = (row["doc_id"], text)
        by_key[key].append(row)

    dups = {k: v for k, v in by_key.items() if len(v) > 1}
    extra = sum(len(v) - 1 for v in dups.values())
    print(f"\n{table}: {len(all_rows)} rows, {len(dups)} dup groups, {extra} extra rows")
    return len(all_rows), extra

for table, cols in [
    ("corpus_documents_mini_paragraphs", "id,doc_id,text,section_number"),
    ("corpus_documents_mini_sentences", "id,doc_id,text,section_number"),
    ("corpus_documents_mini_sentences_indiv_class", "id,doc_id,text,section_number"),
]:
    try:
        check_table(table, cols)
    except Exception as e:
        print(f"\n{table}: error - {e}")
