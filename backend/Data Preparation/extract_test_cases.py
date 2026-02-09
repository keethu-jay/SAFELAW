#!/usr/bin/env python3
"""
Extract test cases for RAG baseline testing:
- Find 6 files: 3 UKSC (majority, dissenting, concurring) + 3 Tribunal (majority, dissenting, concurring)
- For each file, extract 3 paragraphs: beginning, middle, end
- Each test case includes: paragraph text, prev/next paragraph text
- Note: Semantic scores are computed when running RAG (Tab in Writer) - fill in after testing
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from openai import OpenAI
from typing import Dict, List, Tuple, Optional
import re

# Load environment variables from backend .env file manually
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip()

# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent
# Try to locate data directory relative to script
# Check backend/data/raw_xml
INPUT_DIR = SCRIPT_DIR.parent / "data" / "raw_xml"
if not INPUT_DIR.exists():
    # Fallback: Check project_root/data/raw_xml
    INPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "raw_xml"

OUTPUT_JSON = SCRIPT_DIR.parent / "RAG_TEST_CASES.json"
OUTPUT_MD = SCRIPT_DIR.parent / "RAG_TEST_CASES.md"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def extract_last_1000_chars(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract last 1000 chars and detect court type."""
    try:
        tree = ET.parse(file_path)
        full_text = "".join(tree.getroot().itertext())
        
        # Check for UKSC first, then tribunal (EAT, Upper Tribunal, etc.)
        if "Supreme Court" in full_text or "UKSC" in full_text or "[UKSC" in full_text:
            court = "uksc"
        elif "Tribunal" in full_text or "EAT" in full_text or "[EAT" in full_text or "[UKEAT" in full_text:
            court = "tribunal"
        else:
            court = "uksc"  # Default fallback
            
        return court, full_text[-1000:] if len(full_text) >= 1000 else full_text
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None

def classify_opinion(text_snippet: str) -> str:
    """Classify opinion type using GPT-4o-mini on last 1000 chars."""
    if not client:
        raise ValueError("OPENAI_API_KEY not set")
        
    prompt = f"""
    Analyze the following end-of-judgment text (last ~1000 characters) from a UK court case.
    Classify into exactly one category:
    1. "dissenting": If ANY judge explicitly dissents, disagrees, or says "I would dismiss/allow" differently from the majority.
    2. "concurring": If NO dissent, but a judge writes a separate opinion saying "I agree" with different reasoning or adds their own analysis.
    3. "majority": If it is a single judgment or simple agreement without separate concurring/dissenting speeches.

    Text:
    "{text_snippet}"

    Return ONLY one word: "majority", "concurring", or "dissenting".
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    result = response.choices[0].message.content.strip().lower()
    
    if result not in ["majority", "concurring", "dissenting"]:
        return "majority"  # Default fallback
    return result

def extract_paragraphs(file_path: str) -> List[str]:
    """Extract all paragraphs from XML, return as list of text strings."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Find all paragraph elements (common patterns in UK court XML)
        paragraphs = []
        
        # Try different XML structures
        for para in root.iter():
            if para.tag.endswith('paragraph') or para.tag.endswith('p'):
                text = "".join(para.itertext()).strip()
                if text and len(text) > 50:  # Filter very short fragments
                    paragraphs.append(text)
        
        # Fallback: split by paragraph markers if structured differently
        if not paragraphs:
            full_text = "".join(root.itertext())
            # Split by numbered paragraphs (e.g., "1.", "2.", etc.)
            parts = re.split(r'\n\s*(\d+)\.\s+', full_text)
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    para = parts[i] + parts[i+1]
                    para = para.strip()
                    if para and len(para) > 50:
                        paragraphs.append(para)
                        
        return paragraphs
    except Exception as e:
        print(f"Error extracting paragraphs from {file_path}: {e}")
        return []

def get_test_paragraphs(paragraphs: List[str]) -> List[Dict[str, str]]:
    """Get 3 paragraphs: beginning, middle, end."""
    if len(paragraphs) < 3:
        return [{"text": p, "position": "beginning" if i == 0 else "end"} 
                for i, p in enumerate(paragraphs)]
    
    beginning_idx = 0
    middle_idx = len(paragraphs) // 2
    end_idx = len(paragraphs) - 1
    
    return [
        {"text": paragraphs[beginning_idx], "position": "beginning"},
        {"text": paragraphs[middle_idx], "position": "middle"},
        {"text": paragraphs[end_idx], "position": "end"},
    ]

def find_files_by_opinion(files: List[str], court: str, opinion: str, needed: int = 1) -> List[str]:
    """Find files matching court and opinion type."""
    found = []
    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        detected_court, last_1000 = extract_last_1000_chars(file_path)
        
        if detected_court != court:
            continue
            
        try:
            opinion_type = classify_opinion(last_1000)
            if opinion_type == opinion:
                found.append(filename)
                if len(found) >= needed:
                    break
        except Exception as e:
            print(f"Error classifying {filename}: {e}")
            continue
            
    return found

