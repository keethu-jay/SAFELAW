#!/usr/bin/env python3
"""
Extract paragraphs from zip, classify them using LLM, create paragraph and sentence files.

1. Extract HTML files from parsed_cases_safelaw.zip
2. Parse paragraphs
3. Preprocess: fix typos, chunk into ~1000 character segments
4. Classify each paragraph/chunk using LLM
5. Create paragraph HTML with classifications
6. Create sentence HTML with individual classifications (no para-class inheritance)
7. Move old files to old/ folder
"""

import argparse
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple


class ClassificationRateLimitError(Exception):
    """Raised when API rate limit is hit and retries are exhausted. Stops script to avoid wasting requests."""

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
SMALL_CORPUS_DIR = BACKEND_DIR / "small_corpus"
ZIP_PATH = SMALL_CORPUS_DIR / "parsed_cases_safelaw.zip"
OLD_DIR = SMALL_CORPUS_DIR / "old"
PARA_CLASSIFIED_DIR = SMALL_CORPUS_DIR / "paragraphs_classified"
SENTENCES_INDIV_DIR = SMALL_CORPUS_DIR / "sentences_indiv_class"

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

Paragraph to classify:
{paragraph}

Respond with ONLY the category name (Introduction, Facts, Authority, Doctrine and Policy, Reasoning, or Judgment)."""

# Map HTML filenames to doc_id
DOC_ID_MAP = {
    "Ann_Kelly_(Plaintiff)_v_Fergus_Hennessy_(Defendant)": "Ann Kelly v Fergus Hennessy [1995] 3 IR 253",
    "Donoghue_v_Stevenson_[1932]_UKHL_100_(26_May_1932)": "Donoghue v Stevenson [1932] UKHL 100",
    "McGee_v._Attorney_General": "McGee v A.G. and Anor [1973] IESC 2",
    "McLoughlin_v_O'Brian": "McLoughlin v O'Brian [1982] UKHL 3",
    "Norris_v._Ireland": "Norris v A.G. [1983] IESC 3",
}


# EXTRACTION: ZIP & PARAGRAPHS
class ParagraphExtractor(HTMLParser):
    """Extract paragraphs from HTML."""
    
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current_para = []
        self.in_p = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True
            self.current_para = []
    
    def handle_endtag(self, tag):
        if tag == 'p' and self.in_p:
            para_text = ' '.join(self.current_para).strip()
            if para_text and len(para_text) >= 10:
                self.paragraphs.append(para_text)
            self.in_p = False
            self.current_para = []
    
    def handle_data(self, data):
        if self.in_p:
            self.current_para.append(data.strip())


def extract_paragraphs_from_html(html_content: str) -> List[str]:
    """Extract paragraphs from HTML content."""
    parser = ParagraphExtractor()
    parser.feed(html_content)
    return parser.paragraphs


CHUNK_TARGET = 1000
CHUNK_MIN = 800
CHUNK_MAX = 1200


# Placeholder to protect abbreviations from sentence-splitting (period not followed by space)
_ABBR_PLACEHOLDER = "\x00"

# Legal/editorial abbreviations: period here is NOT a sentence boundary. Order: longer first.
_ABBREVIATIONS = [
    " pp. ", " I.L.R.M. ", " A.L.R. ", " W.L.R. ", " et al. ", " e.g. ", " i.e. ",
    " v. ", " p. ", " Ltd. ", " Co. ", " Inc. ", " No. ", " Vol. ", " U.S. ",
    " A.C. ", " K.B. ", " Q.B. ", " I.R. ", " S.C. ", " E.R. ", " App. ", " L.R. ",
    " etc. ", " cf. ", " para. ", " art. ", " Dr. ", " Mr. ", " Mrs. ", " Prof. ",
]


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences. Avoids splitting on legal abbreviations (v., p., Ltd., etc.)."""
    protected = text
    for abbr in _ABBREVIATIONS:
        # Replace period with placeholder so it won't match (?<=[.!?])\s+
        protected = protected.replace(abbr, abbr[:-2] + _ABBR_PLACEHOLDER + abbr[-1])
    sentences = re.split(r'(?<=[.!?])\s+', protected)
    result = []
    for s in sentences:
        restored = s.replace(_ABBR_PLACEHOLDER, ".")
        restored = restored.strip()
        if restored and len(restored) >= 10:
            result.append(restored)
    return result


