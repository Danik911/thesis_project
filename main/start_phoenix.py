#!/usr/bin/env python3
"""Start Phoenix server for observability."""

import os

import phoenix as px

# Set environment variables
os.environ["PHOENIX_PORT"] = "6006"
os.environ["PHOENIX_HOST"] = "localhost"

print("🚀 Starting Phoenix server...")
print("📊 Phoenix will be available at http://localhost:6006/")
print("Press Ctrl+C to stop")

# Launch Phoenix and keep it running
session = px.launch_app()
print(f"\n✅ Phoenix is running at: {session.url}")

# Keep the server running
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 Shutting down Phoenix server...")
