#!/usr/bin/env python3
"""
Generate Corpus Studio Baseline output for the 5 XML files in Test Files/xml docs.

Reads the 5 XMLs, extracts test paragraphs (Beginning, Middle, End), queries Supabase
for semantic suggestions, and outputs CSV/TSV in the same format as Corpus_Studio_Baseline_Output.

Usage:
  python run_baseline_for_test_files.py

Requires: .env with SUPABASE_URL, SUPABASE_KEY, ISAACUS_API_KEY, OPENAI_API_KEY.
OPENAI_API_KEY: GPT-4o-mini validates all text (Context, Test Paragraph) before embeddings/RAG - rejects bad data (DEFENDANTS, lone numbers, judge names only).
Output: backend/Test_Files_Baseline_Semantic_Only.tsv (semantic columns only; tab-separated; use Tab as separator in Google Sheets)
"""

import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

# Load .env from backend directory
SCRIPT_DIR = Path(__file__).resolve().parent
_env_path = SCRIPT_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

BASE_DIR = SCRIPT_DIR.parent
FINAL_DATASET_DIR = BASE_DIR / "Final Dataset"
RAW_XML_DIR = BASE_DIR / "data" / "raw_xml"
TEST_XML_DIR = SCRIPT_DIR / "Test Files" / "xml docs"
OUTPUT_TSV = SCRIPT_DIR / "Test_Files_Baseline_Semantic_Only.tsv"
INPUT_TSV = SCRIPT_DIR / "Test_Files_Baseline_Input.tsv"

# Court/Opinion mapping by filename pattern
COURT_MAP = {
    "UKHL": "UKSC",
    "IESC": "Tribunal",
}


def extract_paragraphs_from_xml(path: Path) -> list[str]:
    """Extract paragraph text from our simple XML format."""
    paras = []

    def _parse_and_extract(content: str) -> list[str]:
        result = []
        root = ET.fromstring(content)
        for p in root.findall(".//p"):
            text = "".join(p.itertext()).strip()
            if text:
                result.append(text)
        return result

    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for p in root.findall(".//p"):
            text = "".join(p.itertext()).strip()
            if text:
                paras.append(text)
    except ET.ParseError:
        # Fallback: sanitize invalid XML chars and re-parse
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", raw)
            paras = _parse_and_extract(sanitized)
        except Exception:
            pass
    except Exception:
        pass
    return paras


def _truncate(s: str, max_len: int = 150) -> str:
    return (s[:max_len] + "...") if len(s) > max_len else s


# Patterns that indicate RTF/Word formatting metadata, not real legal content
_FORMATTING_PATTERNS = [
    r"Times New Roman",
    r"Default Paragraph Font",
    r"Body Text\b",
    r"heading \d+",
    r"Law\d*\s*Law\d*",
    r"Title;?\s*Body",
    r"\*\s*\.\s*\*\s*\.\s*\*",  # "* . * . *"
    r"^\s*[\*\;\s\.\(\)]+\s*$",  # mostly punctuation
]


def _is_formatting_metadata(text: str) -> bool:
    """True if paragraph looks like RTF/Word font or style metadata, not legal content."""
    s = (text or "").strip()
    if len(s) < 30:
        return False
    lower = s.lower()
    for pat in _FORMATTING_PATTERNS:
        if re.search(pat, s, re.IGNORECASE):
            return True
    # High ratio of semicolons + style-like words
    if lower.count(";") >= 3 and any(
        w in lower for w in ["font", "normal", "heading", "body text", "title", "paragraph"]
    ):
        return True
    return False


def _substantive(p: str, min_len: int = 50) -> bool:
    """True if paragraph has real content (not placeholder, junk, or too short)."""
    s = (p or "").strip()
    if len(s) < min_len:
        return False
    if s in ("~", "-", "—"):
        return False
    if _is_formatting_metadata(s):
        return False
    return True


