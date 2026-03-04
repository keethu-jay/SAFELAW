#!/usr/bin/env python3
"""
Rebuild ivfflat indexes for context_tag and case_summary tables.
Uses direct DB connection to avoid SQL Editor timeout.

Requires DATABASE_URL in .env (use direct connection, not pooler, for long-running DDL).
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
_env_path = BACKEND_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Build from components if DATABASE_PASSWORD set (avoids URL encoding issues with special chars)
if os.environ.get("DATABASE_PASSWORD"):
    from urllib.parse import quote_plus
    host = os.environ.get("DATABASE_HOST", "aws-1-us-east-2.pooler.supabase.com")
    port = os.environ.get("DATABASE_PORT", "5432")
    user = os.environ.get("DATABASE_USER", "postgres.ywrwweexwsxvchbnwiju")
    password = os.environ.get("DATABASE_PASSWORD")
    dbname = os.environ.get("DATABASE_NAME", "postgres")
    DB_URL = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"
else:
    DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")


def main():
    if not DB_URL:
        print("DATABASE_URL or DATABASE_PASSWORD not set in .env")
        sys.exit(1)
    # Debug: show which user we're connecting as (no password)
    try:
        from urllib.parse import urlparse
        p = urlparse(DB_URL)
        print(f"Connecting as user: {p.username or '(from URL)'}")
    except Exception:
        pass

    try:
        import psycopg2
    except ImportError:
        print("Install psycopg2: pip install psycopg2-binary")
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()

        # Set timeout for this session (15 min)
        cur.execute("SET statement_timeout = '900000'")
        print("Set statement_timeout = 900s")
        # Increase memory for index build (needs ~231 MB)
        cur.execute("SET maintenance_work_mem = '256MB'")
        print("Set maintenance_work_mem = 256MB")

        print("Dropping idx_mini_sentences_ct_embedding...")
        cur.execute("DROP INDEX IF EXISTS idx_mini_sentences_ct_embedding")
        print("Creating idx_mini_sentences_ct_embedding (lists=500)...")
        cur.execute("""
            CREATE INDEX idx_mini_sentences_ct_embedding
            ON corpus_documents_mini_sentences_context_tag
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 500)
        """)
        print("  Done.")

        print("Dropping idx_mini_sentences_cs_embedding...")
        cur.execute("DROP INDEX IF EXISTS idx_mini_sentences_cs_embedding")
        print("Creating idx_mini_sentences_cs_embedding (lists=500)...")
        cur.execute("""
            CREATE INDEX idx_mini_sentences_cs_embedding
            ON corpus_documents_mini_sentences_case_summary
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 500)
        """)
        print("  Done.")

        cur.close()
        print("\nIndex rebuild completed.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
