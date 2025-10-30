#!/usr/bin/env python
"""Direct cross-validation execution using the working end-to-end approach."""

import json
import time
from pathlib import Path
from datetime import datetime, UTC
import subprocess
import os

# Load environment
from dotenv import load_dotenv
load_dotenv(override=True)

def run_single_document(doc_path, output_dir):
    """Run a single document through the workflow."""
    print(f"\n[CV] Processing: {doc_path.name}")
    start_time = time.time()
    
    # Run using the WORKING main.py approach
    cmd = [
        "python", "main.py",
        str(doc_path),
        "--verbose"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd="."
        )
        
        duration = time.time() - start_time
        
        # Check for success
        success = "test generation completed" in result.stdout.lower() or \
                  "oq-suite" in result.stdout.lower()
        
        return {
            "document": doc_path.name,
            "success": success,
            "duration": duration,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "document": doc_path.name,
            "success": False,
            "duration": 600,
            "error": "Timeout after 10 minutes"
        }
    except Exception as e:
        return {
            "document": doc_path.name,
            "success": False,
            "duration": time.time() - start_time,
            "error": str(e)
        }

def main():
    """Run cross-validation on all 17 documents."""
    
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/cv_direct_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("DIRECT CROSS-VALIDATION EXECUTION")
    print("=" * 80)
    print(f"Output: {output_dir}")
    print(f"Timeout: 600 seconds per document")
    
    # Load fold assignments
    fold_file = Path("../datasets/cross_validation/fold_assignments.json")
    with open(fold_file, 'r') as f:
        folds = json.load(f)
    
    all_documents = folds['document_inventory']
    print(f"Documents to process: {len(all_documents)}")
    
    # Process each document
    results = []
    total_start = time.time()
    
    for i, doc_id in enumerate(all_documents, 1):
        print(f"\n[{i}/{len(all_documents)}] Processing {doc_id}")
        
        # Find document file
        doc_path = None
        for category in ['category_3', 'category_4', 'category_5', 'ambiguous']:
            test_path = Path(f"../datasets/urs_corpus/{category}/{doc_id}.md")
            if test_path.exists():
                doc_path = test_path
                break
        
        if not doc_path:
            print(f"  [X] Document not found: {doc_id}")
            results.append({
                "document": doc_id,
                "success": False,
                "error": "File not found"
            })
            continue
        
        # Process document
        result = run_single_document(doc_path, output_dir)
        results.append(result)
        
        if result['success']:
            print(f"  [SUCCESS] Completed in {result['duration']:.1f}s")
        else:
            print(f"  [FAILED] {result.get('error', 'Unknown error')}")
        
        # Save intermediate results
        with open(output_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
    
    # Final summary
    total_duration = time.time() - total_start
    successful = sum(1 for r in results if r['success'])
    
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Total Documents: {len(all_documents)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(all_documents) - successful}")
    print(f"Success Rate: {successful/len(all_documents)*100:.1f}%")
    print(f"Total Time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)
    
    # Save final report
    report = {
        "timestamp": timestamp,
        "total_documents": len(all_documents),
        "successful": successful,
        "failed": len(all_documents) - successful,
        "success_rate": successful/len(all_documents),
        "total_duration_seconds": total_duration,
        "results": results
    }
    
    with open(output_dir / "final_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    return successful > 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)