def pick_test_paragraphs(paras: list[str]) -> list[tuple[str, str, str, str, int]]:
    """
    Pick exactly 3 test paragraphs: Beginning, Middle, End.
    Skips placeholder paragraphs (e.g. "~") so Context and Test Paragraph always have real content from the file.
    Returns list of (position, ctx_prev, test_para, ctx_next, test_idx).
    """
    if not paras:
        return [("Beginning", "", "", "", 0), ("Middle", "", "", "", 0), ("End", "", "", "", 0)]

    n = len(paras)
    result = []

    # Beginning: first substantive paragraph after skipping first 1-3
    skip = min(3, n - 1)
    start_idx = skip
    for i in range(skip, min(skip + 10, n)):
        if _substantive(paras[i]):
            start_idx = i
            break
    def _prev_context(idx: int) -> str:
        """Actual previous paragraph from file - use adjacent content so context is never blank."""
        if idx <= 0:
            return ""
        p = (paras[idx - 1] or "").strip()
        if p in ("~",):  # skip only true placeholders
            for k in range(idx - 2, -1, -1):
                q = (paras[k] or "").strip()
                if q and q != "~":
                    return q
            return ""
        return p

    def _next_context(idx: int) -> str:
        """Actual next paragraph from file - use adjacent content so context is never blank."""
        if idx + 1 >= n:
            return ""
        p = (paras[idx + 1] or "").strip()
        if p in ("~",):
            for k in range(idx + 2, n):
                q = (paras[k] or "").strip()
                if q and q != "~":
                    return q
            return ""
        return p

    ctx_prev_begin = _prev_context(start_idx)
    ctx_next_begin = _next_context(start_idx)
    result.append(("Beginning", ctx_prev_begin, paras[start_idx], ctx_next_begin, start_idx))

    # Middle: center, but if not substantive search nearby for first substantive
    mid = n // 2
    mid_idx = mid
    for j in range(mid, min(mid + 20, n)):
        if _substantive(paras[j]):
            mid_idx = j
            break
    for j in range(mid - 1, max(mid - 20, -1), -1):
        if _substantive(paras[j]):
            mid_idx = j
            break
    ctx_prev_mid = _prev_context(mid_idx)
    ctx_next_mid = _next_context(mid_idx)
    result.append(("Middle", ctx_prev_mid, paras[mid_idx], ctx_next_mid, mid_idx))

    # End: last substantive paragraph (skip final 1-3), so we never pick "~" or boilerplate
    end_idx = n - 1
    for i in range(max(0, n - 1 - 3), mid - 1, -1):  # from near end backwards down to mid
        if _substantive(paras[i]):
            end_idx = i
            break
    ctx_prev_end = _prev_context(end_idx)
    result.append(("End", ctx_prev_end, paras[end_idx], "", end_idx))

    return result


# Boilerplate that must never appear as Context or Test Paragraph (same across many files = bad data)
_BAD_CONTEXT_PATTERNS = [
    r"^THE SUPREME COURT\s*$",
    r"^HOUSE OF LORDS?\s*$",
    r"^\[?\d{4}\s+No\.\s*\d+\s*[Pp]\]?\s*$",  # [1971 No. 2314 P]
    r"^Walsh J\.?$", r"^Budd J\.?$", r"^Henchy J\.?$", r"^Griffin J\.?$", r"^Fitzgerald C\.?J\.?$",
    r"^DEFENDANTS?\s*$", r"^PLAINTIFFS?\s*$", r"^BETWEEN\s*$", r"^\s*and\s*$",
    r"^JUDGMENT of .+ delivered .+\s*$",  # short judgment header only
    r"^[A-Z][a-z]+ J\.\s*$",  # Judge name only
    r"^THE (REVENUE )?COMMISSIONERS\s*$",
    r"^THE ATTORNEY GENERAL\s*$",
]


def _is_bad_context(text: str) -> bool:
    """Heuristic: reject boilerplate that appears in many files and has no substantive legal content."""
    s = (text or "").strip()
    if len(s) < 50:  # Context must be substantial
        return True
    lower = s.lower()
    for pat in _BAD_CONTEXT_PATTERNS:
        if re.search(pat, s, re.IGNORECASE):
            return True
    if s.upper() == s and len(s) < 80:  # All caps short = likely heading
        return True
    if s in ("THE SUPREME COURT", "HOUSE OF LORDS", "DEFENDANTS", "PLAINTIFF"):
        return True
    return False


