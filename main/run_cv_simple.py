#!/usr/bin/env python
"""Simple cross-validation runner using subprocess to avoid event loop issues."""

import subprocess
import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime, UTC

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"

# Document paths to test
documents = [
    ("URS-001", "../datasets/urs_corpus/category_3/URS-001.md"),
    ("URS-002", "../datasets/urs_corpus/category_4/URS-002.md"),
    ("URS-003", "../datasets/urs_corpus/category_5/URS-003.md"),
    ("URS-004", "../datasets/urs_corpus/ambiguous/URS-004.md"),
    ("URS-005", "../datasets/urs_corpus/ambiguous/URS-005.md"),
]

# Results storage
results = []
timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
output_dir = Path(f"output/cv_results_{timestamp}")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CROSS-VALIDATION EXECUTION (SUBPROCESS)")
print("=" * 80)
print(f"Documents to process: {len(documents)}")
print(f"Output directory: {output_dir}")
print("=" * 80)

total_start = time.time()

for i, (doc_id, doc_path) in enumerate(documents, 1):
    print(f"\n[{i}/{len(documents)}] Processing {doc_id}")
    doc_start = time.time()
    
    try:
        # Run with subprocess to avoid event loop issues
        result = subprocess.run(
            ["uv", "run", "python", "main.py", doc_path, "--verbose"],
            capture_output=True,
            text=True,
            timeout=600,
            env={**subprocess.os.environ, "VALIDATION_MODE": "true"}
        )
        
        duration = time.time() - doc_start
        success = result.returncode == 0
        
        # Parse output for details
        output = result.stdout if result.stdout else ""
        category = None
        tests_generated = 0
        
        if "GAMP Category:" in output:
            for line in output.split('\n'):
                if "GAMP Category:" in line:
                    try:
                        category = int(line.split("GAMP Category:")[1].strip().split()[0])
                    except:
                        pass
                if "Generated" in line and "test" in line:
                    try:
                        tests_generated = int([w for w in line.split() if w.isdigit()][0])
                    except:
                        pass
        
        results.append({
            "document": doc_id,
            "path": doc_path,
            "success": success,
            "duration": duration,
            "category": category,
            "tests_generated": tests_generated,
            "returncode": result.returncode
        })
        
        if success:
            print(f"  [SUCCESS] Category {category}, {tests_generated} tests in {duration:.1f}s")
        else:
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            print(f"  [FAILED] {error_msg}")
            
    except subprocess.TimeoutExpired:
        duration = time.time() - doc_start
        results.append({
            "document": doc_id,
            "path": doc_path,
            "success": False,
            "duration": duration,
            "error": "Timeout after 600s"
        })
        print(f"  [TIMEOUT] after {duration:.1f}s")
        
    except Exception as e:
        duration = time.time() - doc_start
        results.append({
            "document": doc_id,
            "path": doc_path,
            "success": False,
            "duration": duration,
            "error": str(e)
        })
        print(f"  [ERROR] {str(e)[:100]}")
    
    # Save intermediate results
    with open(output_dir / "results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Brief pause between documents
    time.sleep(2)

# Summary
total_duration = time.time() - total_start
successful = sum(1 for r in results if r.get('success', False))

print("\n" + "=" * 80)
print("CROSS-VALIDATION COMPLETE")
print("=" * 80)
print(f"Total Documents: {len(documents)}")
print(f"Successful: {successful}")
print(f"Failed: {len(documents) - successful}")
print(f"Success Rate: {successful/len(documents)*100:.1f}%")
print(f"Total Time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
print(f"Results saved to: {output_dir}")
print("=" * 80)

# Final report
report = {
    "timestamp": timestamp,
    "total_documents": len(documents),
    "successful": successful,
    "failed": len(documents) - successful,
    "success_rate": successful/len(documents),
    "total_duration_seconds": total_duration,
    "average_duration": total_duration / len(documents),
    "results": results
}

with open(output_dir / "final_report.json", 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"\n[REPORT] Final report saved to: {output_dir / 'final_report.json'}")