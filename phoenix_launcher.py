#!/usr/bin/env python3
"""Simple Phoenix launcher without Unicode characters."""

import requests
import time

def check_phoenix():
    """Check if Phoenix is accessible."""
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        return True, response.status_code
    except Exception as e:
        return False, str(e)

def main():
    print("Checking Phoenix server status...")
    
    running, status = check_phoenix()
    
    if running:
        print("SUCCESS: Phoenix server is running at http://localhost:6006")
        print("OpenTelemetry endpoint ready: http://localhost:6006/v1/traces")
        print("Status code:", status)
        
        # Check for existing traces
        try:
            traces_response = requests.get("http://localhost:6006/v1/traces", timeout=5)
            print("Traces endpoint accessible:", traces_response.status_code)
        except Exception as e:
            print("Traces endpoint check:", str(e))
            
    else:
        print("Phoenix server not running. Error:", status)
        print("Attempting to start Phoenix...")
        
        # Try basic Phoenix launch
        try:
            import phoenix as px
            print("Launching Phoenix app...")
            session = px.launch_app(host="localhost", port=6006)
            print("Phoenix session created")
            
            # Verify it's working
            time.sleep(3)
            running, status = check_phoenix()
            if running:
                print("SUCCESS: Phoenix started at http://localhost:6006")
                print("OpenTelemetry endpoint: http://localhost:6006/v1/traces")
            else:
                print("FAILED: Could not verify Phoenix startup")
                
        except Exception as e:
            print("Failed to start Phoenix:", str(e))

if __name__ == "__main__":
    main()