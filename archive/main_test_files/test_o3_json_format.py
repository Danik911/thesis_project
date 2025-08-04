"""Test o3 model JSON generation with corrected schema."""
import asyncio
import json
from datetime import UTC, datetime
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from src.core.events import GAMPCategory

load_dotenv()

async def test_o3_json_generation():
    """Test o3 model generates correct JSON format."""
    
    llm = OpenAI(
        model="o3-2025-04-16",
        temperature=0.1,
        timeout=300,  # 5 minutes
        max_completion_tokens=2000
    )
    
    # Simple prompt with exact schema
    prompt = """Generate a simple OQ test suite JSON with exactly 2 tests.

Output ONLY valid JSON, no explanations.

{
    "suite_id": "OQ-SUITE-0001",
    "gamp_category": 5,
    "document_name": "test.md",
    "test_cases": [
        {
            "test_id": "OQ-001",
            "test_name": "Verify batch management functionality",
            "test_category": "functional",
            "gamp_category": 5,
            "objective": "Verify the batch management system operates correctly",
            "prerequisites": ["System installed", "User logged in"],
            "test_steps": [
                {
                    "step_number": 1,
                    "description": "Create new batch",
                    "expected_result": "Batch created successfully"
                }
            ],
            "acceptance_criteria": ["Batch created with unique ID"],
            "regulatory_basis": ["21 CFR Part 11"],
            "risk_level": "high",
            "data_integrity_requirements": ["Audit trail maintained"],
            "urs_requirements": ["URS-001"],
            "related_tests": [],
            "estimated_duration_minutes": 30,
            "required_expertise": ["Validation Engineer"]
        }
    ],
    "test_categories": {"functional": 1},
    "requirements_coverage": {"URS-001": ["OQ-001"]},
    "risk_coverage": {"low": 0, "medium": 0, "high": 1},
    "compliance_coverage": {"21_cfr_part_11": true, "gamp5": true, "alcoa_plus": true},
    "generation_timestamp": "2024-08-03T14:30:00Z",
    "total_execution_time_minutes": 30,
    "review_required": true,
    "pharmaceutical_compliance": {
        "alcoa_plus_compliant": true,
        "gamp5_compliant": true,
        "cfr_part_11_compliant": true,
        "audit_trail_verified": true,
        "data_integrity_assured": true
    },
    "validation_status": {
        "structure_validated": true,
        "requirements_traced": true,
        "coverage_adequate": true,
        "ready_for_execution": true
    },
    "generation_metadata": {
        "llm_model": "o3-2025-04-16",
        "prompt_tokens": 0,
        "completion_tokens": 0
    }
}"""
    
    try:
        print("Testing o3 JSON generation...")
        response = await llm.acomplete(prompt)
        response_text = response.text
        
        # Extract JSON
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            print(f"ERROR: No JSON found in response:\n{response_text}")
            return False
            
        json_str = response_text[json_start:json_end]
        
        # Parse JSON
        data = json.loads(json_str)
        print("SUCCESS: JSON parsed successfully")
        print(f"Suite ID: {data.get('suite_id')}")
        print(f"Test count: {len(data.get('test_cases', []))}")
        
        # Validate key fields
        if data.get('suite_id') and data.get('test_cases'):
            print("SUCCESS: Key fields present")
            return True
        else:
            print("ERROR: Missing key fields")
            return False
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_o3_json_generation())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")