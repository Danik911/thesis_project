#!/usr/bin/env python3
"""
Complete End-to-End OSS Pharmaceutical Workflow Test
Using DeepSeek V3 (671B MoE) via OpenRouter with basic categorization approach
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Load environment
from dotenv import load_dotenv

load_dotenv()
os.environ["LLM_PROVIDER"] = "openrouter"

# Import necessary components
from src.agents.categorization.agent import (
    categorize_with_structured_output,
    create_gamp_categorization_agent,
)
from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.parallel.context_provider import create_context_provider_agent
from src.agents.parallel.research_agent import create_research_agent
from src.agents.parallel.sme_agent import create_sme_agent
from src.config.llm_config import LLMConfig
from src.core.events import AgentRequestEvent


async def run_oss_workflow():
    """Run the complete pharmaceutical test generation workflow with OSS models using basic approach."""
    print("=== Complete End-to-End OSS Pharmaceutical Workflow Test ===")
    print("Using DeepSeek V3 (671B MoE) via OpenRouter")
    print("Target: Generate 25+ OQ tests for Category 5 GAMP system")
    print("Using basic categorization approach (not structured output)")
    print("")

    start_time = time.time()

    # 1. Load test document
    print("1. Loading test document...")
    test_doc = Path("tests/test_data/gamp5_test_data/testing_data.md")
    content = test_doc.read_text(encoding="utf-8")
    print(f"   Document loaded: {len(content)} characters")

    # 2. GAMP-5 Categorization using basic approach
    print("\\n2. GAMP-5 Categorization with DeepSeek V3 (basic approach)...")
    try:
        # Create categorization agent
        categorization_agent = create_gamp_categorization_agent(
            llm=None,  # Will use LLMConfig.get_llm()
            enable_error_handling=True,
            confidence_threshold=0.40,
            verbose=True,
            use_structured_output=False  # Use basic approach
        )

        # Run categorization
        classification = categorize_with_structured_output(
            categorization_agent,
            content,
            test_doc.name
        )

        print(f'   Category: {classification["category"]}')
        print(f'   Confidence: {classification["confidence"]:.1%}')
        print(f'   Reasoning: {classification["reasoning"][:100]}...')
        print("   Status: SUCCESS")

        # Convert to proper format
        from src.core.events import GAMPCategory
        gamp_category = GAMPCategory(int(classification["category"]))
        confidence = float(classification["confidence"])

    except Exception as e:
        print(f"   Status: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return None

    # 3. Parallel Agent Execution
    print("\\n3. Parallel Agent Execution...")
    agent_results = {}

    # 3a. Context Provider Agent
    print("   3a. Context Provider Agent...")
    try:
        context_agent = create_context_provider_agent(verbose=False, enable_phoenix=False)
        context_request = AgentRequestEvent(
            request_id=str(uuid4()),
            agent_type="context_provider",
            request_data={
                "gamp_category": str(gamp_category.value),
                "test_strategy": {
                    "test_types": ["operational_qualification"],
                    "validation_approach": "risk_based"
                }
            }
        )
        context_result = await context_agent.process_request(context_request)
        print(f'      Status: {"SUCCESS" if context_result.success else "FAILED"}')
        if context_result.success:
            agent_results["context_provider"] = context_result.result_data
        else:
            print(f"      Error: {context_result.error_message}")
    except Exception as e:
        print(f"      Status: FAILED - {e}")

    # 3b. Research Agent (for Category 5)
    print("   3b. Research Agent...")
    try:
        research_agent = create_research_agent(verbose=False, enable_phoenix=False)
        research_request = AgentRequestEvent(
            request_id=str(uuid4()),
            agent_type="research_agent",
            request_data={
                "research_focus": ["gamp_validation", "data_integrity"],
                "regulatory_scope": ["FDA", "EMA"],
                "depth_level": "comprehensive"
            }
        )
        research_result = await research_agent.process_request(research_request)
        print(f'      Status: {"SUCCESS" if research_result.success else "FAILED"}')
        if research_result.success:
            agent_results["research_findings"] = research_result.result_data
        else:
            print(f"      Error: {research_result.error_message}")
    except Exception as e:
        print(f"      Status: FAILED - {e}")

    # 3c. SME Agent
    print("   3c. SME Agent...")
    try:
        sme_agent = create_sme_agent(specialty="pharmaceutical_validation", verbose=False, enable_phoenix=False)
        sme_request = AgentRequestEvent(
            request_id=str(uuid4()),
            agent_type="sme_agent",
            request_data={
                "specialty": "pharmaceutical_validation",
                "test_focus": "operational_qualification",
                "categorization_context": {
                    "gamp_category": str(gamp_category.value),
                    "confidence_score": confidence
                }
            }
        )
        sme_result = await sme_agent.process_request(sme_request)
        print(f'      Status: {"SUCCESS" if sme_result.success else "FAILED"}')
        if sme_result.success:
            agent_results["sme_insights"] = sme_result.result_data
        else:
            print(f"      Error: {sme_result.error_message}")
    except Exception as e:
        print(f"      Status: FAILED - {e}")

    # 4. OQ Test Generation
    print("\\n4. OQ Test Generation with DeepSeek V3...")
    try:
        oq_generator = OQTestGenerator(llm=LLMConfig.get_llm(), verbose=True)

        test_suite = oq_generator.generate_oq_test_suite(
            gamp_category=gamp_category,
            urs_content=content,
            document_name=test_doc.name,
            context_data=agent_results
        )

        print(f"   Test Suite ID: {test_suite.suite_id}")
        print(f"   Tests Generated: {len(test_suite.test_cases)}")
        print("   Target Range: 23-33 tests (pharmaceutical standard)")
        print(f"   Compliance: {test_suite.pharmaceutical_compliance}")
        print("   Status: SUCCESS")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/test_suites/oss_deepseek_v3_basic_workflow_{timestamp}.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        execution_time = time.time() - start_time

        # Create comprehensive output
        output_data = {
            "workflow_metadata": {
                "suite_id": test_suite.suite_id,
                "execution_timestamp": datetime.now().isoformat(),
                "execution_time_seconds": execution_time,
                "llm_provider": "openrouter",
                "llm_model": "deepseek/deepseek-chat",
                "model_description": "DeepSeek V3 (671B MoE parameters)",
                "workflow_type": "complete_oss_pharmaceutical_basic"
            },
            "categorization_result": {
                "gamp_category": gamp_category.value,
                "confidence": confidence,
                "reasoning": classification.get("reasoning", ""),
                "approach": "basic_structured_output"
            },
            "agent_execution_summary": {
                "context_provider": "context_provider" in agent_results,
                "research_agent": "research_findings" in agent_results,
                "sme_agent": "sme_insights" in agent_results,
                "total_successful_agents": len(agent_results)
            },
            "test_generation_result": {
                "total_tests": len(test_suite.test_cases),
                "pharmaceutical_compliance": test_suite.pharmaceutical_compliance,
                "generation_timestamp": test_suite.generation_timestamp.isoformat() if test_suite.generation_timestamp else None
            },
            "test_cases": [
                {
                    "test_id": tc.test_id,
                    "title": tc.title,
                    "description": tc.description,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority,
                    "estimated_duration_minutes": tc.estimated_duration_minutes,
                    "test_category": tc.test_category,
                    "urs_requirements": tc.urs_requirements,
                    "test_steps": [
                        {
                            "step_number": step.step_number,
                            "action": step.action,
                            "expected_result": step.expected_result
                        } for step in tc.test_steps
                    ]
                } for tc in test_suite.test_cases
            ]
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"   Output saved: {output_file}")

        # Generate summary report
        print("\\n=== WORKFLOW COMPLETION SUMMARY ===")
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"GAMP Category: {gamp_category.value} (Category 5 - Custom System)")
        print(f"Categorization Confidence: {confidence:.1%}")
        print(f"Tests generated: {len(test_suite.test_cases)}")
        print(f"Successful agents: {len(agent_results)}/3")
        print(f'Context Provider: {"✓" if "context_provider" in agent_results else "✗"}')
        print(f'Research Agent: {"✓" if "research_findings" in agent_results else "✗"}')
        print(f'SME Agent: {"✓" if "sme_insights" in agent_results else "✗"}')
        print("OSS Model: DeepSeek V3 (deepseek/deepseek-chat)")
        print("Provider: OpenRouter")
        print(f"Pharmaceutical Compliance: {test_suite.pharmaceutical_compliance}")
        print("Status: COMPLETE")

        return {
            "success": True,
            "execution_time": execution_time,
            "test_count": len(test_suite.test_cases),
            "output_file": output_file,
            "gamp_category": gamp_category.value,
            "confidence": confidence,
            "agent_results": len(agent_results)
        }

    except Exception as e:
        print(f"   Status: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the complete workflow
    result = asyncio.run(run_oss_workflow())

    # Exit with appropriate code
    sys.exit(0 if result and result.get("success") else 1)
