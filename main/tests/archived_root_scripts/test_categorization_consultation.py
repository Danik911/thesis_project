#!/usr/bin/env python3
"""
Test script to validate categorization workflow consultation trigger.
"""

import asyncio
import logging
from pathlib import Path

from src.core.categorization_workflow import run_categorization_workflow


async def test_categorization_with_ambiguous_document():
    """Test categorization workflow with ambiguous document to trigger consultation."""
    
    print("="*60)
    print("CATEGORIZATION CONSULTATION TEST")
    print("="*60)
    
    # Read the ambiguous URS document
    document_path = Path("test_ambiguous_urs.md")
    
    if not document_path.exists():
        print("ERROR: test_ambiguous_urs.md not found")
        return False
        
    document_content = document_path.read_text()
    
    print(f"Document: {document_path.name}")
    print(f"Content length: {len(document_content)} characters")
    print("\nStarting categorization workflow...")
    print("NOTE: If confidence is low, consultation should be triggered")
    
    try:
        result = await run_categorization_workflow(
            urs_content=document_content,
            document_name=document_path.name,
            enable_error_handling=True,
            verbose=True,
            confidence_threshold=0.70,  # Set high threshold to likely trigger consultation
            enable_document_processing=False
        )
        
        if result:
            summary = result.get("summary", {})
            consultation = result.get("consultation", {})
            
            print("\nRESULTS:")
            print(f"  Category: {summary.get('category', 'Unknown')}")
            print(f"  Confidence: {summary.get('confidence', 0):.2%}")
            print(f"  Review Required: {summary.get('review_required', False)}")
            print(f"  Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
            
            if consultation:
                print(f"\nCONSULTATION:")
                print(f"  Required: {consultation.get('required', False)}")
                if consultation.get('required'):
                    event = consultation.get('event')
                    if event:
                        print(f"  Consultation ID: {event.consultation_id}")
                        print(f"  Type: {event.consultation_type}")
                        print(f"  Urgency: {event.urgency}")
                        print("  PASS: Consultation was triggered successfully")
                        return True
                else:
                    print("  FAIL: Consultation was not triggered despite ambiguous document")
                    return False
            else:
                print("  FAIL: No consultation information in result")
                return False
        else:
            print("ERROR: Categorization workflow returned no result")
            return False
            
    except Exception as e:
        print(f"ERROR: Categorization workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    try:
        success = asyncio.run(test_categorization_with_ambiguous_document())
        
        if success:
            print("\n" + "="*60)
            print("TEST RESULT: CONSULTATION TRIGGER SUCCESSFUL")
            print("The categorization workflow correctly identified low confidence")
            print("and triggered the human consultation system.")
        else:
            print("\n" + "="*60)
            print("TEST RESULT: CONSULTATION TRIGGER FAILED")
            print("The categorization workflow did not trigger consultation as expected.")
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()