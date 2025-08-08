#!/usr/bin/env python3
"""
Test script to verify Phoenix handlers are properly registered.
"""

import os
import sys

# Set environment variables
os.environ['PHOENIX_ENABLE_TRACING'] = 'true'
os.environ['PHOENIX_EXTERNAL'] = 'true'  # Use Docker Phoenix

print("=" * 60)
print("Testing Phoenix Handler Registration")
print("=" * 60)

# Step 1: Check initial state
print("\n1. Initial LlamaIndex Settings state...")
try:
    from llama_index.core import Settings
    
    print(f"   Has callback_manager: {hasattr(Settings, 'callback_manager')}")
    if hasattr(Settings, 'callback_manager'):
        cm = Settings.callback_manager
        print(f"   Initial handlers: {len(cm.handlers) if hasattr(cm, 'handlers') else len(cm._handlers) if hasattr(cm, '_handlers') else 'unknown'}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Step 2: Set global handler explicitly
print("\n2. Setting global Phoenix handler...")
try:
    import llama_index.core
    
    # This should create/configure the global callback_manager with Phoenix handler
    llama_index.core.set_global_handler("arize_phoenix")
    print("[OK] Global handler set to 'arize_phoenix'")
    
    # Check the callback_manager again
    from llama_index.core import Settings
    
    if hasattr(Settings, 'callback_manager'):
        cm = Settings.callback_manager
        print(f"[OK] Callback manager exists: {cm}")
        
        # Try different ways to access handlers
        handlers = []
        if hasattr(cm, 'handlers'):
            handlers = cm.handlers
        elif hasattr(cm, '_handlers'):
            handlers = cm._handlers
        elif hasattr(cm, 'event_handlers'):
            handlers = cm.event_handlers
            
        print(f"   Handlers after setting global handler: {len(handlers)}")
        for handler in handlers:
            print(f"   - {type(handler).__name__}")
            
        # Check if there's an arize handler
        if hasattr(cm, 'arize_phoenix_handler'):
            print(f"   Has arize_phoenix_handler attribute: True")
    else:
        print("[FAIL] No callback_manager in Settings after setting global handler")
        
except Exception as e:
    print(f"[FAIL] Error setting global handler: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Initialize Phoenix and check again
print("\n3. Initializing Phoenix observability...")
try:
    from src.monitoring.phoenix_config import setup_phoenix
    phoenix_manager = setup_phoenix()
    print("[OK] Phoenix initialized")
    
    # Check callback_manager status after Phoenix init
    from llama_index.core import Settings
    
    if hasattr(Settings, 'callback_manager'):
        cm = Settings.callback_manager
        
        # Try different ways to access handlers
        handlers = []
        if hasattr(cm, 'handlers'):
            handlers = cm.handlers
        elif hasattr(cm, '_handlers'):
            handlers = cm._handlers
        elif hasattr(cm, 'event_handlers'):
            handlers = cm.event_handlers
            
        print(f"   Handlers after Phoenix init: {len(handlers)}")
        for handler in handlers:
            print(f"   - {type(handler).__name__}")
            
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Step 4: Try to manually create ArizePhoenixCallbackHandler
print("\n4. Attempting to create ArizePhoenixCallbackHandler manually...")
try:
    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
    
    if arize_phoenix_callback_handler:
        print(f"[OK] arize_phoenix_callback_handler exists: {arize_phoenix_callback_handler}")
        print(f"   Type: {type(arize_phoenix_callback_handler).__name__}")
        
        # Check if it's in the callback_manager
        from llama_index.core import Settings
        
        if hasattr(Settings, 'callback_manager'):
            cm = Settings.callback_manager
            
            # Try to add it manually if not present
            if hasattr(cm, 'add_handler'):
                cm.add_handler(arize_phoenix_callback_handler)
                print("[OK] Manually added handler to callback_manager")
            elif hasattr(cm, 'handlers') and isinstance(cm.handlers, list):
                if arize_phoenix_callback_handler not in cm.handlers:
                    cm.handlers.append(arize_phoenix_callback_handler)
                    print("[OK] Manually appended handler to handlers list")
                    
            # Check final handler count
            handlers = []
            if hasattr(cm, 'handlers'):
                handlers = cm.handlers
            elif hasattr(cm, '_handlers'):
                handlers = cm._handlers
                
            print(f"   Final handler count: {len(handlers)}")
            for handler in handlers:
                print(f"   - {type(handler).__name__}")
    else:
        print("[FAIL] arize_phoenix_callback_handler is None")
        
except ImportError as e:
    print(f"[FAIL] ArizePhoenixCallbackHandler not available: {e}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

try:
    from llama_index.core import Settings
    
    if hasattr(Settings, 'callback_manager'):
        cm = Settings.callback_manager
        
        handlers = []
        if hasattr(cm, 'handlers'):
            handlers = cm.handlers
        elif hasattr(cm, '_handlers'):
            handlers = cm._handlers
            
        if len(handlers) > 0:
            print(f"[OK] Callback manager has {len(handlers)} handler(s)")
            print("[SUCCESS] Phoenix handlers are properly registered!")
        else:
            print("[WARNING] Callback manager exists but has no handlers")
            print("LLM spans may not be captured by Phoenix")
    else:
        print("[FAIL] No callback_manager in Settings")
        
except Exception as e:
    print(f"[FAIL] Error in summary: {e}")