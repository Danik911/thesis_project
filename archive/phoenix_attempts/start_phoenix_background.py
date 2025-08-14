#!/usr/bin/env python3
"""Start Phoenix server in the background."""

import subprocess
import sys
import time


def start_phoenix():
    """Start Phoenix server as a background process."""
    try:
        # Start Phoenix in the background
        process = subprocess.Popen(
            [sys.executable, "-m", "phoenix.server.main", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print("Phoenix server starting...")
        time.sleep(5)  # Give it time to start

        # Check if process is still running
        if process.poll() is None:
            print("Phoenix server started successfully in background")
            print("Access Phoenix at: http://localhost:6006")
            return True
        print("Phoenix server failed to start")
        stdout, stderr = process.communicate()
        print(f"Error: {stderr}")
        return False

    except Exception as e:
        print(f"Failed to start Phoenix: {e}")
        return False

if __name__ == "__main__":
    start_phoenix()
