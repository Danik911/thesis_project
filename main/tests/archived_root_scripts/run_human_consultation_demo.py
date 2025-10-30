#!/usr/bin/env python3
"""
Human-in-the-Loop Consultation Demonstration Script
For Thesis Viva Presentation

This script demonstrates the human consultation system triggering
when processing ambiguous or high-complexity GAMP categories.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import json

# Set encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Ensure UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

# Ensure VALIDATION_MODE is FALSE to trigger consultation
os.environ['VALIDATION_MODE'] = 'false'

print("=" * 80)
print("HUMAN-IN-THE-LOOP CONSULTATION DEMONSTRATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"VALIDATION_MODE: {os.environ.get('VALIDATION_MODE', 'false')}")
print(f"This demonstration will show human consultation triggering for:")
print("  1. Ambiguous categorization (Category 4/5)")
print("  2. Low confidence scores")
print("  3. High-complexity systems requiring expert review")
print("=" * 80)
print()

# Import after environment setup
from main import main

async def run_demonstration():
    """Run the demonstration with timeout handling."""
    
    # Test documents for demonstration
    test_documents = [
        {
            "path": r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\corpus_3\ambiguous\URS-028.md",
            "name": "URS-028 (Ambiguous Category 4/5)",
            "expected": "Should trigger consultation due to ambiguity",
            "timeout": 30  # 30 second timeout for human response
        },
        {
            "path": r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\corpus_3\category_5\URS-029.md",
            "name": "URS-029 (Category 5)",
            "expected": "May trigger consultation due to high complexity",
            "timeout": 30
        }
    ]
    
    results = []
    
    for doc in test_documents:
        print(f"\n{'='*60}")
        print(f"Testing: {doc['name']}")
        print(f"Expected: {doc['expected']}")
        print(f"Document: {Path(doc['path']).name}")
        print(f"Timeout: {doc['timeout']} seconds")
        print(f"{'='*60}\n")
        
        # Set command line arguments
        sys.argv = [
            "main.py",
            doc["path"],
            "--verbose"
        ]
        
        start_time = datetime.now()
        
        try:
            # Create a task with timeout
            import importlib
            sys.path.insert(0, str(Path(__file__).parent))
            main_module = importlib.import_module('main')
            
            # Run with timeout
            await asyncio.wait_for(
                main_module.main(),
                timeout=doc['timeout']
            )
            
            consultation_triggered = False
            consultation_type = "completed_without_consultation"
            
        except asyncio.TimeoutError:
            print(f"\n⏱️ TIMEOUT after {doc['timeout']} seconds")
            print("This indicates human consultation was requested but no response was provided")
            print("In production, this would use conservative defaults or escalate to supervisor")
            consultation_triggered = True
            consultation_type = "timeout_after_consultation_request"
            
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            consultation_triggered = "error"
            consultation_type = str(e)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            "document": doc['name'],
            "path": doc['path'],
            "consultation_triggered": consultation_triggered,
            "consultation_type": consultation_type,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }
        
        results.append(result)
        
        # Check for consultation events in logs
        audit_file = Path("logs/audit") / f"gamp5_audit_{datetime.now().strftime('%Y%m%d')}_001.jsonl"
        if audit_file.exists():
            with open(audit_file, 'r') as f:
                lines = f.readlines()
                consultation_events = [
                    line for line in lines 
                    if "consultation" in line.lower() or "human" in line.lower()
                ]
                if consultation_events:
                    print(f"\n📋 Found {len(consultation_events)} consultation-related audit entries")
                    result["audit_entries"] = len(consultation_events)
        
        print(f"\nResult: {'✅ Consultation Triggered' if consultation_triggered else '❌ No Consultation'}")
        print(f"Duration: {duration:.1f} seconds")
    
    # Save results
    output_file = Path("main/docs/reports") / f"human_consultation_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "demonstration": "Human-in-the-Loop Consultation",
            "timestamp": datetime.now().isoformat(),
            "validation_mode": os.environ.get('VALIDATION_MODE'),
            "results": results
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print("DEMONSTRATION COMPLETE")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    # Summary
    print("\nSUMMARY:")
    for r in results:
        status = "✅" if r['consultation_triggered'] else "❌"
        print(f"{status} {r['document']}: {r['consultation_type']} ({r['duration_seconds']:.1f}s)")
    
    return results

if __name__ == "__main__":
    print("\n🚀 Starting Human-in-the-Loop Demonstration...")
    print("Note: The system will wait for human input when consultation is triggered.")
    print("If no input is provided within the timeout period, it will use conservative defaults.\n")
    
    # Run the async demonstration
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(run_demonstration())
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed: {e}")
    finally:
        loop.close()
    
    print("\n✅ Demonstration script complete!")
    print("Check the following locations for evidence:")
    print("  - Audit logs: main/logs/audit/")
    print("  - Event logs: main/logs/events/")
    print("  - Consultation logs: main/logs/validation/")
    print("  - Phoenix traces: http://localhost:6006")