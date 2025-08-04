#!/usr/bin/env uv run python
"""
Phoenix Client Bypass Test
Test direct Phoenix client access to bypass broken GraphQL API
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import phoenix as px


def test_direct_phoenix_client():
    """Test direct Phoenix client to bypass GraphQL issues."""
    print("🔍 Testing Direct Phoenix Client Access")
    print("=" * 50)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "success": False,
        "traces_accessible": False
    }
    
    # Test 1: Phoenix session check
    print("\n1. Checking Phoenix session...")
    try:
        session = px.active_session()
        if session:
            print(f"✅ Active session found: {session}")
            print(f"   URL: {session.url}")
            results["tests"]["active_session"] = {
                "success": True, 
                "url": str(session.url) if session.url else None
            }
        else:
            print("❌ No active session found")
            results["tests"]["active_session"] = {"success": False}
    except Exception as e:
        print(f"❌ Session check failed: {e}")
        results["tests"]["active_session"] = {"success": False, "error": str(e)}
    
    # Test 2: Direct client instantiation
    print("\n2. Testing direct Phoenix client...")
    phoenix_url = "http://localhost:6006"
    
    try:
        # Create client with different configurations
        clients_to_test = [
            ("Default Client", lambda: px.Client()),
            ("Explicit Endpoint", lambda: px.Client(endpoint=phoenix_url)),
            ("With Headers", lambda: px.Client(endpoint=phoenix_url, headers={})),
        ]
        
        successful_clients = []
        
        for client_name, client_factory in clients_to_test:
            try:
                print(f"   Testing {client_name}...")
                client = client_factory()
                print(f"   ✅ {client_name} created successfully")
                successful_clients.append((client_name, client))
                results["tests"][f"client_{client_name.lower().replace(' ', '_')}"] = {"success": True}
            except Exception as e:
                print(f"   ❌ {client_name} failed: {e}")
                results["tests"][f"client_{client_name.lower().replace(' ', '_')}"] = {
                    "success": False, 
                    "error": str(e)
                }
        
        if not successful_clients:
            print("❌ No Phoenix clients could be created")
            return results
            
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        results["tests"]["client_creation"] = {"success": False, "error": str(e)}
        return results
    
    # Test 3: Data access via Phoenix client
    print("\n3. Testing data access via Phoenix client...")
    
    for client_name, client in successful_clients:
        print(f"\n   Testing data access with {client_name}...")
        
        # Test get_spans_dataframe with timeout handling
        try:
            print("   Attempting get_spans_dataframe()...")
            start_time = time.time()
            
            # Set a reasonable timeout by wrapping in a timeout context if possible
            spans_df = client.get_spans_dataframe()
            elapsed = time.time() - start_time
            
            print(f"   ✅ get_spans_dataframe() succeeded in {elapsed:.2f}s")
            print(f"   📊 Retrieved {len(spans_df)} spans")
            
            if len(spans_df) > 0:
                print(f"   📋 Columns: {list(spans_df.columns)}")
                print(f"   📅 Date range: {spans_df['start_time'].min()} to {spans_df['start_time'].max()}")
                print(f"   🔢 Unique traces: {spans_df['trace_id'].nunique()}")
                
                # Show sample of recent spans
                recent_spans = spans_df.head(3)
                print("   📝 Sample spans:")
                for idx, row in recent_spans.iterrows():
                    print(f"      - {row['name']} (trace: {row['trace_id'][:8]}...)")
                
                results["tests"][f"data_access_{client_name.lower().replace(' ', '_')}"] = {
                    "success": True,
                    "span_count": len(spans_df),
                    "trace_count": spans_df['trace_id'].nunique(),
                    "columns": list(spans_df.columns),
                    "elapsed_seconds": elapsed
                }
                results["traces_accessible"] = True
                
            else:
                print("   ⚠️ No spans retrieved - database may be empty")
                results["tests"][f"data_access_{client_name.lower().replace(' ', '_')}"] = {
                    "success": True,
                    "span_count": 0,
                    "elapsed_seconds": elapsed
                }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ get_spans_dataframe() failed after {elapsed:.2f}s: {e}")
            results["tests"][f"data_access_{client_name.lower().replace(' ', '_')}"] = {
                "success": False,
                "error": str(e),
                "elapsed_seconds": elapsed
            }
    
    # Test 4: Alternative data access methods
    print("\n4. Testing alternative Phoenix data access methods...")
    
    if successful_clients:
        client_name, client = successful_clients[0]  # Use first working client
        
        # Try alternative methods if they exist
        methods_to_try = [
            ("get_evaluations", lambda: getattr(client, 'get_evaluations', lambda: None)()),
            ("get_trace_dataset", lambda: getattr(client, 'get_trace_dataset', lambda: None)()),
        ]
        
        for method_name, method_call in methods_to_try:
            try:
                print(f"   Testing {method_name}...")
                result = method_call()
                if result is not None:
                    print(f"   ✅ {method_name} returned data")
                    results["tests"][f"alt_method_{method_name}"] = {"success": True}
                else:
                    print(f"   ⚠️ {method_name} returned None or not available")
                    results["tests"][f"alt_method_{method_name}"] = {"success": False, "result": "none"}
            except Exception as e:
                print(f"   ❌ {method_name} failed: {e}")
                results["tests"][f"alt_method_{method_name}"] = {"success": False, "error": str(e)}
    
    # Determine overall success
    successful_tests = sum(1 for test in results["tests"].values() if test.get("success", False))
    total_tests = len(results["tests"])
    results["success"] = successful_tests > 0 and results["traces_accessible"]
    
    print("\n" + "=" * 50)
    print("📋 DIRECT CLIENT TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"📊 Traces accessible: {'YES' if results['traces_accessible'] else 'NO'}")
    
    if results["traces_accessible"]:
        print("🎯 RESOLUTION: Direct Phoenix client bypasses GraphQL issues!")
        print("💡 Use direct client for trace access until GraphQL is fixed")
    else:
        print("❌ ISSUE PERSISTS: Direct client also cannot access trace data")
        print("🔧 Next steps: Check database integrity or restart Phoenix server")
    
    return results


def suggest_phoenix_restart():
    """Provide instructions for Phoenix server restart."""
    print("\n" + "=" * 50)
    print("🔄 PHOENIX SERVER RESTART INSTRUCTIONS")
    print("=" * 50)
    print("If direct client access also fails, restart Phoenix server:")
    print()
    print("1. Stop current Phoenix server (Ctrl+C if running in terminal)")
    print("2. Start fresh Phoenix server:")
    print("   cd main")
    print("   uv run python start_phoenix.py")
    print()
    print("3. Wait for server to fully initialize (30-60 seconds)")
    print("4. Re-run this test to verify fix")
    print("=" * 50)


def main():
    """Run direct Phoenix client bypass test."""
    results = test_direct_phoenix_client()
    
    # Save results
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phoenix_client_bypass_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {filename}")
    
    if not results["success"]:
        suggest_phoenix_restart()
    
    return results["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)