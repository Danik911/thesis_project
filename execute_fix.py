#!/usr/bin/env python3
"""Simple execution of the dataset generation process."""

import os
import sys

# Change to project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_dir)

# Execute the dataset generation
try:
    print("Executing dataset generation...")
    exec(open("generate_dataset.py").read())
    print("Dataset generation script executed successfully!")
except Exception as e:
    print(f"Error executing dataset generation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
