#!/usr/bin/env python3
"""
Ingest context-enriched sentences into Supabase (context_tag and case_summary tables).

Requires:
- Run supabase_mini_corpus_context_migration.sql first
- Run extract_case_metadata.py to build case_metadata.json
- paragraphs_classified and sentences_indiv_class HTML files

Context tag format: "ShortName Year Judges. First 50-100 chars of paragraph."
Case summary: First 400-500 chars of judgment (or LLM-generated - extend later).
"""

import argparse
import json
import os
import sys
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
SMALL_CORPUS_DIR = BACKEND_DIR / "small_corpus"
PARA_DIR = SMALL_CORPUS_DIR / "paragraphs_classified"
SENT_DIR = SMALL_CORPUS_DIR / "sentences_indiv_class"
METADATA_PATH = BACKEND_DIR / "case_metadata.json"  # Built by extract_case_metadata.py

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


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    return text.replace("\u0000", " ")


# PARSING: CLASSIFIED SENTENCES
class ClassifiedSentenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sentences: List[Tuple[str, str]] = []
        self.current_text = ""
        self.current_class = ""
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
            self.current_text = ""
            for attr_name, attr_value in attrs:
                if attr_name == "class":
                    class_val = (attr_value.split()[0] if attr_value else "").strip()
                    if class_val.startswith("para-"):
                        class_val = class_val[5:]
                    elif class_val.startswith("sent-"):
                        class_val = class_val[5:]
                    self.current_class = class_val.replace("-", " ").title() if class_val else ""
                    for lower, std in [
                        ("introduction", "Introduction"),
                        ("facts", "Facts"),
                        ("authority", "Authority"),
                        ("doctrine", "Doctrine and Policy"),
                        ("policy", "Doctrine and Policy"),
                        ("reasoning", "Reasoning"),
                        ("judgment", "Judgment"),
                    ]:
                        if lower in self.current_class.lower():
                            self.current_class = std
                            break
                    break

    def handle_endtag(self, tag):
        if tag == "p" and self.in_p:
            t = self.current_text.strip()
            if t and self.current_class:
                self.sentences.append((t, self.current_class))
            self.in_p = False

    def handle_data(self, data):
        if self.in_p:
            self.current_text += data.strip() + " "


class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs: List[Tuple[str, str]] = []
        self.current_text = ""
        self.current_class = ""
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
            self.current_text = ""
            for attr_name, attr_value in attrs:
                if attr_name == "class":
                    class_val = (attr_value.split()[0] if attr_value else "").strip()
                    if class_val.startswith("para-"):
                        class_val = class_val[5:]
                    self.current_class = class_val.replace("-", " ").title() if class_val else "Reasoning"
                    for lower, std in [("introduction", "Introduction"), ("facts", "Facts"), ("authority", "Authority"),
                                       ("doctrine", "Doctrine and Policy"), ("policy", "Doctrine and Policy"),
                                       ("reasoning", "Reasoning"), ("judgment", "Judgment")]:
                        if lower in self.current_class.lower():
                            self.current_class = std
                            break
                    break

    def handle_endtag(self, tag):
        if tag == "p" and self.in_p:
            t = self.current_text.strip()
            if t:
                self.paragraphs.append((t, self.current_class))
            self.in_p = False

    def handle_data(self, data):
        if self.in_p:
            self.current_text += data.strip() + " "


def parse_sentences(html_path: Path) -> List[Tuple[str, str]]:
    parser = ClassifiedSentenceParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    return parser.sentences


def parse_paragraphs(html_path: Path) -> List[Tuple[str, str]]:
    parser = ParagraphParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    return parser.paragraphs


# Match classify_and_ingest_mini_corpus split logic (avoids splitting on v., p., Ltd., etc.)
_ABBR_PLACEHOLDER = "\x00"
_ABBREVIATIONS = [
    " pp. ", " I.L.R.M. ", " A.L.R. ", " W.L.R. ", " et al. ", " e.g. ", " i.e. ",
    " v. ", " p. ", " Ltd. ", " Co. ", " Inc. ", " No. ", " Vol. ", " U.S. ",
    " A.C. ", " K.B. ", " Q.B. ", " I.R. ", " S.C. ", " E.R. ", " App. ", " L.R. ",
    " etc. ", " cf. ", " para. ", " art. ", " Dr. ", " Mr. ", " Mrs. ", " Prof. ",
]


