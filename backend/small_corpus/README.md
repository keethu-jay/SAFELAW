# Small Corpus

Mini corpus for specialized testing (5 papers, manageable corpus size). Contains scripts, data, and SQL for setup.

## Structure

- `extracted_html/` – Extracted HTML from BAILII
- `Additional Cases/` – Source BAILII HTML before conversion
- `paragraphs_classified/` – Paragraph-level classified HTML
- `sentences_indiv_class/` – Sentence-level with individual classifications
- `sentences_para_class/` – Sentence-level with paragraph-inherited classifications
- `scripts/` – All small corpus scripts (classification, ingestion, comparison, etc.)

## Pipeline

1. `classify_and_ingest_mini_corpus.py` – Extract, classify, create HTML
2. `ingest_classified_mini_corpus.py` – Ingest to Supabase
3. `ingest_context_enriched_sentences.py` – Ingest context_tag and case_summary tables
4. `run_sentence_context_comparison.py` – Run v1–v4 comparison

Or use `python scripts/run_full_pipeline.py` from the backend directory.

---

## SQL

Run these in order in the Supabase SQL Editor. **All SQL is also in [SUPABASE_SQL.md](../../SUPABASE_SQL.md)** at the project root. Run the schema first, then the migrations.

### 1. Schema (`supabase_mini_corpus_schema.sql`)

```sql
-- Mini corpus tables for specialized testing (5 papers, manageable corpus size)
-- Run this in Supabase SQL Editor before ingesting small corpus data.
-- Tables mirror corpus_documents schema for compatibility with existing RAG code.

-- Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Mini paragraph-level corpus (5 papers, paragraph chunks)
CREATE TABLE IF NOT EXISTS corpus_documents_mini_paragraphs (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    section_title TEXT DEFAULT 'Main',
    section_number TEXT,
    sentence_index INTEGER DEFAULT 0,
    global_index INTEGER DEFAULT 0,
    court TEXT DEFAULT 'UKSC',
    decision TEXT DEFAULT 'majority',
    embedding vector(1792)
);

CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_embedding 
    ON corpus_documents_mini_paragraphs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 5);
CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_doc_id 
    ON corpus_documents_mini_paragraphs (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_doc_section_idx 
    ON corpus_documents_mini_paragraphs (doc_id, section_title, sentence_index);

-- 2. Mini sentence-level corpus (5 papers, sentence chunks)
CREATE TABLE IF NOT EXISTS corpus_documents_mini_sentences (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    section_title TEXT DEFAULT 'Main',
    section_number TEXT,
    sentence_index INTEGER DEFAULT 0,
    global_index INTEGER DEFAULT 0,
    court TEXT DEFAULT 'UKSC',
    decision TEXT DEFAULT 'majority',
    embedding vector(1792)
);

CREATE INDEX IF NOT EXISTS idx_mini_sentences_embedding 
    ON corpus_documents_mini_sentences USING ivfflat (embedding vector_cosine_ops) WITH (lists = 5);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_doc_id 
    ON corpus_documents_mini_sentences (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_doc_section_idx 
    ON corpus_documents_mini_sentences (doc_id, section_title, sentence_index);

-- RPC: match mini paragraphs (same interface as match_corpus_documents)
CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT 0.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.doc_id,
        d.text,
        d.section_title,
        d.section_number,
        d.sentence_index,
        d.global_index,
        d.court,
        d.decision,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM corpus_documents_mini_paragraphs d
    WHERE 1 - (d.embedding <=> query_embedding) > similarity_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

-- RPC: match mini sentences (same interface as match_corpus_documents)
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT 0.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.doc_id,
        d.text,
        d.section_title,
        d.section_number,
        d.sentence_index,
        d.global_index,
        d.court,
        d.decision,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM corpus_documents_mini_sentences d
    WHERE 1 - (d.embedding <=> query_embedding) > similarity_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

-- RPC: KNN variant using inner product (<#>) instead of cosine distance (<=>)
CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.doc_id,
        d.text,
        d.section_title,
        d.section_number,
        d.sentence_index,
        d.global_index,
        d.court,
        d.decision,
        (-1.0) * (d.embedding <#> query_embedding) AS similarity
    FROM corpus_documents_mini_paragraphs d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;

CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.doc_id,
        d.text,
        d.section_title,
        d.section_number,
        d.sentence_index,
        d.global_index,
        d.court,
        d.decision,
        (-1.0) * (d.embedding <#> query_embedding) AS similarity
    FROM corpus_documents_mini_sentences d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;
```

