
#!/usr/bin/env python3
import argparse
import csv
import os
import random
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from bs4 import BeautifulSoup

DEFAULT_SELECTORS_TO_STRIP = ["script", "style", "nav", "footer", "noscript"]


def extract_text_from_html(html: str, structured: bool = False) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # remove noisy blocks
    for tag in DEFAULT_SELECTORS_TO_STRIP:
        for el in soup.find_all(tag):
            el.decompose()

    if structured:
        parts = []
        # Headings
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                parts.append(f"[H{level}] {h.get_text(strip=True)}")
        # Paragraphs
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            if txt:
                parts.append(txt)
        # Lists
        for li in soup.find_all("li"):
            txt = li.get_text(" ", strip=True)
            if txt:
                parts.append(f"- {txt}")
        # Tables (basic)
        for tr in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                parts.append(" | ".join(cells))
        return "\n".join(parts) + "\n"
    else:
        return soup.get_text("\n", strip=True) + "\n"

from typing import Optional

def process_file(path: Path, out_dir: Path, structured: bool = False, rel_root: Optional[Path] = None) -> dict:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = extract_text_from_html(raw, structured=structured)

        # mirror relative directory structure in out_dir
        rel = path.relative_to(rel_root) if rel_root else path.name
        if isinstance(rel, Path):
            out_path = out_dir / rel.with_suffix(".txt")
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_path = out_dir / (Path(rel).stem + ".txt")

        out_path.write_text(text, encoding="utf-8")
        return {
            "file": str(path),
            "out_text": str(out_path),
            "chars": len(text),
            "status": "ok",
        }
    except Exception as e:
        return {"file": str(path), "out_text": "", "chars": 0, "status": f"error: {e}"}


def main():
    ap = argparse.ArgumentParser(description="Sample ~N HTML files and extract text to .txt files.")
    ap.add_argument("--input-dir", required=True, help="Path to local folder containing .html/.htm files (e.g., your synced Dropbox folder)")
    ap.add_argument("--out-dir", default="./out", help="Where to write extracted .txt files and the log.csv")
    ap.add_argument("--sample-size", type=int, default=50, help="How many files to sample (set <= 0 to process all)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling")
    ap.add_argument("--pattern", default="*.html,*.htm", help="Glob patterns (comma-separated) to discover HTML files")
    ap.add_argument("--structured", action="store_true", help="Preserve some structure (headings, lists, tables) in the output")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Parallel workers")
    args = ap.parse_args()

    in_dir = Path(args.input_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover files
    patterns = [p.strip() for p in args.pattern.split(",") if p.strip()]
    files = []
    for pat in patterns:
        files.extend(in_dir.rglob(pat))

    files = [f for f in files if f.is_file()]
    if not files:
        print("No HTML files found. Check --input-dir and --pattern.")
        return

    # Sample
    rng = random.Random(args.seed)
    if args.sample_size and args.sample_size > 0 and args.sample_size < len(files):
        files = rng.sample(files, args.sample_size)

    print(f"Processing {len(files)} files with {args.workers} workers...")

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        fut2file = {
            ex.submit(process_file, f, out_dir, args.structured, in_dir): f for f in files
        }
        for fut in as_completed(fut2file):
            res = fut.result()
            results.append(res)
            status = res["status"]
            print(f"[{status}] {res['file']}")

    # Write log
    log_path = out_dir / "log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["file", "out_text", "chars", "status"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Wrote {len(results)} results.")
    print(f"Outputs in: {out_dir}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
