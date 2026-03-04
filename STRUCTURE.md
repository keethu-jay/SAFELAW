# SAFELAW Directory Structure

This document walks through the project layout and how the pieces fit together.

---

## Top Level

```
SAFELAW/
├── README.md           # Project overview, pipeline, retrieval, issues
├── LOCAL_SETUP.md      # Setup guide: Supabase, env vars, run steps
├── SUPABASE_SQL.md     # All Supabase SQL (app tables, corpus schema, migrations)
├── STRUCTURE.md        # This file – directory walkthrough
├── backend/            # Data pipelines, server, retrieval, testing
├── frontend/           # Vite + React app (Reader, Writer, auth)
├── References/        # CorpusStudios and GP-TSM documentation
├── Final Dataset/     # Processed UK court XML (Supreme Court, Tribunal)
└── data/              # Raw data (gitignored); raw_xml from TNA API
```

---

## Data Directories (project root)

### `Final Dataset/`

Processed UK court case XML used for main corpus ingestion, baselines, and sentence comparison. Created by `dataset_processing.py` from raw XML.

| Path | Contents |
|------|----------|
| `Supreme Court (uksc)/` | UK Supreme Court cases |
| `Tribunal Court (ukut)/` | Upper Tribunal cases |
| `Tribunal Court (eat)/` | Employment Appeal Tribunal (if present) |

Each court folder has subfolders: `majority/`, `concurring/`, `dissenting/` – one XML file per case.

**Used by:** `main_corpus/scripts/supabase_ingestion.py`, `run_baseline_corpus_studio.py`, `run_baseline_for_test_files.py`, `run_classification_comparison.py`, `compare_case_similarity.py`, sentence comparison `_runner` (Classification_Comparison TSV).

**Path note:** Some scripts resolve `Final Dataset` from project root (`BACKEND_DIR.parent`), others from `backend/` (`BACKEND_DIR`). Ensure the folder exists where your script expects it.

### `data/`

Raw data (gitignored). Created when running TNA API ingestion.

| Path | Contents |
|------|----------|
| `raw_xml/` | Raw XML from TNA API – UK Supreme Court and Tribunal cases before processing |

**Used by:** `tna_api_ingestion.py` (writes here), `dataset_processing.py` (reads, processes into Final Dataset), `extract_test_cases.py`, baseline scripts.


---

## Backend (`backend/`)

The backend handles data preparation, ingestion, vector retrieval, embeddings, and the API server.

### Overview

| Directory | Purpose |
|-----------|---------|
| `small_corpus/` | Small curated corpus (5 base cases + BAILII extras) – data + scripts |
| `main_corpus/` | Full UK Supreme Court / Tribunal corpus from TNA API |
| `Data Preparation/` | Shared parsing, regex parsers, corpus initialization |
| `scripts/` | Pipeline orchestration, baselines, utilities |
| `testing_scripts/` | Sentence comparison (v1–v4), TSV utils, output |
| `server/` | FastAPI server (embeddings, vector search) |
| `src/` | Retrieval, embeddings, stores, GP-TSM logic |

---

### `backend/small_corpus/`

Small corpus for development and testing. Contains both data and scripts.

| Path | Contents |
|------|-----------|
| `extracted_html/` | Extracted HTML from BAILII (sanitized, ready for parsing) |
| `Additional Cases/` | Original BAILII HTML before conversion |
| `paragraphs_classified/` | Paragraph-level classified HTML output |
| `sentences_indiv_class/` | Sentence-level with per-sentence labels |
| `sentences_para_class/` | Sentence-level with paragraph-inherited labels |
| `old/` | Legacy outputs (docx, TSV) |
| `scripts/` | All small corpus scripts |
| `README.md` | SQL schema, migrations, pipeline steps |

**Key scripts in `small_corpus/scripts/`:**

- `classify_and_ingest_mini_corpus.py` – Extract, classify (LLM), create HTML
- `ingest_classified_mini_corpus.py` – Ingest paragraphs/sentences to Supabase
- `ingest_context_enriched_sentences.py` – Ingest context_tag and case_summary tables
- `run_sentence_context_comparison.py` – Run v1–v4 comparison (or via `--version N`)
- `convert_bailii_additional_cases.py` – Convert BAILII HTML to extracted format
- `check_classification_progress.py`, `verify_ingestion.py`, `verify_filtering.py`, etc.

---

### `backend/main_corpus/`

Full UK Supreme Court / Tribunal corpus ingestion.

| Path | Contents |
|------|-----------|
| `scripts/` | TNA API fetch, dataset processing, Supabase ingestion |

**Scripts:**

- `tna_api_ingestion.py` – Fetch cases from TNA API
- `dataset_processing.py` – Process dataset
- `supabase_ingestion.py` – Ingest into Supabase

---

### `backend/Data Preparation/`

Shared data preparation and parsing used by both small and main corpus.

