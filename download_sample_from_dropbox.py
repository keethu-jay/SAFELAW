import dropbox
import random
import os
from pathlib import Path

# === CONFIG ===
ACCESS_TOKEN = "sl.u.AGEXOjPaK-mb9iUoNCWN7lv8j8VSvD2wfCkPUVNO7doSBCqSUssi1nqyMZmwiWd0VB9O5BktkGbbLkqYR5f09JGmIGtF5ilREnyjrKsY40U6BAVZ9SZWP8HYAda_AGpdT4-7A0AiqNRW5sLp__wNcniCaETt0KpzwKAUmKORZKpIeYmLMuaZT4-gP93ps4KRxLQ8uBodRVhjTtyS2e7UZv-6U1h-W3hPtpm7EXJSmuMR0oVjnWQLV0CE8GUJ8z3Gs5o_pe7HUGsvgF-Sgq_PjynSChlGJED4fUutWDNyJfvDFkZx0KjPqQQ9Rz4CVKTSAkwBQLBUAXfyLyHrDXjQ6kYE3EpPdLY4Utnwl1bHnMg2IQKE-scBZLD68gtDM98bJY43cfgWGv3rDDXXYyF0DkUwMh26uklOpzJ8t5Ubcit07Y4u16mJeU9PwsBY7-CuCuBgeDa6Xxp4DxpefiAinKga2RQJhM_GfDhzGMglH_sgMxj1-0GAXvMbXsGANLbn3WYn3O78hH14CrAhE5b1RjSZh__s14pNtvkhNH449Efy-au6rKHyenq_obTTrFeP27KChFrvb6qV56IBOWHZ0PPPeDz0-Vj2g47Q7kfJIXld8dtsmQOJtsVcIOY7Mj_B1UmGzFQZiq3XK41wB_SeIfwxrzJkqL2cpF-GO6LYQsXWUl7vQynBi-uO8exiZruETWoUjAwbB2_PzZ57_9WPAzxmaWdr2bRipUY598Xz46IyvnqaHWmoBocAOmkTdemTu2OjMA6kwQM8LT-3Akz64hd79zf2U-iHD5htWi5QE3Ouwvkm9UkGVwW2dYSE5K9xhozukNdvZfpyg-3HLsoJbrhUtTj0J5PXvLBQda6rxlfa_TH4Qsesu7Mk2ndb9PvXG-qHkPmuLyckSz6hJ-AgznV2cAuhPCTsGM8jFXc7zuVr1bmOunJJ3is5Wa0nfbQyRXb4hJcrRBSS5F3uHQYLl8_KMEJQREbaC0t2u96_Uzp-Mv4JICRDqfAlF9BgMgKY27d22XPfxO-AgTEcSql9UpJSyStJFzkh0vtTQ0IhYQ6fU010Mv4dhTRu1K1sPprvZNqfUBWW6dsJQZ7LggKRX5Q1pmassPhJHdfkEeVkacHYGRX5DYc397I-Z0YiU1z3wfuzUFvG6uvVj1_X5vdPFvbVUoZTGiXgPVCtgBtzJoBZhNqNxNjcMRwK1saUOvGo0c6RFmjzWqC8SlEoNvUEkIsUQ9jeEZUTAtcqbSRhTJWyyWBIHxKkcuhERvjnl2a-0Clyw9fun0-zvZppWVbfXn2r"
FOLDERS = ["/2012_complete"]
OUT_DIR = Path("docs")
SAMPLE_SIZE = 20

# ===============

def list_html_files(dbx, folder):
    entries = []
    res = dbx.files_list_folder(folder, recursive=True)
    entries.extend(res.entries)
    while res.has_more:
        res = dbx.files_list_folder_continue(res.cursor)
        entries.extend(res.entries)
    htmls = [e for e in entries if e.name.lower().endswith((".html", ".htm"))]
    return htmls

def main():
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
