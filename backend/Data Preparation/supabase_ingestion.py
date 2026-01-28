"""
Supabase Ingestion Script

Loads all documents from the Final Dataset folder and inserts them into Supabase.
Each paragraph in the XML files is treated as a sentence/document unit.

Features:
- Parses XML paragraphs directly (no LLM splitting needed - paragraphs already numbered)
- Generates embeddings using Isaacus kanon-2-embedder (legal-domain embedder)
- Extracts court type (UKSC or UKUT) and decision type (majority/dissenting/concurring)
- Inserts all data into Supabase corpus_documents table
"""

import os
import json
import logging
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass

from corpus_studio_initialization import Document, EmbeddingModel
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FINAL_DATASET_DIR = Path(__file__).parent.parent.parent / "Final Dataset"
# Switched from OpenAI to Isaacus kanon-2-embedder for legal document embeddings
EMBEDDING_MODEL = "kanon-2-embedder"
BATCH_SIZE = 50  # Insert in batches

# Court mapping
COURT_TYPE_MAPPING = {
    "Supreme Court (uksc)": "UKSC",
    "Tribunal Court (ukut)": "UKUT",
}

# Decision types
VALID_DECISIONS = ["majority", "concurring", "dissenting"]


@dataclass
class ParsedParagraph:
    """Represents a parsed paragraph from an XML document."""
    para_num: str
    text: str
    level_heading: Optional[str] = None


def extract_text_from_element(element: ET.Element) -> str:
    """
    Recursively extract all text from an XML element and its children.
    
    Args:
        element: XML element to extract text from
        
    Returns:
        Cleaned text content
    """
    text_parts = []
    
    if element.text:
        text_parts.append(element.text.strip())
    
    for child in element:
        child_text = extract_text_from_element(child)
        if child_text:
            text_parts.append(child_text)
        if child.tail:
            text_parts.append(child.tail.strip())
    
    text = " ".join(text_parts)
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_xml_paragraphs(file_path: Path) -> List[ParsedParagraph]:
    """
    Parse XML file and extract all paragraphs with their numbers and text.
    
    Args:
        file_path: Path to XML file
        
    Returns:
        List of ParsedParagraph objects
    """
    paragraphs = []
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Handle namespace
        ns = {'ns': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'}
        
        # Find all paragraphs in the document
        all_paragraphs = root.findall('.//ns:paragraph', ns)
        
        for para_elem in all_paragraphs:
            # Get paragraph number
            num_elem = para_elem.find('ns:num', ns)
            para_num = num_elem.text if num_elem is not None else "unknown"
            
            # Extract paragraph text
            text = extract_text_from_element(para_elem)
            
            if text:  # Only add non-empty paragraphs
                paragraphs.append(ParsedParagraph(
                    para_num=para_num,
                    text=text,
                    level_heading=None
                ))
        
        logger.info(f"Extracted {len(paragraphs)} paragraphs from {file_path.name}")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return []


def get_court_type(court_folder: str) -> str:
    """
    Extract court type from folder name.
    
    Args:
        court_folder: Folder name like "Supreme Court (uksc)" or "Tribunal Court (ukut)"
        
    Returns:
        Court code (UKSC or UKUT)
    """
    return COURT_TYPE_MAPPING.get(court_folder, "UNKNOWN")


def process_final_dataset(supabase_client) -> None:
    """
    Process all documents in Final Dataset and insert into Supabase corpus_documents table.
    
    Args:
        supabase_client: Initialized Supabase client
    """
    # Using Isaacus kanon-2-embedder instead of OpenAI for legal domain specificity
    embedding_model = EmbeddingModel(EMBEDDING_MODEL)
    documents_to_insert = []
    global_index = 0
    
    if not FINAL_DATASET_DIR.exists():
        logger.error(f"Final Dataset directory not found: {FINAL_DATASET_DIR}")
        return
    
    # Iterate through court types
    for court_folder in FINAL_DATASET_DIR.iterdir():
        if not court_folder.is_dir():
            continue
        
        court_type = get_court_type(court_folder.name)
        logger.info(f"\nProcessing {court_folder.name} ({court_type})...")
        
        # Iterate through decision types
        for decision_folder in court_folder.iterdir():
            if not decision_folder.is_dir():
                continue
            
            decision = decision_folder.name
            if decision not in VALID_DECISIONS:
                logger.warning(f"Skipping invalid decision type: {decision}")
                continue
            
            logger.info(f"  Processing {decision} decisions...")
            
            # Iterate through XML files
            xml_files = list(decision_folder.glob("*.xml"))
            logger.info(f"    Found {len(xml_files)} files")
            
            for xml_file in xml_files:
                doc_id = xml_file.stem  # Filename without extension
                paragraphs = parse_xml_paragraphs(xml_file)
                
                if not paragraphs:
                    logger.warning(f"    No paragraphs found in {xml_file.name}")
                    continue
                
                # Process each paragraph
                for sentence_idx, para in enumerate(paragraphs):
                    # Skip very short text
                    if len(para.text) < 10:
                        continue
                    
                    # Generate embedding
                    embedding = embedding_model.embed(para.text)
                    
                    # Create Document object
                    document = {
                        "doc_id": doc_id,
                        "text": para.text,
                        "section_title": para.level_heading or "Main",
                        "section_number": para.para_num,
                        "sentence_index": sentence_idx,
                        "global_index": global_index,
                        "court": court_type,
                        "decision": decision,
                        "embedding": embedding,
                    }
                    
                    documents_to_insert.append(document)
                    global_index += 1
                    
                    # Batch insert
                    if len(documents_to_insert) >= BATCH_SIZE:
                        insert_batch(supabase_client, documents_to_insert)
                        documents_to_insert = []
                
                logger.info(f"    Processed {xml_file.name}: {len(paragraphs)} paragraphs")
    
    # Insert remaining documents
    if documents_to_insert:
        insert_batch(supabase_client, documents_to_insert)
    
    logger.info(f"\n✅ Ingestion complete! Total global index: {global_index}")


def insert_batch(supabase_client, documents: List[Dict]) -> None:
    """
    Insert a batch of documents into Supabase.
    
    Args:
        supabase_client: Initialized Supabase client
        documents: List of document dictionaries to insert
    """
    try:
        result = supabase_client.table("corpus_documents").insert(documents).execute()
        logger.info(f"  ✅ Inserted {len(documents)} documents")
        return True
    except Exception as e:
        # Check for dimension mismatch error specifically to fail fast
        error_str = str(e)
        if "dimensions" in error_str and "expected" in error_str:
            logger.critical("\n🛑 CRITICAL DATABASE ERROR: Embedding dimension mismatch.")
            logger.critical("The database expects 1024 dimensions, but the model outputs 1792.")
            logger.critical("Please run this SQL in your Supabase SQL Editor:")
            logger.critical("ALTER TABLE corpus_documents ALTER COLUMN embedding TYPE vector(1792);")
            sys.exit(1)
            
        logger.error(f"  ❌ Error inserting batch: {e}")
        # Try inserting one by one to identify problematic documents
        for doc in documents:
            try:
                supabase_client.table("corpus_documents").insert([doc]).execute()
            except Exception as single_error:
                logger.error(f"    Failed to insert doc {doc['doc_id']}: {single_error}")
        return False


def main():
    """
    Main entry point.
    """
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    
    # Initialize Supabase client
    try:
        from supabase import create_client, Client
        
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Connected to Supabase")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase: {e}")
        return
    
    # Process dataset
    logger.info(f"Starting ingestion from {FINAL_DATASET_DIR}")
    process_final_dataset(supabase)


if __name__ == "__main__":
    main()
