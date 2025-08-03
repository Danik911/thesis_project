#!/usr/bin/env python3
"""Test SME Agent with real API call"""
import asyncio
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

from src.agents.parallel.sme_agent import SMEAgent, SMEAgentRequest, SMEAgentResponse
from llama_index.llms.openai import OpenAI

async def test_sme_agent():
    """Test SME agent with recommendations generation"""
    
    # Initialize LLM
    llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create SME agent
    sme_agent = SMEAgent(
        llm=llm,
        specialty="Pharmaceutical Validation",
        verbose=True
    )
    
    # Create test request
    request = SMEAgentRequest(
        specialty="Pharmaceutical Validation", 
        compliance_level="GAMP-5",
        test_focus="OQ",
        categorization_context={
            "gamp_category": "5",
            "confidence_score": 0.95
        },
        domain_knowledge=["GAMP-5", "21 CFR Part 11"],
        validation_focus=["Data Integrity", "Audit Trail"],
        correlation_id=str(uuid.uuid4())
    )
    
    print("Testing SME Agent recommendations generation...")
    print("This will test if the array parsing fix works with real LLM responses")
    
    try:
        # Call the _generate_recommendations method directly
        recommendations = await sme_agent._generate_recommendations(
            request,
            compliance_assessment={"level": "high", "applicable_standards": ["21 CFR Part 11"]},
            risk_analysis={"risk_level": "high", "key_risks": ["data integrity"]}
        )
        
        print(f"\nSUCCESS: Parsed recommendations")
        print(f"Type: {type(recommendations)}")
        print(f"Is list: {isinstance(recommendations, list)}")
        print(f"Count: {len(recommendations)}")
        
        if recommendations:
            print(f"\nFirst recommendation:")
            print(f"  Category: {recommendations[0].get('category')}")
            print(f"  Priority: {recommendations[0].get('priority')}")
            print(f"  Recommendation: {recommendations[0].get('recommendation')[:100]}...")
            
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sme_agent())