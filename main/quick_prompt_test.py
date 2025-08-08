#!/usr/bin/env python3
"""Quick test of the optimized prompts."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.agents.oq_generator.templates import OQPromptTemplates
from src.core.events import GAMPCategory

# Test Category 5 (most challenging - 25-30 tests required)
sample_urs = """
User Requirements Specification (URS) - Laboratory Information Management System (LIMS)

REQ-001: System Installation
The system must be installed on approved hardware with all required components.

REQ-002: User Authentication  
The system must provide secure user authentication with role-based access controls.

REQ-003: Data Integrity
The system must maintain complete audit trails for all data modifications.

REQ-004: Performance
The system must respond to user queries within 3 seconds under normal load.
"""

print("Testing GAMP Category 5 with 25 tests required...")
print("="*60)

# Generate optimized prompt
prompt = OQPromptTemplates.get_generation_prompt(
    gamp_category=GAMPCategory.CATEGORY_5,
    urs_content=sample_urs,
    document_name="LIMS Custom Application",
    test_count=25,
    context_summary="OSS model optimization test"
)

print(f"Prompt length: {len(prompt)} characters")
print(f"Test count '25' appears: {prompt.count('25')} times")
print("\nFirst 2000 characters of optimized prompt:")
print("-" * 50)
print(prompt[:2000])
print("\n" + "-" * 50)
print("Key sections found:")
print(f"- Has 🚨 emphasis: {'🚨' in prompt}")
print(f"- Has counting instructions: {'Count them as you generate' in prompt}")
print(f"- Has step-by-step: {'STEP-BY-STEP GENERATION INSTRUCTIONS' in prompt}")
print(f"- Has validation checklist: {'VALIDATION CHECKLIST' in prompt}")
print(f"- Has example structure: {'example_test_structure' in prompt.lower()}")

# Save full prompt
with open('optimized_category5_prompt.txt', 'w', encoding='utf-8') as f:
    f.write(prompt)
    
print(f"\nFull prompt saved to: optimized_category5_prompt.txt")
print("✅ Quick test completed successfully!")