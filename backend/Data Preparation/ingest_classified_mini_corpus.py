#!/usr/bin/env python3
"""
Ingest classified mini corpus from HTML files into Supabase.

Reads HTML files created by classify_and_ingest_mini_corpus.py:
- *_sentences_para_class.html: sentences with paragraph classifications inherited
- *_sentences_indiv_class.html: sentences with individual classifications

For each sentence:
- Appends classification to text before embedding (like Corpus Studio)
- Stores classification in separate column
- Inserts into appropriate Supabase table

Requires: Run supabase_mini_corpus_classification_migration.sql first.
"""

import os
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
SMALL_CORPUS_DIR = BACKEND_DIR / "Small Corpus"

_env_path = BACKEND_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

DOC_ID_MAP = {
    "Ann_Kelly_(Plaintiff)_v_Fergus_Hennessy_(Defendant)": "Ann Kelly v Fergus Hennessy [1995] 3 IR 253",
    "Donoghue_v_Stevenson_[1932]_UKHL_100_(26_May_1932)": "Donoghue v Stevenson [1932] UKHL 100",
    "McGee_v._Attorney_General": "McGee v A.G. and Anor [1973] IESC 2",
    "McLoughlin_v_O'Brian": "McLoughlin v O'Brian [1982] UKHL 3",
    "Norris_v._Ireland": "Norris v A.G. [1983] IESC 3",
}


class ClassifiedSentenceParser(HTMLParser):
    """Parse HTML to extract sentences with classifications."""
    
    def __init__(self):
        super().__init__()
        self.sentences = []
        self.current_text = ""
        self.current_class = ""
        self.in_p = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True
            self.current_text = ""
            # Extract class (e.g., "para-introduction" or "sent-reasoning")
            for attr_name, attr_value in attrs:
                    if attr_name == 'class':
                        # Extract classification from class name (e.g., "introduction", "doctrine-and-policy")
                        class_val = (attr_value.split()[0] if attr_value else "").strip()
                        # Handle with or without para-/sent- prefix
                        if class_val.startswith('para-'):
                            class_val = class_val[5:]
                        elif class_val.startswith('sent-'):
                            class_val = class_val[5:]
                        self.current_class = class_val.replace('-', ' ').title() if class_val else ""
                        # Normalize classification names
                        if self.current_class:
                            # Map variations to standard names
                            class_lower = self.current_class.lower()
                            if 'introduction' in class_lower:
                                self.current_class = "Introduction"
                            elif 'facts' in class_lower:
                                self.current_class = "Facts"
                            elif 'authority' in class_lower:
                                self.current_class = "Authority"
                            elif 'doctrine' in class_lower or 'policy' in class_lower:
                                self.current_class = "Doctrine and Policy"
                            elif 'reasoning' in class_lower:
                                self.current_class = "Reasoning"
                            elif 'judgment' in class_lower:
                                self.current_class = "Judgment"
                        break
    
    def handle_endtag(self, tag):
        if tag == 'p' and self.in_p:
            text = self.current_text.strip()
            if text and self.current_class:
                self.sentences.append((text, self.current_class))
            self.in_p = False
            self.current_text = ""
            self.current_class = ""
    
    def handle_data(self, data):
        if self.in_p:
            self.current_text += data.strip() + " "


def parse_classified_html(html_path: Path) -> List[Tuple[str, str]]:
    """Parse HTML file and return list of (sentence, classification) tuples."""
    parser = ClassifiedSentenceParser()
    html_content = html_path.read_text(encoding="utf-8")
    parser.feed(html_content)
    return parser.sentences


