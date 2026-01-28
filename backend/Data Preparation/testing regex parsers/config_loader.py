import yaml
import os

# Get the directory where this script is located (Data Preperation)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Since court_config.yaml is in the SAME folder, we just join the path directly
CONFIG_PATH = os.path.join(BASE_DIR, "court_config.yaml")

def load_court_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    with open(path, 'r') as file:
        return yaml.safe_load(file)

# Load the config once
CONFIG = load_court_config(CONFIG_PATH)