#!/usr/bin/env python3
"""
DEPRECATED: Use testing_scripts/run_sentence_comparison_v1.py through v4.py instead.

This script delegates to the version-specific scripts.
Output goes to testing_scripts/output/ with standardized names.
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
TESTING_SCRIPTS = BACKEND_DIR / "testing_scripts"


def main():
    parser = argparse.ArgumentParser(description="Run sentence comparison TSV scripts (delegates to testing_scripts)")
    parser.add_argument("--version", type=int, choices=[1, 2, 3, 4], default=None, help="Run only this version (default: all)")
    args = parser.parse_args()

    versions = [args.version] if args.version else [1, 2, 3, 4]
    for v in versions:
        script = TESTING_SCRIPTS / f"run_sentence_comparison_v{v}.py"
        if not script.exists():
            print(f"Script not found: {script}")
            sys.exit(1)
        print(f"\n>>> Running version {v}...")
        rc = subprocess.call([sys.executable, str(script)])
        if rc != 0:
            sys.exit(rc)
    print("\nDone. TSV files in testing_scripts/output/")


if __name__ == "__main__":
    main()
