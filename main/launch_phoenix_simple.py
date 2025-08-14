#!/usr/bin/env python
"""Launch Phoenix observability server."""

import os
import sys
import time

import phoenix as px

# Set encoding for Windows
os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    # Launch Phoenix with pharmaceutical project settings
    print("[INFO] Starting Phoenix observability server...")
    session = px.launch_app(
        host="0.0.0.0",  # Allow connections from any interface
        port=6006,
    )

    print(f"[SUCCESS] Phoenix launched at: {session.url}")
    print("[INFO] Phoenix is ready for pharmaceutical workflow tracing")
    print("[INFO] Access Phoenix UI at: http://localhost:6006")
    print("[INFO] Press Ctrl+C to stop Phoenix")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Phoenix shutdown requested")
        sys.exit(0)

except Exception as e:
    print(f"[ERROR] Failed to launch Phoenix: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
