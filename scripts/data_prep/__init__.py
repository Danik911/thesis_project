"""Data preparation pipeline for L10-L16 pharmaceutical test generation tasks.

Transforms raw PaddleOCR PP-Structure output into clean, structured artifacts:
- OCR error correction (character-level only)
- Spatial reordering using bbox coordinates
- Section hierarchy detection
- Table cleaning and extraction
- Per-document assembled artifacts

Uses ONLY Python stdlib. NO FALLBACK LOGIC.
"""
