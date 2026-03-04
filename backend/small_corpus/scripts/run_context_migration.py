#!/usr/bin/env python3
"""
Run supabase_mini_corpus_context_migration.sql against Supabase.

Requires DATABASE_URL or SUPABASE_DB_URL in .env (Postgres connection string).
Get it from: Supabase Dashboard > Project Settings > Database > Connection string (URI).

If not set, run the SQL manually in Supabase SQL Editor.
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

DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")


def main():
    if not DB_URL:
        print("DATABASE_URL or SUPABASE_DB_URL not set in .env")
        print("Get the Postgres connection string from: Supabase Dashboard > Project Settings > Database")
        print("Then add to .env: DATABASE_URL=postgresql://postgres.[ref]:[password]@...")
        print("\nAlternatively, run the SQL manually in Supabase SQL Editor:")
        print("  Copy the 'Context Migration' block from backend/small_corpus/README.md")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Install psycopg2: pip install psycopg2-binary")
        sys.exit(1)

    # Read SQL from small_corpus README (SQL section 3: Context Migration)
    readme_path = BACKEND_DIR / "small_corpus" / "README.md"
    if not readme_path.exists():
        print(f"README not found: {readme_path}")
        sys.exit(1)
    text = readme_path.read_text(encoding="utf-8")
    # Extract the Context Migration sql block (### 3. Context Migration ... ```sql ... ```)
    import re
    match = re.search(
        r"### 3\. Context Migration.*?```sql\s*\n(.*?)```",
        text,
        re.DOTALL,
    )
    if not match:
        print("Could not find Context Migration SQL block in README.md")
        sys.exit(1)
    sql_content = match.group(1).strip()

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql_content)
        cur.close()
        print("Migration completed.")
    except Exception as e:
        print(f"Connection/execution error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
