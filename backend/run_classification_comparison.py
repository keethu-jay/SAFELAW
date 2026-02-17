#!/usr/bin/env python3
"""
Run classification comparison test: three versions of mini corpus retrieval.

Tests three corpus configurations:
1. Paragraphs with classifications
2. Sentences with paragraph-inherited classifications
3. Sentences with individual classifications

User input is classified and prefixed with [Classification] before embedding, so embeddings
match the format used in the corpus (labels make matching useful).

Usage:
  python run_classification_comparison.py

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY, OPENAI_API_KEY.
"""

import csv
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
_env_path = SCRIPT_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

INPUT_TSV = SCRIPT_DIR / "Simplified_Test_Input.tsv"
TEST_XML_DIR = SCRIPT_DIR / "Test Files" / "xml docs"
FINAL_DATASET_DIR = SCRIPT_DIR.parent / "Final Dataset"
RAW_XML_DIR = SCRIPT_DIR.parent / "data" / "raw_xml"

# Three corpus configurations to test
# Same classification categories as ingest - used to label user input before embedding
CLASSIFICATIONS = [
    "Introduction",
    "Facts",
    "Authority",
    "Doctrine and Policy",
    "Reasoning",
    "Judgment",
]

CLASSIFICATION_PROMPT = """You are classifying paragraphs from legal judgments into one of these categories:

1. **Introduction**: The opening section that establishes procedural history, identifies parties, and specifies legal remedies/orders/declarations being sought.

2. **Facts**: The factual narrative as determined by the court - sequence of events, medical/technical evidence, witness testimony summaries. Record of circumstances without legal analysis.

3. **Authority**: Identification of existing legal sources - prior judicial decisions, statutes, regulations, constitutional provisions. Established law before the court's interpretation.

4. **Doctrine and Policy**: Substantive legal principles and underlying rationales. General rules for application beyond immediate parties, discussion of broader consequences, moral considerations, systematic limits.

5. **Reasoning**: Analytical application of law to specific facts. Deductive logic, evaluation of evidence merits, specific rebuttal of party arguments. Mental process from facts/law to conclusion.

6. **Judgment**: Final authoritative resolution - ultimate ruling, specific orders issued, formal granting/refusal of declarations or damages.

Paragraph to classify (character count: {char_count}):
{paragraph}

Respond with ONLY the category name (Introduction, Facts, Authority, Doctrine and Policy, Reasoning, or Judgment)."""

CORPUS_CONFIGS = {
    "paragraphs_classified": {
        "rpc": "match_corpus_mini_paragraphs_knn",
        "description": "Paragraphs with classifications",
    },
    "sentences_para_class": {
        "rpc": "match_corpus_mini_sentences_knn",
        "description": "Sentences with paragraph-inherited classifications",
    },
    "sentences_indiv_class": {
        "rpc": "match_corpus_mini_sentences_indiv_class_knn",
        "description": "Sentences with individual classifications",
    },
}


def classify_paragraph(paragraph: str, char_count: int, model_client) -> str:
    """Classify a paragraph using LLM (same format as corpus ingest)."""
    prompt = CLASSIFICATION_PROMPT.format(
        char_count=char_count,
        paragraph=paragraph[:2000]
    )
    try:
        response = model_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal document classifier. Respond with only the category name."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        for cat in CLASSIFICATIONS:
            if cat.lower() in result.lower():
                return cat
        return "Reasoning"
    except Exception as e:
        print(f"  Classification error: {e}")
        return "Reasoning"