# CHUNKING & SENTENCE SPLITTING
def chunk_paragraphs(paragraphs: List[str]) -> List[str]:
    """
    Split and merge paragraphs into roughly equal chunks of ~1000 characters.
    - Long paragraphs (>CHUNK_MAX): split at sentence boundaries
    - Short consecutive paragraphs: merged until ~CHUNK_TARGET
    """
    if not paragraphs:
        return []

    result = []
    buffer: List[str] = []
    buffer_len = 0

    def flush_buffer():
        nonlocal buffer, buffer_len, result
        if buffer:
            result.append(" ".join(buffer))
            buffer = []
            buffer_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) > CHUNK_MAX:
            # Flush current buffer first
            flush_buffer()
            # Split long paragraph at sentence boundaries
            sentences = split_into_sentences(para)
            chunk = []
            chunk_len = 0
            for sent in sentences:
                if chunk_len + len(sent) + 1 > CHUNK_MAX and chunk:
                    result.append(" ".join(chunk))
                    chunk = []
                    chunk_len = 0
                chunk.append(sent)
                chunk_len += len(sent) + 1
            if chunk:
                result.append(" ".join(chunk))
        elif buffer_len + len(para) + 1 <= CHUNK_MAX:
            # Add to buffer (merge short paragraphs toward ~1000)
            buffer.append(para)
            buffer_len += len(para) + 1
            if buffer_len >= CHUNK_TARGET:
                flush_buffer()
        else:
            # Buffer + para would exceed max: flush buffer first, then handle para
            if buffer:
                flush_buffer()
            if len(para) >= CHUNK_MIN:
                result.append(para)
            else:
                buffer = [para]
                buffer_len = len(para)

    flush_buffer()
    return result


# CLASSIFICATION: LLM API
class GeminiClient:
    """Wrapper for Google Gemini API, mimics OpenAI interface."""
    _is_gemini = True
    # Model names: gemini-2.0-flash is current; gemini-1.5-flash can 404 on v1beta
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str, model: str | None = None):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model or self.DEFAULT_MODEL)

    def generate(self, user_content: str, system_content: str, temperature: float, max_tokens: int) -> str:
        full_prompt = f"{system_content}\n\n{user_content}" if system_content else user_content
        config = {"temperature": temperature, "max_output_tokens": max_tokens}
        response = self._model.generate_content(full_prompt, generation_config=config)
        return (response.text or "").strip()


def _call_llm(messages: List[dict], model_client, temperature: float = 0, max_tokens: int = 2000) -> str:
    """Unified LLM call for OpenAI or Gemini."""
    user_content = next((m["content"] for m in messages if m["role"] == "user"), "")
    system_content = next((m["content"] for m in messages if m["role"] == "system"), "")
    if hasattr(model_client, "_is_gemini") and model_client._is_gemini:
        return model_client.generate(user_content, system_content, temperature, max_tokens)
    response = model_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def fix_typos_batch(texts: List[str], model_client, batch_size: int = 5) -> List[str]:
    """Use LLM to fix obvious typos. Preserves legal terms and citations."""
    if not texts:
        return []
    result = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        prompt_parts = [f"[{j+1}]\n{batch[j][:1000]}" for j in range(len(batch))]
        prompt = f"""Fix only obvious typos and OCR errors. Preserve legal terms, citations, case names.
Output each corrected text on its own block, prefixed with its number [1], [2], etc.

Inputs:
{chr(10).join(prompt_parts)}

Corrected (same numbering):"""
        try:
            content = _call_llm(
                [
                    {"role": "system", "content": "Fix typos only. Output each block with [N] prefix. Preserve legal formatting."},
                    {"role": "user", "content": prompt}
                ],
                model_client,
                temperature=0,
                max_tokens=2000,
            ).strip()
            # Parse [1]...[2]...[3] blocks
            for j in range(len(batch)):
                pat = rf"\[{j+1}\]\s*\n?(.*?)(?=\[{j+2}\]|$)"
                m = re.search(pat, content, re.DOTALL)
                if m:
                    result.append(m.group(1).strip())
                else:
                    result.append(batch[j])
        except Exception as e:
            print(f"  Typo fix warning: {e}, using originals for batch")
            result.extend(batch)
    return result


