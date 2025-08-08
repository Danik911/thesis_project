#!/usr/bin/env python3
"""
Simple LLM Test - Just test the core migration without agents
"""

import os
import sys
from pathlib import Path

# Add the main directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Load environment variables from .env file
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"')
        print(f"Loaded environment from {env_path}")
    else:
        print(f"No .env file found at {env_path}")

# Load environment variables
load_env()

def main():
    """Test core LLM functionality."""
    print("Simple LLM Migration Test")
    print("=" * 30)
    
    try:
        # Test 1: Import and validate config
        from src.config.llm_config import LLMConfig
        print("LLM Config imported successfully")
        print(f"  Provider: {LLMConfig.PROVIDER.value}")
        
        # Test 2: Validate configuration
        is_valid, message = LLMConfig.validate_configuration()
        print(f"Configuration valid: {is_valid}")
        if not is_valid:
            print(f"  Error: {message}")
            return 1
            
        # Test 3: Get LLM instance
        llm = LLMConfig.get_llm()
        print(f"LLM instance created: {type(llm).__name__}")
        
        # Test 4: Test basic completion
        response = llm.complete("Hello, respond with just 'Working!'")
        response_text = response.text.strip()
        safe_text = response_text.encode('ascii', 'ignore').decode('ascii')
        print(f"LLM response: {safe_text}")
        
        print("\nSUCCESS: OSS migration core functionality working!")
        print(f"   Model: {LLMConfig.get_provider_info()['configuration']['model']}")
        print(f"   Provider: {LLMConfig.PROVIDER.value}")
        
        return 0
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())