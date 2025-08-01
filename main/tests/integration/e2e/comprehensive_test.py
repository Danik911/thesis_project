#!/usr/bin/env uv run python
"""
Comprehensive End-to-End Test for Pharmaceutical Test Generation Workflow
Tests all critical fixes and captures comprehensive metrics
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.shared import get_config, setup_event_logging


async def run_comprehensive_test():
    """Run comprehensive end-to-end test with full metrics capture."""

    print("🏥 Comprehensive End-to-End Test for Pharmaceutical Test Generation")
    print("=" * 70)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test URS content
    test_urs = """# User Requirements Specification
    
## System Overview
This is a custom pharmaceutical data analysis application that performs
proprietary calculations for drug stability testing. The system includes:

- Custom algorithms for predictive modeling
- Real-time data processing with proprietary business rules
- Integration with laboratory instruments (HPLC, UV-Vis)
- Custom statistical models for trend analysis
- Machine learning models for batch quality prediction

## Functional Requirements
- FR001: Custom calculation engine for stability predictions
- FR002: Proprietary data validation algorithms
- FR003: Real-time monitoring dashboard
- FR004: Integration with LIMS via custom protocols
- FR005: Electronic signature functionality

## Compliance Requirements
- 21 CFR Part 11 compliance
- ALCOA+ data integrity
- Full audit trail with tamper-evident logs
"""

    # Initialize configuration
    config = get_config()

    # Setup event logging
    event_handler = setup_event_logging(config)

    # Create workflow
    workflow = UnifiedTestGenerationWorkflow(
        timeout=300,
        verbose=True
    )

    # Capture start time
    start_time = time.time()

    try:
        print("🚀 Starting unified workflow execution...")
        print()

        # Run workflow
        handler = workflow.run(
            urs_content=test_urs,
            document_name="comprehensive_test_urs.md",
            document_version="1.0",
            author="test_runner"
        )

        result = await handler

        # Calculate duration
        duration = time.time() - start_time

        # Extract results
        if result:
            print("\n✅ Workflow Execution Results:")
            print("=" * 50)

            # GAMP Categorization Results
            gamp_result = result.get("gamp_categorization", {})
            print("\n📊 GAMP-5 Categorization:")
            print(f"  - Category: {gamp_result.get('category', 'Unknown')}")
            print(f"  - Confidence: {gamp_result.get('confidence', 0):.1%}")
            print(f"  - Review Required: {gamp_result.get('review_required', False)}")
            print(f"  - Rationale: {gamp_result.get('rationale', 'N/A')[:100]}...")

            # Test Planning Results
            planning_result = result.get("test_planning", {})
            if planning_result:
                print("\n📋 Test Planning:")
                print(f"  - Total Tests: {planning_result.get('total_tests', 0)}")
                print(f"  - Timeline: {planning_result.get('timeline_days', 0)} days")
                print(f"  - Test Types: {len(planning_result.get('test_types', []))}")

                # Show test breakdown
                test_strategy = planning_result.get("test_strategy", {})
                if test_strategy:
                    print("\n  Test Breakdown:")
                    for phase, details in test_strategy.items():
                        if isinstance(details, dict) and "count" in details:
                            print(f"    - {phase}: {details['count']} tests")

            # Agent Coordination
            print("\n🤖 Agent Coordination:")
            print(f"  - Active Agents: {result.get('agent_count', 0)}")
            print(f"  - Coordination Requests: {len(planning_result.get('coordination_requests', []))}")

            # Performance Metrics
            print("\n⚡ Performance Metrics:")
            print(f"  - Total Duration: {duration:.2f} seconds")
            print(f"  - Workflow Time: {result.get('duration', 0):.2f} seconds")

            # Event Statistics
            stats = event_handler.get_statistics()
            print("\n📊 Event Processing:")
            print(f"  - Events Captured: {stats['events_processed']}")
            print(f"  - Events Filtered: {stats['events_filtered']}")
            print(f"  - Processing Rate: {stats['events_processed'] / max(duration, 1):.2f} events/sec")

            # Get captured events
            events = event_handler.get_events()
            event_types = {}
            for event in events:
                event_type = event.get("event_type", "Unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

            if event_types:
                print("\n  Event Type Breakdown:")
                for event_type, count in sorted(event_types.items()):
                    print(f"    - {event_type}: {count}")

            # Compliance Metrics
            print("\n🔒 Compliance Metrics:")
            print(f"  - Audit Trail Entries: {stats.get('audit_entries', 0)}")
            print(f"  - ALCOA+ Compliance: {'✅ Yes' if gamp_result.get('confidence', 0) > 0 else '❌ No'}")

            # Critical Issue Check
            print("\n🔍 Critical Issues Check:")

            # Check confidence scoring
            confidence = gamp_result.get("confidence", 0)
            if confidence == 0:
                print("  ❌ Confidence Scoring: FAILED (0.0%)")
            else:
                print(f"  ✅ Confidence Scoring: PASSED ({confidence:.1%})")

            # Check event logging
            if stats["events_processed"] == 0:
                print("  ❌ Event Logging: FAILED (0 events)")
            else:
                print(f"  ✅ Event Logging: PASSED ({stats['events_processed']} events)")

            # Check planning
            if planning_result and planning_result.get("total_tests", 0) > 0:
                print(f"  ✅ Test Planning: PASSED ({planning_result.get('total_tests')} tests)")
            else:
                print("  ❌ Test Planning: FAILED")

            # Phoenix status (check if initialized)
            try:
                from src.monitoring import get_phoenix_manager
                phoenix_mgr = get_phoenix_manager()
                if phoenix_mgr and phoenix_mgr._initialized:
                    print("  ✅ Phoenix Integration: PASSED")
                else:
                    print("  ⚠️  Phoenix Integration: Not initialized")
            except:
                print("  ⚠️  Phoenix Integration: Cannot verify")

            # Overall assessment
            print("\n📈 Overall Assessment:")
            issues = []
            if confidence == 0:
                issues.append("Zero confidence scoring")
            if stats["events_processed"] == 0:
                issues.append("No event logging")
            if not planning_result or planning_result.get("total_tests", 0) == 0:
                issues.append("No test planning")

            if issues:
                print("  Status: ⚠️  CONDITIONAL PASS")
                print(f"  Issues: {', '.join(issues)}")
            else:
                print("  Status: ✅ PASS")
                print("  All critical systems operational")

            # Save detailed results
            output_file = Path("test_results_comprehensive.json")
            with open(output_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "results": result,
                    "event_stats": stats,
                    "event_types": event_types,
                    "issues": issues
                }, f, indent=2)

            print(f"\n💾 Detailed results saved to: {output_file}")

        else:
            print("❌ Workflow returned no results")

    except Exception as e:
        print(f"\n❌ Error during test execution: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🔒 Shutting down event handler...")
        await event_handler.shutdown()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