### 2. Classification Migration (`supabase_mini_corpus_classification_migration.sql`)

Run after schema. Adds classification columns and `corpus_documents_mini_sentences_indiv_class` table.

```sql
-- Migration: Add classification columns to mini corpus tables
-- Run this AFTER running supabase_mini_corpus_schema.sql

-- 1. Add classification column to paragraphs table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'corpus_documents_mini_paragraphs' AND column_name = 'classification'
  ) THEN
    ALTER TABLE corpus_documents_mini_paragraphs ADD COLUMN classification TEXT;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_classification 
  ON corpus_documents_mini_paragraphs (classification);

-- 2. Add classification column to sentences table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'corpus_documents_mini_sentences' AND column_name = 'classification'
  ) THEN
    ALTER TABLE corpus_documents_mini_sentences ADD COLUMN classification TEXT;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_mini_sentences_classification 
  ON corpus_documents_mini_sentences (classification);

-- 3. New table: Sentences with individual classifications
CREATE TABLE IF NOT EXISTS corpus_documents_mini_sentences_indiv_class (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT NOT NULL,
  text TEXT NOT NULL,
  section_title TEXT DEFAULT 'Main',
  section_number TEXT,
  sentence_index INTEGER DEFAULT 0,
  global_index INTEGER DEFAULT 0,
  court TEXT DEFAULT 'UKSC',
  decision TEXT DEFAULT 'majority',
  classification TEXT NOT NULL,
  embedding vector(1792)
);

CREATE INDEX IF NOT EXISTS idx_mini_sentences_indiv_embedding 
  ON corpus_documents_mini_sentences_indiv_class USING ivfflat (embedding vector_cosine_ops) WITH (lists = 5);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_indiv_doc_id 
  ON corpus_documents_mini_sentences_indiv_class (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_indiv_classification 
  ON corpus_documents_mini_sentences_indiv_class (classification);

-- 4. RPC: match sentences with individual classifications
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_indiv_class_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences_indiv_class d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- 5. Update match_corpus_mini_paragraphs_knn to return classification
DROP FUNCTION IF EXISTS match_corpus_mini_paragraphs_knn(vector, double precision, integer);
CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_paragraphs d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- 6. Update match_corpus_mini_sentences_knn to return classification
DROP FUNCTION IF EXISTS match_corpus_mini_sentences_knn(vector, double precision, integer);
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;
```

### 3. Context Migration (`supabase_mini_corpus_context_migration.sql`)

Run after classification migration. Creates `context_tag` and `case_summary` tables.

```sql
-- Migration: Context-enriched sentence tables for RAG comparison testing
-- Run AFTER supabase_mini_corpus_classification_migration.sql

-- 1. Sentences with context tag
CREATE TABLE IF NOT EXISTS corpus_documents_mini_sentences_context_tag (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    classification TEXT NOT NULL,
    context_tag TEXT NOT NULL,
    section_title TEXT DEFAULT 'Main',
    section_number TEXT,
    sentence_index INTEGER DEFAULT 0,
    global_index INTEGER DEFAULT 0,
    court TEXT DEFAULT 'UKSC',
    decision TEXT DEFAULT 'majority',
    embedding vector(1792)
);

CREATE INDEX IF NOT EXISTS idx_mini_sentences_ct_embedding
    ON corpus_documents_mini_sentences_context_tag USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_ct_doc_id
    ON corpus_documents_mini_sentences_context_tag (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_ct_classification
    ON corpus_documents_mini_sentences_context_tag (classification);

-- 2. Sentences with case summary
CREATE TABLE IF NOT EXISTS corpus_documents_mini_sentences_case_summary (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    classification TEXT NOT NULL,
    case_summary TEXT NOT NULL,
    section_title TEXT DEFAULT 'Main',
    section_number TEXT,
    sentence_index INTEGER DEFAULT 0,
    global_index INTEGER DEFAULT 0,
    court TEXT DEFAULT 'UKSC',
    decision TEXT DEFAULT 'majority',
    embedding vector(1792)
);

CREATE INDEX IF NOT EXISTS idx_mini_sentences_cs_embedding
    ON corpus_documents_mini_sentences_case_summary USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_cs_doc_id
    ON corpus_documents_mini_sentences_case_summary (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_cs_classification
    ON corpus_documents_mini_sentences_case_summary (classification);

-- 3. RPC: KNN for context_tag table
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_context_tag_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    classification text,
    context_tag text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id, d.doc_id, d.text, d.classification, d.context_tag,
        d.section_title, d.section_number, d.sentence_index, d.global_index,
        d.court, d.decision,
        (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
    FROM corpus_documents_mini_sentences_context_tag d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;

-- 4. RPC: KNN for case_summary table
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_case_summary_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    classification text,
    case_summary text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id, d.doc_id, d.text, d.classification, d.case_summary,
        d.section_title, d.section_number, d.sentence_index, d.global_index,
        d.court, d.decision,
        (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
    FROM corpus_documents_mini_sentences_case_summary d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;
```

