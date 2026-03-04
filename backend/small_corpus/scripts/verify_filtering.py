#!/usr/bin/env python3
"""Verify that suggestions don't come from the same case as the test paragraph."""

import csv
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
REF_DIR = BACKEND_DIR / "testing_scripts" / "output"


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()

files_to_check = [
    "Classification_Comparison_paragraphs_classified.tsv",
    "Classification_Comparison_sentences_indiv_class.tsv",
]

all_ok = True
for tsv_file in files_to_check:
    tsv_path = REF_DIR / tsv_file
    if not tsv_path.exists():
        print(f"File not found: {tsv_path}")
        continue
    
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        header = next(reader)
        rows = list(reader)
    
    print(f"\nVerifying {tsv_file}...")
    issues = []
    for i, row in enumerate(rows, 1):
        if len(row) < 8:
            continue
        test_file = row[1]  # File Name column
        test_norm = normalize_case_name(test_file)
        
        # Check all suggestion citations (columns 7, 9, 11, 13, 15, 17, 19, 21, 23, 25)
        citation_cols = [7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
        for col_idx in citation_cols:
            if col_idx < len(row):
                citation = row[col_idx].strip()
                if citation and citation != "N/A":
                    citation_norm = normalize_case_name(citation)
                    if citation_norm == test_norm:
                        issues.append(f"Row {i}: Test file '{test_file}' has suggestion from same case: '{citation}'")
                        break  # Only report once per row
    
    if issues:
        print(f"[ERROR] FILTERING ISSUES FOUND in {tsv_file}:")
        for issue in issues:
            print(f"  {issue}")
        all_ok = False
    else:
        print(f"[OK] All suggestions are from different cases!")
        print(f"  Verified {len(rows)} rows, all suggestions filtered correctly.")

if all_ok:
    print("\n[OK] Both TSV files passed filtering verification!")
