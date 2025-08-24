#!/usr/bin/env python3
"""
Direct Phoenix test to diagnose issues
"""

import os
import sys
from pathlib import Path

import requests

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_phoenix_connectivity():
    """Test direct connectivity to Phoenix"""

    print("Testing Phoenix connectivity...")

    # Test basic Phoenix UI
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Phoenix UI is accessible")
        else:
            print(f"WARNING: Phoenix UI returned status {response.status_code}")
    except Exception as e:
        print(f"FAILED: Phoenix UI not accessible: {e}")
        return False

    # Test Phoenix traces endpoint (might fail, that's expected)
    try:
        response = requests.post(
            "http://localhost:6006/v1/traces",
            headers={"Content-Type": "application/x-protobuf"},
            data=b"test",
            timeout=5
        )
        print(f"INFO: Traces endpoint responded with status {response.status_code}")
    except Exception as e:
        print(f"INFO: Traces endpoint error (expected): {e}")

    return True

def test_phoenix_config_creation():
    """Test Phoenix configuration creation"""

    print("Testing Phoenix configuration creation...")

    try:
        from src.monitoring.phoenix_config import PhoenixConfig

        config = PhoenixConfig()
        print("SUCCESS: Phoenix config created")
        print(f"  - Host: {config.phoenix_host}")
        print(f"  - Port: {config.phoenix_port}")
        print(f"  - OTLP endpoint: {config.otlp_endpoint}")
        print(f"  - Service name: {config.service_name}")
        print(f"  - Tracing enabled: {config.enable_tracing}")

        return True

    except Exception as e:
        print(f"FAILED: Phoenix config creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_opentelemetry_basic():
    """Test basic OpenTelemetry functionality"""

    print("Testing basic OpenTelemetry functionality...")

    try:
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.resources import Resource

        # Create a basic tracer provider
        resource = Resource.create({"service.name": "phoenix_test"})
        tracer_provider = trace_sdk.TracerProvider(resource=resource)

        # Get a tracer
        tracer = tracer_provider.get_tracer("test_tracer")

        # Create a basic span
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test", "value")
            print("SUCCESS: Basic OpenTelemetry span created")

        return True

    except Exception as e:
        print(f"FAILED: OpenTelemetry basic test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test environment variable setup"""

    print("Testing environment variables...")

    env_vars = [
        "PHOENIX_HOST",
        "PHOENIX_PORT",
        "OTEL_SERVICE_NAME",
        "PHOENIX_ENABLE_TRACING",
        "OPENAI_API_KEY"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Don't print API key value for security
            if "API_KEY" in var:
                print(f"  {var}: SET (hidden)")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: NOT SET")

    return True

def main():
    """Main test function"""
    print("Starting Phoenix direct connectivity and setup test")

    tests = [
        ("Phoenix connectivity", test_phoenix_connectivity),
        ("Phoenix config creation", test_phoenix_config_creation),
        ("OpenTelemetry basic", test_opentelemetry_basic),
        ("Environment variables", test_environment_variables),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"FAILED: {test_name} threw exception: {e}")
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)

    print("\n=== TEST SUMMARY ===")
    print(f"Passed: {passed}/{total}")

    for i, (test_name, _) in enumerate(tests):
        status = "PASS" if results[i] else "FAIL"
        print(f"  {test_name}: {status}")

    if passed == total:
        print("All basic Phoenix infrastructure tests PASSED")
    else:
        print("Some Phoenix infrastructure tests FAILED")

    return passed == total

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
