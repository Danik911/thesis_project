#!/usr/bin/env python3
"""Quick check for pdfplumber installation status."""

try:
    import pdfplumber
    print(f"✅ pdfplumber IS installed - version {pdfplumber.__version__}")
    print("   Cross-validation should work after dependency fix")
except ImportError as e:
    print(f"❌ pdfplumber NOT installed: {e}")
    print("   Need to install with: uv add pdfplumber")
    print("   Or: pip install pdfplumber")
