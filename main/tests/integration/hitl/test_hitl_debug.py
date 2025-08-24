#!/usr/bin/env uv run python
"""
Debug runner for HITL consultation system tests.
Captures and analyzes test failures to identify root causes.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_hitl_tests():
    """Run HITL consultation tests and capture output."""

    # Change to main directory
    os.chdir("/home/anteb/thesis_project/main")

    # Run the specific test file
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/core/test_human_consultation.py",
        "-v", "--tb=short", "--no-header"
    ]

    print("🔍 Running HITL consultation system tests...")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(
            cmd,
            check=False, capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return False, "", "Test execution timed out"
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False, "", str(e)

def analyze_failures(stdout, stderr):
    """Analyze test failures to identify patterns."""

    print("\n🔍 FAILURE ANALYSIS:")
    print("=" * 40)

    failures = []

    # Look for specific error patterns
    if "session ID" in stdout or "session ID" in stderr:
        failures.append("SESSION_ID_MISMATCH")
        print("❌ Found session ID mismatch errors")

    if "No such file or directory" in stdout or "No such file or directory" in stderr:
        failures.append("FILE_SYSTEM_ERROR")
        print("❌ Found file system errors")

    if "coroutine" in stdout and "was never awaited" in stdout:
        failures.append("ASYNC_MOCK_WARNING")
        print("❌ Found async mock warnings")

    if "FAILED" in stdout:
        # Count failed tests
        failed_count = stdout.count("FAILED")
        print(f"📊 Total failed tests: {failed_count}")

    return failures

def main():
    """Main debug runner."""

    print("🚀 HITL Consultation System Debug Runner")
    print("========================================")

    success, stdout, stderr = run_hitl_tests()

    if not success:
        print("\n❌ Tests failed - analyzing failures...")
        failures = analyze_failures(stdout, stderr)

        print(f"\n📋 Identified failure patterns: {failures}")

        # Write results to debug file
        debug_file = Path("/home/anteb/thesis_project/main/hitl_test_debug_output.txt")
        with open(debug_file, "w") as f:
            f.write("HITL Test Debug Output\n")
            f.write("=====================\n\n")
            f.write(f"Failures identified: {failures}\n\n")
            f.write("STDOUT:\n")
            f.write(stdout)
            f.write("\n\nSTDERR:\n")
            f.write(stderr)

        print(f"📝 Debug output saved to: {debug_file}")

    else:
        print("✅ All tests passed!")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
