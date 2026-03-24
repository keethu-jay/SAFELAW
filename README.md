# SAFELAW

Skill-Augmenting Framework for Enhanced Legal Analysis & Writing

This tool combines the logic behind CorpusStudios and GP-TSM (Grammar-Preserving Text Saliency Modulation) to support current workflows in the legal field. Built as a Major Qualifying Project at Worcester Polytechnic Institute by Brett Gerlach, Keerthana Jayamoorthy, and Julian Mariscal, under the guidance of Professor Erin Solovey (WPI), Professor Brian Flanagan (Maynooth), Professor Elena Glassman (Harvard), and Chelse Swoopes (Harvard).

---

## What We Started With

- CorpusStudios: a legal RAG tool for retrieving relevant case passages
- GP-TSM: grammar-preserving text saliency modulation
- Goal: combine these into a single tool that fits real legal workflows

---

## What Was Done

### Data Pipeline

- **Small corpus**: 5 curated cases (Donoghue, McGee, Norris, McLoughlin, Ann Kelly) plus additional BAILII cases. Extracted from HTML, classified by paragraph/sentence (Introduction, Facts, Authority, Doctrine and Policy, Reasoning, Judgment), ingested into Supabase with embeddings.
- **Main corpus**: Full UK Supreme Court / Tribunal dataset from TNA API, processed and ingested.
- **Classification**: LLM-based (GPT-4o-mini or Gemini) for paragraph and sentence labels. Labels are prefixed to text before embedding so retrieval matches on both content and role.
- **Context enrichment**: Two variants for sentence retrieval—context_tag (case date, judges, para preview) and case_summary (first ~500 chars of judgment). Used to compare retrieval quality.

### Retrieval

- Vector search via Supabase/pgvector. Embeddings from kanon-2-embedder (legal-domain).
- Initially used cosine distance (`<=>`) in RPCs; all similarity scores came back 0. Switched to inner product (`<#>`) KNN—same conceptual similarity for normalized embeddings, but scores work. No clear root cause for the cosine failure.
- Env vars: `RAG_CORPUS` (main, mini_paragraphs, mini_sentences) and `RAG_MATCH_FN` (cosine, knn). Server reads these at startup. Restart backend after changing.

### Testing

- Sentence comparison scripts (v1–v4) compare retrieval variants: label-filtered only, context tag, case summary, label-filtered + context tag.
- Output TSVs go to `backend/testing_scripts/output/`.
- Baselines for Corpus Studio and test files for semantic comparison.

---

## Issues & Limitations

### Tab Sometimes Shows No Suggestions (0) Then Fills on Retry

When you press Tab in Corpus Studio and get no suggestions or 0 similarity, but a second Tab works:

1. **Cold start** – First request after idle can hit a waking server; that request may time out or return empty.
2. **Timeout** – Embedding + vector search can take a few seconds. Short frontend/gateway timeouts can cut off the first request.
3. **Race / debouncing** – Multiple Tabs before the first response can overwrite or ignore the first response.
4. **Backend/DB briefly down** – A single failed response gives 0 or blank; next Tab triggers a new request that succeeds.

So it’s usually transient (cold start, timeout, race) rather than a bug in ordering. The baseline scripts avoid this by only recording rows when all 10 suggestions are non-blank.

### Other Limitations

- Regex-based parsing of judgments is brittle; different court formats break it.
- Sentence splitting can truncate at legal abbreviations (v., p., Ltd.)—handled with placeholder protection.
- Classification is LLM-dependent; rate limits and cost apply.
- Mini corpus is small (5 base cases + extras); main corpus is larger but still UK-focused.

---

## Repository Layout

See **[STRUCTURE.md](STRUCTURE.md)** for a full directory walkthrough.

- `frontend/` – Vite + React client, Tailwind + Material UI
- `backend/` – data prep, server, scripts
- `References/` – CorpusStudios, GP-TSM docs

### Backend

- `backend/small_corpus/` – Small corpus data, scripts, README with SQL
- `backend/main_corpus/` – Main corpus ingestion scripts
- `backend/Data Preparation/` – Shared prep (corpus_studio_initialization, parsers)
- `backend/scripts/` – Run scripts (baselines, full pipeline, etc.)
- `backend/testing_scripts/` – Sentence comparison v1–v4, tsv_utils, `_runner`
- `backend/testing_scripts/output/` – Generated TSVs and CSVs
- `backend/src/` – Embedding helper, stores, retriever

---

## Frontend

- React, TypeScript, Vite, React Router, Tailwind, Material UI, ESLint

---

## Backend

### Sentence Comparison TSVs

From `backend/`:

```bash
python testing_scripts/run_sentence_comparison_v1.py   # label-filtered
python testing_scripts/run_sentence_comparison_v2.py   # context tag
python testing_scripts/run_sentence_comparison_v3.py   # case summary
python testing_scripts/run_sentence_comparison_v4.py   # label-filter + context tag
# or: python small_corpus/scripts/run_sentence_context_comparison.py [--version N]
```

Output: `backend/testing_scripts/output/Classification_Comparison_sentences_v*.tsv`

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```
