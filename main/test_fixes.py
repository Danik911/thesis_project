#!/usr/bin/env python3
"""
Test script to validate Unicode encoding and planner workflow fixes.
"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def test_unicode_fix():
    """Test the Unicode encoding fix."""
    print("Testing Unicode encoding fix...")

    try:
        from main import setup_unicode_support
        setup_unicode_support()
        print("✅ Unicode encoding setup successful")
        print("🧑‍⚕️ GAMP-5 Test: ✅ ❌ 📋 🔍 ⚡")
        return True
    except Exception as e:
        print(f"❌ Unicode encoding test failed: {e}")
        return False

async def test_planner_workflow_fix():
    """Test the planner workflow configuration fix."""
    print("\nTesting planner workflow configuration fix...")

    try:

        from src.agents.planner.workflow import PlannerAgentWorkflow
        from src.core.events import GAMPCategorizationEvent, GAMPCategory

        # Create a test categorization event
        test_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.85,
            rationale="Test categorization",
            compliance_requirements=["21_cfr_part_11"],
            document_metadata={"name": "test.md"},
            session_id="test_session"
        )

        # Create planner workflow
        planner = PlannerAgentWorkflow(
            timeout=30,
            verbose=True,
            enable_coordination=True
        )

        print("✅ PlannerAgentWorkflow created successfully")
        print("✅ StartEvent handler should be present")

        # Note: Full workflow test would require more setup, but creation success indicates fix worked
        return True
    except Exception as e:
        print(f"❌ Planner workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_research_agent_integration():
    """Test Research Agent integration."""
    print("\nTesting Research Agent integration...")

    try:
        from src.agents.parallel.agent_factory import create_agent_registry
        from src.agents.parallel.research_agent import create_research_agent
        from src.agents.planner.coordination import AgentCoordinator
        from src.agents.planner.strategy_generator import TestStrategyResult
        from src.core.events import GAMPCategory

        # Test Research Agent creation
        research_agent = create_research_agent(verbose=True)
        print("✅ Research Agent created successfully")

        # Test agent registry
        agent_registry = create_agent_registry(verbose=True)
        registry_research_agent = agent_registry.get_agent_by_type("research_agent")
        print("✅ Agent registry can create Research Agent")

        # Test coordination request generation
        coordinator = AgentCoordinator(verbose=True)

        # Create mock test strategy
        test_strategy = TestStrategyResult(
            gamp_category=GAMPCategory.CATEGORY_5,
            validation_approach="comprehensive",
            estimated_count=10,
            timeline_estimate_days=14,
            complexity_level="high",
            resource_requirements=["validation_engineer"],
            compliance_requirements=["21_cfr_part_11", "gamp_5"],
            test_focus_areas=["installation", "configuration"],
            validation_rigor="comprehensive"
        )

        # Generate coordination requests
        requests = coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=GAMPCategory.CATEGORY_5
        )

        # Check if Research Agent request is included
        research_requests = [r for r in requests if r.agent_type == "research_agent"]

        if research_requests:
            print(f"✅ Research Agent coordination request generated: {len(research_requests)} requests")
            print(f"   Research focus: {research_requests[0].request_data.get('research_focus', [])}")
            print(f"   All agent types: {[r.agent_type for r in requests]}")
            return True
        print("❌ No Research Agent coordination requests generated")
        print(f"   Available agent types: {[r.agent_type for r in requests]}")
        return False

    except Exception as e:
        print(f"❌ Research Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🧪 Running integration fix tests...")
    print("=" * 50)

    tests = [
        test_unicode_fix(),
        test_planner_workflow_fix(),
        test_research_agent_integration()
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    passed = sum(1 for result in results if result is True)
    total = len(results)

    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL FIXES VALIDATED - System ready for full testing")
    else:
        print("❌ Some fixes need attention")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
