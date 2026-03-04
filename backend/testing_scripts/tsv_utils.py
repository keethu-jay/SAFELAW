# Shared helpers for v1–v4: load rows, classify, filter hits (no same-case, no dupes), embed, RPC/DB fallback.

import csv
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
_env_path = BACKEND_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Paths
INPUT_TSV = BACKEND_DIR / "Simplified_Test_Input.tsv"
METADATA_PATH = BACKEND_DIR / "case_metadata.json"
REFERENCE_OUTPUT_DIR = BACKEND_DIR / "testing_scripts" / "output"

FILE_TO_DOC_ID = {
    "Donoghue v Stevenson [1932] UKHL 100.xml": "Donoghue v Stevenson [1932] UKHL 100",
    "Norris v A.G. [1983] IESC 3.xml": "Norris v A.G. [1983] IESC 3",
    "McGee v A.G. and Anor [1973] IESC 2.xml": "McGee v A.G. and Anor [1973] IESC 2",
    "McLoughlin v O'Brian [1982] UKHL 3.xml": "McLoughlin v O'Brian [1982] UKHL 3",
    "Ann Kelly v Fergus Hennessy [1995] 3 IR 253.xml": "Ann Kelly v Fergus Hennessy [1995] 3 IR 253",
}

CLASSIFICATIONS = [
    "Introduction", "Facts", "Authority", "Doctrine and Policy", "Reasoning", "Judgment",
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

SUBSTR_LEN, SUBSTR_STEP = 100, 30


def classify_paragraph(paragraph: str, openai_client) -> str:
    if not openai_client:
        return "Reasoning"
    prompt = CLASSIFICATION_PROMPT.format(paragraph=(paragraph or "")[:2000])
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal document classifier. Respond with only the category name."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        for cat in CLASSIFICATIONS:
            if cat.lower() in result.lower():
                return cat
        return "Reasoning"
    except Exception as e:
        print(f"  Classification error: {e}")
        return "Reasoning"


def load_input_rows() -> List[List[str]]:
    rows = []
    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[1:]:
        line = line.rstrip("\n\r")
        parts = line.split("\t", 2)
        court_opinion = (parts[0] if len(parts) > 0 else "").strip()
        file_name = (parts[1] if len(parts) > 1 else "").strip()
        test_para = (parts[2] if len(parts) > 2 else "").strip()
        if court_opinion or file_name or test_para:
            rows.append([court_opinion, file_name, test_para])
    return rows


def file_name_to_doc_id(file_name: str) -> str:
    if not file_name:
        return ""
    f = file_name.strip()
    if f in FILE_TO_DOC_ID:
        return FILE_TO_DOC_ID[f]
    return f.replace(".xml", "").strip()


def normalize_case_name(s: str) -> str:
    s = (s or "").strip().strip("()").replace(".xml", "")
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def is_same_case(source_file: str, doc_id: str) -> bool:
    if not (source_file and doc_id):
        return False
    src = normalize_case_name(source_file.replace(".xml", ""))
    hit = normalize_case_name(doc_id)
    if src == hit:
        return True
    src_core = re.sub(r"\s*\[\d{4}\][^\]]*\]?\s*", " ", src)
    hit_core = re.sub(r"\s*\[\d{4}\][^\]]*\]?\s*", " ", hit)
    src_core = re.sub(r"\s+", " ", src_core).strip()
    hit_core = re.sub(r"\s+", " ", hit_core).strip()
    if src_core and hit_core:
        if src_core in hit_core or hit_core in src_core:
            return True
        if len(src_core) >= 10 and len(hit_core) >= 10 and src_core[:25] == hit_core[:25]:
            return True
    return False


def core_text_for_dedup(text: str) -> str:
    t = (text or "").strip()
    while True:
        m = re.match(r"^\[\s*s?\d+\s*\]\s*", t, re.IGNORECASE)
        if not m:
            break
        t = t[m.end():].strip()
    t = t.lower()[:900]
    t = re.sub(r"[\"\'""'']", " ", t)
    t = re.sub(r"[\—\-\–,;:]\s*", " ", t)
    t = re.sub(r"-\s+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:450]


def filter_hits(
    hits: List[Dict],
    source_file: str,
    test_label: str,
    filter_by_label: bool,
    max_suggestions: int = 10,
) -> List[Dict]:
    """
    Apply universal rules: no same-case, no repeats, optional role filter.
    Returns up to max_suggestions hits.
    """
    filtered = []
    seen_texts = set()
    seen_substrings = set()
    for hit in hits:
        doc_id = (hit.get("doc_id") or "").strip()
        text = (hit.get("text") or "").strip()
        classification = (hit.get("classification") or "").strip()

        if source_file and doc_id and is_same_case(source_file, doc_id):
            continue
        if filter_by_label and classification != test_label:
            continue

        core = core_text_for_dedup(text)
        if not core or core in seen_texts:
            continue
        if any((n := min(130, len(core), len(prev))) >= 80 and core[:n] == prev[:n] for prev in seen_texts):
            continue
        core_substrs = {
            core[i : i + SUBSTR_LEN]
            for i in range(0, max(0, len(core) - SUBSTR_LEN) + 1, SUBSTR_STEP)
            if len(core[i : i + SUBSTR_LEN]) >= 80
        }
        if core_substrs & seen_substrings:
            continue
        seen_texts.add(core)
        seen_substrings.update(core_substrs)
        filtered.append(hit)
        if len(filtered) >= max_suggestions:
            break
    return filtered


def get_db_url() -> Optional[str]:
    if os.environ.get("DATABASE_PASSWORD"):
        from urllib.parse import quote_plus
        host = os.environ.get("DATABASE_HOST", "aws-1-us-east-2.pooler.supabase.com")
        port = os.environ.get("DATABASE_PORT", "5432")
        user = os.environ.get("DATABASE_USER", "postgres.ywrwweexwsxvchbnwiju")
        password = os.environ.get("DATABASE_PASSWORD")
        dbname = os.environ.get("DATABASE_NAME", "postgres")
        return f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"
    return os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")


def run_direct_db_knn(
    table: str,
    extra_col: str,
    vec: List[float],
    max_res: int,
    exclude_doc_id: str = "",
) -> List[Dict]:
    """Run KNN via direct DB (bypasses RPC timeout). Excludes source case if exclude_doc_id set."""
    db_url = get_db_url()
    if not db_url:
        return []
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '300000'")
        vec_str = "[" + ",".join(str(x) for x in vec) + "]"
        cols = ["id", "doc_id", "text", "classification", extra_col, "section_title", "section_number", "sentence_index", "global_index", "court", "decision", "similarity"]
        if exclude_doc_id:
            cur.execute(f"""
                SELECT id, doc_id, text, classification, {extra_col},
                    section_title, section_number, sentence_index, global_index, court, decision,
                    (-1.0) * (embedding <#> %s::vector)::float AS similarity
                FROM {table}
                WHERE (doc_id IS NULL OR (doc_id IS NOT NULL AND doc_id NOT ILIKE %s || '%%'))
                ORDER BY embedding <#> %s::vector
                LIMIT %s
            """, (vec_str, exclude_doc_id, vec_str, max_res))
        else:
            cur.execute(f"""
                SELECT id, doc_id, text, classification, {extra_col},
                    section_title, section_number, sentence_index, global_index, court, decision,
                    (-1.0) * (embedding <#> %s::vector)::float AS similarity
                FROM {table}
                ORDER BY embedding <#> %s::vector
                LIMIT %s
            """, (vec_str, vec_str, max_res))
        rows = cur.fetchall()
        hits = [dict(zip(cols, r)) for r in rows]
        cur.close()
        conn.close()
        return hits
    except Exception as e:
        print(f"  Direct DB fallback failed: {e}")
        return []


def load_case_metadata() -> Dict:
    meta = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH, encoding="utf-8") as f:
            meta = json.load(f)
    return meta


def get_context_tag(doc_id: str, case_metadata: Dict, test_para: str) -> str:
    """Build context tag: short_name year judges. para_preview."""
    meta = case_metadata.get(doc_id)
    if not meta:
        stem_key = doc_id.replace(" ", "_").replace("[", "[").replace("]", "]")
        meta = case_metadata.get(stem_key)
    if not meta:
        for k, v in case_metadata.items():
            if isinstance(v, dict) and doc_id and (doc_id in k or (k.replace("_", " ").split("[")[0].strip() == doc_id.split("[")[0].strip())):
                meta = v
                break
    meta = meta or {}
    short_name = meta.get("short_name", doc_id.split("[")[0].strip() if "[" in doc_id else doc_id)
    year = meta.get("year", "")
    judges = meta.get("judges", [])
    judges_str = ", ".join(judges[:6]) if judges else "Various"
    para_preview = test_para.strip()[:100].replace("\n", " ")
    return f"{short_name} {year} Judges: {judges_str}. {para_preview}"


def sanitize_cell(s) -> str:
    if s is None:
        return ""
    s = str(s)
    return s.replace("\t", " ").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()


def ensure_reference_output_dir():
    REFERENCE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_tsv(output_path: Path, header: List[str], rows: List[List], n_cols: int):
    ensure_reference_output_dir()
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerow(header)
        for r in rows:
            cells = [sanitize_cell(c) for c in r]
            while len(cells) < n_cols:
                cells.append("")
            w.writerow(cells[:n_cols])
