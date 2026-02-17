#!/usr/bin/env python3
"""
Extract paragraphs from zip, classify them using LLM, create sentence-level files,
and ingest into Supabase with classifications.

1. Extract HTML files from parsed_cases_safelaw.zip
2. Parse paragraphs and get character counts
3. Classify each paragraph using LLM (6 categories)
4. Create sentence-level HTMLs with paragraph classifications inherited
5. Create sentence-level HTMLs with individual sentence classifications
6. Move old files to old/ folder
7. Update Supabase with classifications in embeddings and columns
"""

import os
import re
import sys
import zipfile
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
SMALL_CORPUS_DIR = BACKEND_DIR / "Small Corpus"
ZIP_PATH = SMALL_CORPUS_DIR / "parsed_cases_safelaw.zip"
OLD_DIR = SMALL_CORPUS_DIR / "old"

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

# Map HTML filenames to doc_id
DOC_ID_MAP = {
    "Ann_Kelly_(Plaintiff)_v_Fergus_Hennessy_(Defendant)": "Ann Kelly v Fergus Hennessy [1995] 3 IR 253",
    "Donoghue_v_Stevenson_[1932]_UKHL_100_(26_May_1932)": "Donoghue v Stevenson [1932] UKHL 100",
    "McGee_v._Attorney_General": "McGee v A.G. and Anor [1973] IESC 2",
    "McLoughlin_v_O'Brian": "McLoughlin v O'Brian [1982] UKHL 3",
    "Norris_v._Ireland": "Norris v A.G. [1983] IESC 3",
}


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


def classify_paragraph(paragraph: str, char_count: int, model_client) -> str:
    """Classify a paragraph using LLM."""
    prompt = CLASSIFICATION_PROMPT.format(
        char_count=char_count,
        paragraph=paragraph[:2000]  # Limit for prompt
    )
    try:
        # Use OpenAI-compatible API
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
        # Validate result
        for cat in CLASSIFICATIONS:
            if cat.lower() in result.lower():
                return cat
        # Default fallback
        return "Reasoning"
    except Exception as e:
        print(f"  Classification error: {e}")
        return "Reasoning"  # Default


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 10]


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


def create_sentence_html_with_para_classification(
    doc_id: str, paragraphs: List[Tuple[str, str]], output_path: Path
):
    """Create HTML with sentences inheriting paragraph classifications."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><title>Sentences with Paragraph Classifications</title></head><body>",
        f"<h1>{doc_id}</h1>",
    ]
    
    for para_text, para_class in paragraphs:
        sentences = split_into_sentences(para_text)
        for sent in sentences:
            html_parts.append(f'<p class="{para_class.lower().replace(" ", "-")}">{sent}</p>')
    
    html_parts.append("</body></html>")
    output_path.write_text("\n".join(html_parts), encoding="utf-8")


def create_sentence_html_with_individual_classification(
    doc_id: str, sentences: List[Tuple[str, str]], output_path: Path, model_client
):
    """Create HTML with each sentence individually classified."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><title>Sentences with Individual Classifications</title></head><body>",
        f"<h1>{doc_id}</h1>",
    ]
    
    for sent_text, _ in sentences:
        char_count = len(sent_text)
        sent_class = classify_paragraph(sent_text, char_count, model_client)
        html_parts.append(f'<p class="{sent_class.lower().replace(" ", "-")}">{sent_text}</p>')
    
    html_parts.append("</body></html>")
    output_path.write_text("\n".join(html_parts), encoding="utf-8")


def main():
    # Load env
    _env_path = BACKEND_DIR / ".env"
    if _env_path.exists():
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    
    # Initialize OpenAI client
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Set OPENAI_API_KEY in .env")
            sys.exit(1)
        openai_client = OpenAI(api_key=api_key)
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
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(extracted_dir)
    
    html_files = list(extracted_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML files")
    
    # Process each HTML file
    all_para_classifications = {}
    all_sentences_para_class = {}
    
    for html_file in html_files:
        stem = html_file.stem
        doc_id = DOC_ID_MAP.get(stem, stem.replace("_", " "))
        
        print(f"\nProcessing {stem}...")
        html_content = html_file.read_text(encoding="utf-8")
        paragraphs = extract_paragraphs_from_html(html_content)
        print(f"  Extracted {len(paragraphs)} paragraphs")
        
        # Classify paragraphs
        para_classifications = []
        for i, para in enumerate(paragraphs):
            char_count = len(para)
            print(f"  Classifying paragraph {i+1}/{len(paragraphs)} ({char_count} chars)...", end=" ")
            classification = classify_paragraph(para, char_count, openai_client)
            print(classification)
            para_classifications.append((para, classification))
        
        all_para_classifications[doc_id] = para_classifications
        
        # Create paragraph HTML
        para_html = SMALL_CORPUS_DIR / f"{stem}_paragraphs_classified.html"
        create_paragraph_html(doc_id, para_classifications, para_html)
        print(f"  Created {para_html.name}")
        
        # Collect sentences with paragraph classifications
        sentences_with_para_class = []
        for para_text, para_class in para_classifications:
            sentences = split_into_sentences(para_text)
            for sent in sentences:
                sentences_with_para_class.append((sent, para_class))
        all_sentences_para_class[doc_id] = sentences_with_para_class
        
        # Create sentence HTML with paragraph classifications
        sent_para_html = SMALL_CORPUS_DIR / f"{stem}_sentences_para_class.html"
        create_sentence_html_with_para_classification(
            doc_id, para_classifications, sent_para_html
        )
        print(f"  Created {sent_para_html.name}")
        
        # Create sentence HTML with individual classifications
        print(f"  Classifying {len(sentences_with_para_class)} sentences individually...")
        sent_indiv_html = SMALL_CORPUS_DIR / f"{stem}_sentences_indiv_class.html"
        create_sentence_html_with_individual_classification(
            doc_id, sentences_with_para_class, sent_indiv_html, openai_client
        )
        print(f"  Created {sent_indiv_html.name}")
    
    # Move old files to old/ folder
    print("\nMoving old files to old/ folder...")
    OLD_DIR.mkdir(exist_ok=True)
    old_patterns = ["*_paragraphs.docx", "*_sentences.docx", "*_paragraphs_reviewed.docx"]
    moved = 0
    for pattern in old_patterns:
        for old_file in SMALL_CORPUS_DIR.glob(pattern):
            if old_file.name not in ["parsed_cases_safelaw.zip"]:
                dest = OLD_DIR / old_file.name
                old_file.rename(dest)
                moved += 1
                print(f"  Moved {old_file.name}")
    print(f"Moved {moved} old files")
    
    print("\n✅ Classification complete!")
    print("\nNext steps:")
    print("1. Review the generated HTML files")
    print("2. Run updated ingestion script to upload to Supabase")
    print("3. The ingestion script will include classifications in embeddings and columns")


if __name__ == "__main__":
    main()