def _split_sentences(text: str) -> List[str]:
    import re
    protected = text
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr, abbr[:-2] + _ABBR_PLACEHOLDER + abbr[-1])
    parts = re.split(r"(?<=[.!?])\s+", protected)
    return [s.replace(_ABBR_PLACEHOLDER, ".").strip() for s in parts if s.strip() and len(s.strip()) >= 10]


def align_sentences_with_paragraphs(
    para_tuples: List[Tuple[str, str]],
    sent_tuples: List[Tuple[str, str]],
) -> List[Tuple[str, str, str]]:
    """
    Match sentences (from indiv_class) to their source paragraphs by index.
    Sentences are produced in order: para1_sent1..para1_sentN, para2_sent1.., etc.
    Returns (sentence, classification, paragraph_preview).
    """
    sent_idx = 0
    result = []
    for para_text, _ in para_tuples:
        para_sents = _split_sentences(para_text)
        preview = para_text.strip()[:100].replace("\n", " ")
        for _ in para_sents:
            if sent_idx < len(sent_tuples):
                sent_text, sent_class = sent_tuples[sent_idx]
                result.append((sent_text, sent_class, preview))
                sent_idx += 1
    while sent_idx < len(sent_tuples):
        sent_text, sent_class = sent_tuples[sent_idx]
        result.append((sent_text, sent_class, ""))
        sent_idx += 1
    return result


