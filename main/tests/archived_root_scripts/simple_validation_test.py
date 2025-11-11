#!/usr/bin/env python3
"""
Simple test to check validation mode configuration parsing.
"""

import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

print("=== SIMPLE VALIDATION MODE TEST ===")

# Check current working directory and .env location
print(f"Current working directory: {os.getcwd()}")
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
print(f"Looking for .env at: {env_file}")
print(f".env exists: {env_file.exists()}")

# Load environment variables and check immediately
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded .env from: {env_file}")
else:
    print("ERROR: .env file not found!")

# Check environment variable directly
raw_env_value = os.getenv("VALIDATION_MODE", "NOT_SET")
print(f"Raw VALIDATION_MODE env var: '{raw_env_value}'")

# Test the exact logic from ValidationModeConfig
test_result = os.getenv("VALIDATION_MODE", "false").lower() == "true"
print(f"ValidationModeConfig logic result: {test_result}")

# Show the comparison step by step
env_value = os.getenv("VALIDATION_MODE", "false")
lower_value = env_value.lower()
equals_true = lower_value == "true"
print("Step by step:")
print(f"  os.getenv('VALIDATION_MODE', 'false') = '{env_value}'")
print(f"  .lower() = '{lower_value}'")
print(f"  == 'true' = {equals_true}")

# Check if there are other .env files that might be loaded
possible_env_files = [
    Path.cwd() / ".env",
    Path(__file__).parent / ".env",
    project_root / ".env"
]

print("\nChecking for multiple .env files:")
for env_path in possible_env_files:
    if env_path.exists():
        print(f"  Found: {env_path}")
        # Check content
        with open(env_path) as f:
            lines = f.readlines()
        validation_lines = [line.strip() for line in lines if "VALIDATION_MODE" in line and not line.strip().startswith("#")]
        print(f"    VALIDATION_MODE lines: {validation_lines}")

print("\n=== TEST COMPLETE ===")
