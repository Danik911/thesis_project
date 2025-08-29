#!/usr/bin/env python3
"""
Debug script to identify why validation mode is active despite VALIDATION_MODE=false.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging first
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("=== DEBUG VALIDATION MODE ISSUE ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[0]}")

# Check environment variable directly
env_validation_mode = os.getenv("VALIDATION_MODE", "NOT_SET")
env_validation_explicit = os.getenv("VALIDATION_MODE_EXPLICIT", "NOT_SET")

print(f"\n1. Environment Variables:")
print(f"   VALIDATION_MODE = '{env_validation_mode}'")
print(f"   VALIDATION_MODE_EXPLICIT = '{env_validation_explicit}'")

# Check .env file directly
env_file_path = Path(__file__).parent.parent / ".env"
print(f"\n2. .env File Check:")
print(f"   .env file path: {env_file_path}")
print(f"   .env file exists: {env_file_path.exists()}")

if env_file_path.exists():
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
    
    validation_lines = [line.strip() for line in lines if 'VALIDATION_MODE' in line and not line.strip().startswith('#')]
    print(f"   VALIDATION_MODE lines in .env: {validation_lines}")

# Import and check config
print(f"\n3. Config Loading:")
try:
    from src.shared.config import ValidationModeConfig
    print("   ValidationModeConfig imported successfully")
    
    # Create config instance
    validation_config = ValidationModeConfig()
    print(f"   validation_config.validation_mode = {validation_config.validation_mode}")
    print(f"   validation_config.require_explicit_validation_mode = {validation_config.require_explicit_validation_mode}")
    
except Exception as e:
    print(f"   ERROR importing/creating config: {e}")
    import traceback
    traceback.print_exc()

print(f"\n4. Test Main Function Call:")
try:
    from src.core.unified_workflow import run_unified_test_generation_workflow
    print("   run_unified_test_generation_workflow imported successfully")
    
    # Check function signature
    import inspect
    sig = inspect.signature(run_unified_test_generation_workflow)
    validation_mode_param = sig.parameters.get('validation_mode')
    print(f"   validation_mode parameter default: {validation_mode_param.default if validation_mode_param else 'NOT_FOUND'}")
    
except Exception as e:
    print(f"   ERROR importing function: {e}")

print(f"\n=== DEBUG COMPLETE ===")