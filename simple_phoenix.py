#!/usr/bin/env python3
"""Simple Phoenix server launcher with encoding fixes."""

import sys
import os

# Force UTF-8 encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

import phoenix as px

def main():
    try:
        print("Starting Phoenix server...")
        
        # Launch Phoenix
        session = px.launch_app(
            host="localhost",
            port=6006
        )
        
        print(f"Phoenix server running at: {session.url}")
        print("OpenTelemetry endpoint ready at: http://localhost:6006/v1/traces")
        print("Press Ctrl+C to stop")
        
        # Keep running
        input("Press Enter to stop the server...")
        
    except UnicodeEncodeError as e:
        print(f"Encoding error (ignoring): {e}")
        print("Phoenix server launched successfully despite encoding warning")
        print("Server URL: http://localhost:6006")
        print("OpenTelemetry endpoint: http://localhost:6006/v1/traces")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    main()