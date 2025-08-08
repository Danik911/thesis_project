#!/usr/bin/env python3
"""
Debug script to understand callback_manager structure.
"""

import os
os.environ['PHOENIX_ENABLE_TRACING'] = 'true'
os.environ['PHOENIX_EXTERNAL'] = 'true'

print("Investigating CallbackManager structure...")
print("=" * 60)

# Import and check initial state
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager

print("\n1. Initial callback_manager:")
cm = Settings.callback_manager
print(f"   Type: {type(cm).__name__}")
print(f"   ID: {id(cm)}")

# Explore all attributes
print("\n2. CallbackManager attributes:")
for attr in dir(cm):
    if not attr.startswith('_'):
        try:
            value = getattr(cm, attr)
            if not callable(value):
                print(f"   {attr}: {value}")
        except:
            pass

# Check handlers specifically
print("\n3. Handler-related attributes:")
if hasattr(cm, 'handlers'):
    print(f"   handlers: {cm.handlers}")
if hasattr(cm, '_handlers'):
    print(f"   _handlers: {cm._handlers}")
if hasattr(cm, 'event_handlers'):
    print(f"   event_handlers: {cm.event_handlers}")

# Try setting global handler and check what changes
print("\n4. After set_global_handler('arize_phoenix'):")
import llama_index.core
llama_index.core.set_global_handler("arize_phoenix")

# Check if Settings.callback_manager changed
cm2 = Settings.callback_manager
print(f"   Same object? {cm is cm2}")
print(f"   New ID: {id(cm2)}")

# Check handlers again
if hasattr(cm2, 'handlers'):
    print(f"   handlers: {cm2.handlers}")
if hasattr(cm2, '_handlers'):
    print(f"   _handlers: {cm2._handlers}")

# Try to find the Phoenix handler
print("\n5. Looking for Phoenix handler:")
try:
    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
    print(f"   arize_phoenix_callback_handler type: {type(arize_phoenix_callback_handler)}")
    
    # Call it to see what it returns
    handler = arize_phoenix_callback_handler()
    print(f"   Called handler type: {type(handler)}")
    print(f"   Handler: {handler}")
    
    # Try to manually add it
    if hasattr(cm2, 'add_handler'):
        cm2.add_handler(handler)
        print(f"   Added handler via add_handler")
        
        # Check handlers again
        if hasattr(cm2, 'handlers'):
            print(f"   handlers after add: {cm2.handlers}")
            
except Exception as e:
    print(f"   Error: {e}")
    
# Check event handling methods
print("\n6. Event handling methods:")
for method in ['on_event_start', 'on_event_end', 'dispatch_event']:
    if hasattr(cm2, method):
        print(f"   Has {method}: True")
        
# Create a new CallbackManager with handler
print("\n7. Creating new CallbackManager with handler:")
try:
    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
    
    # Create new manager with handler
    new_cm = CallbackManager([arize_phoenix_callback_handler()])
    print(f"   New manager created")
    
    if hasattr(new_cm, 'handlers'):
        print(f"   handlers: {new_cm.handlers}")
    if hasattr(new_cm, '_handlers'):
        print(f"   _handlers: {new_cm._handlers}")
        
    # Set it as global
    Settings.callback_manager = new_cm
    print(f"   Set as global callback_manager")
    
    # Verify
    cm3 = Settings.callback_manager
    if hasattr(cm3, 'handlers'):
        print(f"   Global handlers: {cm3.handlers}")
        
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()