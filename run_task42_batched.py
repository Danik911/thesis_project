#!/usr/bin/env python3
"""
Task 42: Batched Cross-Validation Execution
Processes documents in small batches to avoid timeouts and improve monitoring.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Any

# Add main to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "main"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def setup_environment():
    """Verify environment setup."""
    print("Verifying environment setup...")
    
    # Check API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openrouter_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return False
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False
    
    print("[OK] API keys configured")
    
    # Check Phoenix
    import requests
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("[OK] Phoenix monitoring accessible")
        else:
            print("[WARNING] Phoenix monitoring not fully accessible")
    except:
        print("[WARNING] Phoenix monitoring not running")
    
    return True

def get_test_documents() -> List[Dict[str, str]]:
    """Get list of test documents for cross-validation."""
    docs_dir = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/main/datasets/urs_corpus")
    
    documents = []
    if docs_dir.exists():
        # Get first 5 documents for initial test
        for doc_file in list(docs_dir.glob("*.md"))[:5]:
            documents.append({
                "id": doc_file.stem,
                "path": str(doc_file),
                "name": doc_file.name
            })
    else:
        # Use test document if corpus not available
        test_doc = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/main/tests/test_data/gamp5_test_data/testing_data.md")
        if test_doc.exists():
            documents.append({
                "id": "test_doc",
                "path": str(test_doc),
                "name": test_doc.name
            })
    
    return documents

async def process_single_document(doc: Dict[str, str], timeout_seconds: int = 300) -> Dict[str, Any]:
    """Process a single document with timeout."""
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    from src.shared.config import SystemConfig
    
    print(f"\n[DOC] Processing: {doc['name']}")
    print(f"   Timeout: {timeout_seconds} seconds")
    
    start_time = time.time()
    result = {
        "document_id": doc["id"],
        "document_name": doc["name"],
        "success": False,
        "error": None,
        "processing_time": 0,
        "tests_generated": 0,
        "gamp_category": None,
        "confidence": 0.0
    }
    
    try:
        # Load document content
        with open(doc["path"], "r", encoding="utf-8") as f:
            content = f.read()
        
        # Create workflow configuration
        config = SystemConfig()
        config.enable_phoenix = True
        config.enable_event_logging = True
        
        # Run workflow with timeout
        workflow = UnifiedTestGenerationWorkflow(
            config=config,
            timeout=timeout_seconds
        )
        
        # Use asyncio timeout
        async with asyncio.timeout(timeout_seconds):
            workflow_result = await workflow.run(
                urs_content=content,
                document_name=doc["name"]
            )
        
        # Parse results
        if workflow_result and workflow_result.output:
            result["success"] = True
            result["gamp_category"] = workflow_result.output.get("gamp_category")
            result["confidence"] = workflow_result.output.get("confidence", 0.0)
            result["tests_generated"] = workflow_result.output.get("test_count", 0)
        else:
            result["error"] = "Workflow completed but no output generated"
            
    except asyncio.TimeoutError:
        result["error"] = f"Timeout after {timeout_seconds} seconds"
        print(f"   [FAIL] Timeout exceeded")
    except Exception as e:
        result["error"] = str(e)
        print(f"   [FAIL] Error: {e}")
    
    result["processing_time"] = time.time() - start_time
    
    # Print result
    if result["success"]:
        print(f"   [OK] Success: {result['tests_generated']} tests generated")
        print(f"   Category: {result['gamp_category']} (confidence: {result['confidence']:.1%})")
    else:
        print(f"   [FAIL] Failed: {result['error']}")
    print(f"   Time: {result['processing_time']:.1f} seconds")
    
    return result

async def run_batched_cross_validation(batch_size: int = 1, timeout_per_doc: int = 600):
    """Run cross-validation in batches."""
    print("=" * 60)
    print("TASK 42: BATCHED CROSS-VALIDATION EXECUTION")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        print("\n[ERROR] Environment setup failed")
        return
    
    # Get documents
    documents = get_test_documents()
    print(f"\n[INFO] Found {len(documents)} documents to process")
    print(f"[INFO] Batch size: {batch_size}")
    print(f"[INFO] Timeout per document: {timeout_per_doc} seconds")
    
    # Process in batches
    all_results = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_num}/{total_batches}")
        print(f"{'='*60}")
        
        # Process batch sequentially to avoid overload
        batch_results = []
        for doc in batch:
            result = await process_single_document(doc, timeout_per_doc)
            batch_results.append(result)
            
            # Small delay between documents
            if doc != batch[-1]:
                print("\n[WAIT] Waiting 5 seconds before next document...")
                await asyncio.sleep(5)
        
        all_results.extend(batch_results)
        
        # Print batch summary
        successful = sum(1 for r in batch_results if r["success"])
        print(f"\n[SUMMARY] Batch {batch_num} Summary:")
        print(f"   Success rate: {successful}/{len(batch_results)} ({successful/len(batch_results)*100:.0f}%)")
        
        # Delay between batches
        if i + batch_size < len(documents):
            print("\n[WAIT] Waiting 10 seconds before next batch...")
            await asyncio.sleep(10)
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    successful = sum(1 for r in all_results if r["success"])
    total_tests = sum(r["tests_generated"] for r in all_results)
    avg_time = sum(r["processing_time"] for r in all_results) / len(all_results)
    
    print(f"[OK] Success rate: {successful}/{len(all_results)} ({successful/len(all_results)*100:.0f}%)")
    print(f"[INFO] Total tests generated: {total_tests}")
    print(f"[INFO] Average processing time: {avg_time:.1f} seconds")
    
    # Save results
    results_file = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/task42_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {
                "total_documents": len(all_results),
                "successful": successful,
                "success_rate": successful / len(all_results),
                "total_tests": total_tests,
                "avg_processing_time": avg_time
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\n[SAVED] Results saved to: {results_file}")
    
    return all_results

if __name__ == "__main__":
    print("Starting Task 42 Batched Cross-Validation...")
    print("This will process documents in small batches to avoid timeouts.\n")
    
    # Run with configurable parameters
    batch_size = 1  # Process 1 document at a time (sequential for reliability)
    timeout_per_doc = 600  # 10 minutes per document (matches successful end-to-end test)
    
    try:
        results = asyncio.run(run_batched_cross_validation(batch_size, timeout_per_doc))
        
        if results:
            print("\n[SUCCESS] Cross-validation execution complete!")
        else:
            print("\n[ERROR] Cross-validation failed to produce results")
    except KeyboardInterrupt:
        print("\n[WARNING] Execution interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()