# SUPABASE INSERTION
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="Clear tables and full re-ingest")
    ap.add_argument("--context-tag-only", action="store_true", help="Only ingest context_tag table")
    ap.add_argument("--case-summary-only", action="store_true", help="Only ingest case_summary table")
    args = ap.parse_args()

    if not METADATA_PATH.exists():
        print("Run extract_case_metadata.py first to create case_metadata.json")
        sys.exit(1)
    with open(METADATA_PATH, encoding="utf-8") as f:
        case_metadata = json.load(f)

    sys.path.insert(0, str(BACKEND_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

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

    def embed_batch(texts: List[str]) -> List:
        if not texts:
            return []
        truncated = [t[:8000] + ("..." if len(t) > 8000 else "") for t in texts if t and str(t).strip()]
        if not truncated:
            import numpy as np
            return [np.zeros(1792) for _ in texts]
        try:
            resp = model.client.embeddings.create(model=model.model_name, texts=truncated, task="retrieval/document")
            import numpy as np
            return [np.array(e.embedding) for e in resp.embeddings]
        except Exception as e:
            print(f"  Embed failed: {e}")
            return []

    indiv_files = sorted(SENT_DIR.glob("*_sentences_indiv_class.html"))
    if not indiv_files:
        indiv_files = sorted(SMALL_CORPUS_DIR.glob("*_sentences_indiv_class.html"))
    indiv_files = [f for f in indiv_files if "Cromane_test" not in f.stem]

    para_files = sorted(PARA_DIR.glob("*_paragraphs_classified.html"))
    if not para_files:
        para_files = sorted(SMALL_CORPUS_DIR.glob("*_paragraphs_classified.html"))
    para_files = [f for f in para_files if "Cromane_test" not in f.stem]

    para_by_stem = {}
    for p in para_files:
        stem = p.stem.replace("_paragraphs_classified", "")
        para_by_stem[stem] = parse_paragraphs(p)

    if args.full:
        for table in ["corpus_documents_mini_sentences_context_tag", "corpus_documents_mini_sentences_case_summary"]:
            if (args.context_tag_only and "context_tag" not in table) or (args.case_summary_only and "case_summary" not in table):
                continue
            try:
                supabase.table(table).delete().neq("id", 0).execute()
                print(f"  Cleared {table}")
            except Exception as e:
                print(f"  Note: {e}")

    BATCH_SIZE = 15
    global_idx = 0
    for html_path in indiv_files:
        stem = html_path.stem.replace("_sentences_indiv_class", "")
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))

        meta = case_metadata.get(doc_id) or case_metadata.get(stem) or {}
        short_name = meta.get("short_name", doc_id.split("[")[0].strip() if "[" in doc_id else doc_id)
        year = meta.get("year", "")
        judges = meta.get("judges", [])
        judges_str = ", ".join(judges[:6]) if judges else "Various"

        para_tuples = para_by_stem.get(stem, [])
        sent_tuples = parse_sentences(html_path)
        aligned = align_sentences_with_paragraphs(para_tuples, sent_tuples)

        case_summary_text = ""
        if para_tuples:
            first_paras = " ".join(p[0] for p in para_tuples[:3])
            case_summary_text = first_paras[:500].replace("\n", " ").strip()

        if not args.case_summary_only:
            rows_ct = []
            for gidx, (sent_text, sent_class, para_preview) in enumerate(aligned):
                context_tag = f"{short_name} {year} Judges: {judges_str}. {para_preview}"
                text_to_embed = f"[{sent_class}] {context_tag} {_sanitize_text(sent_text)}"
                rows_ct.append({
                    "doc_id": doc_id,
                    "text": _sanitize_text(sent_text),
                    "classification": sent_class,
                    "context_tag": context_tag[:500],
                    "section_title": "Main",
                    "section_number": str(gidx + 1),
                    "sentence_index": gidx,
                    "global_index": global_idx + gidx,
                    "court": "UKSC",
                    "decision": "majority",
                    "embedding": None,
                })

            for i in range(0, len(rows_ct), BATCH_SIZE):
                batch = rows_ct[i : i + BATCH_SIZE]
                texts = [f"[{r['classification']}] {r['context_tag']} {r['text']}" for r in batch]
                embs = embed_batch(texts)
                if len(embs) != len(batch):
                    continue
                for j, r in enumerate(batch):
                    r["embedding"] = embs[j].tolist()
                try:
                    supabase.table("corpus_documents_mini_sentences_context_tag").insert(batch).execute()
                except Exception as ex:
                    print(f"  Batch insert error: {ex}, falling back to row-by-row")
                    for row in batch:
                        try:
                            supabase.table("corpus_documents_mini_sentences_context_tag").insert(row).execute()
                        except Exception as e2:
                            print(f"    Row insert failed: {e2}")
            print(f"  Ingested context_tag: {doc_id} ({len(rows_ct)} sentences)")

        gidx_offset = global_idx
        if not args.context_tag_only:
            rows_cs = []
            for gidx, (sent_text, sent_class, _) in enumerate(aligned):
                text_to_embed = f"[{sent_class}] {case_summary_text} {_sanitize_text(sent_text)}"
                rows_cs.append({
                    "doc_id": doc_id,
                    "text": _sanitize_text(sent_text),
                    "classification": sent_class,
                    "case_summary": case_summary_text,
                    "section_title": "Main",
                    "section_number": str(gidx + 1),
                    "sentence_index": gidx,
                    "global_index": global_idx + gidx,
                    "court": "UKSC",
                    "decision": "majority",
                    "embedding": None,
                })

            for i in range(0, len(rows_cs), BATCH_SIZE):
                batch = rows_cs[i : i + BATCH_SIZE]
                texts = [f"[{r['classification']}] {r['case_summary']} {r['text']}" for r in batch]
                embs = embed_batch(texts)
                if len(embs) != len(batch):
                    continue
                for j, r in enumerate(batch):
                    r["embedding"] = embs[j].tolist()
                try:
                    supabase.table("corpus_documents_mini_sentences_case_summary").insert(batch).execute()
                except Exception as ex:
                    print(f"  Batch insert error: {ex}, falling back to row-by-row")
                    for row in batch:
                        try:
                            supabase.table("corpus_documents_mini_sentences_case_summary").insert(row).execute()
                        except Exception as e2:
                            print(f"    Row insert failed: {e2}")
            print(f"  Ingested case_summary: {doc_id} ({len(rows_cs)} sentences)")

        global_idx += len(aligned)

    print("\nDone.")


if __name__ == "__main__":
    main()
