import os
import shutil
import xml.etree.ElementTree as ET
from openai import OpenAI

# Load environment variables from backend .env file manually
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

# --- CONFIGURATION ---
INPUT_DIR = "./data/raw_xml"
PARENT_DIR = "./Final Dataset"
PROCESSED_DIR = os.path.join(PARENT_DIR)
TARGET_PER_CATEGORY = 50 # We stop once we hit this number

# OpenAI Setup (Using a cheap model: gpt-4o-mini)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create folder structure
COURT_NAMES = {
    "uksc": "Supreme Court (uksc)",
    "eat": "Tribunal Court (eat)"
}
TYPES = ["majority", "concurring", "dissenting"]

# Create parent directory
os.makedirs(PARENT_DIR, exist_ok=True)

# Create court directories with proper names
for court_key, court_name in COURT_NAMES.items():
    court_path = os.path.join(PROCESSED_DIR, court_name)
    for t in TYPES:
        os.makedirs(os.path.join(court_path, t), exist_ok=True)

# Counters to track when to stop
counts = {
    "uksc": {"majority": 0, "concurring": 0, "dissenting": 0},
    "eat": {"majority": 0, "concurring": 0, "dissenting": 0}
}

def extract_decision_text(file_path):
    """
    Parses XML and gets the last ~1000 chars of the text body.
    This is where 'I agree' or 'I dissent' usually appears.
    """
    try:
        tree = ET.parse(file_path)
        # Find all paragraph text
        # Namespaces might be tricky, scanning all text is safer for 'peek'
        full_text = "".join(tree.getroot().itertext())
        
        # Determine court type from text/metadata heuristic
        court = "uksc" if "Supreme Court" in full_text else "eat"
        
        # Return the end of the text for classification
        return court, full_text[-1500:] 
    except:
        return None, None

def classify_opinion(text_snippet):
    """
    Asks LLM to label the file based on the ending text where any concurring or dissenting opinions are present, if there are none then it's majority.
    """
    prompt = f"""
    Analyze the following end-of-judgment text from a UK court case.
    Classify the file into exactly one category based on this logic:
    1. "dissenting": If ANY judge explicitly dissents or disagrees.
    2. "concurring": If NO dissent, but a judge explicitly writes a separate opinion saying "I agree" or adds their own reasoning.
    3. "majority": If it is a single judgment or simple agreement without separate concurring speeches.

    Text Snippet:
    "{text_snippet}"

    Return ONLY one word: "majority", "concurring", or "dissenting".
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()

def extract_year_from_filename(filename):
    """
    Extract the year from a neutral citation in the filename.
    e.g., "[2024] UKSC 5 Case Name.xml" → 2024
    Returns a high number if year not found, so unsorted files go to the end.
    """
    import re
    match = re.search(r'\[(\d{4})\]', filename)
    return int(match.group(1)) if match else 0

def process_all_files():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xml")]
    
    # Sort by year in descending order (most recent first)
    files.sort(key=extract_year_from_filename, reverse=True)
    
    print(f"Found {len(files)} raw files. Processing most recent first...")
    print(f"Year range: {extract_year_from_filename(files[0])} to {extract_year_from_filename(files[-1])}")

    for filename in files:
        # check if we are full
        uksc_full = all(v >= TARGET_PER_CATEGORY for v in counts["uksc"].values())
        eat_full = all(v >= TARGET_PER_CATEGORY for v in counts["eat"].values())
        if uksc_full and eat_full:
            print("✅ All categories filled!")
            break

        file_path = os.path.join(INPUT_DIR, filename)
        court_detected, text_tail = extract_decision_text(file_path)
        
        if not text_tail: continue
        
        # Skip if this court's quotas are already met
        if all(v >= TARGET_PER_CATEGORY for v in counts[court_detected].values()):
            continue

        # Classify
        label = classify_opinion(text_tail)
        
        # Validation: Ensure label is valid
        if label not in TYPES:
            print(f"⚠️ Unknown label '{label}' for {filename}")
            continue
            
        # Check quota for specific category
        if counts[court_detected][label] < TARGET_PER_CATEGORY:
            # Truncate filename if it's too long for Windows (260 char limit)
            # Keep the .xml extension and truncate the base name
            base_name = filename[:-4]  # Remove .xml
            if len(base_name) > 100:  # Truncate to 100 chars
                base_name = base_name[:100]
            safe_filename = base_name + ".xml"
            
            # Move file to correct location using court name
            court_name = COURT_NAMES[court_detected]
            dest_path = os.path.join(PROCESSED_DIR, court_name, label, safe_filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            shutil.copy(file_path, dest_path)
            
            counts[court_detected][label] += 1
            print(f"[{court_detected.upper()}] Classified {filename} as {label.upper()} ({counts[court_detected][label]}/{TARGET_PER_CATEGORY})")

if __name__ == "__main__":
    process_all_files()