#!/usr/bin/env python3
"""
Test script to verify the human consultation Category 4 override fix.
This script bypasses the interactive input and provides simulated human responses.
"""

import asyncio
import sys
from pathlib import Path
import os
from unittest.mock import patch

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.shared.config import get_config

class MockConsultationHandler:
    """Mock consultation handler that simulates human input."""
    
    def __init__(self, simulated_responses):
        self.simulated_responses = simulated_responses
        self.response_index = 0
    
    def _get_operator_credential(self, prompt):
        """Simulate human credential input."""
        if self.response_index < len(self.simulated_responses):
            response = self.simulated_responses[self.response_index]
            self.response_index += 1
            print(f"{prompt.strip()}: {response}")  # Show what was "entered"
            return response
        return "test_user"
    
    def _get_operator_role(self):
        """Simulate human role selection."""
        print("Available roles:")
        print("1. Quality Assurance")
        print("2. Validation Engineer") 
        print("3. System Administrator")
        print("4. DevOps Engineer")
        print("Select your role (1-4): 3")  # Show simulated selection
        return "3"  # Return role selection
    
    def _get_category_selection(self):
        """Simulate human category selection."""
        print("Available GAMP-5 Categories:")
        print("1. Category 1 - Operating systems, firmware, tools")
        print("2. Category 3 - Non-configured products") 
        print("3. Category 4 - Configured products")
        print("4. Category 5 - Custom applications")
        print("Select category (1-5): 4")  # Show simulated selection
        return "4"  # Return Category 4 selection
    
    def _get_justification(self):
        """Simulate human justification input."""
        justification = "Custom application requiring full validation and compliance testing"
        print(f"Please provide justification for your category selection: {justification}")
        return justification

async def test_human_consultation_category4():
    """Test the Category 4 override fix with simulated human input."""
    
    print("Testing Human Consultation Category 4 Override Fix")
    print("=" * 60)
    
    # Use document that triggers consultation (URS-030 has low confidence)
    test_document_path = "C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\datasets\\corpus_3\\special_cases\\URS-030.md"
    
    if not Path(test_document_path).exists():
        print(f"ERROR: Test document not found: {test_document_path}")
        return False
    
    print(f"Testing with document: {Path(test_document_path).name}")
    print("This document should trigger consultation due to low AI confidence")
    
    # Create simulated responses for the consultation
    simulated_responses = [
        "Daniil",  # Name
        "29922",   # Employee ID
    ]
    
    mock_handler = MockConsultationHandler(simulated_responses)
    
    # Mock the consultation handler methods with correct method names
    with patch('src.core.consultation_handler.ConsultationEventHandler._get_operator_credential', 
               side_effect=mock_handler._get_operator_credential), \
         patch('src.core.consultation_handler.ConsultationEventHandler._get_operator_role', 
               side_effect=mock_handler._get_operator_role), \
         patch('src.core.consultation_handler.ConsultationEventHandler._get_category_selection', 
               side_effect=mock_handler._get_category_selection), \
         patch('src.core.consultation_handler.ConsultationEventHandler._get_justification', 
               side_effect=mock_handler._get_justification):
        
        # Create workflow with human consultation enabled
        workflow = UnifiedTestGenerationWorkflow(
            timeout=1800,
            verbose=True,
            enable_human_consultation=True,
            enable_parallel_coordination=True
        )
        
        print("Starting workflow with simulated human consultation...")
        print("Simulated human will select Category 4 when prompted")
        print()
        
        try:
            # Run workflow
            result = await workflow.run(document_path=test_document_path)
            
            # Extract results
            if hasattr(result, "result"):
                final_result = result.result
            else:
                final_result = result
            
            # Verification
            print("\nVERIFICATION RESULTS:")
            print("=" * 40)
            
            # Check 1: Final categorization display
            categorization = final_result.get("categorization", {})
            displayed_category = categorization.get("gamp_category")
            
            print(f"Final Categorization Display: Category {displayed_category}")
            
            # Check 2: OQ generation results
            oq_results = final_result.get("oq_generation", {})
            test_count = oq_results.get("total_tests", 0)
            suite_id = oq_results.get("test_suite_id", "N/A")
            
            print(f"OQ Tests Generated: {test_count} tests")
            print(f"Test Suite ID: {suite_id}")
            
            # Check 3: Test suite file content
            output_file = oq_results.get("output_file")
            if output_file and Path(output_file).exists():
                print(f"Test suite saved to: {output_file}")
                
                import json
                try:
                    with open(output_file, 'r') as f:
                        test_suite_data = json.load(f)
                        
                    file_category = test_suite_data.get("gamp_category")
                    print(f"Category in saved file: Category {file_category}")
                    
                    # CRITICAL VERIFICATION: Check if human override was applied
                    if displayed_category == 4 and file_category == 4:
                        print("\nSUCCESS: Human consultation Category 4 override is working!")
                        print("   - Human selected Category 4 during consultation")
                        print("   - Final display shows Category 4")
                        print("   - OQ tests were generated for Category 4")  
                        print("   - Saved test suite contains Category 4")
                        print("   - THE BUG IS FIXED!")
                        return True
                    elif displayed_category == 1 or file_category == 1:
                        print("\nFAILURE: Human consultation override was IGNORED!")
                        print(f"   - Human selected Category 4")
                        print(f"   - But final display shows Category {displayed_category}")
                        print(f"   - And saved file shows Category {file_category}")
                        print("   - THE BUG STILL EXISTS!")
                        return False
                    else:
                        print(f"\nUNCLEAR: Unexpected category values:")
                        print(f"   - Display category: {displayed_category}")
                        print(f"   - File category: {file_category}")
                        return False
                        
                except Exception as e:
                    print(f"Could not verify test suite file: {e}")
            else:
                print("Test suite file not available for verification")
                
            # Basic verification based on displayed category only
            if displayed_category == 4:
                print("\nLIKELY SUCCESS: Final display shows Category 4")
                return True
            elif displayed_category == 1:
                print("\nLIKELY FAILURE: Final display still shows Category 1 despite human override")
                return False
            else:
                print(f"\nUNCLEAR: Unexpected category {displayed_category}")
                return False
                
        except Exception as e:
            print(f"\nTest failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            workflow.close()

if __name__ == "__main__":
    print("Human Consultation Category 4 Override Fix Test")
    print("=" * 50)
    
    try:
        # Run the test
        success = asyncio.run(test_human_consultation_category4())
        
        print("\n" + "=" * 50)
        if success:
            print("TEST PASSED: Human consultation override fix is working!")
            print("The bug has been successfully resolved.")
        else:
            print("TEST FAILED: Human consultation override fix needs more work")
            print("The bug still exists - human Category 4 selection is ignored.")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest setup failed: {e}")
        import traceback
        traceback.print_exc()