def load_input_rows() -> List[List[str]]:
    """Load rows by splitting on first two tabs so Test Paragraph can contain quotes."""
    rows = []
    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return rows
    # Skip header
    for line in lines[1:]:
        line = line.rstrip("\n\r")
        parts = line.split("\t", 2)
        court_opinion = (parts[0] if len(parts) > 0 else "").strip()
        file_name = (parts[1] if len(parts) > 1 else "").strip()
        test_para = (parts[2] if len(parts) > 2 else "").strip()
        if court_opinion or file_name or test_para:
            rows.append([court_opinion, file_name, test_para])
    return rows


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def find_xml_file(case_name: str, search_dirs: List[Path]) -> Path | None:
    raw = (case_name or "").strip().strip("()").replace(".xml", "")
    if not raw:
        return None
    targets = [normalize_case_name(raw)]
    no_cite = re.sub(r"\s*\[\d{4}\][^\]]*\]?\s*", " ", raw).strip()
    if no_cite and no_cite != raw:
        targets.append(normalize_case_name(no_cite))
    for target_norm in targets:
        target_prefix = target_norm.replace("...", "").strip()
        if len(target_prefix) > 50:
            target_prefix = target_prefix[:50]
        for base_dir in search_dirs:
            base = Path(base_dir)
            if not base.exists():
                continue
            for xml_path in base.rglob("*.xml"):
                stem_norm = normalize_case_name(xml_path.stem)
                if stem_norm == target_norm:
                    return xml_path
                if target_prefix and len(target_prefix) >= 8 and stem_norm.startswith(target_prefix[:30]):
                    return xml_path
                if target_prefix and stem_norm.startswith(target_prefix.split()[0]) and len(stem_norm) > 10:
                    if sum(1 for w in target_prefix.split()[:5] if w in stem_norm) >= 2:
                        return xml_path
    return None


def extract_full_text(file_path: Path) -> str:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        parts = [t.strip() for t in root.itertext() if t and t.strip()]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception:
        return ""


