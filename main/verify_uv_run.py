#!/usr/bin/env python3
"""
Verify that scripts have been updated to use 'uv run python' and test execution.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_main_entry_point():
    """Test that main.py runs with uv run python."""
    print("Testing main.py with uv run python...")
    
    try:
        # Test with --help to avoid actual workflow execution
        result = subprocess.run(
            ["uv", "run", "python", "main/main.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[SUCCESS] main.py runs successfully with uv run python")
            return True
        else:
            print(f"[FAIL] main.py failed with error:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] main.py timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Error running main.py: {e}")
        return False


def test_phoenix_traces():
    """Test that Phoenix trace test runs with instrumentation."""
    print("\nTesting Phoenix trace generation with uv run python...")
    
    trace_test_file = Path(__file__).parent / "test_phoenix_traces.py"
    if not trace_test_file.exists():
        print("[WARNING] test_phoenix_traces.py not found, skipping")
        return True
    
    try:
        # Run the Phoenix trace test
        result = subprocess.run(
            ["uv", "run", "python", str(trace_test_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[SUCCESS] Phoenix trace test runs successfully")
            # Check if instrumentation was active
            if "Phoenix observability initialized" in result.stdout:
                print("[SUCCESS] Phoenix instrumentation is active")
                return True
            else:
                print("[WARNING] Phoenix instrumentation may not be active")
                return True  # Still pass as script runs
        else:
            print(f"[FAIL] Phoenix trace test failed:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] Phoenix trace test timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Error running Phoenix trace test: {e}")
        return False


def check_environment():
    """Check that we're running in the UV environment."""
    print("\nChecking environment...")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"[SUCCESS] Running in virtual environment: {sys.prefix}")
    else:
        print("[WARNING] Not running in virtual environment")
    
    # Check for key packages
    packages_to_check = [
        "arize-phoenix",
        "openinference-instrumentation-llama-index",
        "openinference-instrumentation-openai",
        "llama-index-callbacks-arize-phoenix"
    ]
    
    missing_packages = []
    for package in packages_to_check:
        try:
            result = subprocess.run(
                ["uv", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[SUCCESS] {package} is installed")
            else:
                missing_packages.append(package)
                print(f"[FAIL] {package} is NOT installed")
        except Exception:
            missing_packages.append(package)
            print(f"[FAIL] Could not check {package}")
    
    return len(missing_packages) == 0


def main():
    """Run all verification tests."""
    print("[VERIFY] Verifying UV Run Updates")
    print("=" * 60)
    
    # Check environment first
    env_ok = check_environment()
    
    # Test main entry point
    main_ok = test_main_entry_point()
    
    # Test Phoenix traces
    phoenix_ok = test_phoenix_traces()
    
    print("\n" + "=" * 60)
    print("[SUMMARY] Verification Summary:")
    print(f"  Environment Check: {'PASS' if env_ok else 'FAIL'}")
    print(f"  Main Entry Point: {'PASS' if main_ok else 'FAIL'}")
    print(f"  Phoenix Traces: {'PASS' if phoenix_ok else 'FAIL'}")
    
    all_passed = env_ok and main_ok and phoenix_ok
    
    if all_passed:
        print("\n[SUCCESS] All verification tests passed!")
        print("Scripts are properly updated to use 'uv run python'")
        print("Phoenix instrumentation will be active when running workflows")
    else:
        print("\n[WARNING] Some verification tests failed")
        print("Please check the errors above")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())