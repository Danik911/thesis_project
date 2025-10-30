#!/usr/bin/env python
"""Quick test of cross-validation with single document."""

import asyncio
import sys
import os
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv(override=True)

from src.cross_validation.fold_manager import URSDocument

async def test_single_document():
    """Test cross-validation with a single document."""
    
    # Create a simple test document
    test_doc = URSDocument(
        document_id="TEST-001",
        file_path=Path("test_document.md"),
        content="""# URS-TEST: Simple Test System
**GAMP Category**: 3
**System Type**: Standard software
**Domain**: Testing

## 1. Introduction
This is a test URS document for validating cross-validation.

## 2. Functional Requirements
- URS-TEST-001: The system shall perform basic operations
- URS-TEST-002: The system shall maintain data integrity
- URS-TEST-003: The system shall provide user authentication

## 3. Regulatory Requirements  
- URS-TEST-004: System shall comply with 21 CFR Part 11
- URS-TEST-005: System shall maintain audit trails

## 4. Performance Requirements
- URS-TEST-006: System shall respond within 2 seconds
- URS-TEST-007: System shall support 100 concurrent users
""",
        category_folder="category_3",
        file_size_bytes=1024
    )
    
    print("[TEST] Created test document")
    
    # Import workflow components
    from src.cross_validation.batch_executor import BatchCrossValidationExecutor
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    
    # Create batch executor
    batch_executor = BatchCrossValidationExecutor(
        batch_size=1,
        timeout_per_doc=600,
        enable_monitoring=True
    )
    
    print("[TEST] Initialized batch executor")
    
    # Create workflow
    workflow = UnifiedTestGenerationWorkflow()
    
    print("[TEST] Created unified workflow")
    
    # Create a simple workflow executor wrapper
    class SimpleWorkflowExecutor:
        def __init__(self, workflow):
            self.workflow = workflow
            
        async def process_document(self, document, fold_id):
            """Process a single document."""
            print(f"[TEST] Processing document {document.document_id} for fold {fold_id}")
            
            try:
                # First create a temporary file with the document content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(document.content)
                    temp_path = f.name
                
                # Run the workflow with document path
                result = await self.workflow.run(
                    document_path=temp_path,
                    verbose=True
                )
                
                # Clean up temp file
                import os
                os.unlink(temp_path)
                
                print(f"[TEST] Workflow returned: {type(result)}")
                
                # Check if result is successful
                if hasattr(result, 'success'):
                    print(f"[TEST] Success: {result.success}")
                    
                return result
                
            except Exception as e:
                print(f"[TEST] Error processing document: {str(e)}")
                return {
                    'success': False,
                    'error': str(e)
                }
    
    # Create executor wrapper
    executor = SimpleWorkflowExecutor(workflow)
    
    # Test batch processing
    print("\n[TEST] Starting batch execution test...")
    
    try:
        result = await batch_executor.execute_fold_in_batches(
            fold_id="test_fold",
            documents=[test_doc],
            workflow_executor=executor,
            resume_from_checkpoint=False
        )
        
        print(f"\n[TEST] Batch execution result:")
        print(f"  - Fold ID: {result['fold_id']}")
        print(f"  - Documents processed: {result['processed_documents']}")
        print(f"  - Documents failed: {result['failed_documents']}")
        print(f"  - Total time: {result['total_time_seconds']:.2f}s")
        
        if result['processed_documents']:
            print("\nSUCCESS: Document processed successfully!")
            return True
        else:
            print("\nFAILURE: Document processing failed")
            return False
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_single_document())
    sys.exit(0 if success else 1)