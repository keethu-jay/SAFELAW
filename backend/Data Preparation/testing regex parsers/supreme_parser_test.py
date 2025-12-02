import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


JUDGE_HEADER_REGEX = re.compile(r"^(LORD|LADY)\s+[A-Z\- ]+:\s*$", re.MULTILINE)
PARAGRAPH_SPLIT_REGEX = re.compile(r"\n\s*(\d+)\.\s+")
CITATION_REGEX = re.compile(r"\[\d{4}\]\s+UKSC\s+\d+")


def strip_xml_tags(text: str) -> str:
    """Very naive XML/HTML stripper just for this experiment."""
    return re.sub(r"<[^>]+>", " ", text)


def classify_section(para_num: int, content: str, is_lead: bool) -> str:
    """Heuristic labelling of paragraph section type. Intentionally brittle."""
    first_line = content.split("\n", 1)[0]
    # Facts – early paragraphs of the lead opinion with typical headings.
    if is_lead and para_num <= 25 and re.search(
        r"(?i)(background|facts|introduction|procedural history)", first_line
    ):
        return "facts"

    # History of lower court – looks for mentions of lower courts.
    if re.search(
        r"(?i)(court of appeal|high court|judge at first instance|tribunal below|lower court)",
        content,
    ):
        return "history_lower_court"

    # Conclusions – end-of-judgment style phrases.
    if re.search(
        r"(?i)(for (all )?these reasons|i (would|will) (allow|dismiss) the appeal|"
        r"the appeal (is|should be) (allowed|dismissed))",
        content,
    ):
        return "conclusion"

    return "analysis"


def extract_citations(text: str):
    return CITATION_REGEX.findall(text)


def split_into_paragraphs(text_block: str, author: str, opinion_type: str, is_lead: bool):
    """Split a judge's block into paragraphs with metadata."""
    chunks = []
    parts = re.split(PARAGRAPH_SPLIT_REGEX, text_block)

    # [pre, num, text, num, text, ...]
    for idx in range(1, len(parts), 2):
        try:
            para_num = int(parts[idx])
        except ValueError:
            continue
        content = parts[idx + 1].strip()
        if not content:
            continue

        section_type = classify_section(para_num, content, is_lead=is_lead)

        # Crude dissent detection inside paragraphs as well.
        local_opinion = opinion_type
        if re.search(r"(?i)\b(i respectfully )?dissent\b", content):
            local_opinion = "dissenting"

        citations_found = extract_citations(content)
        has_citation = bool(citations_found)

        chunks.append(
            {
                "para_number": para_num,
                "content_text": content,
                "author_name": author,
                "opinion_type": local_opinion,
                "section_type": section_type,
                "has_citation": has_citation,
                "cited_cases": citations_found,
            }
        )

    return chunks


def process_document(raw_text: str, filename: str):
    """
    Extremely simplified Supreme Court parser, contained entirely in this file.
    It ignores YAML and tries to do everything with regex heuristics to show
    how brittle this approach is on real XML judgments.
    """
    text = strip_xml_tags(raw_text)

    citation_match = CITATION_REGEX.search(text)
    citation = citation_match.group(0) if citation_match else "Unknown Citation"

    case_data = {
        "filename": filename,
        "citation": citation,
        "court_level": "UKSC",
        "chunks": [],
    }

    segments = re.split(JUDGE_HEADER_REGEX, text)

    current_author = "Unknown Judge"
    seen_first_judge = False

    for idx, segment in enumerate(segments):
        # If this piece looks like a judge header (e.g. LORD REED:)
        if JUDGE_HEADER_REGEX.match(segment + ":"):
            current_author = segment.strip().rstrip(":")
            continue

        block = segment.strip()
        if len(block) < 50:
            continue

        is_lead = not seen_first_judge
        opinion_type = "majority" if is_lead else "concurring"

        if re.search(r"(?i)\bdissent\b", current_author) or re.search(r"(?i)\bdissent\b", block):
            opinion_type = "dissenting"

        new_chunks = split_into_paragraphs(block, current_author, opinion_type, is_lead=is_lead)
        if new_chunks and is_lead:
            seen_first_judge = True

        case_data["chunks"].extend(new_chunks)

    return case_data


def run_supreme_tests():
    """
    Test harness for the Supreme Court (seriatim) regex parser.

    - Reads XML sample files from `supreme_samples/`
    - Runs them through the local `process_document`
    - Writes JSON outputs to `output_json/`
    - Prints a short summary so you can inspect how brittle the metadata is
    """
    samples_dir = BASE_DIR / "supreme_samples"
    output_dir = BASE_DIR / "output_json"

    output_dir.mkdir(parents=True, exist_ok=True)

    sample_files = sorted([p for p in samples_dir.iterdir() if p.is_file() and p.suffix.lower() == ".xml"])

    if not sample_files:
        print("No XML sample files found in:", samples_dir)
        print("Place your three Supreme Court XML judgments in that folder and re-run.")
        return

    for path in sample_files:
        print("\n==============================")
        print(f"Running parser on: {path.name}")
        raw_text = path.read_text(encoding="utf-8", errors="ignore")

        result = process_document(raw_text, path.name)
        chunks = result.get("chunks", [])
        print(f"- Detected citation: {result.get('citation')}")
        print(f"- Court level: {result.get('court_level')}")
        print(f"- Total chunks: {len(chunks)}")

        if chunks:
            first = chunks[0]
            print(
                "- Example chunk:",
                f"para {first.get('para_number')} | author={first.get('author_name')} |",
                f"opinion={first.get('opinion_type')} | section={first.get('section_type')} "
                f"| has_citation={first.get('has_citation')}",
            )

        output_path = output_dir / f"{path.stem}.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"- JSON written to: {output_path.relative_to(BASE_DIR)}")
        print("Open this JSON to see how often the regex heuristics mislabel or miss metadata.")


if __name__ == "__main__":
    run_supreme_tests()


