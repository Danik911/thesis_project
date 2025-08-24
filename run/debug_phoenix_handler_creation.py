#!/usr/bin/env python3
"""
Debug Phoenix handler creation order.
"""

import os

os.environ["PHOENIX_ENABLE_TRACING"] = "true"
os.environ["PHOENIX_EXTERNAL"] = "true"

print("Testing Phoenix handler creation order...")
print("=" * 60)

# Step 1: Try handler before Phoenix init
print("\n1. Before Phoenix initialization:")
try:
    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
    handler = arize_phoenix_callback_handler()
    print(f"   Handler created: {handler}")
    print(f"   Handler type: {type(handler)}")
except Exception as e:
    print(f"   Error: {e}")

# Step 2: Initialize Phoenix
print("\n2. Initializing Phoenix...")
try:
    from src.monitoring.phoenix_config import setup_phoenix
    phoenix_manager = setup_phoenix()
    print(f"   Phoenix initialized: {phoenix_manager._initialized}")
except Exception as e:
    print(f"   Error: {e}")

# Step 3: Try handler after Phoenix init
print("\n3. After Phoenix initialization:")
try:
    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
    handler = arize_phoenix_callback_handler()
    print(f"   Handler created: {handler}")
    print(f"   Handler type: {type(handler)}")

    # Check if handler has any useful attributes
    if handler:
        print(f"   Handler attributes: {dir(handler)}")
except Exception as e:
    print(f"   Error: {e}")

# Step 4: Check what set_global_handler does internally
print("\n4. Checking set_global_handler internals...")
try:
    import llama_index.core
    from llama_index.core import Settings

    # Store original callback_manager
    original_cm = Settings.callback_manager
    print(f"   Original CM: {original_cm}")
    print(f"   Original handlers: {original_cm.handlers if hasattr(original_cm, 'handlers') else 'N/A'}")

    # Set global handler
    llama_index.core.set_global_handler("arize_phoenix")

    # Check if it changed
    new_cm = Settings.callback_manager
    print(f"   After set_global_handler CM: {new_cm}")
    print(f"   Same object? {original_cm is new_cm}")
    print(f"   New handlers: {new_cm.handlers if hasattr(new_cm, 'handlers') else 'N/A'}")

except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Try alternative approach - use OpenInference directly
print("\n5. Trying OpenInference instrumentation directly...")
try:
    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

    # Check if already instrumented
    instrumentor = LlamaIndexInstrumentor()
    print(f"   LlamaIndexInstrumentor created: {instrumentor}")

    # Check if it can create handlers
    if hasattr(instrumentor, "get_callback_handler"):
        handler = instrumentor.get_callback_handler()
        print(f"   Handler from instrumentor: {handler}")

except ImportError as e:
    print(f"   OpenInference not available: {e}")
except Exception as e:
    print(f"   Error: {e}")

# Step 6: Check if Phoenix created any global handlers
print("\n6. Checking for Phoenix global state...")
try:
    import phoenix

    # Check if Phoenix has a global session
    if hasattr(phoenix, "active_session"):
        print(f"   Phoenix active_session: {phoenix.active_session}")

    # Check for global tracer
    if hasattr(phoenix, "tracer"):
        print(f"   Phoenix tracer: {phoenix.tracer}")

    # Check for global callback
    if hasattr(phoenix, "callback_handler"):
        print(f"   Phoenix callback_handler: {phoenix.callback_handler}")

except ImportError:
    print("   Phoenix module not available")
except Exception as e:
    print(f"   Error: {e}")
