#!/usr/bin/env python3
"""
Direct test to reproduce and fix the validation mode issue.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file FIRST
from dotenv import load_dotenv

# Setup exactly like main.py
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
load_dotenv(env_file)

# Add the main directory to the path (same as main.py)
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging with reduced verbosity (same as main.py)
import logging

logging.basicConfig(
    level=logging.WARNING,  # Same as main.py default
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("=== DIRECT FIX TEST ===")
print(f"Environment VALIDATION_MODE: '{os.getenv('VALIDATION_MODE', 'NOT_SET')}'")

# Import config exactly as main.py does
from src.shared import get_config

config = get_config()

print(f"Config validation_mode: {config.validation_mode.validation_mode}")

# If config shows validation_mode=True when env var is "false", that's the bug
if config.validation_mode.validation_mode and os.getenv("VALIDATION_MODE", "false").lower() != "true":
    print("❌ CONFIRMED BUG: Config validation_mode=True but VALIDATION_MODE env var != 'true'")

    # Apply direct fix - override the config to match environment
    config.validation_mode.validation_mode = False
    print("✅ APPLIED FIX: Set config.validation_mode.validation_mode = False")

    # This should suppress the warning in ValidationModeConfig.__post_init__
    print(f"Config validation_mode after fix: {config.validation_mode.validation_mode}")
else:
    print("✅ Config correctly reflects environment variable")

# Now test if human consultation would trigger
print("\n=== TESTING HUMAN CONSULTATION REQUIREMENTS ===")

# Test with the actual URS-001.md document
document_path = "C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\datasets\\urs_corpus\\category_3\\URS-001.md"

if Path(document_path).exists():
    print(f"Testing with: {document_path}")
    print("This is a Category 3 document - should trigger human consultation if validation_mode=False")

    # Just show what would happen without running full workflow
    print(f"Current validation_mode setting: {config.validation_mode.validation_mode}")

    if not config.validation_mode.validation_mode:
        print("✅ Human consultation should trigger (validation_mode=False)")
    else:
        print("❌ Human consultation will be bypassed (validation_mode=True)")

else:
    print(f"Document not found: {document_path}")

print("\n=== TEST COMPLETE ===")