def _gpt_validate_content(texts: list[str]) -> list[bool]:
    """
    Use GPT-4o-mini to check if each snippet is good legal content.
    Heuristic _is_bad_context is applied first; GPT is the second check.
    """
    if not texts:
        return []
    # Heuristic first - never allow known boilerplate
    heuristic_invalid = [_is_bad_context(t) for t in texts]
    to_check = [(i, t) for i, t in enumerate(texts) if not heuristic_invalid[i]]
    if not to_check:
        return [False] * len(texts)
    key = os.environ.get("OPENAI_API_KEY")
    if not key or not _OPENAI_AVAILABLE:
        return [not heuristic_invalid[i] for i in range(len(texts))]
    try:
        client = OpenAI(api_key=key)
        parts = []
        indices = []
        for i, t in to_check:
            s = (t or "").strip()
            snippet = (s[:400] + "..." if len(s) > 400 else s).replace("\n", " ")
            parts.append(f"{len(parts)+1}. {snippet}")
            indices.append(i)
        prompt = f"""For each snippet below from legal judgment XMLs, reply Y or N.
Y = substantive legal content: reasoning, facts, holdings, legal analysis, real case discussion (multiple sentences or a substantial paragraph)
N = bad: court names (THE SUPREME COURT, HOUSE OF LORDS), headings, judge names alone (Walsh J.), party labels (DEFENDANTS, PLAINTIFF), case numbers alone ([1971 No. 2314 P]), short headings, formatting

Snippets:
{chr(10).join(parts)}

Reply with exactly {len(parts)} letters (Y or N), no spaces."""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip().upper().replace(" ", "")
        result = [False] * len(texts)
        for j, idx in enumerate(indices):
            result[idx] = j < len(raw) and raw[j] == "Y"
        return result
    except Exception as e:
        print(f"  GPT validation skipped ({e})")
        return [not heuristic_invalid[i] for i in range(len(texts))]


