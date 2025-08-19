#!/usr/bin/env python
"""Sequential cross-validation execution - direct calls."""

import os
import json
import time
from pathlib import Path
from datetime import datetime, UTC

# Change to main directory
os.chdir('main')

# Results storage
results = []
timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
output_dir = Path(f"THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/cv_sequential_{timestamp}")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("SEQUENTIAL CROSS-VALIDATION EXECUTION")
print("=" * 80)

# Document paths
documents = [
    ("URS-001", "../datasets/urs_corpus/category_3/URS-001.md"),
    ("URS-002", "../datasets/urs_corpus/category_4/URS-002.md"),
    ("URS-003", "../datasets/urs_corpus/category_5/URS-003.md"),
    ("URS-004", "../datasets/urs_corpus/ambiguous/URS-004.md"),
    ("URS-005", "../datasets/urs_corpus/ambiguous/URS-005.md"),
    ("URS-006", "../datasets/urs_corpus/category_3/URS-006.md"),
    ("URS-007", "../datasets/urs_corpus/category_3/URS-007.md"),
    ("URS-008", "../datasets/urs_corpus/category_3/URS-008.md"),
    ("URS-009", "../datasets/urs_corpus/category_3/URS-009.md"),
    ("URS-010", "../datasets/urs_corpus/category_4/URS-010.md"),
    ("URS-011", "../datasets/urs_corpus/category_4/URS-011.md"),
    ("URS-012", "../datasets/urs_corpus/category_4/URS-012.md"),
    ("URS-013", "../datasets/urs_corpus/category_4/URS-013.md"),
    ("URS-014", "../datasets/urs_corpus/category_5/URS-014.md"),
    ("URS-015", "../datasets/urs_corpus/category_5/URS-015.md"),
    ("URS-016", "../datasets/urs_corpus/category_5/URS-016.md"),
    ("URS-017", "../datasets/urs_corpus/category_5/URS-017.md"),
]

print(f"Documents to process: {len(documents)}")
print(f"Output directory: {output_dir}")
print("=" * 80)

total_start = time.time()

for i, (doc_id, doc_path) in enumerate(documents, 1):
    print(f"\n[{i}/{len(documents)}] Processing {doc_id}")
    doc_start = time.time()
    
    # Import here to get fresh workflow each time
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    import asyncio
    
    try:
        # Create workflow
        workflow = UnifiedTestGenerationWorkflow(
            verbose=True,
            enable_parallel_coordination=True,
            enable_phoenix=True
        )
        
        # Run workflow
        result = asyncio.run(workflow.run(document_path=doc_path))
        
        duration = time.time() - doc_start
        
        # Check success
        success = hasattr(result, 'success') and result.success
        
        results.append({
            "document": doc_id,
            "success": success,
            "duration": duration,
            "category": getattr(result, 'gamp_category', None) if hasattr(result, 'gamp_category') else None,
            "tests_generated": getattr(result, 'tests_generated', 0) if hasattr(result, 'tests_generated') else 0
        })
        
        if success:
            print(f"  [SUCCESS] Category {results[-1]['category']}, {results[-1]['tests_generated']} tests in {duration:.1f}s")
        else:
            print(f"  [FAILED] After {duration:.1f}s")
            
    except Exception as e:
        duration = time.time() - doc_start
        results.append({
            "document": doc_id,
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
successful = sum(1 for r in results if r['success'])

print("\n" + "=" * 80)
print("SEQUENTIAL CROSS-VALIDATION COMPLETE")
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

# If we have Phoenix spans, count them
trace_files = list(Path("logs/traces").glob(f"*{timestamp[:8]}*.jsonl"))
if trace_files:
    total_spans = sum(len(open(f).readlines()) for f in trace_files)
    print(f"\nPhoenix Spans Captured: {total_spans}")
    print(f"Average Spans per Document: {total_spans // len(documents)}")