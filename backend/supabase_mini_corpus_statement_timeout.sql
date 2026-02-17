-- Increase statement timeout for mini corpus KNN RPCs (avoids 'canceling statement due to statement timeout')
-- Run in Supabase SQL Editor before rerunning Classification Comparison. Timeout is 120 seconds (120000 ms).

-- 1. match_corpus_mini_paragraphs_knn
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

-- 2. match_corpus_mini_sentences_knn
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
  PERFORM set_config('statement_timeout', '300000', true);  -- 300 seconds (5 min)
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

-- 3. match_corpus_mini_sentences_indiv_class_knn
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
  PERFORM set_config('statement_timeout', '300000', true);  -- 300 seconds (5 min)
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
