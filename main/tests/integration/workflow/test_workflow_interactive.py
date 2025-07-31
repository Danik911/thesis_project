#!/usr/bin/env python3
"""Interactive test script for workflow with HITL consultation."""

import subprocess
import sys
import time
from pathlib import Path


def main():
    """Run the workflow with interactive consultation support."""
    print("🚀 Starting interactive workflow test...")
    print("=" * 60)

    # Prepare test responses for consultation
    responses = [
        "4",      # GAMP category
        "This is a configured product that requires minimal customization",  # Rationale
        "0.85",   # Confidence level
        "test_user_123",  # User ID
        "validation_specialist"  # Role
    ]

    # Create input for the process
    input_text = "\n".join(responses) + "\n"

    # Run the workflow
    cmd = [sys.executable, "main.py", "test_urs_hitl.txt", "--verbose"]

    print(f"Running command: {' '.join(cmd)}")
    print(f"Prepared responses: {responses}")
    print("=" * 60)

    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=Path(__file__).parent
        )

        # Monitor output and provide input when needed
        consultation_detected = False

        for line in iter(process.stdout.readline, ""):
            print(line, end="")

            # Detect when consultation is required
            if "Enter GAMP category" in line and not consultation_detected:
                consultation_detected = True
                print("\n🤖 Detected consultation prompt - providing automated responses...")
                process.stdin.write(input_text)
                process.stdin.flush()

        # Wait for process to complete
        process.wait()

        print("\n" + "=" * 60)
        print(f"✅ Process completed with exit code: {process.returncode}")

        # Give Phoenix time to export traces
        print("\n⏳ Waiting 5 seconds for Phoenix to export traces...")
        time.sleep(5)

        print("\n📊 Check Phoenix UI at http://localhost:6006/ for traces")
        print("Look for:")
        print("  - URSIngestionEvent")
        print("  - GAMPCategorizationEvent")
        print("  - ConsultationRequiredEvent")
        print("  - HumanResponseEvent")
        print("  - PlanningEvent")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