def main():
    """Main: find 6 files and extract test cases."""
    if not client:
        print("ERROR: OPENAI_API_KEY not set. Set it in environment or .env file.")
        return
        
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xml")]
    print(f"Found {len(files)} XML files. Classifying and selecting test files...")
    
    # Target: 3 UKSC (majority, dissenting, concurring) + 3 Tribunal (majority, dissenting, concurring)
    targets = {
        ("uksc", "majority"): None,
        ("uksc", "dissenting"): None,
        ("uksc", "concurring"): None,
        ("tribunal", "majority"): None,
        ("tribunal", "dissenting"): None,
        ("tribunal", "concurring"): None,
    }
    
    # Find files for each category
    for (court, opinion), _ in targets.items():
        found = find_files_by_opinion(files, court, opinion, needed=1)
        if found:
            targets[(court, opinion)] = found[0]
            print(f"✓ Found {court} {opinion}: {found[0]}")
        else:
            print(f"✗ No {court} {opinion} file found")
            
    # Extract test cases from each file
    test_cases = []
    for (court, opinion), filename in targets.items():
        if not filename:
            continue
            
        file_path = os.path.join(INPUT_DIR, filename)
        paragraphs = extract_paragraphs(file_path)
        test_paras = get_test_paragraphs(paragraphs)
        
        for test_para in test_paras:
            para_idx = paragraphs.index(test_para["text"]) if test_para["text"] in paragraphs else -1
            
            prev_para = paragraphs[para_idx - 1] if para_idx > 0 else ""
            next_para = paragraphs[para_idx + 1] if para_idx >= 0 and para_idx < len(paragraphs) - 1 else ""
            
            test_cases.append({
                "file": filename,
                "court": court,
                "opinion_type": opinion,
                "test_paragraph": {
                    "text": test_para["text"],
                    "position": test_para["position"],
                    "semantic_score": None,  # Fill in after running RAG (Tab in Writer)
                },
                "previous_paragraph": {
                    "text": prev_para,
                    "semantic_score": None,  # Fill in after running RAG
                },
                "next_paragraph": {
                    "text": next_para,
                    "semantic_score": None,  # Fill in after running RAG
                },
            })
            
    # Save to JSON
    json_path = Path(OUTPUT_JSON)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2, ensure_ascii=False)
        
    # Generate Markdown document
    md_path = Path(OUTPUT_MD)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# RAG Baseline Test Cases\n\n")
        f.write("Use these paragraphs in the Writer text box, then press **Tab** (last 1000 chars are sent). ")
        f.write("Check the **raw semantic scores** box and record the scores for each test paragraph and its prev/next.\n\n")
        f.write("All source files are from `data/raw_xml` and are **not** in the Final Dataset (used for baseline testing only).\n\n")
        f.write("---\n\n")
        
        # Group by court and opinion
        by_court = {}
        for tc in test_cases:
            key = (tc["court"], tc["opinion_type"])
            if key not in by_court:
                by_court[key] = []
            by_court[key].append(tc)
            
        court_names = {"uksc": "UK Supreme Court", "tribunal": "Upper Tribunal / EAT"}
        opinion_names = {"majority": "Majority", "dissenting": "Dissenting", "concurring": "Concurring"}
        
        for (court, opinion), cases in sorted(by_court.items()):
            if not cases:
                continue
            f.write(f"## {court_names.get(court, court.upper())} — {opinion_names.get(opinion, opinion)}\n\n")
            f.write(f"**File:** `{cases[0]['file']}`  \n")
            f.write(f"**Opinion Type:** {opinion}  \n\n")
            
            for i, tc in enumerate(cases, 1):
                pos = tc["test_paragraph"]["position"]
                f.write(f"### Test Case {i}: {pos.capitalize()} Paragraph\n\n")
                f.write("**Test paragraph to paste:**\n\n")
                f.write("```\n")
                f.write(tc["test_paragraph"]["text"])
                f.write("\n```\n")
                f.write("**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  \n")
                f.write("**Expected semantic score:** `[fill after testing]`\n\n")
                
                if tc["previous_paragraph"]["text"]:
                    f.write("**Previous paragraph:**\n\n")
                    f.write("```\n")
                    f.write(tc["previous_paragraph"]["text"])
                    f.write("\n```\n")
                    f.write("**Previous paragraph semantic score:** `[fill after testing]`\n\n")
                
                if tc["next_paragraph"]["text"]:
                    f.write("**Next paragraph:**\n\n")
                    f.write("```\n")
                    f.write(tc["next_paragraph"]["text"])
                    f.write("\n```\n")
                    f.write("**Next paragraph semantic score:** `[fill after testing]`\n\n")
                
                f.write("---\n\n")
                
    print(f"\n✓ Extracted {len(test_cases)} test cases from {len([f for f in targets.values() if f])} files")
    print(f"✓ Saved JSON to {OUTPUT_JSON}")
    print(f"✓ Saved Markdown to {OUTPUT_MD}")
    print("\nNote: semantic_score fields are None. Run RAG (Tab in Writer) and fill in scores manually.")

if __name__ == "__main__":
    main()
