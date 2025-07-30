#!/usr/bin/env python3
"""
Test HITL consultation with a pseudo-terminal to simulate true interactive mode.
"""

import os
import sys
import pty
import subprocess
import signal
import time

def test_with_pty():
    """Test the consultation system using a pseudo-terminal."""
    print("🧪 Testing HITL Consultation with Pseudo-Terminal")
    print("=" * 50)
    
    # Test input sequence
    test_inputs = [
        "4\n",  # GAMP category
        "This is a configured product requiring moderate validation\n",  # rationale
        "0.85\n",  # confidence
        "test_validator\n",  # user ID
        "validation_engineer\n"  # user role
    ]
    
    try:
        # Create pseudo-terminal
        master_fd, slave_fd = pty.openpty()
        
        print("🔄 Starting workflow with pseudo-terminal...")
        
        # Start the process with pseudo-terminal
        proc = subprocess.Popen(
            [sys.executable, "main.py", "test_urs_hitl.txt", "--verbose"],
            stdin=slave_fd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Close slave fd in parent process
        os.close(slave_fd)
        
        # Function to send input after delay
        def send_inputs():
            time.sleep(2)  # Wait for startup
            for i, input_text in enumerate(test_inputs):
                print(f"📝 Sending input {i+1}: {input_text.strip()}")
                os.write(master_fd, input_text.encode())
                time.sleep(0.5)  # Small delay between inputs
        
        # Start input sender in background
        import threading
        input_thread = threading.Thread(target=send_inputs)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait for process to complete with timeout
        try:
            stdout, stderr = proc.communicate(timeout=30)
            
            print("📊 STDOUT:")
            print(stdout)
            print("\n📊 STDERR:")
            print(stderr)
            print(f"\n📊 Return code: {proc.returncode}")
            
            # Check for success indicators
            if "✅ Consultation completed!" in stdout:
                print("\n🎉 SUCCESS: Interactive consultation worked!")
                print("Category: 4")
                print("User: test_validator (validation_engineer)")
            elif "Non-interactive terminal detected" in stdout:
                print("\n⚠️ Still detecting as non-interactive (expected in some environments)")
            else:
                print("\n❓ Unexpected result - check output above")
                
        except subprocess.TimeoutExpired:
            print("⏰ Process timed out - terminating...")
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.kill()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            os.close(master_fd)
        except:
            pass

if __name__ == "__main__":
    test_with_pty()