#!/usr/bin/env python
"""Test workflow import with signature integration"""
import sys
import os
sys.path.insert(0, 'main')
os.chdir('main')

try:
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    print("SUCCESS: UnifiedTestGenerationWorkflow imported successfully")
    
    # Check if signature service is available
    workflow = UnifiedTestGenerationWorkflow(enable_part11_compliance=True)
    if workflow.signature_service:
        print("SUCCESS: Signature service initialized")
    else:
        print("WARNING: Signature service not available")
        
except ImportError as e:
    print(f"ERROR Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"ERROR Unexpected error: {e}")
    import traceback
    traceback.print_exc()