def _is_rate_limit_error(e: Exception) -> bool:
    """Check if exception is a rate limit / resource exhausted error."""
    err_str = str(e).lower()
    return "429" in err_str or "rate limit" in err_str or "resource exhausted" in err_str


def classify_paragraph(paragraph: str, model_client, max_retries: int = 3) -> str:
    """Classify a paragraph using LLM. Retries on 429 with backoff. Raises ClassificationRateLimitError if retries exhausted."""
    prompt = CLASSIFICATION_PROMPT.format(
        paragraph=paragraph[:2000]  # Limit for prompt
    )
    messages = [
        {"role": "system", "content": "You are a legal document classifier. Respond with only the category name."},
        {"role": "user", "content": prompt}
    ]
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = _call_llm(messages, model_client, temperature=0.1, max_tokens=20)
            # Validate result
            for cat in CLASSIFICATIONS:
                if cat.lower() in result.lower():
                    return cat
            raise ValueError(f"Model returned unrecognized category: {result!r}")
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e) and attempt < max_retries:
                wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                print(f"  Rate limit hit, waiting {wait}s before retry {attempt + 1}/{max_retries}...", flush=True)
                time.sleep(wait)
            else:
                if _is_rate_limit_error(e):
                    raise ClassificationRateLimitError(
                        f"Rate limit exhausted after {max_retries} retries. "
                        "Saving progress and stopping to avoid wasting requests. Try again later with --delay."
                    ) from e
                raise
    raise last_error  # unreachable


BATCH_SENTENCE_PROMPT = """Classify each sentence from a legal judgment into one category:

Categories: Introduction, Facts, Authority, Doctrine and Policy, Reasoning, Judgment

For each sentence, respond with ONLY the category name on a numbered line:
1. Category
2. Category
..."""


def classify_sentences_batch(
    sentences: List[str], model_client, max_retries: int = 3
) -> List[str]:
    """Classify multiple sentences in one API call. Returns list of classifications."""
    if not sentences:
        return []
    prompt_parts = [f"{i+1}. {s[:400]}" for i, s in enumerate(sentences)]
    prompt = f"{BATCH_SENTENCE_PROMPT}\n\nSentences:\n" + "\n".join(prompt_parts)
    prompt += "\n\nClassifications (one per line, format: N. Category):"
    messages = [
        {"role": "system", "content": "You are a legal document classifier. Output one category per sentence."},
        {"role": "user", "content": prompt},
    ]
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = _call_llm(
                messages, model_client, temperature=0.1, max_tokens=min(500, 50 * len(sentences))
            )
            classifications = []
            lines = result.strip().split("\n")
            line_map = {}
            for line in lines:
                m = re.match(r"^(\d+)[\.\)]\s*(.+)", line.strip(), re.IGNORECASE)
                if m:
                    line_map[int(m.group(1))] = m.group(2).strip()
            for i in range(len(sentences)):
                raw = line_map.get(i + 1, "")
                for cat in CLASSIFICATIONS:
                    if cat.lower() in raw.lower():
                        classifications.append(cat)
                        break
                else:
                    classifications.append("Reasoning")
            return classifications
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e) and attempt < max_retries:
                wait = (2 ** attempt) * 5
                print(f"  Rate limit hit, waiting {wait}s before retry {attempt + 1}/{max_retries}...", flush=True)
                time.sleep(wait)
            else:
                if _is_rate_limit_error(e):
                    raise ClassificationRateLimitError(
                        f"Rate limit exhausted after {max_retries} retries. "
                        "Saving progress and stopping."
                    ) from e
                raise
    raise last_error


