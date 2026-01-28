import requests
import xml.etree.ElementTree as ET
import os
import time

# --- CONFIGURATION ---
BASE_URL = "https://caselaw.nationalarchives.gov.uk"
ATOM_ENDPOINT = f"{BASE_URL}/atom.xml"
OUTPUT_DIR = "./data/raw_xml"
USER_AGENT = "SafeLaw-WPI/1.0 (Research Project; mailto:kjayamoorthy@wpi.edu)"

# Rate Limit: 0.5s delay = ~120 reqs/min. 
# 5000 files will take ~40 minutes. Run this in background.
RATE_LIMIT_DELAY = 0.5 

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_url(url, params=None, retry_count=0):
    print(f"Fetching: {url} {params if params else ''}")
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            print("⚠️ Rate limit hit. Waiting 60s...")
            time.sleep(60)
            return fetch_url(url, params, retry_count)
        elif response.status_code == 500 and retry_count < 3:
            print(f"⚠️ Server error 500. Retrying in 30s... (attempt {retry_count + 1}/3)")
            time.sleep(30)
            return fetch_url(url, params, retry_count + 1)
        else:
            print(f"Error {response.status_code}: {response.text[:200] if response.text else 'No content'}")
            return None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def process_entry(entry):
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    title_elem = entry.find('atom:title', ns)
    if title_elem is None: return
    title = title_elem.text

    xml_link = entry.find("atom:link[@type='application/akn+xml']", ns)
    if xml_link is None:
        xml_link = entry.find("atom:link[@type='application/xml']", ns)

    if xml_link is not None:
        download_url = xml_link.attrib['href']
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
        file_name = f"{safe_title}.xml"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        
        if os.path.exists(file_path): return

        print(f"  ⬇️ Downloading: {title}")
        xml_content = fetch_url(download_url)
        if xml_content:
            with open(file_path, "wb") as f:
                f.write(xml_content)
            time.sleep(RATE_LIMIT_DELAY)

def ingest_court_data(court_code, max_cases):
    print(f"\n--- Ingesting {max_cases} cases from: {court_code.upper()} ---")
    next_url = ATOM_ENDPOINT
    params = {"court": court_code} 
    cases_downloaded = 0
    
    while next_url and cases_downloaded < max_cases:
        content = fetch_url(next_url, params=params if next_url == ATOM_ENDPOINT else None)
        if not content: break
        try:
            root = ET.fromstring(content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                if cases_downloaded >= max_cases: break
                process_entry(entry)
                cases_downloaded += 1
                
            next_link = root.find("atom:link[@rel='next']", ns)
            next_url = next_link.attrib['href'] if next_link is not None else None
            time.sleep(RATE_LIMIT_DELAY)
        except ET.ParseError:
            break

if __name__ == "__main__":
    # Gather large pool to find rare opinion types
    # UKSC: [2024] UKSC 1 → Code: uksc
    # UKUT Chambers:
    #   - ukut/aac: Administrative Appeals Chamber (Social security, child support, etc.)
    #   - ukut/lc: Lands Chamber (Property disputes, valuation)
    #   - ukut/tcc: Tax and Chancery Chamber (Financial regulations)
    #   - ukut/iac: Immigration and Asylum Chamber (Immigration law)
    
    ingest_court_data("uksc", max_cases=2000)
    
    # Ingest from all four UKUT chambers (500 cases each = 2000 total)
    ukut_chambers = [
        ("ukut/aac", "Administrative Appeals Chamber"),
        ("ukut/lc", "Lands Chamber"),
        ("ukut/tcc", "Tax and Chancery Chamber"),
        ("ukut/iac", "Immigration and Asylum Chamber")
    ]
    
    for chamber_code, chamber_name in ukut_chambers:
        print(f"\n--- Ingesting from {chamber_name} ({chamber_code}) ---")
        ingest_court_data(chamber_code, max_cases=500)