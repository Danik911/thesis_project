#!/usr/bin/env python3
"""Standalone E2E test: Full LIMS pipeline with a single PDF.

Runs the two-layer pipeline directly (no FastAPI server needed).
Tests: classification -> extraction -> RAG query -> augmentation -> generation.

Usage:
    python scripts/test_e2e_pipeline.py demo_data/AND_ACS_AQ126-LAB-2349.pdf
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(".env.local", override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_pipeline(pdf_path: str) -> None:
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf.resolve()}")

    pdf_content = pdf.read_bytes()

    print(f"\n{'='*70}")
    print(f"  E2E Pipeline Test: {pdf.name} ({len(pdf_content)} bytes)")
    print(f"{'='*70}")

    # Step 1: Init Langfuse
    print("\n[1/5] Initializing Langfuse tracing...")
    from main.src.lims.langfuse_tracing import init_lims_langfuse, flush_lims_langfuse
    langfuse = init_lims_langfuse()
    print(f"  Langfuse: {'ENABLED' if langfuse else 'DISABLED (keys missing)'}")

    # Step 2: Load config
    print("\n[2/5] Loading LIMS config...")
    from main.src.lims.config import get_lims_config
    config = get_lims_config()
    print(f"  Model: {config.openrouter_model}")
    print(f"  RAG top_k: mda={config.rag_mda_top_k}, standards={config.rag_standards_top_k}")

    # Step 3: Run pipeline
    print("\n[3/5] Running TwoLayerPipeline...")
    from main.src.lims.pipeline import TwoLayerPipeline

    pipeline = TwoLayerPipeline(config=config)
    t0 = time.time()
    result = await pipeline.run(pdf_content=pdf_content, filename=pdf.name)
    elapsed = time.time() - t0
    print(f"  Pipeline completed in {elapsed:.1f}s")

    # Step 4: Show results
    print("\n[4/5] Results:")
    if "classification" in result:
        cls = result["classification"]
        print(f"  Test type: {cls.get('test_type', '?')}")
        print(f"  Confidence: {cls.get('confidence', '?')}")

    if "mda_template" in result:
        mda = result["mda_template"]
        if isinstance(mda, dict):
            print(f"  Analyses: {len(mda.get('analyses', []))}")
            print(f"  Components: {len(mda.get('components', []))}")
            print(f"  Calc Variables: {len(mda.get('calc_variables', []))}")
            print(f"  Calculations: {len(mda.get('calculations', []))}")

    if "augmentation" in result and result["augmentation"]:
        aug = result["augmentation"]
        suggestions = aug.get("suggestions", [])
        print(f"  Augmentation suggestions: {len(suggestions)}")

    # Step 5: Flush Langfuse
    if langfuse:
        print("\n[5/5] Flushing Langfuse traces...")
        flush_lims_langfuse()
        print("  Done. Check Langfuse Cloud for spans:")
        print("    - rag-mda-templates-query")
        print("    - rag-standards-query")
        print("    - pipeline-augment-rag / pipeline-augment-llm")
        print("    - mda-gen-rag-query / mda-gen-llm-call")

    # Save result for inspection
    out_path = Path("output/lims") / f"{pdf.stem}_e2e_result.json"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Full result saved to: {out_path}")
    except PermissionError:
        # WSL cross-filesystem permission issue -- try /tmp instead
        out_path = Path("/tmp") / f"{pdf.stem}_e2e_result.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Full result saved to: {out_path}")

    print(f"\n{'='*70}")
    print(f"  E2E test complete")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "demo_data/AND_ACS_AQ126-LAB-2349.pdf"
    asyncio.run(run_pipeline(pdf))
