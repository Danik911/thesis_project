#!/usr/bin/env python3
"""
Simple test runner to execute the event flow validation test
"""

import sys
import asyncio
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Import the test module
from test_event_flow_validation import main

if __name__ == "__main__":
    result = main()
    print(f"\nTest result exit code: {result}")
    sys.exit(result)