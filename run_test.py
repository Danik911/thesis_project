#!/usr/bin/env python3
"""
Execute the final OSS test from project root.
"""

import sys
import os
import subprocess

# Add the main directory to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
main_path = os.path.join(project_root, "main")
sys.path.insert(0, main_path)

# Change to main directory
os.chdir(main_path)

# Run the test
result = subprocess.run([sys.executable, "test_oss_final.py"], 
                       capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")