#!/usr/bin/env python3
"""
Test configuration initialization to debug validation mode issue.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables from .env file FIRST
from dotenv import load_dotenv

# Check that we're loading from the right place
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
print(f"Loading .env from: {env_file}")

if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ .env loaded successfully")
else:
    print(f"✗ .env file not found at {env_file}")
    sys.exit(1)

# Check raw environment variable
raw_validation_mode = os.getenv("VALIDATION_MODE", "NOT_SET")
print(f"Raw VALIDATION_MODE: '{raw_validation_mode}'")

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

print("\n=== Testing ValidationModeConfig initialization ===")

# Import and create config
from src.shared.config import ValidationModeConfig

# This should trigger our debug logging
print("Creating ValidationModeConfig instance...")
validation_config = ValidationModeConfig()

print(f"\nResult:")
print(f"  validation_config.validation_mode = {validation_config.validation_mode}")
print(f"  Expected: False (since VALIDATION_MODE=false)")

if validation_config.validation_mode:
    print("\n❌ PROBLEM: validation_mode is True but should be False!")
    print("This explains why the warning appears and consultation doesn't trigger.")
else:
    print("\n✅ SUCCESS: validation_mode is correctly False")

print("\n=== Test complete ===")