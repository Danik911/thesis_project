#!/usr/bin/env python
"""Test compliance with VALIDATION_MODE set"""
import os
import subprocess

# Set the environment variable
os.environ['VALIDATION_MODE'] = 'true'

# Run the compliance test
print("Testing with VALIDATION_MODE=true")
print("=" * 60)

result = subprocess.run(['python', 'test_single_urs_compliance.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)