#!/usr/bin/env python3
"""
Check the current state by running the same command that was failing.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main"))

async def test_original_command():
    """Run the original failing command."""
    print("=== TESTING ORIGINAL COMMAND ===")
    
    try:
        from src.core.unified_workflow import run_unified_test_generation_workflow
        
        # Use the same document path the user was using
        doc_path = project_root / "datasets" / "corpus_3" / "special_cases" / "URS-030.md"
        
        print(f"📁 Document path: {doc_path}")
        print(f"📄 Document exists: {doc_path.exists()}")
        
        if not doc_path.exists():
            print("❌ Document not found!")
            return
        
        print("🚀 Running the original failing command...")
        
        # Run the same command that was failing
        result = await run_unified_test_generation_workflow(
            document_path=str(doc_path),
            timeout=300,
            verbose=True,
            validation_mode=True  # Enable validation mode to bypass consultation
        )
        
        print("✅ COMMAND COMPLETED!")
        print(f"Result status: {result.get('status', 'Unknown')}")
        
        if 'categorization' in result:
            cat = result['categorization']
            if cat:
                print(f"Category: {cat.get('category', 'Unknown')}")
                print(f"Confidence: {cat.get('confidence', 0):.2%}")
        
        print("🎉 SUCCESS - Command completed without early termination!")
        
    except Exception as e:
        print(f"❌ COMMAND STILL FAILS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_original_command())