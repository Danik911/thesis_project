#!/usr/bin/env python3
"""
Quick test to validate OQ generator required fields fix.
Tests that all required fields are properly included in prompts.
"""

from main.src.agents.oq_generator.templates import OQPromptTemplates
from main.src.core.events import GAMPCategory

def test_required_fields_in_prompt():
    """Test that all required fields are mentioned in the prompt template."""
    
    # Test with GAMP Category 4 (typical case)
    gamp_category = GAMPCategory.CATEGORY_4
    urs_content = "Test URS content for validation"
    document_name = "TEST-URS-001"
    test_count = 7
    context_summary = "Test context"
    
    # Generate the prompt
    prompt = OQPromptTemplates.get_generation_prompt(
        gamp_category=gamp_category,
        urs_content=urs_content,
        document_name=document_name,
        test_count=test_count,
        context_summary=context_summary
    )
    
    print("=== CHECKING REQUIRED FIELDS IN PROMPT ===")
    
    # Check for all required suite-level fields
    required_suite_fields = [
        "suite_id",
        "gamp_category", 
        "document_name",
        "test_cases",
        "total_test_count",
        "estimated_execution_time"  # This was the missing field
    ]
    
    # Check for all required test-level fields
    required_test_fields = [
        "test_id",
        "test_name",
        "test_category", 
        "gamp_category",
        "objective",
        "prerequisites",
        "test_steps", 
        "acceptance_criteria",
        "estimated_duration_minutes"  # Individual test execution time
    ]
    
    all_fields_found = True
    
    print("\nSUITE-LEVEL REQUIRED FIELDS:")
    for field in required_suite_fields:
        if field in prompt:
            print(f"  ✅ {field} - FOUND")
        else:
            print(f"  ❌ {field} - MISSING")
            all_fields_found = False
    
    print("\nTEST-LEVEL REQUIRED FIELDS:")
    for field in required_test_fields:
        if field in prompt:
            print(f"  ✅ {field} - FOUND") 
        else:
            print(f"  ❌ {field} - MISSING")
            all_fields_found = False
            
    print("\n=== CRITICAL INSTRUCTIONS CHECK ===")
    critical_instructions = [
        "MANDATORY SUITE FIELDS",
        "MANDATORY TEST FIELDS", 
        "estimated_execution_time",
        "estimated_duration_minutes",
        "sum of all test execution times",
        "ALL REQUIRED FIELDS"
    ]
    
    for instruction in critical_instructions:
        if instruction in prompt:
            print(f"  ✅ '{instruction}' - FOUND")
        else:
            print(f"  ❌ '{instruction}' - MISSING")
            all_fields_found = False
    
    print("\n=== RESULT ===")
    if all_fields_found:
        print("🎉 SUCCESS: All required fields and instructions are present in prompt!")
        print("The OQ generator should now include estimated_execution_time field.")
    else:
        print("❌ FAILURE: Some required fields or instructions are missing!")
        return False
    
    print(f"\nPrompt length: {len(prompt)} characters")
    
    # Show a snippet of the output structure
    print("\n=== OUTPUT STRUCTURE SNIPPET ===")
    if "Output Structure" in prompt:
        start = prompt.find("Output Structure")
        end = prompt.find("Return complete JSON", start)
        if end == -1:
            end = start + 500
        print(prompt[start:end])
    
    return True

if __name__ == "__main__":
    success = test_required_fields_in_prompt()
    exit(0 if success else 1)