### 4. Statement Timeout (optional)

Run before Classification Comparison if you hit timeouts. Paragraphs/sentences: 300s. Context tag & case summary: 600s.

```sql
-- Increase statement timeout for mini corpus KNN RPCs
-- Run in Supabase SQL Editor before rerunning Classification Comparison.

-- match_corpus_mini_paragraphs_knn
CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM set_config('statement_timeout', '300000', true);  -- 300 seconds (5 min)
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_paragraphs d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- match_corpus_mini_sentences_knn
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM set_config('statement_timeout', '300000', true);
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- match_corpus_mini_sentences_indiv_class_knn
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_indiv_class_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int,
  court text,
  decision text,
  classification text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM set_config('statement_timeout', '300000', true);
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.section_title, d.section_number,
    d.sentence_index, d.global_index, d.court, d.decision,
    d.classification,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences_indiv_class d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- match_corpus_mini_sentences_context_tag_knn (600s)
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_context_tag_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    classification text,
    context_tag text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM set_config('statement_timeout', '600000', true);  -- 600 seconds (10 min)
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.classification, d.context_tag,
    d.section_title, d.section_number, d.sentence_index, d.global_index,
    d.court, d.decision,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences_context_tag d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

-- match_corpus_mini_sentences_case_summary_knn (600s)
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_case_summary_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    text text,
    classification text,
    case_summary text,
    section_title text,
    section_number text,
    sentence_index int,
    global_index int,
    court text,
    decision text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM set_config('statement_timeout', '600000', true);
  RETURN QUERY
  SELECT
    d.id, d.doc_id, d.text, d.classification, d.case_summary,
    d.section_title, d.section_number, d.sentence_index, d.global_index,
    d.court, d.decision,
    (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences_case_summary d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;
```

### 5. Rebuild Indexes (optional)

For faster KNN search on larger tables (~25k rows):

```sql
-- Rebuild ivfflat indexes with more lists for faster KNN search
DROP INDEX IF EXISTS idx_mini_sentences_ct_embedding;
CREATE INDEX idx_mini_sentences_ct_embedding
    ON corpus_documents_mini_sentences_context_tag USING ivfflat (embedding vector_cosine_ops) WITH (lists = 500);

DROP INDEX IF EXISTS idx_mini_sentences_cs_embedding;
CREATE INDEX idx_mini_sentences_cs_embedding
    ON corpus_documents_mini_sentences_case_summary USING ivfflat (embedding vector_cosine_ops) WITH (lists = 500);
```

### 6. Deduplicate (if needed)

Run each block repeatedly until 0 rows deleted. Keeps the row with lowest id per (doc_id, text).

```sql
-- PARAGRAPHS: Run repeatedly until 0 rows deleted
WITH dupes AS (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY doc_id, text ORDER BY id) AS rn
    FROM corpus_documents_mini_paragraphs
  ) t
  WHERE rn > 1
  LIMIT 500
)
DELETE FROM corpus_documents_mini_paragraphs
WHERE id IN (SELECT id FROM dupes);

-- SENTENCES (para_class): Uncomment and run after paragraphs done
-- WITH dupes AS (
--   SELECT id FROM (
--     SELECT id, ROW_NUMBER() OVER (PARTITION BY doc_id, text ORDER BY id) AS rn
--     FROM corpus_documents_mini_sentences
--   ) t
--   WHERE rn > 1
--   LIMIT 2000
-- )
-- DELETE FROM corpus_documents_mini_sentences
-- WHERE id IN (SELECT id FROM dupes);

-- SENTENCES INDIV_CLASS: Uncomment and run after sentences done
-- WITH dupes AS (
--   SELECT id FROM (
--     SELECT id, ROW_NUMBER() OVER (PARTITION BY doc_id, text ORDER BY id) AS rn
--     FROM corpus_documents_mini_sentences_indiv_class
--   ) t
--   WHERE rn > 1
--   LIMIT 2000
-- )
-- DELETE FROM corpus_documents_mini_sentences_indiv_class
-- WHERE id IN (SELECT id FROM dupes);
```
