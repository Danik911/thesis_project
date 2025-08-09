"""
Quick test to debug import issues step by step.
"""

import sys
print(f"Python path: {sys.path}")

print("\n1. Testing basic core events import...")
try:
    from src.core.events import GAMPCategory
    print("✓ Basic events import successful")
except Exception as e:
    print(f"✗ Basic events import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing OQ events import...")
try:
    from src.agents.oq_generator.events import OQTestSuiteEvent
    print("✓ OQ events import successful")
except Exception as e:
    print(f"✗ OQ events import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing models import...")
try:
    from src.core.models import WorkflowConfiguration
    print("✓ Models import successful")
except Exception as e:
    print(f"✗ Models import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing error handler import...")
try:
    from src.core.error_handler import ErrorHandler
    print("✓ Error handler import successful")
except Exception as e:
    print(f"✗ Error handler import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing unified workflow import...")
try:
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    print("✓ Unified workflow import successful!")
    print("🎉 ALL CRITICAL IMPORTS WORKING!")
except Exception as e:
    print(f"✗ Unified workflow import failed: {e}")
    import traceback
    traceback.print_exc()