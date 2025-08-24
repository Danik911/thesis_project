#!/usr/bin/env python3
"""
Start Phoenix Server for Enhanced Observability

This script starts the Phoenix server and validates it's working correctly.
"""

import os
import sys
import time
from pathlib import Path

# Add main to path
sys.path.append(str(Path.cwd() / "main"))

print("🚀 Starting Phoenix Server for Enhanced Observability...")

try:
    import phoenix as px

    # Set environment variables
    os.environ["PHOENIX_PORT"] = "6006"
    os.environ["PHOENIX_HOST"] = "localhost"

    print("📊 Launching Phoenix at http://localhost:6006/")

    # Launch Phoenix
    session = px.launch_app(
        host="localhost",
        port=6006
    )

    print("✅ Phoenix server started successfully!")
    print(f"🌐 Phoenix UI available at: {session.url}")

    # Test connectivity
    print("🔍 Testing server connectivity...")
    time.sleep(2)  # Give server time to start

    try:
        import requests
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("✅ Phoenix server is accessible and responding")
        else:
            print(f"⚠️  Phoenix server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")

    print("\n" + "="*60)
    print("🎯 PHOENIX SERVER STATUS: RUNNING")
    print("🌐 UI Access: http://localhost:6006/")
    print("🔗 GraphQL Endpoint: http://localhost:6006/graphql")
    print("="*60)

    print("\n📋 Server is ready for enhanced observability testing!")
    print("Press Ctrl+C to stop the server when done testing...")

    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Phoenix server...")

except ImportError as e:
    print(f"❌ Phoenix import failed: {e}")
    print("🔧 Install with: uv add arize-phoenix")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to start Phoenix server: {e}")
    sys.exit(1)
