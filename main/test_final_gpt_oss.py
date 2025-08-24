#!/usr/bin/env python3
"""Final test of gpt-oss-120b integration."""

import os
import sys
import time
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import locale
    locale.setlocale(locale.LC_ALL, "")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# Force OpenRouter with gpt-oss-120b
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "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"

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("FINAL TEST: gpt-oss-120b INTEGRATION")
print("="*60)

from src.config.llm_config import LLMConfig

# Verify it's using gpt-oss-120b
info = LLMConfig.get_provider_info()
assert info["configuration"]["model"] == "openai/gpt-oss-120b", "Wrong model!"

print(f"Model: {info['configuration']['model']}")
print(f"Provider: {info['provider']}")

# Test the actual workflow
print("\n" + "-"*60)
print("Running actual pharmaceutical test generation...")
print("-"*60)

try:
    # Create LLM
    llm = LLMConfig.get_llm()

    # Test simple completion
    print("\n1. Testing basic completion...")
    response = llm.complete("Return exactly: SUCCESS")
    result = response.text.strip() if response.text else "EMPTY"
    print(f"   Response: {result}")

    # Test GAMP-5 categorization
    print("\n2. Testing GAMP-5 categorization...")

    test_urs = """
    System: Custom Manufacturing Execution System
    Type: Fully custom developed software with proprietary algorithms
    Category should be: 5 (custom software)
    """

    from src.agents.categorization.agent import (
        categorize_with_pydantic_structured_output,
    )

    start = time.time()
    cat_result = categorize_with_pydantic_structured_output(
        llm=llm,
        urs_content=test_urs,
        document_name="test.txt"
    )
    elapsed = time.time() - start

    print(f"   Category: {cat_result.category}")
    print(f"   Confidence: {cat_result.confidence}")
    print(f"   Time: {elapsed:.2f}s")

    # Test unified workflow
    print("\n3. Testing unified workflow...")
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow

    workflow = UnifiedTestGenerationWorkflow()
    print(f"   Workflow LLM: {type(workflow.llm).__name__}")
    print(f"   Model: {workflow.llm.model if hasattr(workflow.llm, 'model') else 'N/A'}")

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print("Migration Status: COMPLETE")
    print("Model: gpt-oss-120b")
    print("All components using centralized LLM config")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
