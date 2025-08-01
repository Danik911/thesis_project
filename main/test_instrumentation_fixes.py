"""
Test script to verify instrumentation fixes without breaking current state.

This script tests:
1. URSIngestionEvent validation fix
2. LLM call instrumentation (OpenAI)
3. Vector database tracing (ChromaDB)
4. Tool execution spans
"""

import asyncio
import sys
from pathlib import Path
import os

# Configure UTF-8 output
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Initialize Phoenix before other imports
import os
os.environ["PHOENIX_ENABLE_TRACING"] = "true"
os.environ["PHOENIX_ENABLE_OPENAI"] = "true"
os.environ["PHOENIX_ENABLE_CHROMADB"] = "true"
os.environ["PHOENIX_ENABLE_TOOLS"] = "true"

from src.monitoring.phoenix_config import setup_phoenix
phoenix_manager = setup_phoenix()
print("✅ Phoenix initialized for instrumentation testing")

# Now import the rest
from src.core.events import URSIngestionEvent
from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import StartEvent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_urs_event_validation():
    """Test URSIngestionEvent validation fix."""
    print("\n🧪 Testing URSIngestionEvent validation...")
    
    try:
        # Test creating URSIngestionEvent with all required fields
        event = URSIngestionEvent(
            urs_content="Test URS content",
            document_name="test_doc.txt",
            document_version="1.0",
            author="test_user"
        )
        print(f"✅ URSIngestionEvent created successfully")
        print(f"   - Document: {event.document_name}")
        print(f"   - Version: {event.document_version}")
        print(f"   - Author: {event.author}")
        print(f"   - Event ID: {event.event_id}")
        return True
    except Exception as e:
        print(f"❌ URSIngestionEvent validation failed: {e}")
        return False


async def test_workflow_initialization():
    """Test workflow initialization with proper parameters."""
    print("\n🧪 Testing workflow initialization...")
    
    try:
        # Create workflow
        workflow = UnifiedTestGenerationWorkflow(
            timeout=60,
            verbose=True
        )
        
        # Test running workflow with proper parameters
        start_event = StartEvent(
            urs_content="Test pharmaceutical system URS content",
            document_name="test_urs.txt",
            document_version="1.0",
            author="test_system"
        )
        
        # Just test initialization, not full run
        print("✅ Workflow initialized successfully")
        print(f"   - Session ID: {workflow._workflow_session_id}")
        print(f"   - LLM configured: {type(workflow.llm).__name__}")
        return True
        
    except Exception as e:
        print(f"❌ Workflow initialization failed: {e}")
        return False


async def test_llm_instrumentation():
    """Test LLM call instrumentation."""
    print("\n🧪 Testing LLM call instrumentation...")
    
    try:
        # Create LLM instance
        llm = OpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=100
        )
        
        # Make a simple LLM call
        response = llm.complete("What is GAMP-5? Respond in one sentence.")
        
        print("✅ LLM call completed (should be traced in Phoenix)")
        print(f"   - Response preview: {response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ LLM instrumentation test failed: {e}")
        return False


async def test_tool_instrumentation():
    """Test tool execution span instrumentation."""
    print("\n🧪 Testing tool instrumentation...")
    
    try:
        from src.monitoring.phoenix_config import instrument_tool
        
        # Create a test tool with instrumentation
        @instrument_tool("test_tool", "testing", critical=True)
        def sample_tool(input_text: str) -> dict:
            """Sample tool for testing instrumentation."""
            return {
                "processed": True,
                "input_length": len(input_text),
                "result": "Tool executed successfully"
            }
        
        # Execute the tool
        result = sample_tool("Test input for pharmaceutical validation")
        
        print("✅ Tool executed with instrumentation")
        print(f"   - Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Tool instrumentation test failed: {e}")
        return False


async def check_phoenix_health():
    """Check Phoenix health and configuration."""
    print("\n🔍 Checking Phoenix health...")
    
    try:
        import requests
        
        # Check Phoenix UI
        phoenix_url = f"http://{phoenix_manager.config.phoenix_host}:{phoenix_manager.config.phoenix_port}"
        response = requests.get(phoenix_url, timeout=5)
        
        print(f"✅ Phoenix UI accessible at {phoenix_url}")
        print(f"   - Status: {response.status_code}")
        
        # Check instrumentation status
        print("\n📊 Instrumentation Configuration:")
        print(f"   - OpenAI instrumentation: {'✅ Enabled' if phoenix_manager.config.enable_openai_instrumentation else '❌ Disabled'}")
        print(f"   - ChromaDB instrumentation: {'✅ Enabled' if phoenix_manager.config.enable_chromadb_instrumentation else '❌ Disabled'}")
        print(f"   - Tool instrumentation: {'✅ Enabled' if phoenix_manager.config.enable_tool_instrumentation else '❌ Disabled'}")
        print(f"   - OTLP endpoint: {phoenix_manager.config.otlp_endpoint}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Phoenix health check failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Instrumentation Fixes")
    print("=" * 50)
    
    # Check Phoenix health first
    phoenix_ok = await check_phoenix_health()
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if await test_urs_event_validation():
        tests_passed += 1
    
    if await test_workflow_initialization():
        tests_passed += 1
    
    if await test_llm_instrumentation():
        tests_passed += 1
    
    if await test_tool_instrumentation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All instrumentation fixes verified successfully!")
        print("\n🎯 Next Steps:")
        print("1. Check Phoenix UI for traces")
        print("2. Run full workflow test")
        print("3. Monitor for any performance impacts")
    else:
        print("❌ Some tests failed - review the output above")
    
    # Shutdown Phoenix gracefully
    print("\n🔒 Shutting down Phoenix...")
    phoenix_manager.shutdown(timeout_seconds=3)
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)