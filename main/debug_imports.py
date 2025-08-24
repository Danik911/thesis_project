"""
Quick test to debug import issues step by step.
"""

import sys

print(f"Python path: {sys.path}")

print("\n1. Testing basic core events import...")
try:
    print("✓ Basic events import successful")
except Exception as e:
    print(f"✗ Basic events import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing OQ events import...")
try:
    print("✓ OQ events import successful")
except Exception as e:
    print(f"✗ OQ events import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing models import...")
try:
    print("✓ Models import successful")
except Exception as e:
    print(f"✗ Models import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing error handler import...")
try:
    print("✓ Error handler import successful")
except Exception as e:
    print(f"✗ Error handler import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing unified workflow import...")
try:
    print("✓ Unified workflow import successful!")
    print("🎉 ALL CRITICAL IMPORTS WORKING!")
except Exception as e:
    print(f"✗ Unified workflow import failed: {e}")
    import traceback
    traceback.print_exc()
