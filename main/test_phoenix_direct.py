#!/usr/bin/env python3
"""Direct test of Phoenix observability to isolate the issue."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_phoenix_direct():
    """Test Phoenix directly without workflow complexity."""
    print("🧪 Direct Phoenix Observability Test")
    print("=" * 50)
    
    # Test 1: Check Phoenix configuration
    print("\n1️⃣ Testing Phoenix Configuration...")
    from src.monitoring.phoenix_config import PhoenixConfig, setup_phoenix, get_phoenix_manager
    
    config = PhoenixConfig()
    print(f"   Phoenix Host: {config.phoenix_host}")
    print(f"   Phoenix Port: {config.phoenix_port}")
    print(f"   OTLP Endpoint: {config.otlp_endpoint}")
    print(f"   Service Name: {config.service_name}")
    print(f"   Tracing Enabled: {config.enable_tracing}")
    
    # Test 2: Initialize Phoenix
    print("\n2️⃣ Initializing Phoenix...")
    phoenix_manager = setup_phoenix(config)
    print(f"   Phoenix Initialized: {phoenix_manager._initialized}")
    print(f"   Global Manager Available: {get_phoenix_manager() is not None}")
    
    if phoenix_manager.phoenix_session:
        print(f"   Phoenix UI URL: {phoenix_manager.phoenix_session.url}")
    
    # Test 3: Create a manual span
    print("\n3️⃣ Creating Manual Test Span...")
    tracer = phoenix_manager.get_tracer("test_phoenix_direct")
    
    with tracer.start_as_current_span("test_span") as span:
        span.set_attribute("test.attribute", "test_value")
        span.set_attribute("test.number", 42)
        print("   ✅ Test span created")
        
        # Nested span
        with tracer.start_as_current_span("nested_span") as nested:
            nested.set_attribute("nested.value", "nested_test")
            print("   ✅ Nested span created")
    
    # Test 4: Test event logging with Phoenix
    print("\n4️⃣ Testing Event Logging Integration...")
    from src.shared import setup_event_logging, shutdown_event_logging
    
    event_handler = setup_event_logging()
    print(f"   Event Handler Type: {type(event_handler).__name__}")
    
    # Wait for export
    print("\n⏳ Waiting for trace export (5 seconds)...")
    await asyncio.sleep(5)
    
    # Test 5: Shutdown
    print("\n5️⃣ Testing Graceful Shutdown...")
    from src.monitoring.phoenix_config import shutdown_phoenix
    
    # Get manager before shutdown
    manager_before = get_phoenix_manager()
    print(f"   Manager before shutdown: {manager_before is not None}")
    
    # Shutdown
    shutdown_phoenix(timeout_seconds=10)
    print("   ✅ Phoenix shutdown called")
    
    # Check manager after
    manager_after = get_phoenix_manager()
    print(f"   Manager after shutdown: {manager_after is not None}")
    
    print("\n✅ Test completed")
    print("📊 Check Phoenix UI at http://localhost:6006/ for the test spans")
    print("💡 Look for spans named 'test_span' and 'nested_span'")


if __name__ == "__main__":
    try:
        asyncio.run(test_phoenix_direct())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()