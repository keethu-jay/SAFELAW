#!/usr/bin/env python3
"""
Deduplicate mini corpus tables. Deletes in small batches to avoid Supabase timeout.
Keeps row with lowest id per (doc_id, text).
"""
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

from supabase import create_client

def dedupe_table(sb, table: str, delete_batch: int = 100):
    """Fetch all rows, find duplicate ids, delete in small batches."""
    print(f"  Fetching {table}...")
    seen = {}  # (doc_id, text) -> id to keep (lowest)
    to_delete = []
    offset = 0
    chunk = 1000
    while True:
        r = sb.table(table).select("id,doc_id,text").range(offset, offset + chunk - 1).execute()
        rows = r.data or []
        for row in rows:
            text = row.get("text") or ""
            key = (row["doc_id"], text[:2000] if len(text) > 2000 else text)
            rid = row["id"]
            if key in seen:
                keeper = seen[key]
                to_delete.append(rid if rid > keeper else keeper)
                seen[key] = min(rid, keeper)
            else:
                seen[key] = rid
        if len(rows) < chunk:
            break
        offset += chunk
        print(f"    ... {offset} rows scanned")

    print(f"  Found {len(to_delete)} duplicates. Deleting in batches of {delete_batch}...")
    total = 0
    for i in range(0, len(to_delete), delete_batch):
        batch = to_delete[i : i + delete_batch]
        for id in batch:
            sb.table(table).delete().eq("id", id).execute()
        total += len(batch)
        print(f"    Deleted {total}/{len(to_delete)}")
    return total

def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    for table in ["corpus_documents_mini_paragraphs", "corpus_documents_mini_sentences", "corpus_documents_mini_sentences_indiv_class"]:
        print(f"\nDeduplicating {table}...")
        n = dedupe_table(sb, table)
        print(f"  Done. Deleted {n} duplicates.")

if __name__ == "__main__":
    main()
