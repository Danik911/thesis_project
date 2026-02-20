#!/usr/bin/env python3
"""Seed ChromaDB mda_templates collection from demo_data/*.xlsx files.

Usage:
    python scripts/populate_lims_chroma.py [demo_data_dir]

Arguments:
    demo_data_dir   Path to directory containing LabWare XLSX files.
                    Defaults to ``./demo_data``.

NO FALLBACK LOGIC: fails explicitly if files are missing or ingestion fails.
"""

import logging
import sys
from pathlib import Path

# Add project root to path so ``main.src.lims`` is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from main.src.lims.rag_loader import seed_mda_templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    demo_dir = sys.argv[1] if len(sys.argv) > 1 else "./demo_data"
    count = seed_mda_templates(demo_dir)
    print(f"Seeded {count} chunks into ChromaDB mda_templates collection")  # noqa: T201