def parse_existing_paragraph_html(html_path: Path) -> List[Tuple[str, str]]:
    """Parse existing HTML file and return list of (paragraph_text, classification) tuples."""
    if not html_path.exists():
        return []
    
    class ParagraphParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.paragraphs = []
            self.current_text = ""
            self.current_class = ""
            self.in_p = False
            
        def handle_starttag(self, tag, attrs):
            if tag == "p":
                self.in_p = True
                self.current_text = ""
                # Extract class attribute
                self.current_class = ""
                for attr_name, attr_value in attrs:
                    if attr_name == "class":
                        self.current_class = attr_value.replace("-", " ").title()
                        break
        
        def handle_data(self, data):
            if self.in_p:
                self.current_text += data
        
        def handle_endtag(self, tag):
            if tag == "p" and self.in_p:
                if self.current_text.strip():
                    # Default to "Reasoning" if no class found
                    cls = self.current_class if self.current_class else "Reasoning"
                    self.paragraphs.append((self.current_text.strip(), cls))
                self.in_p = False
    
    parser = ParagraphParser()
    try:
        html_content = html_path.read_text(encoding="utf-8")
        parser.feed(html_content)
        return parser.paragraphs
    except Exception as e:
        print(f"  Warning: Could not parse existing file {html_path.name}: {e}")
        return []


# OUTPUT: HTML FILES
def create_paragraph_html(
    doc_id: str, paragraphs: List[Tuple[str, str]], output_path: Path
):
    """Create HTML with paragraphs and their classifications."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><title>Paragraphs with Classifications</title></head><body>",
        f"<h1>{doc_id}</h1>",
    ]
    
    for para_text, para_class in paragraphs:
        html_parts.append(f'<p class="{para_class.lower().replace(" ", "-")}">{para_text}</p>')
    
    html_parts.append("</body></html>")
    output_path.write_text("\n".join(html_parts), encoding="utf-8")


def create_sentence_html_with_individual_classification(
    doc_id: str,
    sentences: List[str],
    output_path: Path,
    model_client,
    delay: float = 0.5,
    batch_size: int = 15,
):
    """Create HTML with each sentence individually classified. Uses batch API calls when batch_size > 1."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><title>Sentences with Individual Classifications</title></head><body>",
        f"<h1>{doc_id}</h1>",
    ]
    batch_size = max(1, batch_size)
    for batch_start in range(0, len(sentences), batch_size):
        batch = sentences[batch_start : batch_start + batch_size]
        time.sleep(delay)
        try:
            if batch_size == 1:
                classifications = [classify_paragraph(batch[0], model_client)]
            else:
                classifications = classify_sentences_batch(batch, model_client)
        except ClassificationRateLimitError as e:
            output_path.write_text("\n".join(html_parts) + "\n</body></html>", encoding="utf-8")
            print(f"\n  [Saved {batch_start}/{len(sentences)} sentences before rate limit]")
            print(f"\nStop: {e}")
            raise
        for sent_text, sent_class in zip(batch, classifications):
            html_parts.append(f'<p class="{sent_class.lower().replace(" ", "-")}">{sent_text}</p>')
        done = min(batch_start + batch_size, len(sentences))
        if done % 150 < batch_size or done >= len(sentences):
            print(f"  {done}/{len(sentences)} sentences", flush=True)
    html_parts.append("</body></html>")
    output_path.write_text("\n".join(html_parts), encoding="utf-8")