def main():
    sys.path.insert(0, str(BACKEND_DIR / "src"))
    from embedding_helper import EmbeddingModel
    
    try:
        from supabase import create_client
    except ImportError:
        print("Install supabase: pip install supabase")
        sys.exit(1)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Set ISAACUS_API_KEY in .env")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)

    def embed_batch(texts: List[str], max_chars: int = 8000) -> List:
        """Embed texts, appending classification to each text before embedding."""
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

    BATCH_SIZE = 20

    # ---- Ingest paragraphs with classifications ----
    para_class_files = sorted(SMALL_CORPUS_DIR.glob("*_paragraphs_classified.html"))
    print(f"\nIngesting {len(para_class_files)} paragraph files with classifications into corpus_documents_mini_paragraphs...")

    try:
        supabase.table("corpus_documents_mini_paragraphs").delete().neq("id", 0).execute()
        print("  Cleared existing mini_paragraphs rows.")
    except Exception as e:
        print(f"  Note: Could not clear mini_paragraphs: {e}")

    global_idx = 0
    for html_path in para_class_files:
        stem = html_path.stem.replace("_paragraphs_classified", "")
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        
        paragraphs_with_class = parse_classified_html(html_path)
        print(f"  Processing {html_path.name}: {len(paragraphs_with_class)} paragraphs")
        
        for i in range(0, len(paragraphs_with_class), BATCH_SIZE):
            batch = paragraphs_with_class[i : i + BATCH_SIZE]
            # Append classification to text before embedding
            texts_with_class = [f"[{cls}] {text}" for text, cls in batch]
            embs = embed_batch(texts_with_class)
            
            if len(embs) != len(batch):
                print(f"  Embed mismatch for {html_path.name} batch")
                continue
            
            rows = []
            for j, ((text, classification), emb) in enumerate(zip(batch, embs)):
                rows.append({
                    "doc_id": doc_id,
                    "text": text,  # Store original text without classification prefix
                    "section_title": "Main",
                    "section_number": str(i + j + 1),
                    "sentence_index": i + j,
                    "global_index": global_idx,
                    "court": "UKSC",
                    "decision": "majority",
                    "classification": classification,
                    "embedding": emb.tolist(),
                })
                global_idx += 1
            
            try:
                supabase.table("corpus_documents_mini_paragraphs").insert(rows).execute()
            except Exception as e:
                print(f"  Insert error: {e}")
                for r in rows:
                    try:
                        supabase.table("corpus_documents_mini_paragraphs").insert([r]).execute()
                    except Exception as e2:
                        print(f"    Failed: {e2}")
        
        print(f"  Ingested {html_path.name}: {len(paragraphs_with_class)} paragraphs")

    # ---- Ingest sentences with paragraph classifications (inherited) ----
    para_class_files = sorted(SMALL_CORPUS_DIR.glob("*_sentences_para_class.html"))
    print(f"\nIngesting {len(para_class_files)} files with paragraph classifications into corpus_documents_mini_sentences...")

    try:
        supabase.table("corpus_documents_mini_sentences").delete().neq("id", 0).execute()
        print("  Cleared existing mini_sentences rows.")
    except Exception as e:
        print(f"  Note: Could not clear mini_sentences: {e}")

    global_idx = 0
    for html_path in para_class_files:
        # Extract doc_id from filename
        stem = html_path.stem.replace("_sentences_para_class", "")
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        
        sentences_with_class = parse_classified_html(html_path)
        print(f"  Processing {html_path.name}: {len(sentences_with_class)} sentences")
        
        for i in range(0, len(sentences_with_class), BATCH_SIZE):
            batch = sentences_with_class[i : i + BATCH_SIZE]
            # Append classification to text before embedding
            texts_with_class = [f"[{cls}] {text}" for text, cls in batch]
            embs = embed_batch(texts_with_class)
            
            if len(embs) != len(batch):
                print(f"  Embed mismatch for {html_path.name} batch")
                continue
            
            rows = []
            for j, ((text, classification), emb) in enumerate(zip(batch, embs)):
                rows.append({
                    "doc_id": doc_id,
                    "text": text,  # Store original text without classification prefix
                    "section_title": "Main",
                    "section_number": str(i + j + 1),
                    "sentence_index": i + j,
                    "global_index": global_idx,
                    "court": "UKSC",
                    "decision": "majority",
                    "classification": classification,
                    "embedding": emb.tolist(),
                })
                global_idx += 1
            
            try:
                supabase.table("corpus_documents_mini_sentences").insert(rows).execute()
            except Exception as e:
                print(f"  Insert error: {e}")
                for r in rows:
                    try:
                        supabase.table("corpus_documents_mini_sentences").insert([r]).execute()
                    except Exception as e2:
                        print(f"    Failed: {e2}")
        
        print(f"  Ingested {html_path.name}: {len(sentences_with_class)} sentences")

    # ---- Ingest sentences with individual classifications ----
    indiv_class_files = sorted(SMALL_CORPUS_DIR.glob("*_sentences_indiv_class.html"))
    print(f"\nIngesting {len(indiv_class_files)} files with individual classifications into corpus_documents_mini_sentences_indiv_class...")

    try:
        supabase.table("corpus_documents_mini_sentences_indiv_class").delete().neq("id", 0).execute()
        print("  Cleared existing mini_sentences_indiv_class rows.")
    except Exception as e:
        print(f"  Note: Could not clear mini_sentences_indiv_class: {e}")

    global_idx = 0
    for html_path in indiv_class_files:
        stem = html_path.stem.replace("_sentences_indiv_class", "")
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        
        sentences_with_class = parse_classified_html(html_path)
        print(f"  Processing {html_path.name}: {len(sentences_with_class)} sentences")
        
        for i in range(0, len(sentences_with_class), BATCH_SIZE):
            batch = sentences_with_class[i : i + BATCH_SIZE]
            # Append classification to text before embedding
            texts_with_class = [f"[{cls}] {text}" for text, cls in batch]
            embs = embed_batch(texts_with_class)
            
            if len(embs) != len(batch):
                print(f"  Embed mismatch for {html_path.name} batch")
                continue
            
            rows = []
            for j, ((text, classification), emb) in enumerate(zip(batch, embs)):
                rows.append({
                    "doc_id": doc_id,
                    "text": text,  # Store original text without classification prefix
                    "section_title": "Main",
                    "section_number": str(i + j + 1),
                    "sentence_index": i + j,
                    "global_index": global_idx,
                    "court": "UKSC",
                    "decision": "majority",
                    "classification": classification,
                    "embedding": emb.tolist(),
                })
                global_idx += 1
            
            try:
                supabase.table("corpus_documents_mini_sentences_indiv_class").insert(rows).execute()
            except Exception as e:
                print(f"  Insert error: {e}")
                for r in rows:
                    try:
                        supabase.table("corpus_documents_mini_sentences_indiv_class").insert([r]).execute()
                    except Exception as e2:
                        print(f"    Failed: {e2}")
        
        print(f"  Ingested {html_path.name}: {len(sentences_with_class)} sentences")

    print("\n✅ Classified mini corpus ingestion complete.")


if __name__ == "__main__":
    main()
