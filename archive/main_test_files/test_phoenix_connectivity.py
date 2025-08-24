#!/usr/bin/env uv run python
"""
Phoenix Connectivity Test Script
Test basic connectivity and troubleshoot API issues
"""

import sys
import time
from datetime import datetime

import phoenix as px
import requests


def test_http_connectivity(url: str = "http://localhost:6006", timeout: int = 5):
    """Test basic HTTP connectivity to Phoenix server."""
    print(f"Testing HTTP connectivity to {url}...")

    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"✅ Content Length: {len(response.content)} bytes")
        return True
    except requests.exceptions.ConnectRefused:
        print(f"❌ Connection refused - Phoenix server not running on {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def test_phoenix_client(url: str = "http://localhost:6006"):
    """Test Phoenix client initialization and basic operations."""
    print(f"\nTesting Phoenix client at {url}...")

    try:
        # Test client creation
        client = px.Client(endpoint=url)
        print("✅ Phoenix client created successfully")

        # Test basic client operations with timeout
        print("Testing get_spans_dataframe()...")
        start_time = time.time()

        try:
            spans_df = client.get_spans_dataframe()
            elapsed = time.time() - start_time
            print(f"✅ Retrieved spans dataframe in {elapsed:.2f}s")
            print(f"✅ Spans count: {len(spans_df)}")
            print(f"✅ Columns: {list(spans_df.columns)}")
            return True, spans_df
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ get_spans_dataframe() failed after {elapsed:.2f}s: {e}")
            return False, None

    except Exception as e:
        print(f"❌ Phoenix client creation failed: {e}")
        return False, None


def test_graphql_endpoint(url: str = "http://localhost:6006", timeout: int = 5):
    """Test GraphQL endpoint directly."""
    graphql_url = f"{url}/graphql"
    print(f"\nTesting GraphQL endpoint at {graphql_url}...")

    # Simple query to get schema or basic info
    query = {
        "query": "{ __schema { types { name } } }"
    }

    try:
        response = requests.post(
            graphql_url,
            json=query,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ GraphQL Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {data['errors']}")
                return False
            print("✅ GraphQL query successful")
            return True
        print(f"❌ GraphQL failed with status: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"❌ GraphQL request failed: {e}")
        return False


def check_phoenix_processes():
    """Check for running Phoenix processes."""
    print("\nChecking for Phoenix processes...")

    try:
        import psutil
        phoenix_processes = []

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and "phoenix" in proc.info["name"].lower():
                    phoenix_processes.append(proc.info)
                elif proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"]).lower()
                    if "phoenix" in cmdline or "6006" in cmdline:
                        phoenix_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if phoenix_processes:
            print(f"✅ Found {len(phoenix_processes)} Phoenix-related processes:")
            for proc in phoenix_processes:
                print(f"  PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
            return True
        print("❌ No Phoenix processes found")
        return False

    except ImportError:
        print("⚠️ psutil not available, cannot check processes")
        return None


def main():
    """Run comprehensive Phoenix connectivity tests."""
    print("Phoenix API Connectivity Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")

    # Test 1: Check for Phoenix processes
    check_phoenix_processes()

    # Test 2: Basic HTTP connectivity
    http_ok = test_http_connectivity()

    if not http_ok:
        print("\n❌ Basic HTTP connectivity failed. Phoenix server may not be running.")
        print("Try starting Phoenix with: uv run phoenix serve")
        sys.exit(1)

    # Test 3: GraphQL endpoint
    graphql_ok = test_graphql_endpoint()

    # Test 4: Phoenix client
    client_ok, spans_df = test_phoenix_client()

    # Summary
    print("\n" + "=" * 50)
    print("CONNECTIVITY TEST SUMMARY")
    print("=" * 50)
    print(f"HTTP Connectivity: {'✅ OK' if http_ok else '❌ FAILED'}")
    print(f"GraphQL Endpoint: {'✅ OK' if graphql_ok else '❌ FAILED'}")
    print(f"Phoenix Client: {'✅ OK' if client_ok else '❌ FAILED'}")

    if client_ok and spans_df is not None:
        print("\nTrace Data Summary:")
        print(f"Total spans: {len(spans_df)}")
        if len(spans_df) > 0:
            print(f"Date range: {spans_df['start_time'].min()} to {spans_df['start_time'].max()}")
            print(f"Unique traces: {spans_df['trace_id'].nunique()}")


if __name__ == "__main__":
    main()