# MAIN PIPELINE
def main():
    ap = argparse.ArgumentParser(description="Classify legal corpus paragraphs and sentences.")
    ap.add_argument("--skip-typos", action="store_true", help="Skip typo-fixing (faster, cheaper)")
    ap.add_argument("--force", action="store_true", help="Re-classify even if output files exist")
    ap.add_argument("--provider", choices=["openai", "gemini"], default=None,
                    help="LLM provider (default: gemini if GOOGLE_API_KEY set, else openai)")
    ap.add_argument("--model", default=None, help="Model name (Gemini: gemini-2.0-flash, gemini-1.5-flash, gemini-pro)")
    ap.add_argument("--delay", type=float, default=0.5, help="Seconds between classification requests (default 0.5 to avoid rate limits)")
    ap.add_argument("--sentence-batch-size", type=int, default=15, help="Sentences per API call (default 15, use 1 to disable batching)")
    args = ap.parse_args()

    # Load env
    _env_path = BACKEND_DIR / ".env"
    if _env_path.exists():
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    
    # Initialize LLM client (OpenAI or Gemini)
    provider = args.provider
    if provider is None:
        provider = "gemini" if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") else "openai"

    if provider == "gemini":
        try:
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("Set GOOGLE_API_KEY or GEMINI_API_KEY in .env for Gemini")
                sys.exit(1)
            model_client = GeminiClient(api_key=api_key, model=args.model)
            print(f"Using Gemini ({args.model or GeminiClient.DEFAULT_MODEL})")
        except ImportError:
            print("Install google-generativeai: pip install google-generativeai")
            sys.exit(1)
    else:
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("Set OPENAI_API_KEY in .env")
                sys.exit(1)
            model_client = OpenAI(api_key=api_key)
            print("Using OpenAI gpt-4o-mini")
        except ImportError:
            print("Install openai: pip install openai")
            sys.exit(1)
    
    # Extract zip
    print("Extracting HTML files from zip...")
    if not ZIP_PATH.exists():
        print(f"Zip not found: {ZIP_PATH}")
        sys.exit(1)
    
    extracted_dir = SMALL_CORPUS_DIR / "extracted_html"
    extracted_dir.mkdir(exist_ok=True)
    PARA_CLASSIFIED_DIR.mkdir(exist_ok=True)
    SENTENCES_INDIV_DIR.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(extracted_dir)
    
    # Convert BAILII Additional Cases to extracted_html format
    additional_cases_dir = SMALL_CORPUS_DIR / "Additional Cases"
    if additional_cases_dir.exists():
        print("\nConverting Additional Cases to extracted_html format...")
        import subprocess
        conv_script = SCRIPT_DIR / "convert_bailii_additional_cases.py"
        if conv_script.exists():
            subprocess.run([sys.executable, str(conv_script)], cwd=str(BACKEND_DIR), check=False)
        else:
            print(f"  (convert script not found: {conv_script})")
    
    html_files = list(extracted_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML files")
    
    # Process each HTML file
    for html_file in html_files:
        stem = html_file.stem
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        
        # Skip if already classified (resume support), unless --force
        para_html = PARA_CLASSIFIED_DIR / f"{stem}_paragraphs_classified.html"
        sent_indiv_html = SENTENCES_INDIV_DIR / f"{stem}_sentences_indiv_class.html"
        if not args.force and para_html.exists() and sent_indiv_html.exists():
            print(f"\nSkipping {stem} (already classified)...", flush=True)
            continue
        
        print(f"\nProcessing {stem}...", flush=True)
        html_content = html_file.read_text(encoding="utf-8")
        paragraphs = extract_paragraphs_from_html(html_content)
        print(f"  Extracted {len(paragraphs)} paragraphs", flush=True)
        
        # Preprocess: fix typos (optional), then chunk to ~1000 chars
        if not args.skip_typos:
            print(f"  Fixing typos...", flush=True)
            paragraphs = fix_typos_batch(paragraphs, model_client)
        print(f"  Chunking to ~{CHUNK_TARGET} chars...", flush=True)
        chunks = chunk_paragraphs(paragraphs)
        print(f"  {len(chunks)} chunks (target ~{CHUNK_TARGET} chars each)", flush=True)
        
        # Check for existing partial progress
        para_html = PARA_CLASSIFIED_DIR / f"{stem}_paragraphs_classified.html"
        existing_classifications = parse_existing_paragraph_html(para_html)
        
        # Verify existing classifications match chunks (check first few)
        start_idx = 0
        para_classifications = []
        if existing_classifications:
            # Check if first few match to ensure we're resuming correctly
            match_count = 0
            for i in range(min(5, len(existing_classifications), len(chunks))):
                if existing_classifications[i][0] == chunks[i]:
                    match_count += 1
            
            if match_count >= 3:  # At least 3 match, assume we can resume
                start_idx = len(existing_classifications)
                if start_idx >= len(chunks):
                    print(f"  File already complete ({len(existing_classifications)} paragraphs), skipping paragraph classification...", flush=True)
                    para_classifications = existing_classifications
                else:
                    print(f"  Resuming from paragraph {start_idx + 1}/{len(chunks)} (found {start_idx} already classified)...", flush=True)
                    para_classifications = existing_classifications.copy()
            else:
                print(f"  Warning: Existing file doesn't match current chunks, starting fresh...", flush=True)
                existing_classifications = []
        
        # Only classify if not already complete
        if start_idx < len(chunks):
            # Save incrementally every 100 paragraphs
            SAVE_INTERVAL = 100
            try:
                for i in range(start_idx, len(chunks)):
                    time.sleep(args.delay)
                    print(f"  Classifying paragraph {i+1}/{len(chunks)}...", end=" ", flush=True)
                    classification = classify_paragraph(chunks[i], model_client)
                    print(classification, flush=True)
                    para_classifications.append((chunks[i], classification))
                    
                    # Save incrementally to avoid losing progress
                    if (i + 1) % SAVE_INTERVAL == 0 or i == len(chunks) - 1:
                        create_paragraph_html(doc_id, para_classifications, para_html)
                        print(f"  [Saved progress: {i+1}/{len(chunks)} paragraphs]", flush=True)
            except ClassificationRateLimitError as e:
                create_paragraph_html(doc_id, para_classifications, para_html)
                print(f"\n  [Saved progress: {len(para_classifications)}/{len(chunks)} paragraphs]")
                print(f"\nStop: {e}")
                sys.exit(1)
            
            # Final save
            create_paragraph_html(doc_id, para_classifications, para_html)
            print(f"  Created {para_html.name}")
        
        # Extract sentences from chunks and classify each individually
        all_sentences = []
        for para_text, _ in para_classifications:
            all_sentences.extend(split_into_sentences(para_text))
        print(f"  Classifying {len(all_sentences)} sentences individually...", flush=True)
        sent_indiv_html = SENTENCES_INDIV_DIR / f"{stem}_sentences_indiv_class.html"
        try:
            create_sentence_html_with_individual_classification(
                doc_id,
                all_sentences,
                sent_indiv_html,
                model_client,
                delay=args.delay,
                batch_size=args.sentence_batch_size,
            )
        except ClassificationRateLimitError as e:
            print(f"\nStop: {e}")
            sys.exit(1)
        print(f"  Created {sent_indiv_html.name}", flush=True)
    
    # Move old files to old/ folder
    print("\nMoving old files to old/ folder...")
    OLD_DIR.mkdir(exist_ok=True)
    old_patterns = ["*_paragraphs.docx", "*_sentences.docx", "*_paragraphs_reviewed.docx"]
    moved = 0
    for pattern in old_patterns:
        for old_file in SMALL_CORPUS_DIR.glob(f"**/{pattern}"):
            if old_file.name not in ["parsed_cases_safelaw.zip"]:
                dest = OLD_DIR / old_file.name
                old_file.rename(dest)
                moved += 1
                print(f"  Moved {old_file.name}")
    print(f"Moved {moved} old files")
    
    print("\n✅ Classification complete!")
    print("\nNext step: Run ingest to push to Supabase and create embeddings:")
    print("  python \"Data Preparation/ingest_classified_mini_corpus.py\"")
    print("  (Embeddings include the label as spatial context: [Classification] text)")


if __name__ == "__main__":
    main()
