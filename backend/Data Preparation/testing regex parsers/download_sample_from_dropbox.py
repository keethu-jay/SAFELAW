"""
Downloads a random sample of HTML files from a Dropbox folder. Used for testing
parsers on real Bloomberg/BNA content. Set DROPBOX_ACCESS_TOKEN in .env (do not
commit tokens to git).
"""
import os
import random
from pathlib import Path

import dropbox

ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN", "")
FOLDERS = ["/2012_complete"]
OUT_DIR = Path("docs")
SAMPLE_SIZE = 20


def list_html_files(dbx, folder):
    """Lists all .html/.htm files in a Dropbox folder, recursing into subfolders."""
    entries = []
    res = dbx.files_list_folder(folder, recursive=True)
    entries.extend(res.entries)
    while res.has_more:
        res = dbx.files_list_folder_continue(res.cursor)
        entries.extend(res.entries)
    htmls = [e for e in entries if e.name.lower().endswith((".html", ".htm"))]
    return htmls

def main():
    if not ACCESS_TOKEN:
        print("Set DROPBOX_ACCESS_TOKEN in .env (or in your environment) and re-run.")
        return
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    OUT_DIR.mkdir(exist_ok=True)
    all_htmls = []

    print("Listing HTML files from folders...")
    for f in FOLDERS:
        try:
            htmls = list_html_files(dbx, f)
            print(f"  {f}: {len(htmls)} HTML files found.")
            all_htmls.extend(htmls)
        except Exception as e:
            print(f"  Failed to list {f}: {e}")

    if not all_htmls:
        print("No HTML files found.")
        return

    sample = random.sample(all_htmls, min(SAMPLE_SIZE, len(all_htmls)))
    print(f"\nDownloading {len(sample)} random files...")

    for entry in sample:
        local_path = OUT_DIR / entry.name
        try:
            md, res = dbx.files_download(entry.path_lower)
            local_path.write_bytes(res.content)
            print(f"  ✅ {entry.name}")
        except Exception as e:
            print(f"  ⚠️ Error downloading {entry.name}: {e}")

    print(f"\nDone. Files saved to: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
