"""
Central parser for UK court judgments. Routes documents to the right parser
(seriatim vs unitary) based on YAML config. Lives alongside config_loader and
court_config.yaml.
"""
import re
import json
import os

from config_loader import CONFIG


def process_document(raw_text, filename):
    """
    Traffic controller: I loop through courts in YAML, detect which court this
    file belongs to, then route to the right logic (seriatim vs unitary).
    """
    detected_court = None

    for court in CONFIG['courts']:
        if re.search(court['identification_regex'], raw_text):
            detected_court = court
            break

    if not detected_court:
        print(f"Skipping {filename}: Could not identify court from YAML patterns.")
        return None

    print(f"Processing {filename} as {detected_court['name']} ({detected_court['structure_type']})")

    if detected_court['structure_type'] == "seriatim":
        return parse_seriatim_judgment(raw_text, detected_court)

    elif detected_court['structure_type'] == "unitary":
        return parse_unitary_judgment(raw_text, detected_court)

    return None


# PARSER TYPE A: SERIATIM (Multiple Judges)
def parse_seriatim_judgment(text, court_config):
    """
    Handles cases where judges write separate opinions (e.g. UK Supreme Court).
    Splits by judge headers and chunks each opinion into paragraphs.
    """
    case_data = {
        "citation": find_main_citation(text, court_config['identification_regex']),
        "court_level": court_config['db_code'],
        "chunks": []
    }

    judge_regex = CONFIG['parsing_rules']['judge_header_regex']
    segments = re.split(judge_regex, text, flags=re.MULTILINE)

    current_author = "Unknown"

    for i, segment in enumerate(segments):
        # append ':' because the regex expects a colon at the end of judge names
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

            new_chunks = split_into_paragraphs(
                segment,
                current_author,
                opinion_type,
                is_lead=(opinion_type == "majority")
            )
            case_data['chunks'].extend(new_chunks)

    return case_data


# PARSER TYPE B: UNITARY (Single Decision)
def parse_unitary_judgment(text, court_config):
    """
    Handles cases with one unified decision (e.g. tribunals). Treats the whole
    text as a single block from the panel.
    """
    case_data = {
        "citation": find_main_citation(text, court_config['identification_regex']),
        "court_level": court_config['db_code'],
        "chunks": []
    }

    author = "Tribunal Panel"
    new_chunks = split_into_paragraphs(text, author, opinion_type="majority", is_lead=True)
    case_data['chunks'].extend(new_chunks)

    return case_data


# CORE LOGIC: CHUNKING & METADATA
def split_into_paragraphs(text_block, author, opinion_type, is_lead):
    """
    Splits text blocks into paragraphs and tags each with metadata (section type,
    citations, etc.). Uses YAML patterns for facts, history, conclusions, dissent.
    """
    chunks = []
    para_regex = CONFIG['parsing_rules']['paragraph_split_regex']
    parts = re.split(para_regex, text_block)

    # re.split gives [text_before, num, text_after, num, text_after, ...]; step by 2
    for k in range(1, len(parts), 2):
        para_num = int(parts[k])
        content = parts[k + 1].strip()

        # I detect section type using YAML patterns; default to "analysis"
        section_type = "analysis"
        first_line = content.split('\n')[0]

        if is_lead and para_num < 25:
            for pattern in CONFIG['section_patterns']['facts']:
                if re.search(pattern, first_line):
                    section_type = "facts"
                    break

        if section_type == "analysis":
            for pattern in CONFIG['section_patterns'].get('history_lower_court', []):
                if re.search(pattern, content):
                    section_type = "history_lower_court"
                    break

        # conclusion markers – brittle; different drafting styles break it
        for pattern in CONFIG['section_patterns'].get('conclusions', []):
            if re.search(pattern, content):
                section_type = "conclusion"
                break

        if para_num < 10:
            for pattern in CONFIG['section_patterns']['dissent_indicators']:
                if re.search(pattern, content):
                    opinion_type = "dissenting"
                    break

        citations_found = extract_citations(content)
        has_citation = len(citations_found) > 0

        chunks.append({
            "para_number": para_num,
            "content_text": content,
            "author_name": author,
            "opinion_type": opinion_type,
            "section_type": section_type,
            "has_citation": has_citation,
            "cited_cases": citations_found,
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
    """Finds the main citation for the case file itself (e.g. [2024] UKSC 43)."""
    match = re.search(regex_pattern, text)
    return match.group(0) if match else "Unknown Citation"