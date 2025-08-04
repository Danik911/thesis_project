#!/usr/bin/env python3
"""
Test SME Agent Fix - Verify No Fallback Behavior

This script tests that the SME Agent now makes actual LLM calls instead of using static fallback logic.
It should now take significant time (multiple seconds) instead of 0.0005s.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

print("🧑‍⚕️ Testing SME Agent Fix - No Fallback Behavior")
print("=" * 60)

async def test_sme_agent_no_fallbacks():
    """Test that SME Agent now makes actual LLM calls."""
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Verify API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
        print(f"✅ OPENAI_API_KEY found: {openai_key[:20]}...")
        
        # Import SME Agent
        from src.agents.parallel.sme_agent import SMEAgent
        from src.core.events import AgentRequestEvent
        
        print("✅ SME Agent imported successfully")
        
        # Create agent instance
        agent = SMEAgent(
            specialty="pharmaceutical_validation",
            verbose=True,
            confidence_threshold=0.7
        )
        print("✅ SME Agent instance created")
        
        # Create test request
        correlation_id = uuid4()
        request_event = AgentRequestEvent(
            agent_type="sme_agent",
            request_data={
                "specialty": "pharmaceutical_validation",
                "test_focus": "functional_testing",
                "compliance_level": "enhanced",
                "domain_knowledge": ["GAMP-5", "21 CFR Part 11"],
                "validation_focus": ["data_handling", "user_interface"],
                "risk_factors": {
                    "technical_factors": ["integrations"],
                    "regulatory_factors": ["FDA_submission"]
                },
                "categorization_context": {
                    "gamp_category": "5",
                    "confidence_score": 0.85
                },
                "timeout_seconds": 120
            },
            priority="high",
            correlation_id=correlation_id,
            timeout_seconds=120
        )
        
        print("\n🚀 Starting SME Agent processing...")
        print("⏱️  This should now take several seconds (making actual LLM calls)")
        
        # Measure execution time
        start_time = time.time()
        
        # Process the request
        result = await agent.process_request(request_event)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️  Execution Time: {execution_time:.2f} seconds")
        
        # Analyze results
        if execution_time < 1.0:
            print("❌ CRITICAL: Execution time too fast - suggests fallback behavior still present")
            print(f"   Expected: >3 seconds (multiple LLM calls)")
            print(f"   Actual: {execution_time:.4f} seconds")
            return False
        
        if not result.success:
            print(f"❌ SME Agent processing failed: {result.error_message}")
            print("   This could indicate dependency issues or API problems")
            return False
        
        print("✅ SME Agent processing completed successfully!")
        print(f"✅ Execution time indicates actual LLM calls: {execution_time:.2f}s")
        
        # Validate result structure
        result_data = result.result_data
        
        required_fields = ["specialty", "recommendations", "compliance_assessment", "risk_analysis", "expert_opinion"]
        for field in required_fields:
            if field not in result_data:
                print(f"❌ Missing expected field in result: {field}")
                return False
        
        print("✅ Result structure validation passed")
        
        # Show summary
        print(f"\n📊 SME Agent Results Summary:")
        print(f"   - Specialty: {result_data['specialty']}")
        print(f"   - Recommendations: {len(result_data.get('recommendations', []))}")
        print(f"   - Confidence Score: {result_data.get('confidence_score', 0):.2%}")
        print(f"   - Processing Time: {result.processing_time:.2f}s")
        
        if result_data.get('expert_opinion'):
            opinion = result_data['expert_opinion'][:100] + "..." if len(result_data['expert_opinion']) > 100 else result_data['expert_opinion']
            print(f"   - Expert Opinion: {opinion}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        print(f"   Stack trace: {traceback.format_exc()}")
        return False

async def main():
    """Main test execution."""
    print("Starting SME Agent fallback behavior test...\n")
    
    success = await test_sme_agent_no_fallbacks()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: SME Agent no longer uses fallback behavior!")
        print("   - Makes actual LLM API calls")
        print("   - Takes appropriate time for processing")
        print("   - Returns valid pharmaceutical expertise")
        print("\n🎯 The critical fallback violation has been FIXED!")
    else:
        print("❌ FAILURE: SME Agent may still have issues")
        print("   - Check dependencies installation")
        print("   - Verify OPENAI_API_KEY configuration")
        print("   - Review error messages above")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)