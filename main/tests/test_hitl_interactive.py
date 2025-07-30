#!/usr/bin/env python3
"""
Interactive test of HITL consultation system.
This script will simulate an interactive terminal to test the consultation properly.
"""

import sys
import subprocess
import tempfile

def test_interactive_consultation():
    """Test the consultation system interactively."""
    print("🧪 Testing HITL Consultation System Interactively")
    print("=" * 50)
    
    # Create input simulation
    test_input = "4\nCategory 4 is appropriate for this configured product\n0.85\ntest_validator\nvalidation_engineer\n"
    
    # Run the main script with simulated input
    cmd = [sys.executable, "main.py", "test_urs_hitl.txt", "--verbose"]
    
    try:
        print("🔄 Running workflow with simulated user input...")
        print("Expected prompts:")
        print("  - GAMP category: 4")
        print("  - Rationale: Category 4 is appropriate for this configured product")
        print("  - Confidence: 0.85")
        print("  - User ID: test_validator")
        print("  - User role: validation_engineer")
        print()
        
        # Run with input simulation
        result = subprocess.run(
            cmd,
            input=test_input,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        print("📊 STDOUT:")
        print(result.stdout)
        print("\n📊 STDERR:")
        print(result.stderr)
        print(f"\n📊 Return code: {result.returncode}")
        
        # Check for expected success patterns
        if "✅ Consultation completed!" in result.stdout:
            print("\n✅ SUCCESS: Consultation system is working!")
        elif "Non-interactive terminal detected" in result.stdout:
            print("\n⚠️ WARNING: Still detecting as non-interactive")
        else:
            print("\n❌ UNEXPECTED: Check output above")
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout: Consultation may be waiting for input")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_interactive_consultation()