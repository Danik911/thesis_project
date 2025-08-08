#!/usr/bin/env python3
"""
Test script to verify OpenRouterCompatLLM instrumentation with Phoenix.

This script tests:
1. OpenRouterCompatLLM initialization with instrumentation
2. Phoenix span creation and attributes
3. Token counting and cost estimation
4. Phoenix trace capture

Run this to debug the OQ generation failure and Phoenix instrumentation.
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Set environment variable to use OpenRouter
os.environ["LLM_PROVIDER"] = "openrouter"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_openrouter_instrumentation():
    """Test OpenRouterCompatLLM instrumentation with Phoenix."""
    print("🔧 Testing OpenRouterCompatLLM instrumentation...")
    
    # Initialize Phoenix first
    try:
        from main.src.monitoring.phoenix_config import setup_phoenix
        phoenix_manager = setup_phoenix()
        print("✅ Phoenix initialized successfully")
    except Exception as e:
        print(f"❌ Phoenix initialization failed: {e}")
        return False
    
    # Test LLM configuration
    try:
        from main.src.config.llm_config import LLMConfig
        
        # Validate configuration
        is_valid, error_msg = LLMConfig.validate_configuration()
        if not is_valid:
            print(f"❌ LLM configuration invalid: {error_msg}")
            return False
        
        print("✅ LLM configuration valid")
        
        # Get LLM instance
        llm = LLMConfig.get_llm()
        print(f"✅ LLM instance created: {llm}")
        
        # Check if instrumentation components are available
        has_tracer = hasattr(llm, 'tracer') and llm.tracer is not None
        has_token_encoder = hasattr(llm, 'token_encoder') and llm.token_encoder is not None
        
        print(f"📊 Tracer available: {has_tracer}")
        print(f"📊 Token encoder available: {has_token_encoder}")
        
    except Exception as e:
        print(f"❌ LLM initialization failed: {e}")
        return False
    
    # Test token counting
    try:
        test_text = "This is a test message for token counting in pharmaceutical workflows."
        token_count = llm._count_tokens(test_text)
        print(f"📝 Token count test: '{test_text[:30]}...' = {token_count} tokens")
        
        # Test cost estimation
        cost = llm._estimate_cost(100, 50)  # 100 input, 50 output tokens
        print(f"💰 Cost estimation test: 100 input + 50 output tokens = ${cost:.6f}")
        
    except Exception as e:
        print(f"❌ Token/cost testing failed: {e}")
        return False
    
    # Test actual LLM call with instrumentation (short test to avoid costs)
    try:
        print("🚀 Testing actual LLM call with instrumentation...")
        
        # Create a very short test message to minimize costs
        from main.src.llms.openrouter_compat import ChatMessage, MessageRole
        
        test_messages = [
            ChatMessage(role=MessageRole.USER, content="Reply with just 'OK' to confirm you're working.")
        ]
        
        start_time = time.time()
        response = llm.chat(test_messages)
        duration = time.time() - start_time
        
        print(f"✅ LLM call successful in {duration:.2f}s")
        print(f"📤 Response: {response.message.content[:100]}...")
        
        # Give Phoenix time to export spans
        print("⏳ Waiting for Phoenix span export...")
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return False
    
    # Test unified workflow with simple document
    try:
        print("🔄 Testing unified workflow with instrumentation...")
        
        # Use a simple test document
        test_doc_path = Path(__file__).parent / "main" / "tests" / "test_data" / "simple_test_data.md"
        
        if not test_doc_path.exists():
            print(f"❌ Test document not found: {test_doc_path}")
            return False
        
        print(f"📄 Using test document: {test_doc_path}")
        
        # Run just categorization to test instrumentation (faster than full workflow)
        from main.src.core.categorization_workflow import run_categorization_workflow
        
        document_content = test_doc_path.read_text(encoding="utf-8")
        
        print("🏥 Running GAMP-5 categorization with instrumentation...")
        start_time = time.time()
        
        result = await run_categorization_workflow(
            urs_content=document_content,
            document_name="simple_test_data.md",
            enable_error_handling=True,
            verbose=True,
            confidence_threshold=0.4,
            enable_document_processing=False
        )
        
        workflow_duration = time.time() - start_time
        print(f"✅ Categorization workflow completed in {workflow_duration:.2f}s")
        
        if result:
            summary = result.get("summary", {})
            print(f"📊 Category: {summary.get('category', 'Unknown')}")
            print(f"📊 Confidence: {summary.get('confidence', 0):.2%}")
            print(f"📊 Review required: {summary.get('review_required', False)}")
        else:
            print("❌ No result returned from categorization workflow")
            return False
        
        # Give Phoenix time to export all spans
        print("⏳ Waiting for Phoenix to export all spans...")
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False
    
    print("✅ All instrumentation tests passed!")
    return True

async def main():
    """Main test function."""
    print("🔍 OpenRouterCompatLLM Instrumentation Test")
    print("=" * 50)
    
    # Check API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("💡 Set OPENROUTER_API_KEY to test LLM instrumentation")
        return 1
    
    print(f"🔑 OpenRouter API key found: {openrouter_key[:8]}...")
    
    # Run instrumentation tests
    success = await test_openrouter_instrumentation()
    
    if success:
        print("\n🎉 Instrumentation test completed successfully!")
        print("💡 Check Phoenix UI for captured spans:")
        print("   http://localhost:6006")
        return 0
    else:
        print("\n❌ Instrumentation test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))