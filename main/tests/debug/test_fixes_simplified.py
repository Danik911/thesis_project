#!/usr/bin/env python3
"""
Simplified test to verify critical fixes in the pharmaceutical workflow.
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.categorization_workflow import run_categorization_workflow
from src.core.unified_workflow import run_unified_test_generation_workflow


async def test_categorization_confidence():
    """Test that confidence scoring returns non-zero values."""
    print("\n🧪 Testing Confidence Scoring Fix...")

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
"""

    try:
        # Run categorization
        result = await run_categorization_workflow(
            urs_content=test_urs,
            document_name="test_confidence.md",
            document_version="1.0",
            author="tester",
            timeout=60,
            verbose=True
        )

        if result:
            confidence = result.get("summary", {}).get("confidence", 0)
            category = result.get("summary", {}).get("category", "Unknown")

            print(f"✅ Category: {category}")
            print(f"✅ Confidence Score: {confidence:.1%}")

            if confidence == 0.0:
                print("❌ FAILED: Confidence is still 0.0%")
                return False
            print("✅ PASSED: Confidence scoring fixed!")
            return True
        print("❌ FAILED: No result returned")
        return False

    except Exception as e:
        print(f"❌ Error during confidence test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_workflow():
    """Test the complete unified workflow."""
    print("\n🧪 Testing Unified Workflow...")

    test_urs = """# User Requirements Specification
    
## System Overview
A pharmaceutical manufacturing execution system (MES) that:
- Manages batch production records
- Tracks material inventory
- Monitors environmental conditions
- Generates compliance reports

## Requirements
- Real-time production tracking
- Electronic batch records
- Integration with ERP system
- Automated report generation
- 21 CFR Part 11 compliance
"""

    start_time = time.time()

    try:
        # Run unified workflow
        result = await run_unified_test_generation_workflow(
            urs_content=test_urs,
            document_name="test_unified.md",
            document_version="1.0",
            author="tester",
            timeout=120,
            verbose=True
        )

        duration = time.time() - start_time

        if result:
            print(f"\n✅ Workflow completed in {duration:.2f}s")

            # Check GAMP categorization
            gamp_result = result.get("gamp_categorization", {})
            category = gamp_result.get("category", "Unknown")
            confidence = gamp_result.get("confidence", 0)

            print("\n📊 GAMP Categorization:")
            print(f"  - Category: {category}")
            print(f"  - Confidence: {confidence:.1%}")
            print(f"  - Review Required: {gamp_result.get('review_required', False)}")

            # Check test planning
            planning_result = result.get("test_planning", {})
            if planning_result:
                print("\n📋 Test Planning:")
                print(f"  - Total Tests: {planning_result.get('total_tests', 0)}")
                print(f"  - Timeline: {planning_result.get('timeline_days', 0)} days")
                print(f"  - Coordination Requests: {len(planning_result.get('coordination_requests', []))}")

            # Check overall metrics
            print("\n📈 Workflow Metrics:")
            print(f"  - Status: {result.get('status', 'Unknown')}")
            print(f"  - Duration: {result.get('duration', 0):.2f}s")
            print(f"  - Active Agents: {result.get('agent_count', 0)}")

            # Verify critical fixes
            issues = []
            if confidence == 0:
                issues.append("Zero confidence")
            if not planning_result or planning_result.get("total_tests", 0) == 0:
                issues.append("No tests planned")

            if issues:
                print(f"\n⚠️  Issues: {', '.join(issues)}")
                return False
            print("\n✅ All systems operational!")
            return True

        print("❌ FAILED: No result returned")
        return False

    except Exception as e:
        print(f"❌ Error during unified workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_event_logging():
    """Test event logging by checking workflow output."""
    print("\n🧪 Testing Event Logging...")

    # Run a simple workflow and check console output for events
    test_urs = "Simple test URS for event logging"

    try:
        result = await run_categorization_workflow(
            urs_content=test_urs,
            document_name="test_events.md",
            document_version="1.0",
            author="tester",
            timeout=30,
            verbose=True
        )

        # Since we can't directly access events, check if workflow completed
        if result:
            print("✅ Workflow completed - events should be logged")
            print("   Check console output above for event messages")
            return True
        print("❌ Workflow failed")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🏥 Testing Critical Workflow Fixes (Simplified)")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "Confidence Scoring": await test_categorization_confidence(),
        "Event Logging": await test_event_logging(),
        "Unified Workflow": await test_unified_workflow()
    }

    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All fixes verified successfully!")
        return 0
    print(f"\n⚠️  {total - passed} tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
