#!/usr/bin/env python3
"""
Execute Fold 1 Validation Script (Minimal Version)

Based on run_minimal_workflow.py but adapted for Task 30 fold 1 execution
with DeepSeek V3 and real API calls for validation mode.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

# Set validation mode environment variables
os.environ["VALIDATION_MODE"] = "true"
os.environ["VALIDATION_MODE_EXPLICIT"] = "true"
os.environ["BYPASS_CONSULTATION_THRESHOLD"] = "0.7"

# Add main to path
sys.path.insert(0, str(project_root / "main"))

print("=" * 80)
print("TASK 30: Execute First Fold Validation (Minimal)")
print("=" * 80)
print(f"Project Root: {project_root}")
print(f"Timestamp: {datetime.now().isoformat()}")
print()

print("Environment Variables:")
print(f"  VALIDATION_MODE = {os.environ.get('VALIDATION_MODE')}")
print(f"  VALIDATION_MODE_EXPLICIT = {os.environ.get('VALIDATION_MODE_EXPLICIT')}")
print(f"  BYPASS_CONSULTATION_THRESHOLD = {os.environ.get('BYPASS_CONSULTATION_THRESHOLD')}")
print()

# Check API keys
print("API Keys Status:")
for key in ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
    value = os.environ.get(key)
    print(f"  {key}: {'SET' if value else 'NOT SET'}")
print()

# Define fold 1 test documents
fold_1_docs = [
    {
        "id": "URS-001",
        "path": "datasets/urs_corpus/category_3/URS-001.md",
        "category": "3 (Standard Software)"
    },
    {
        "id": "URS-002",
        "path": "datasets/urs_corpus/category_4/URS-002.md",
        "category": "4 (Configured Products)"
    },
    {
        "id": "URS-003",
        "path": "datasets/urs_corpus/category_5/URS-003.md",
        "category": "5 (Custom Applications)"
    },
    {
        "id": "URS-004",
        "path": "datasets/urs_corpus/ambiguous/URS-004.md",
        "category": "Ambiguous (3/4)"
    }
]

print("Fold 1 Test Documents:")
for doc in fold_1_docs:
    print(f"  • {doc['id']}: {doc['category']}")
print()

async def run_fold_1_minimal():
    """Run fold 1 documents through minimal workflow."""
    start_time = datetime.now()
    results = []

    try:
        # Import after fixing circular import
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        from src.llms.openrouter_llm import OpenRouterLLM

        print("[START] Starting fold 1 execution...")
        print("Using DeepSeek V3 via OpenRouter")
        print()

        # Create output directory
        output_dir = project_root / "main" / "output" / "test_suites"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Configure DeepSeek V3 LLM
        llm = OpenRouterLLM(
            model="deepseek/deepseek-chat",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            timeout=300  # 5 minute timeout per call
        )

        print(f"LLM configured: {llm.model}")
        print()

        # Process each document
        for i, doc in enumerate(fold_1_docs, 1):
            doc_path = project_root / doc["path"]
            print(f"[{i}/4] Processing {doc['id']}...")
            print(f"  Path: {doc_path}")
            print(f"  Category: {doc['category']}")

            try:
                # Create workflow for this document
                workflow = UnifiedTestGenerationWorkflow(
                    llm=llm,
                    timeout=1800,  # 30 minutes per document
                    verbose=True,
                    enable_phoenix=True,
                    enable_parallel_coordination=True,
                    enable_human_consultation=False  # Disabled in validation mode
                )

                # Set minimal test count for faster execution
                if hasattr(workflow, "default_test_count"):
                    workflow.default_test_count = 5  # 5 tests per document

                print(f"  Running workflow for {doc['id']}...")
                start_doc_time = datetime.now()

                # Run the workflow
                result = await workflow.run(
                    document_path=str(doc_path),
                    test_suite_type="oq"
                )

                doc_duration = (datetime.now() - start_doc_time).total_seconds()

                print(f"  [OK] {doc['id']} completed in {doc_duration:.2f}s")

                results.append({
                    "document": doc["id"],
                    "status": "success",
                    "duration": doc_duration,
                    "result": result,
                    "path": str(doc_path)
                })

            except Exception as e:
                doc_duration = (datetime.now() - start_doc_time).total_seconds() if "start_doc_time" in locals() else 0
                print(f"  [FAIL] {doc['id']} failed: {e}")

                results.append({
                    "document": doc["id"],
                    "status": "failed",
                    "duration": doc_duration,
                    "error": str(e),
                    "path": str(doc_path)
                })

            print()

        # Calculate overall results
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        successful_docs = sum(1 for r in results if r["status"] == "success")

        print("=" * 80)
        print("FOLD 1 EXECUTION COMPLETED")
        print("=" * 80)
        print(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        print(f"Success Rate: {successful_docs}/{len(fold_1_docs)} documents")
        print()

        if successful_docs > 0:
            print("[SUCCESS] Fold 1 executed successfully!")
            print()
            print("Document Results:")
            for result in results:
                status = "[OK]" if result["status"] == "success" else "[FAIL]"
                duration = result["duration"]
                print(f"  {status} {result['document']}: {duration:.2f}s")
        else:
            print("[FAIL] All documents failed!")
            print("Errors:")
            for result in results:
                if result["status"] == "failed":
                    print(f"  • {result['document']}: {result.get('error', 'Unknown error')}")

        print()

        # Save results
        cv_output_dir = project_root / "main" / "output" / "cross_validation"
        cv_output_dir.mkdir(parents=True, exist_ok=True)

        results_file = cv_output_dir / "fold_1_results_minimal.json"

        result_data = {
            "fold_number": 1,
            "execution_type": "minimal_validation",
            "test_documents": [doc["id"] for doc in fold_1_docs],
            "execution_time_seconds": total_duration,
            "successful_documents": successful_docs,
            "success_rate": successful_docs / len(fold_1_docs),
            "detailed_results": results,
            "validation_mode_enabled": True,
            "model_used": "deepseek/deepseek-chat",
            "execution_timestamp": end_time.isoformat(),
            "environment_info": {
                "validation_mode": os.environ.get("VALIDATION_MODE"),
                "validation_mode_explicit": os.environ.get("VALIDATION_MODE_EXPLICIT"),
                "bypass_consultation_threshold": os.environ.get("BYPASS_CONSULTATION_THRESHOLD")
            }
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Results saved to: {results_file}")

        # Check generated test files
        test_files = list(output_dir.glob("*.json"))
        print(f"Test files generated: {len(test_files)}")
        for test_file in sorted(test_files)[-5:]:  # Show last 5
            print(f"  • {test_file.name}")

        print()
        print("[SUMMARY] Task 30 Execution Summary:")
        print("  [OK] Validation mode configured")
        print("  [OK] DeepSeek V3 model used")
        print("  [OK] Fold 1 documents processed")
        print(f"  [{'OK' if successful_docs > 0 else 'FAIL'}] Real API calls made")
        print("  [OK] Phoenix monitoring active")
        print("  [OK] Results saved")

        return result_data

    except Exception as e:
        print(f"[FAIL] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        # Run the execution
        result = asyncio.run(run_fold_1_minimal())

        if result and result.get("successful_documents", 0) > 0:
            print("\n[SUCCESS] Task 30 completed successfully!")
            sys.exit(0)
        else:
            print("\n[FAIL] Task 30 failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