def run_for_corpus(corpus_key: str, config: Dict[str, str], row_indices: List[int] = None, update_tsv: bool = False, use_classification: bool = True) -> Path:
    """Run test for one corpus configuration."""
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("Error: numpy is required for embeddings. Run: pip install numpy")
        sys.exit(1)
    sys.path.insert(0, str(SCRIPT_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

    if not INPUT_TSV.exists():
        print(f"Input not found: {INPUT_TSV}")
        sys.exit(1)

    rows = load_input_rows()
    print(f"\n=== {config['description']} ===")
    print(f"Loaded {len(rows)} rows from {INPUT_TSV}")

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Set ISAACUS_API_KEY in .env")
        sys.exit(1)

    # OpenAI client for classification (labels user input before embedding)
    openai_client = None
    if use_classification:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            print("Set OPENAI_API_KEY in .env for classification")
            sys.exit(1)
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)

    supabase = create_client(supabase_url, supabase_key)
    rpc_name = config["rpc"]
    print(f"Using RPC: {rpc_name}")
    search_dirs = [d for d in [FINAL_DATASET_DIR, RAW_XML_DIR, TEST_XML_DIR] if Path(d).exists()]

    def embed_batch(texts, max_chars=8000):
        if not texts:
            return []
        truncated = [t[:max_chars] + ("..." if len(t) > max_chars else "") for t in texts if t and str(t).strip()]
        if not truncated:
            import numpy as np
            return [np.zeros(1792) for _ in texts]
        try:
            resp = model.client.embeddings.create(
                model=model.model_name, texts=truncated, task="retrieval/document"
            )
            import numpy as np
            return [np.array(e.embedding) for e in resp.embeddings]
        except Exception as e:
            print(f"  Embed failed: {e}")
            return []

    def get_top_10(test_paragraph: str, source_file: str, retries: int = 5, rpc_override: str = None):
        """Get top 10 suggestions, filtering same-case and ensuring no duplicates."""
        if not (test_paragraph or test_paragraph.strip()):
            return []
        embs = embed_batch([test_paragraph.strip()[:8000]])
        if not embs:
            return []
        
        source_norm = ""
        if source_file:
            source_norm = normalize_case_name(source_file.replace(".xml", ""))
        
        seen_texts = set()  # Track seen suggestion texts to avoid duplicates
        
        rpc = rpc_override or rpc_name
        for attempt in range(retries):
            try:
                max_res = 50 if rpc == "match_corpus_mini_sentences_knn" else 500
                r = supabase.rpc(
                    rpc,
                    {
                        "query_embedding": embs[0].tolist(),
                        "similarity_threshold": -2.0,
                        "max_results": max_res,
                    },
                ).execute()
                hits = r.data or []
                
                # Filter: same-case and duplicates
                filtered = []
                for hit in hits:
                    doc_id = (hit.get("doc_id") or "").strip()
                    text = (hit.get("text") or "").strip()
                    
                    # Skip same case
                    if source_norm and doc_id:
                        if normalize_case_name(doc_id) == source_norm:
                            continue
                    
                    # Skip duplicates (same text already seen)
                    text_key = text.lower()[:200]  # Use first 200 chars as key
                    if text_key in seen_texts:
                        continue
                    seen_texts.add(text_key)
                    
                    filtered.append(hit)
                    if len(filtered) >= 10:
                        break
                
                return filtered[:10]
            except Exception as e:
                print(f"  RPC error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(5)  # Longer delay for timeout recovery
        return []

    def cosine_sim(a, b):
        import numpy as np
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    def compute_full_doc(path1: Path, path2: Path) -> float:
        t1, t2 = extract_full_text(path1), extract_full_text(path2)
        if not t1 or not t2:
            return 0.0
        embs = embed_batch([t1[:8000], t2[:8000]])
        if len(embs) < 2:
            return 0.0
        return round(cosine_sim(embs[0], embs[1]), 4)

    out_header = [
        "Court/Opinion Type",
        "File Name",
        "Test Paragraph (To Paste)",
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores",
        "Top Suggestion",
        "Suggestion 1 Citation",
    ]
    for i in range(2, 11):
        out_header.append(f"Suggestion {i} Text")
        out_header.append(f"Suggestion {i} Citation")

    existing_rows = []
    if update_tsv and row_indices is not None:
        output_path = SCRIPT_DIR / f"Classification_Comparison_{corpus_key}.tsv"
        if not output_path.exists():
            print(f"  Error: --update-tsv requires existing {output_path}")
            sys.exit(1)
        with open(output_path, "r", encoding="utf-8") as f:
            rdr = csv.reader(f, delimiter="\t", quotechar='"')
            header = next(rdr)
            existing_rows = [next(rdr) for _ in range(len(rows))]
        print(f"  Loaded existing TSV, re-running rows {[i+1 for i in row_indices]}")

    output_rows = []
    for idx, (court_opinion, file_name, test_para) in enumerate(rows):
        if update_tsv and row_indices is not None and idx not in row_indices:
            output_rows.append(existing_rows[idx])
            continue
        para_sim = ""
        full_doc_sim = ""
        semantic_scores_col = ""
        top_suggestion_col = ""
        suggestion_texts = [""] * 10
        suggestion_citations = [""] * 10

        def _float_sim(hit):
            v = hit.get("similarity")
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            return None

        # Classify and label user input before embedding (matches corpus format - makes labels useful)
        if use_classification and openai_client:
            cls = classify_paragraph(test_para, len(test_para), openai_client)
            text_to_embed = f"[{cls}] {test_para.strip()}" if test_para else ""
        else:
            text_to_embed = test_para.strip() if test_para else ""
        # When updating incomplete rows for sentences_para_class, use indiv_class directly (no timeout, 10 suggestions)
        use_indiv_for_update = update_tsv and rpc_name == "match_corpus_mini_sentences_knn"
        top10 = get_top_10(text_to_embed, file_name, rpc_override="match_corpus_mini_sentences_indiv_class_knn" if use_indiv_for_update else None)
        # Retry failed rows (timeouts) - no empty rows allowed
        if len(top10) == 0 and rpc_name == "match_corpus_mini_sentences_knn":
            for retry in range(4):
                time.sleep(10)
                top10 = get_top_10(text_to_embed, file_name)
                if top10:
                    print(f"  Row {idx+1} succeeded on retry {retry+1}")
                    break
        # Fallback: use indiv_class RPC when para_class times out (same embedding, different table)
        if len(top10) == 0 and rpc_name == "match_corpus_mini_sentences_knn":
            top10 = get_top_10(text_to_embed, file_name, rpc_override="match_corpus_mini_sentences_indiv_class_knn")
            if top10:
                print(f"  Row {idx+1} using fallback (indiv_class) - para_class RPC timed out")
        if len(top10) == 0:
            print(f"  Warning: Row {idx+1} - no cross-case suggestions after retries and fallback")
        # Brief pause between rows for sentences RPC
        if rpc_name == "match_corpus_mini_sentences_knn" and idx < len(rows) - 1:
            time.sleep(3)
        
        if len(top10) >= 1:
            first_sim = _float_sim(top10[0])
            if first_sim is not None:
                para_sim = round(first_sim, 4)

        for i, hit in enumerate(top10[:10]):
            suggestion_texts[i] = (hit.get("text") or "").strip()
            suggestion_citations[i] = (hit.get("doc_id") or "").strip()
        
        scores = [_float_sim(h) or 0.0 for h in top10[:10]]
        if scores:
            semantic_scores_col = ", ".join(f"{s:.4f}" for s in scores)
            first_text = suggestion_texts[0]
            doc_id = suggestion_citations[0]
            top_suggestion_col = f"{first_text} ({doc_id})" if doc_id else first_text
            
            path_source = find_xml_file(file_name.replace(".xml", ""), search_dirs) or find_xml_file(file_name, search_dirs)
            path_sugg = find_xml_file(doc_id, search_dirs)
            if path_source and path_sugg:
                full_doc_sim = compute_full_doc(path_source, path_sugg)

        empty_placeholder = "N/A"
        cells = [court_opinion or empty_placeholder, file_name or empty_placeholder, test_para or empty_placeholder]
        cells += [str(para_sim) if para_sim != "" else "0.0", str(full_doc_sim) if full_doc_sim != "" else "0.0"]
        cells += [semantic_scores_col if semantic_scores_col else "0.0", top_suggestion_col if top_suggestion_col else empty_placeholder]
        cells += [suggestion_citations[0] if suggestion_citations[0] else empty_placeholder]  # Suggestion 1 Citation
        for i in range(1, 10):
            cells.append(suggestion_texts[i] if suggestion_texts[i] else empty_placeholder)
            cells.append(suggestion_citations[i] if suggestion_citations[i] else empty_placeholder)
        
        output_rows.append(cells)
        print(f"Row {idx + 1}/{len(rows)}: {file_name} - para_sim={para_sim}, suggestions={len(top10)}")

    def sanitize_cell(s) -> str:
        if s is None:
            return ""
        if not isinstance(s, str):
            s = str(s)
        return s.replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()

    output_path = SCRIPT_DIR / f"Classification_Comparison_{corpus_key}.tsv"
    n_cols = len(out_header)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerow(out_header)
        for r in output_rows:
            cells = [sanitize_cell(c) for c in r]
            while len(cells) < n_cols:
                cells.append("")
            w.writerow(cells[:n_cols])
    print(f"\nSaved: {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", choices=list(CORPUS_CONFIGS.keys()), default=None,
                        help="Run only this corpus (default: all three)")
    parser.add_argument("--rows", type=str, default=None,
                        help="Comma-separated 1-based row indices to run (e.g. 1,4,5,7). Use with --corpus and --update-tsv.")
    parser.add_argument("--update-tsv", action="store_true",
                        help="Load existing TSV, run only --rows, merge and save. Requires --corpus and --rows.")
    parser.add_argument("--no-classification", action="store_true",
                        help="Skip classifying user input - embed raw text only (for comparing label impact on scores)")
    args = parser.parse_args()
    
    row_indices = None
    if args.rows:
        row_indices = [int(x.strip()) - 1 for x in args.rows.split(",") if x.strip()]
    
    print("Running classification comparison test...")
    if args.corpus:
        configs = [(args.corpus, CORPUS_CONFIGS[args.corpus])]
        print(f"Running corpus: {args.corpus}\n")
    else:
        configs = list(CORPUS_CONFIGS.items())
        print("Testing three corpus configurations:\n")
    
    for corpus_key, config in configs:
        run_for_corpus(corpus_key, config, row_indices=row_indices, update_tsv=args.update_tsv, use_classification=not args.no_classification)
    
    print("\nDone. TSV file(s) generated:")
    for corpus_key, _ in configs:
        print(f"  - Classification_Comparison_{corpus_key}.tsv")


if __name__ == "__main__":
    main()
