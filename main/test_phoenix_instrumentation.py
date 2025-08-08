#!/usr/bin/env python3
"""
Test script to verify Phoenix instrumentation is properly configured for OpenRouterCompatLLM.
"""

import os
import sys

# Set environment variables
os.environ['PHOENIX_ENABLE_TRACING'] = 'true'
os.environ['PHOENIX_EXTERNAL'] = 'true'  # Use Docker Phoenix
os.environ['LLM_PROVIDER'] = 'openrouter'

print("=" * 60)
print("Testing Phoenix Instrumentation for OpenRouterCompatLLM")
print("=" * 60)

# Step 1: Initialize Phoenix
print("\n1. Initializing Phoenix...")
try:
    from src.monitoring.phoenix_config import setup_phoenix
    phoenix_manager = setup_phoenix()
    print("[OK] Phoenix initialized successfully")
except Exception as e:
    print(f"[FAIL] Phoenix initialization failed: {e}")
    sys.exit(1)

# Step 2: Check global callback manager
print("\n2. Checking global callback manager...")
try:
    from llama_index.core import Settings
    
    if hasattr(Settings, 'callback_manager'):
        print(f"[OK] Global callback_manager exists: {Settings.callback_manager}")
        print(f"   Type: {type(Settings.callback_manager).__name__}")
        
        # Check for handlers
        if hasattr(Settings.callback_manager, 'handlers'):
            handlers = Settings.callback_manager.handlers
            print(f"   Handlers count: {len(handlers)}")
            for handler in handlers:
                print(f"   - {type(handler).__name__}")
        elif hasattr(Settings.callback_manager, '_handlers'):
            handlers = Settings.callback_manager._handlers
            print(f"   Handlers count: {len(handlers)}")
            for handler in handlers:
                print(f"   - {type(handler).__name__}")
    else:
        print("[FAIL] No global callback_manager found in Settings")
except Exception as e:
    print(f"[FAIL] Error checking callback_manager: {e}")

# Step 3: Test LLMConfig with mock API key
print("\n3. Testing LLMConfig with callback_manager...")
try:
    # Set a dummy API key to test initialization
    os.environ['OPENROUTER_API_KEY'] = 'test-key-for-verification'
    
    from src.config.llm_config import LLMConfig
    
    # Test that get_llm would pass callback_manager
    llm = LLMConfig.get_llm()
    
    print(f"[OK] LLM created: {type(llm).__name__}")
    print(f"[OK] Has callback_manager: {llm.callback_manager is not None}")
    
    if llm.callback_manager:
        print(f"   Callback manager type: {type(llm.callback_manager).__name__}")
        
        # Check if it matches the global one
        if hasattr(Settings, 'callback_manager'):
            if llm.callback_manager is Settings.callback_manager:
                print("[OK] LLM is using the global callback_manager (same object)")
            else:
                print("[WARNING] LLM has a callback_manager but it's not the global one")
    else:
        print("[FAIL] LLM does not have a callback_manager")
        
except Exception as e:
    print(f"[FAIL] Error creating LLM: {e}")

# Step 4: Test instrumentation methods
print("\n4. Testing OpenRouterCompatLLM instrumentation methods...")
try:
    if 'llm' in locals():
        # Test helper methods
        if hasattr(llm, '_calculate_tokens'):
            tokens = llm._calculate_tokens("Test message")
            print(f"[OK] Token calculation works: {tokens} tokens")
        else:
            print("[FAIL] Missing _calculate_tokens method")
            
        if hasattr(llm, '_emit_llm_event'):
            print("[OK] _emit_llm_event method exists")
        else:
            print("[FAIL] Missing _emit_llm_event method")
except Exception as e:
    print(f"[FAIL] Error testing instrumentation methods: {e}")

# Step 5: Verify Phoenix tracing is enabled
print("\n5. Verifying Phoenix tracing configuration...")
try:
    from opentelemetry import trace
    tracer_provider = trace.get_tracer_provider()
    
    if tracer_provider:
        print(f"[OK] OpenTelemetry tracer provider configured: {type(tracer_provider).__name__}")
        
        # Check for span processors
        if hasattr(tracer_provider, '_active_span_processor'):
            processor = tracer_provider._active_span_processor
            print(f"   Active span processor: {type(processor).__name__}")
    else:
        print("[FAIL] No tracer provider configured")
except Exception as e:
    print(f"[FAIL] Error checking tracer: {e}")

# Step 6: Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_checks_passed = True

if phoenix_manager and phoenix_manager._initialized:
    print("[OK] Phoenix: INITIALIZED")
else:
    print("[FAIL] Phoenix: NOT INITIALIZED")
    all_checks_passed = False

if 'llm' in locals() and llm.callback_manager:
    print("[OK] LLM Instrumentation: CONFIGURED")
else:
    print("[FAIL] LLM Instrumentation: NOT CONFIGURED")
    all_checks_passed = False

if all_checks_passed:
    print("\n[SUCCESS] SUCCESS: Phoenix instrumentation is properly configured!")
    print("   LLM spans should now be captured when making API calls.")
else:
    print("\n[WARNING] WARNING: Some checks failed. LLM spans may not be captured.")

# Cleanup
print("\n6. Shutting down Phoenix...")
try:
    from src.monitoring.phoenix_config import shutdown_phoenix
    shutdown_phoenix()
    print("[OK] Phoenix shutdown complete")
except Exception as e:
    print(f"[FAIL] Error during shutdown: {e}")