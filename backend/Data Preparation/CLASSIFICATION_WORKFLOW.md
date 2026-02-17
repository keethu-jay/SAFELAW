# Mini Corpus Classification Workflow

This workflow classifies paragraphs from the mini corpus using LLM, creates sentence-level files, and ingests everything into Supabase with classifications.

## Overview

1. **Extract and Classify**: Extract paragraphs from HTML zip, classify each paragraph using LLM
2. **Create HTML Files**: Generate HTML files with classifications for paragraphs and sentences
3. **Move Old Files**: Archive old corpus files to `old/` folder
4. **Update Database**: Run migration SQL to add classification columns
5. **Ingest Data**: Upload classified data to Supabase with classifications in embeddings and columns

## Step-by-Step Instructions

### Step 1: Run Classification Script

```bash
cd backend
python "Data Preparation/classify_and_ingest_mini_corpus.py"
```

**What it does:**
- Extracts HTML files from `Small Corpus/parsed_cases_safelaw.zip`
- Extracts paragraphs with character counts
- Classifies each paragraph using GPT-4o-mini into 6 categories:
  - Introduction
  - Facts
  - Authority
  - Doctrine and Policy
  - Reasoning
  - Judgment
- Creates HTML files:
  - `*_paragraphs_classified.html` - paragraphs with classifications
  - `*_sentences_para_class.html` - sentences inheriting paragraph classifications
  - `*_sentences_indiv_class.html` - sentences with individual classifications
- Moves old files (`*_paragraphs.docx`, `*_sentences.docx`, etc.) to `Small Corpus/old/`

**Requirements:**
- `OPENAI_API_KEY` in `.env`
- `parsed_cases_safelaw.zip` in `Small Corpus/` folder

### Step 2: Run Database Migration

In Supabase SQL Editor, run:

```sql
-- Run supabase_mini_corpus_classification_migration.sql
```

**What it does:**
- Adds `classification` column to `corpus_documents_mini_paragraphs`
- Adds `classification` column to `corpus_documents_mini_sentences`
- Creates new table `corpus_documents_mini_sentences_indiv_class` for individually classified sentences
- Updates RPCs to return classification field

### Step 3: Run Ingestion Script

```bash
python "Data Preparation/ingest_classified_mini_corpus.py"
```

**What it does:**
- Reads HTML files created in Step 1
- For each text unit (paragraph/sentence):
  - Appends classification to text before embedding: `[Classification] {text}`
  - Stores original text (without prefix) in `text` column
  - Stores classification in `classification` column
  - Stores embedding (with classification context) in `embedding` column
- Inserts into:
  - `corpus_documents_mini_paragraphs` - paragraphs with classifications
  - `corpus_documents_mini_sentences` - sentences with paragraph classifications inherited
  - `corpus_documents_mini_sentences_indiv_class` - sentences with individual classifications

**Requirements:**
- `SUPABASE_URL`, `SUPABASE_KEY`, `ISAACUS_API_KEY` in `.env`
- Migration SQL already run

## Classification Categories

1. **Introduction**: Opening section establishing procedural history, parties, legal remedies sought
2. **Facts**: Factual narrative as determined by court - events, evidence, witness testimony
3. **Authority**: Existing legal sources - prior decisions, statutes, regulations, constitutional provisions
4. **Doctrine and Policy**: Substantive legal principles and underlying rationales, general rules, broader consequences
5. **Reasoning**: Analytical application of law to facts - deductive logic, evidence evaluation, rebuttal of arguments
6. **Judgment**: Final authoritative resolution - ultimate ruling, specific orders, granting/refusal of declarations

## File Structure

After running the scripts:

```
Small Corpus/
├── parsed_cases_safelaw.zip (source)
├── extracted_html/ (temporary, created during classification)
├── old/ (archived old files)
├── Ann_Kelly_*_paragraphs_classified.html
├── Ann_Kelly_*_sentences_para_class.html
├── Ann_Kelly_*_sentences_indiv_class.html
└── (same for Donoghue, McGee, McLoughlin, Norris)
```

## Database Tables

1. **corpus_documents_mini_paragraphs**
   - Paragraphs with classifications
   - `text`: original paragraph text
   - `classification`: paragraph classification
   - `embedding`: embedding of `[Classification] {text}`

2. **corpus_documents_mini_sentences**
   - Sentences inheriting paragraph classifications
   - `text`: original sentence text
   - `classification`: inherited from paragraph
   - `embedding`: embedding of `[Classification] {text}`

3. **corpus_documents_mini_sentences_indiv_class**
   - Sentences with individual classifications
   - `text`: original sentence text
   - `classification`: sentence's own classification
   - `embedding`: embedding of `[Classification] {text}`

## Notes

- Classifications are appended to text before embedding (like Corpus Studio) so embeddings capture classification context
- Original text is stored separately for display
- Classification is stored in a separate column for filtering/querying
- The `old/` folder preserves previous corpus files
