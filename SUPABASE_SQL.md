# Supabase Database Schema

All SQL required to set up the SafeLaw database. Run these in the Supabase SQL Editor in order. See [LOCAL_SETUP.md](LOCAL_SETUP.md) for the full setup guide.

---

## 1. App Tables (required)

For the Reader (highlights, summaries) and auth.

### text_highlights

```sql
CREATE TABLE IF NOT EXISTS text_highlights (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    original_text TEXT,
    highlighted_text TEXT NOT NULL,
    summarization TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    summarized_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_text_highlights_user_id ON text_highlights(user_id);
```

### profiles

```sql
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    role TEXT DEFAULT 'Legal User'
);
```

---

## 2. Corpus Schema (required for RAG / corpus studies)

Run this first. Enables pgvector and creates the mini paragraph and sentence tables.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

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
CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_doc_id ON corpus_documents_mini_paragraphs (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_doc_section_idx ON corpus_documents_mini_paragraphs (doc_id, section_title, sentence_index);

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
CREATE INDEX IF NOT EXISTS idx_mini_sentences_doc_id ON corpus_documents_mini_sentences (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_doc_section_idx ON corpus_documents_mini_sentences (doc_id, section_title, sentence_index);

CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT d.id, d.doc_id, d.text, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision,
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
RETURNS TABLE (id bigint, doc_id text, text text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT d.id, d.doc_id, d.text, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision,
           (-1.0) * (d.embedding <#> query_embedding) AS similarity
    FROM corpus_documents_mini_sentences d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;
```

---

## 3. Classification Migration (run after schema)

Adds classification columns and the `corpus_documents_mini_sentences_indiv_class` table.

```sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'corpus_documents_mini_paragraphs' AND column_name = 'classification') THEN
    ALTER TABLE corpus_documents_mini_paragraphs ADD COLUMN classification TEXT;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_mini_paragraphs_classification ON corpus_documents_mini_paragraphs (classification);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'corpus_documents_mini_sentences' AND column_name = 'classification') THEN
    ALTER TABLE corpus_documents_mini_sentences ADD COLUMN classification TEXT;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_mini_sentences_classification ON corpus_documents_mini_sentences (classification);

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
CREATE INDEX IF NOT EXISTS idx_mini_sentences_indiv_doc_id ON corpus_documents_mini_sentences_indiv_class (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_indiv_classification ON corpus_documents_mini_sentences_indiv_class (classification);

CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_indiv_class_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, classification text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT d.id, d.doc_id, d.text, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision, d.classification,
         (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences_indiv_class d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

DROP FUNCTION IF EXISTS match_corpus_mini_paragraphs_knn(vector, double precision, integer);
CREATE OR REPLACE FUNCTION match_corpus_mini_paragraphs_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, classification text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT d.id, d.doc_id, d.text, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision, d.classification,
         (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_paragraphs d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;

DROP FUNCTION IF EXISTS match_corpus_mini_sentences_knn(vector, double precision, integer);
CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_knn(
  query_embedding vector(1792),
  similarity_threshold float DEFAULT -2.0,
  max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, classification text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT d.id, d.doc_id, d.text, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision, d.classification,
         (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
  FROM corpus_documents_mini_sentences d
  ORDER BY d.embedding <#> query_embedding
  LIMIT max_results;
END;
$$;
```

---

## 4. Context Migration (run after classification migration)

Creates `corpus_documents_mini_sentences_context_tag` and `corpus_documents_mini_sentences_case_summary` for sentence comparison v2–v4.

```sql
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
CREATE INDEX IF NOT EXISTS idx_mini_sentences_ct_doc_id ON corpus_documents_mini_sentences_context_tag (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_ct_classification ON corpus_documents_mini_sentences_context_tag (classification);

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
CREATE INDEX IF NOT EXISTS idx_mini_sentences_cs_doc_id ON corpus_documents_mini_sentences_case_summary (doc_id);
CREATE INDEX IF NOT EXISTS idx_mini_sentences_cs_classification ON corpus_documents_mini_sentences_case_summary (classification);

CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_context_tag_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, classification text, context_tag text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT d.id, d.doc_id, d.text, d.classification, d.context_tag, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision,
           (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
    FROM corpus_documents_mini_sentences_context_tag d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;

CREATE OR REPLACE FUNCTION match_corpus_mini_sentences_case_summary_knn(
    query_embedding vector(1792),
    similarity_threshold float DEFAULT -2.0,
    max_results int DEFAULT 10
)
RETURNS TABLE (id bigint, doc_id text, text text, classification text, case_summary text, section_title text, section_number text, sentence_index int, global_index int, court text, decision text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT d.id, d.doc_id, d.text, d.classification, d.case_summary, d.section_title, d.section_number, d.sentence_index, d.global_index, d.court, d.decision,
           (-1.0) * (d.embedding <#> query_embedding)::float AS similarity
    FROM corpus_documents_mini_sentences_case_summary d
    ORDER BY d.embedding <#> query_embedding
    LIMIT max_results;
END;
$$;
```

---

## 5. Optional: Statement Timeout

If KNN queries time out, run the updated RPCs with `set_config('statement_timeout', ...)`. See `backend/small_corpus/README.md` for the full SQL.

---

## 6. Optional: Rebuild Indexes

For larger tables (~25k rows), rebuild ivfflat indexes with more lists. See `backend/small_corpus/README.md` for the full SQL.

---

## 7. Optional: Deduplicate

If you have duplicate rows, run the deduplication blocks in `backend/small_corpus/README.md` repeatedly until 0 rows deleted.

---

## After Running SQL

Populate the corpus tables by running the ingestion scripts. See `backend/small_corpus/README.md` for the pipeline.
