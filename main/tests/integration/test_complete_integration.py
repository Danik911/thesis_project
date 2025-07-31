#!/usr/bin/env python3
"""
Complete integration test for Task 15 event logging with real workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent / "main"))

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.shared import run_workflow_with_event_logging, setup_event_logging
from src.shared.config import get_config


async def test_complete_integration():
    """Test complete integration of event logging with workflow."""
    print("🧪 Complete Integration Test: Event Logging + Workflow")
    print("=" * 60)

    # Setup directories
    log_dir = Path("logs/integration_test")
    audit_dir = log_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directories: {log_dir}")

    # Setup event logging with custom config
    config = get_config()
    config.logging.log_directory = str(log_dir)
    config.gamp5_compliance.audit_log_directory = str(audit_dir)

    event_handler = setup_event_logging(config)
    print("✅ Event logging system initialized")

    # Create workflow
    workflow = GAMPCategorizationWorkflow(
        timeout=60,
        verbose=False,
        enable_error_handling=True,
        confidence_threshold=0.60
    )
    print("✅ Workflow created")

    # Test document
    test_content = """
    # Pharmaceutical System URS
    
    This system requires GAMP-5 categorization for:
    - Laboratory Information Management System (LIMS)
    - Custom software components
    - 21 CFR Part 11 compliance
    """

    try:
        # Run workflow with event logging
        print("\n🚀 Running workflow with event logging...")
        result, events = await run_workflow_with_event_logging(
            workflow,
            event_handler,
            urs_content=test_content,
            document_name="pharma_system.md"
        )

        print("\n✅ Workflow completed!")
        print(f"📊 Events captured: {len(events)}")

        # Show results
        if result:
            summary = result.get("summary", {})
            print("\n📋 Results:")
            print(f"  - Category: {summary.get('category', 'Unknown')}")
            print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
            print(f"  - Review Required: {summary.get('review_required', False)}")
            print(f"  - Is Fallback: {summary.get('is_fallback', False)}")

        # Show captured events
        print("\n📡 Captured Events:")
        for i, event in enumerate(events, 1):
            print(f"  {i}. {event['event_type']} - ID: {event['event_id'][:8]}...")

        # Check log files
        print("\n📁 Log Files Created:")
        log_files = list(log_dir.rglob("*.log")) + list(log_dir.rglob("*.jsonl"))
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"  - {log_file.relative_to(log_dir)} ({size} bytes)")

        # Check event handler statistics
        stats = event_handler.get_statistics()
        print("\n📈 Event Processing Statistics:")
        print(f"  - Events Processed: {stats['events_processed']}")
        print(f"  - Events Filtered: {stats['events_filtered']}")
        print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")

        # Check compliance statistics
        compliance_stats = event_handler.compliance_logger.get_audit_statistics()
        print("\n🔒 GAMP-5 Compliance Statistics:")
        print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
        print(f"  - Audit Files: {compliance_stats['audit_file_count']}")
        print(f"  - Storage Size: {compliance_stats['total_size_mb']:.2f} MB")

        # Final assessment
        success = len(events) > 0 and stats["events_processed"] > 0

        if success:
            print("\n✅ SUCCESS: Event logging integration is working!")
            print("   - Real workflow events captured")
            print("   - Events processed by handler")
            print("   - GAMP-5 compliance features active")
        else:
            print("\n❌ FAILURE: Event logging integration issues detected")

        return success

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_complete_integration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
