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
-- For normalized embeddings, -(embedding <#> query) equals cosine similarity.
-- Use these if cosine-distance RPC returns 0 similarity incorrectly.
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
