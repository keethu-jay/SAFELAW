import re
import json
import os

# Import the config variable from the neighbor file
from config_loader import CONFIG

def process_document(raw_text, filename):
    """
    TRAFFIC CONTROLLER:
    1. Loops through the courts defined in YAML.
    2. Detects which court this file belongs to.
    3. Routes it to the correct logic (Seriatim vs Unitary).
    """

    detected_court = None

    # DYNAMIC CHECK: Loop through the 'courts' list from YAML
    for court in CONFIG['courts']:
        if re.search(court['identification_regex'], raw_text):
            detected_court = court
            break

    if not detected_court:
        print(f"Skipping {filename}: Could not identify court from YAML patterns.")
        return None

    print(f"Processing {filename} as {detected_court['name']} ({detected_court['structure_type']})")

    # ROUTING LOGIC: Based on 'structure_type' in YAML
    if detected_court['structure_type'] == "seriatim":
        # Complex structure (UK Supreme Court / House of Lords)
        return parse_seriatim_judgment(raw_text, detected_court)

    elif detected_court['structure_type'] == "unitary":
        # Simple structure (Tribunals)
        return parse_unitary_judgment(raw_text, detected_court)

    return None

# ==========================================
# PARSER TYPE A: SERIATIM (Multiple Judges)
# ==========================================
def parse_seriatim_judgment(text, court_config):
    """
    Handles cases where judges write separate opinions (e.g., Supreme Court).
    """
    case_data = {
        "citation": find_main_citation(text, court_config['identification_regex']),
        "court_level": court_config['db_code'],
        "chunks": []
    }

    # Pull the Judge Header Regex from YAML
    judge_regex = CONFIG['parsing_rules']['judge_header_regex']

    # Split text by Judge Headers
    segments = re.split(judge_regex, text, flags=re.MULTILINE)

    current_author = "Unknown"

    for i, segment in enumerate(segments):
        # Check if this segment is actually a Judge's name header
        # We append ':' to match the regex logic that expects a colon at the end
        if re.match(judge_regex, segment + ":"):
            current_author = segment.strip()
            continue

        # If it's a content block (and not just empty space)
        if len(segment.strip()) > 50:
            # Logic: First judge is usually Majority (Lead)
            opinion_type = "majority" if i < 3 else "concurring"

            # Simple check for dissent in the author name or text
            if "dissent" in current_author.lower():
                opinion_type = "dissenting"

            # Parse the paragraphs within this judge's speech
            new_chunks = split_into_paragraphs(
                segment,
                current_author,
                opinion_type,
                is_lead=(opinion_type=="majority")
            )
            case_data['chunks'].extend(new_chunks)

    return case_data

# ==========================================
# PARSER TYPE B: UNITARY (Single Decision)
# ==========================================
def parse_unitary_judgment(text, court_config):
    """
    Handles cases with one unified decision (e.g., Tribunals).
    """
    case_data = {
        "citation": find_main_citation(text, court_config['identification_regex']),
        "court_level": court_config['db_code'],
        "chunks": []
    }

    author = "Tribunal Panel"

    # Treat the whole text as one block from the Panel
    new_chunks = split_into_paragraphs(text, author, opinion_type="majority", is_lead=True)
    case_data['chunks'].extend(new_chunks)

    return case_data

# ==========================================
# CORE LOGIC: CHUNKING & METADATA
# ==========================================
def split_into_paragraphs(text_block, author, opinion_type, is_lead):
    """
    Splits text blocks into paragraphs and applies metadata tags.
    """
    chunks = []

    # Pull Paragraph Regex from YAML
    para_regex = CONFIG['parsing_rules']['paragraph_split_regex']
    parts = re.split(para_regex, text_block)

    # Loop through pairs (Paragraph Number, Paragraph Text)
    # re.split returns [text_before, number, text_after, number, text_after...]
    for k in range(1, len(parts), 2):
        para_num = int(parts[k])
        content = parts[k+1].strip()

        # 1. DETECT SECTION TYPE (Using Regex Patterns)
        section_type = "analysis" # Default
        first_line = content.split('\n')[0]

        # Only check for "Facts" in the first 25 paragraphs of the Lead opinion
        if is_lead and para_num < 25:
            for pattern in CONFIG['section_patterns']['facts']:
                if re.search(pattern, first_line):
                    section_type = "facts"
                    break

        # 2. CHECK FOR DISSENT INDICATORS (If not already marked)
        if para_num < 10: # Only look for dissent announcements early on
            for pattern in CONFIG['section_patterns']['dissent_indicators']:
                if re.search(pattern, content):
                    opinion_type = "dissenting"
                    break

        # 3. EXTRACT CITATIONS (For Hyperlinking)
        citations_found = extract_citations(content)
        has_citation = len(citations_found) > 0

        chunks.append({
            "para_number": para_num,
            "content_text": content,
            "author_name": author,
            "opinion_type": opinion_type,
            "section_type": section_type,
            "has_citation": has_citation,
            "cited_cases": citations_found # List of strings: ['[2024] UKSC 24']
        })

    return chunks

def extract_citations(text):
    """
    Finds all legal citations in the text block using the YAML regex.
    Returns a list of strings found.
    """
    regex = CONFIG['parsing_rules']['citation_regex']
    return re.findall(regex, text)

def find_main_citation(text, regex_pattern):
    """
    Finds the main citation for the case file itself.
    """
    match = re.search(regex_pattern, text)
    return match.group(0) if match else "Unknown Citation"