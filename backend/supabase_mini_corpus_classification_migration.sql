-- Migration: Add classification columns to mini corpus tables
-- Run this AFTER running supabase_mini_corpus_schema.sql
-- Run each section separately if you encounter errors

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

-- 2. Add classification column to sentences table (inherited from paragraph)
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
-- Must DROP first because return type changed (added classification column)
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
-- Must DROP first because return type changed (added classification column)
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
