#!/usr/bin/env python3
"""Check classification progress by counting files."""

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
EXTRACTED_DIR = BACKEND_DIR / "small_corpus" / "extracted_html"
PARA_DIR = BACKEND_DIR / "small_corpus" / "paragraphs_classified"
SENT_DIR = BACKEND_DIR / "small_corpus" / "sentences_indiv_class"

extracted = list(EXTRACTED_DIR.glob("*.html")) if EXTRACTED_DIR.exists() else []
para_files = list(PARA_DIR.glob("*.html")) if PARA_DIR.exists() else []
sent_files = list(SENT_DIR.glob("*.html")) if SENT_DIR.exists() else []

print(f"Extracted HTML files: {len(extracted)}")
print(f"Classified paragraph files: {len(para_files)}")
print(f"Classified sentence files: {len(sent_files)}")
print(f"\nProgress: {len(para_files)}/{len(extracted)} files classified")

if len(para_files) < len(extracted):
    missing = set(f.stem for f in extracted) - set(f.stem.replace("_paragraphs_classified", "") for f in para_files)
    if missing:
        print(f"\nMissing classifications ({len(missing)} files):")
        for m in sorted(missing)[:10]:
            print(f"  - {m}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
else:
    print("\n[OK] All files classified!")

# Show most recently modified files
if para_files:
    print("\nMost recently modified classified files:")
    recent = sorted(para_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    from datetime import datetime
    for f in recent:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"  {f.name} - {mtime.strftime('%H:%M:%S')}")
