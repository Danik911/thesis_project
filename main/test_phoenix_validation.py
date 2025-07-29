#!/usr/bin/env python3
"""Validation test for Phoenix observability fix."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.shared.output_manager import safe_print


async def validate_phoenix_fix():
    """Validate that Phoenix observability is now working correctly."""
    safe_print("🧪 Phoenix Observability Fix Validation")
    safe_print("=" * 50)
    
    # Import required modules
    from src.shared import setup_event_logging, shutdown_event_logging
    from src.shared.event_logging_integration import run_workflow_with_event_logging
    from src.core.categorization_workflow import GAMPCategorizationWorkflow
    
    try:
        # Step 1: Setup event logging with Phoenix
        safe_print("\n1️⃣ Setting up event logging with Phoenix...")
        event_handler = setup_event_logging()
        safe_print("✅ Event logging initialized")
        
        # Step 2: Create and run a workflow
        safe_print("\n2️⃣ Running GAMP categorization workflow...")
        workflow = GAMPCategorizationWorkflow(
            timeout=60,
            verbose=True,
            enable_error_handling=True
        )
        
        # Run with event logging
        result, events = await run_workflow_with_event_logging(
            workflow,
            event_handler,
            urs_content="""
            User Requirements Specification for Pharmaceutical Manufacturing System
            
            This system requires computerized control of critical manufacturing processes
            including temperature monitoring, batch recording, and quality assurance.
            The system must comply with 21 CFR Part 11 and GAMP-5 guidelines.
            """,
            document_name="phoenix_validation_test.txt"
        )
        
        if result:
            summary = result.get("summary", {})
            safe_print(f"\n✅ Workflow completed successfully!")
            safe_print(f"   - Category: {summary.get('category', 'Unknown')}")
            safe_print(f"   - Confidence: {summary.get('confidence', 0):.1%}")
            safe_print(f"   - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
        
        # Step 3: Check event statistics
        safe_print("\n3️⃣ Event Processing Statistics:")
        stats = event_handler.get_statistics()
        safe_print(f"   - Events Captured: {len(events)}")
        safe_print(f"   - Events Processed: {stats['events_processed']}")
        safe_print(f"   - Processing Rate: {stats['events_per_second']:.2f} events/sec")
        
        # Step 4: Wait for trace export (reduced delay now)
        safe_print("\n4️⃣ Waiting for trace export (2 seconds)...")
        await asyncio.sleep(2)
        
    except Exception as e:
        safe_print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Step 5: Proper shutdown
        safe_print("\n5️⃣ Performing graceful shutdown...")
        try:
            shutdown_event_logging()
            safe_print("✅ Shutdown completed successfully")
        except Exception as shutdown_error:
            safe_print(f"⚠️  Shutdown warning: {shutdown_error}")
    
    # Final check
    safe_print("\n" + "="*50)
    safe_print("📊 VALIDATION COMPLETE")
    safe_print("="*50)
    safe_print("\n🔍 Please check:")
    safe_print("1. Phoenix UI at http://localhost:6006/")
    safe_print("2. Look for traces from 'GAMPCategorizationWorkflow'")
    safe_print("3. Verify no 'Exporter already shutdown' warnings above")
    safe_print("\n✅ If traces appear in Phoenix UI, the fix is working!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(validate_phoenix_fix())
    sys.exit(0 if success else 1)