| Path | Contents |
|------|-----------|
| `corpus_studio_initialization.py` | Corpus Studio setup |
| `dataset_processing.py` | Dataset processing |
| `supabase_ingestion.py` | Supabase ingestion helpers |
| `tna_api_ingestion.py` | TNA API helpers |
| `extract_test_cases.py` | Extract RAG test cases |
| `corpusstudio_implementation_pipeline.py` | Corpus Studio pipeline |
| `testing regex parsers/` | Regex-based judgment parsers |

**`testing regex parsers/`:**

- `central_parser.py` – Central parsing logic
- `config_loader.py` – Config loading
- `extract_cases.py`, `process_html_batch.py` – Batch extraction
- `court_config.yaml`, `legal_glossary_uk.yaml` – Parser configs
- `SUPREME_REGEX_NOTES.md` – Parser notes
- `supreme_samples/`, `output_json/` – Samples and parsed output

---

### `backend/scripts/`

Orchestration and utility scripts. Run from `backend/`.

| Script | Purpose |
|--------|---------|
| `run_full_pipeline.py` | Full pipeline: classify → ingest → context enrich → comparison |
| `run_baseline_corpus_studio.py` | Corpus Studio baseline |
| `run_baseline_for_test_files.py` | Test-file baseline |
| `run_baseline_mini_corpus.py` | Mini corpus baseline |
| `run_rebuild_indexes.py` | Rebuild DB indexes |
| `fill_semantic_columns.py` | Fill semantic columns |
| `compare_case_similarity.py` | Compare case similarity |

---

### `backend/testing_scripts/`

Sentence comparison and evaluation. Output goes to `testing_scripts/output/`.

| Script | Retrieval variant |
|--------|-------------------|
| `run_sentence_comparison_v1.py` | Label-filtered only |
| `run_sentence_comparison_v2.py` | Context tag |
| `run_sentence_comparison_v3.py` | Case summary |
| `run_sentence_comparison_v4.py` | Label-filter + context tag |

| File | Purpose |
|------|---------|
| `_runner.py` | Shared runner for comparison scripts |
| `tsv_utils.py` | TSV read/write utilities |
| `output/` | Generated TSVs and CSVs |

---

### `backend/server/`

| File | Purpose |
|------|---------|
| `server.py` | FastAPI server – embeddings, vector search, RAG endpoints |

---

### `backend/src/`

Core retrieval and embedding logic.

| File | Purpose |
|------|---------|
| `retriever.py` | Vector search / retrieval |
| `embedding_helper.py` | Embedding generation (Isaacus) |
| `stores.py` | Data stores |
| `gptsm_lite.py` | GP-TSM (grammar-preserving text saliency modulation) |

---

### `backend/Test Files/`

Test documents for baselines.

| Path | Contents |
|------|-----------|
| `raw docs/` | Raw RTF test docs |
| `xml docs/` | XML test docs |
| `fetch_tna_xml_for_raw_docs.py` | Fetch TNA XML for raw docs |
| `convert_docs_to_xml.py` | Convert docs to XML |

---

## Frontend (`frontend/`)

Vite + React app with Tailwind and Material UI.

### Overview

| Path | Contents |
|------|----------|
| `src/` | App source |
| `public/` | Static assets |
| `index.html` | Entry HTML |
| `package.json`, `vite.config.ts`, `tailwind.config.js` | Config |
| `README.md` | Frontend setup |

### `frontend/src/`

| Path | Contents |
|------|----------|
| `main.tsx` | Entry point |
| `App.tsx`, `App.css` | Root app |
| `index.css`, `styleguide.css` | Global styles |
| `lib/supabaseClient.ts` | Supabase client |
| `context/AuthContext.tsx` | Auth context |
| `components/` | Header, Footer, layout |
| `pages/` | Home, Login, Profile, Reader, Writer |

**Pages:**

- **Reader** – Highlight text, store summaries
- **Writer** – Corpus Studio: Tab to get RAG suggestions

---

## References (`References/`)

Documentation for CorpusStudios and GP-TSM.

| Path | Contents |
|------|----------|
| `CorpusStudios/` | VISUAL_FLOW.md, PAPER_RETRIEVAL_FLOW.md, CODE_WALKTHROUGH.md, etc. |

---

## Data Flow (High Level)

1. **Small corpus**: BAILII HTML → extract → classify (LLM) → ingest to Supabase (paragraphs, sentences, context_tag, case_summary).
2. **Main corpus**: TNA API → `data/raw_xml/` → `dataset_processing.py` → `Final Dataset/` → ingest to Supabase.
3. **Retrieval**: User query → embed → vector search (KNN) → return top matches.
4. **Testing**: Sentence comparison scripts (v1–v4) compare retrieval variants; output TSVs in `testing_scripts/output/`. Baselines read from `Final Dataset/` and `Classification_Comparison` TSV.

---

## Where to Start

| Goal | Start here |
|------|------------|
| Run the app | `LOCAL_SETUP.md` |
| Understand the project | `README.md` |
| Run corpus pipeline | `backend/scripts/run_full_pipeline.py` |
| Run sentence comparison | `backend/testing_scripts/run_sentence_comparison_v1.py` (or v2–v4) |
| Small corpus SQL & scripts | `backend/small_corpus/README.md` |
| Frontend details | `frontend/README.md` |
