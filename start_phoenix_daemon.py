#!/usr/bin/env python3
"""Start Phoenix server as daemon process."""

import os
import sys
import subprocess
import time
import requests

def check_phoenix_running():
    """Check if Phoenix server is running."""
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    # Check if already running
    if check_phoenix_running():
        print("✓ Phoenix server is already running at http://localhost:6006")
        print("✓ OpenTelemetry endpoint ready at: http://localhost:6006/v1/traces")
        return
    
    print("Starting Phoenix server in background...")
    
    # Create a simple Phoenix launcher
    phoenix_script = '''
import os
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

import phoenix as px

try:
    session = px.launch_app(host="localhost", port=6006)
    print(f"Phoenix running at: {session.url}")
    
    # Keep server alive
    import threading
    import time
    
    def keep_alive():
        while True:
            time.sleep(1)
    
    daemon = threading.Thread(target=keep_alive, daemon=True)
    daemon.start()
    
    # Wait for interrupt
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
        
except UnicodeEncodeError:
    print("Phoenix launched (encoding warning ignored)")
    print("Server at: http://localhost:6006")
    
    import threading
    import time
    
    def keep_alive():
        while True:
            time.sleep(1)
    
    daemon = threading.Thread(target=keep_alive, daemon=True)
    daemon.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
'''
    
    # Write temporary script
    with open("temp_phoenix.py", "w", encoding="utf-8") as f:
        f.write(phoenix_script)
    
    try:
        # Start Phoenix in background
        process = subprocess.Popen([
            sys.executable, "temp_phoenix.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
        
        # Wait for server to start
        print("Waiting for Phoenix server to start...")
        for i in range(10):
            time.sleep(2)
            if check_phoenix_running():
                print("✓ Phoenix server started successfully!")
                print("✓ Server URL: http://localhost:6006")
                print("✓ OpenTelemetry endpoint: http://localhost:6006/v1/traces")
                print("✓ Ready to accept traces")
                return
        
        print("❌ Phoenix server failed to start within timeout")
        
    except Exception as e:
        print(f"❌ Error starting Phoenix: {e}")
    
    finally:
        # Clean up temp file
        if os.path.exists("temp_phoenix.py"):
            os.remove("temp_phoenix.py")

if __name__ == "__main__":
    main()