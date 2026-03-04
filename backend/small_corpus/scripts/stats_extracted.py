#!/usr/bin/env python3
"""Quick stats on extracted HTML paragraph counts and character lengths."""
import re
from pathlib import Path

EXTRACTED = Path(__file__).resolve().parent.parent / "small_corpus" / "extracted_html"
ADDITIONAL = Path(__file__).resolve().parent.parent / "small_corpus" / "Additional Cases"


def sanitize(name: str) -> str:
    stem = name.replace(".html", "").replace(".htm", "")
    stem = re.sub(r"[\s:/\-\u2013\u2014\u2015]+", "_", stem)
    stem = re.sub(r'["\'<>|?*]', "", stem)
    stem = re.sub(r"_+", "_", stem).strip("_") + ".html"
    return stem


# MAIN
def main():
    names = [f.name for f in ADDITIONAL.glob("*.html")]
    converted = [sanitize(n) for n in names]

    rows = []
    for fname in sorted(converted):
        p = EXTRACTED / fname
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8", errors="replace")
        paras = re.findall(r'<p id="p\d+"[^>]*>\[\d+\]\s*(.*?)</p>', html, re.DOTALL)
        if not paras:
            continue
        lens = [len(pa) for pa in paras]
        avg = sum(lens) / len(lens)
        mn, mx = min(lens), max(lens)
        total = sum(lens)
        short = sum(1 for l in lens if l < 500)
        mid = sum(1 for l in lens if 500 <= l <= 1500)
        long_p = sum(1 for l in lens if l > 1500)
        rows.append(
            (fname[:58], len(paras), total, int(avg), mn, mx, short, mid, long_p)
        )

    print(f"{'Case':<60} {'Paras':>5} {'Total':>10} {'Avg':>6} {'Min':>6} {'Max':>6}  <500 500-1500 >1500")
    print("-" * 110)
    for r in rows:
        print(f"{r[0]:<60} {r[1]:>5} {r[2]:>10} {r[3]:>6} {r[4]:>6} {r[5]:>6}  {r[6]:>4} {r[7]:>7} {r[8]:>5}")
    print("-" * 110)
    print(f"{'TOTAL':<60} {sum(r[1] for r in rows):>5} {sum(r[2] for r in rows):>10}")


if __name__ == "__main__":
    main()
