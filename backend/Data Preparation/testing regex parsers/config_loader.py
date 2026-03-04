"""
Loads court_config.yaml from this folder and exposes it as CONFIG. Used by
cenral_parser.py to get court definitions, regex patterns, and section rules.
"""
import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "court_config.yaml")


# CONFIG LOADING
def load_court_config(path):
    """Loads and returns the YAML config. Raises if the file is missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_court_config(CONFIG_PATH)