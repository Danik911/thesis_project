#!/usr/bin/env python3
"""
Demo runner with proper environment loading
"""
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Now import and run main
from main import main

if __name__ == "__main__":
    sys.argv = [
        "main.py",
        r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\urs_corpus\category_3\URS-001.md",
        "--verbose"
    ]
    main()