def _gpt_validate_paragraphs(texts: list[str], file_name: str = "") -> list[bool]:
    """Use GPT-4o-mini to check if each paragraph is real legal content (not formatting/metadata). Returns list of True/False."""
    if not texts:
        return []
    key = os.environ.get("OPENAI_API_KEY")
    if not key or not _OPENAI_AVAILABLE:
        return [True] * len(texts)
    try:
        client = OpenAI(api_key=key)
        parts = []
        for i, t in enumerate(texts):
            snippet = (t[:500] + "..." if len(t) > 500 else t).replace("\n", " ")
            parts.append(f"{i+1}. {snippet}")
        prompt = f"""For each paragraph below from a legal judgment XML, reply with only Y or N for each.
Y = real legal/judgment content (reasoning, facts, holdings, etc.)
N = formatting metadata, font names, style names, RTF/Word junk, or not actual case content.

Paragraphs:
{chr(10).join(parts)}

Reply with exactly {len(texts)} letters (Y or N), no spaces, e.g. YNY"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip().upper().replace(" ", "")
        result = []
        for i in range(len(texts)):
            result.append(i < len(raw) and raw[i] == "Y")
        return result
    except Exception as e:
        print(f"  GPT validation skipped ({e})")
        return [True] * len(texts)


def _gpt_validate_and_fix_all_content(paras: list[str], picks: list[tuple], file_name: str = "") -> list[tuple]:
    """
    Validate ctx_prev, test_para, ctx_next with GPT BEFORE embeddings/RAG.
    Replace any bad data (DEFENDANTS, lone numbers, judge names only) with GPT-approved content from the file.
    """
    if not paras or not picks:
        return picks
    n = len(paras)
    all_texts = []
    for p in picks:
        pos, ctx_prev, test_para, ctx_next, test_idx = p[0], p[1], p[2], p[3], p[4]
        all_texts.extend([ctx_prev, test_para, ctx_next])
    valid = _gpt_validate_content(all_texts)
    result = []
    ptr = 0
    for p in picks:
        pos, ctx_prev, test_para, ctx_next, test_idx = p[0], p[1], p[2], p[3], p[4]
        v_prev = valid[ptr] and not _is_bad_context(ctx_prev)
        v_test = valid[ptr + 1] and not _is_bad_context(test_para)
        v_next = valid[ptr + 2] and not _is_bad_context(ctx_next)
        ptr += 3

        def _find_good_prev(idx: int) -> str:
            for k in range(idx - 1, max(-1, idx - 15), -1):
                if k >= 0:
                    t = (paras[k] or "").strip()
                    if t and t != "~" and len(t) >= 50 and not _is_bad_context(t):
                        return t
            return ""

        def _find_good_next(idx: int) -> str:
            for k in range(idx + 1, min(n, idx + 15)):
                t = (paras[k] or "").strip()
                if t and t != "~" and len(t) >= 50 and not _is_bad_context(t):
                    return t
            return ""

        if not v_prev or _is_bad_context(ctx_prev):
            candidates = [(paras[k] or "").strip() for k in range(test_idx - 1, max(-1, test_idx - 20), -1) if k >= 0]
            candidates = [c for c in candidates if c and c != "~" and len(c) >= 50 and not _is_bad_context(c)]
            if candidates:
                cand_valid = _gpt_validate_content(candidates)
                ctx_prev = next((c for c, v in zip(candidates, cand_valid) if v), _find_good_prev(test_idx))
            else:
                ctx_prev = _find_good_prev(test_idx)
        if not v_test:
            for j in range(test_idx + 1, min(n, test_idx + 30)):
                if _substantive(paras[j]) and not _is_bad_context(paras[j]) and _gpt_validate_content([paras[j]])[0]:
                    test_para, test_idx = paras[j], j
                    ctx_prev = _find_good_prev(j)
                    ctx_next = _find_good_next(j)
                    break
        if not v_next or _is_bad_context(ctx_next):
            candidates = [(paras[k] or "").strip() for k in range(test_idx + 1, min(n, test_idx + 20))]
            candidates = [c for c in candidates if c and c != "~" and len(c) >= 50 and not _is_bad_context(c)]
            if candidates:
                cand_valid = _gpt_validate_content(candidates)
                ctx_next = next((c for c, v in zip(candidates, cand_valid) if v), _find_good_next(test_idx))
            else:
                ctx_next = _find_good_next(test_idx)
        result.append((pos, ctx_prev, test_para, ctx_next, test_idx))
    return result


def _validate_and_replace_picks(paras: list[str], picks: list[tuple]) -> list[tuple]:
    """If GPT flags any picked paragraph as non-content, replace with next substantive candidate."""
    if not paras or not picks:
        return picks
    test_paras = [p[2] for p in picks]
    valid = _gpt_validate_paragraphs(test_paras)
    if all(valid):
        return picks
    n = len(paras)
    substantive_indices = [j for j in range(n) if _substantive(paras[j])]
    result = []
    for i, (pos, ctx_prev, test_para, ctx_next) in enumerate(picks):
        if valid[i]:
            result.append((pos, ctx_prev, test_para, ctx_next))
            continue
        try:
            old_idx = paras.index(test_para)
        except ValueError:
            old_idx = -1
        # Find next substantive index: for Beginning use next after old; Middle use next or prev; End use prev
        if pos == "Beginning":
            idx = next((j for j in substantive_indices if j > old_idx), substantive_indices[0] if substantive_indices else 0)
        elif pos == "Middle":
            mid = n // 2
            idx = next((j for j in substantive_indices if j > old_idx and j >= mid - 20), None)
            if idx is None:
                idx = next((j for j in reversed(substantive_indices) if j < old_idx and abs(j - mid) <= 40), substantive_indices[len(substantive_indices) // 2] if substantive_indices else mid)
        else:
            idx = next((j for j in reversed(substantive_indices) if j < old_idx and j >= n // 2), substantive_indices[-1] if substantive_indices else n - 1)
        if idx is None:
            idx = substantive_indices[min(i * len(substantive_indices) // 3, len(substantive_indices) - 1)] if substantive_indices else 0
        ctx_prev_new = (paras[idx - 1] or "").strip() if idx >= 1 else ""
        if ctx_prev_new in ("~",):
            ctx_prev_new = next(((paras[k] or "").strip() for k in range(idx - 2, -1, -1) if (paras[k] or "").strip() and (paras[k] or "").strip() != "~"), "")
        ctx_next_new = (paras[idx + 1] or "").strip() if idx + 1 < n else ""
        if ctx_next_new in ("~",):
            ctx_next_new = next(((paras[k] or "").strip() for k in range(idx + 2, n) if (paras[k] or "").strip() and (paras[k] or "").strip() != "~"), "")
        result.append((pos, ctx_prev_new, paras[idx], ctx_next_new))
        print(f"  Replaced {pos} (GPT flagged as non-content) with next candidate")
    return result


def infer_court_and_opinion(filename: str) -> tuple[str, str]:
    """Infer Court and Opinion Type from filename."""
    if "UKHL" in filename or "UKSC" in filename:
        return "UKSC", "Majority"
    if "IESC" in filename or "IR" in filename:
        return "Tribunal", "Majority"
    return "UKSC", "Majority"


def load_input_rows_from_tsv() -> list[list] | None:
    """Load rows from Test_Files_Baseline_Input.tsv if it exists (use curated content, skip XML/GPT)."""
    if not INPUT_TSV.exists():
        return None
    import csv
    rows = []
    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            co = row.get("Court/Opinion Type", "").strip().split(None, 1)
            court = co[0] if co else "UKSC"
            opinion = co[1] if len(co) >= 2 else "Majority"
            rows.append([
                court, opinion,
                row.get("File Name", ""),
                row.get("Test Position", ""),
                row.get("Context: Previous", ""),
                row.get("Test Paragraph (To Paste)", ""),
                row.get("Context: Next", ""),
            ])
    return rows if rows else None


def build_input_rows() -> list[list]:
    """Build input rows from the 5 XML files. GPT validates all content before embeddings/RAG."""
    xml_files = sorted(TEST_XML_DIR.glob("*.xml"))
    rows = []
    for xml_path in xml_files:
        if xml_path.name.endswith(".xml"):
            paras = extract_paragraphs_from_xml(xml_path)
            court, opinion = infer_court_and_opinion(xml_path.name)
            file_name = xml_path.name
            picks = pick_test_paragraphs(paras)
            picks = _gpt_validate_and_fix_all_content(paras, picks, file_name)
            for position, ctx_prev, test_para, ctx_next, _ in picks:
                rows.append([court, opinion, file_name, position, ctx_prev, test_para, ctx_next])
    return rows


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def find_xml_file(case_name: str, search_dirs: list) -> Path | None:
    raw = (case_name or "").strip().strip("()").replace(".xml", "")
    if not raw:
        return None
    targets = [normalize_case_name(raw)]
    # Also try without citation e.g. [2024] EWHC 123
    no_cite = re.sub(r"\s*\[\d{4}\][^\]]*\]?\s*", " ", raw).strip()
    if no_cite and no_cite != raw:
        targets.append(normalize_case_name(no_cite))
    for target_norm in targets:
        target_prefix = target_norm.replace("...", "").strip()
        if len(target_prefix) > 50:
            target_prefix = target_prefix[:50]
        for base_dir in search_dirs:
            base = Path(base_dir)
            if not base.exists():
                continue
            for xml_path in base.rglob("*.xml"):
                stem_norm = normalize_case_name(xml_path.stem)
                if stem_norm == target_norm:
                    return xml_path
                if target_prefix and len(target_prefix) >= 8 and stem_norm.startswith(target_prefix[:30]):
                    return xml_path
                if target_prefix and stem_norm.startswith(target_prefix.split()[0]) and len(stem_norm) > 10:
                    # Same leading word + substantial overlap
                    if sum(1 for w in target_prefix.split()[:5] if w in stem_norm) >= 2:
                        return xml_path
    return None


def extract_full_text(file_path: Path) -> str:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        parts = [t.strip() for t in root.itertext() if t and t.strip()]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception:
        return ""


def cosine_sim(a, b):
    import numpy as np
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def main():
    sys.path.insert(0, str(SCRIPT_DIR / "src"))
    from embedding_helper import EmbeddingModel
    from supabase import create_client

    rows = load_input_rows_from_tsv()
    if rows:
        print(f"Using curated content from {INPUT_TSV}")
    else:
        if not TEST_XML_DIR.exists():
            print(f"Directory not found: {TEST_XML_DIR}")
            sys.exit(1)
        if not os.environ.get("OPENAI_API_KEY"):
            print("Set OPENAI_API_KEY in .env (required for GPT validation when extracting from XML)")
            sys.exit(1)
        rows = build_input_rows()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    model = EmbeddingModel(model_name="kanon-2-embedder")
    if not model.client:
        print("Isaacus client not initialized. Set ISAACUS_API_KEY in .env")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)
    search_dirs = [d for d in [FINAL_DATASET_DIR, RAW_XML_DIR, TEST_XML_DIR] if d.exists()]

    def embed_batch(texts, max_chars=8000):
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

    def get_top_10(supabase_client, test_paragraph: str, match_threshold=0.0):
        if not (test_paragraph or test_paragraph.strip()):
            return []
        embs = embed_batch([test_paragraph.strip()[:8000]])
        if not embs:
            return []
        try:
            r = supabase_client.rpc(
                "match_corpus_documents",
                {
                    "query_embedding": embs[0].tolist(),
                    "similarity_threshold": match_threshold,
                    "max_results": 10,
                },
            ).execute()
            return r.data or []
        except Exception as e:
            print(f"  RPC error: {e}")
            return []

    def compute_full_doc(path1: Path, path2: Path) -> float:
        """Embed both full documents and return cosine similarity (same model as pgvector)."""
        t1, t2 = extract_full_text(path1), extract_full_text(path2)
        if not t1 or not t2:
            return 0.0
        embs = embed_batch([t1[:8000], t2[:8000]])
        if len(embs) < 2:
            return 0.0
        return round(cosine_sim(embs[0], embs[1]), 4)

    suggestion_cols = []
    for i in range(1, 11):
        suggestion_cols.append(f"Suggestion {i} Text")
        suggestion_cols.append(f"Suggestion {i} Citation")
    out_header = [
        "Semantic Score Comparison of paragraphs",
        "Semantic Score Comparison of the whole file",
        "Semantic Scores",
        "Top Suggestion",
        *suggestion_cols,
    ]

    output_rows = []
    for idx, row in enumerate(rows):
        court, opinion, file_name, position, ctx_prev, test_para, ctx_next = row[0], row[1], row[2], row[3], row[4], row[5], row[6]

        para_sim = ""
        full_doc_sim = ""
        semantic_scores_col = ""
        top_suggestion_col = ""
        suggestion_texts = [""] * 10
        suggestion_citations = [""] * 10

        def _float_sim(hit):
            v = hit.get("similarity")
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            return None

        top10 = get_top_10(supabase, test_para)
        if len(top10) >= 1:
            first_sim = _float_sim(top10[0])
            if first_sim is not None:
                para_sim = round(first_sim, 4)

        scores = []
        for i, hit in enumerate(top10[:10]):
            suggestion_texts[i] = (hit.get("text") or "").strip()
            suggestion_citations[i] = (hit.get("doc_id") or "").strip()
            sim = _float_sim(hit)
            scores.append(sim if sim is not None else 0.0)
        if scores:
            semantic_scores_col = ", ".join(f"{s:.4f}" for s in scores)
            first_text = (top10[0].get("text") or "").strip()
            doc_id = (top10[0].get("doc_id") or "").strip()
            top_suggestion_col = f"{first_text} ({doc_id})" if doc_id else first_text
            path_source = find_xml_file(file_name.replace(".xml", ""), search_dirs) or find_xml_file(file_name, search_dirs)
            path_sugg = find_xml_file(doc_id, search_dirs)
            if path_source and path_sugg:
                full_doc_sim = compute_full_doc(path_source, path_sugg)

        suggestion_pairs = []
        for i in range(10):
            suggestion_pairs.append(suggestion_texts[i])
            suggestion_pairs.append(suggestion_citations[i])
        output_rows.append(
            [str(para_sim) if para_sim != "" else "", str(full_doc_sim) if full_doc_sim != "" else ""]
            + [semantic_scores_col, top_suggestion_col]
            + suggestion_pairs
        )
        print(f"Row {idx+1}/{len(rows)}: {file_name} {position} - para_sim={para_sim}, full_doc={full_doc_sim}, top10_filled={bool(semantic_scores_col)}")

    def sanitize_cell(s) -> str:
        """One line, no tabs; no newlines (so TSV columns don't break)."""
        if s is None:
            return ""
        if not isinstance(s, str):
            s = str(s)
        return s.replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()

    n_cols = len(out_header)
    out_path = OUTPUT_TSV.resolve()
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(out_header)
        for r in output_rows:
            cells = [sanitize_cell(cell) for cell in r]
            while len(cells) < n_cols:
                cells.append("")
            w.writerow(cells[:n_cols])
        f.flush()
        os.fsync(f.fileno())
    print(f"\nSaved: {out_path}")
    print("Import in Google Sheets: File > Import > Upload, choose Tab as separator.")


if __name__ == "__main__":
    main()
