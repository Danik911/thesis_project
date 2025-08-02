#!/usr/bin/env python3
"""
Simple Phoenix Status Validation

This script checks the current status of Phoenix enhanced observability
without external dependencies or complex async operations.
"""

import sys
from pathlib import Path

# Add main to path
sys.path.append(str(Path.cwd() / "main"))

print("🔍 PHOENIX ENHANCED OBSERVABILITY STATUS CHECK")
print("=" * 60)

# Test 1: Basic imports
print("\n1. Testing basic dependency imports...")

try:
    import aiohttp
    print("   ✅ aiohttp - OK")
except ImportError as e:
    print(f"   ❌ aiohttp - FAILED: {e}")

try:
    import networkx
    print("   ✅ networkx - OK")
except ImportError as e:
    print(f"   ❌ networkx - FAILED: {e}")

try:
    import plotly
    print("   ✅ plotly - OK")
except ImportError as e:
    print(f"   ❌ plotly - FAILED: {e}")

try:
    import pandas
    print("   ✅ pandas - OK")
except ImportError as e:
    print(f"   ❌ pandas - FAILED: {e}")

try:
    import phoenix
    print("   ✅ phoenix - OK")
except ImportError as e:
    print(f"   ❌ phoenix - FAILED: {e}")

# Test 2: Phoenix enhanced module
print("\n2. Testing Phoenix enhanced module import...")

try:
    from src.monitoring.phoenix_enhanced import (
        PhoenixGraphQLClient,
        WorkflowEventFlowVisualizer,
        AutomatedTraceAnalyzer,
        setup_enhanced_phoenix_observability
    )
    print("   ✅ Phoenix enhanced module - OK")
    print("   ✅ All enhanced classes available")
except ImportError as e:
    print(f"   ❌ Phoenix enhanced module - FAILED: {e}")
    sys.exit(1)

# Test 3: Basic Phoenix config
print("\n3. Testing basic Phoenix configuration...")

try:
    from src.monitoring.phoenix_config import PhoenixConfig, PhoenixManager
    config = PhoenixConfig()
    print(f"   ✅ PhoenixConfig - OK")
    print(f"   📍 Phoenix endpoint: {config.phoenix_host}:{config.phoenix_port}")
    print(f"   🔧 OTLP endpoint: {config.otlp_endpoint}")
except Exception as e:
    print(f"   ❌ Phoenix configuration - FAILED: {e}")

# Test 4: Integration status
print("\n4. Checking production integration status...")

try:
    # Check unified workflow
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow
    import inspect
    
    # Get the source code
    source = inspect.getsource(UnifiedTestGenerationWorkflow)
    
    if "phoenix_enhanced" in source:
        print("   ✅ Enhanced Phoenix is integrated into unified workflow")
    else:
        print("   ❌ Enhanced Phoenix is NOT integrated into unified workflow")
        print("   🔧 REQUIRES INTEGRATION: Enhanced features are available but not used")
    
except Exception as e:
    print(f"   ❌ Integration check failed: {e}")

# Test 5: Phoenix server status
print("\n5. Checking Phoenix server status...")

try:
    import requests
    response = requests.get("http://localhost:6006", timeout=2)
    if response.status_code == 200:
        print("   ✅ Phoenix server is running at http://localhost:6006")
    else:
        print(f"   ⚠️  Phoenix server responded with status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ Phoenix server is NOT running")
    print("   🚀 TO START: Run 'uv run python main/start_phoenix.py'")
except Exception as e:
    print(f"   ❌ Server check failed: {e}")

print("\n" + "=" * 60)
print("📋 SUMMARY:")
print("- Dependencies: Check output above")
print("- Enhanced module: Available")
print("- Integration: Needs to be added to unified workflow")
print("- Server: Needs to be started")
print("\n🎯 NEXT STEPS:")
print("1. Start Phoenix server if not running")
print("2. Integrate enhanced features into unified_workflow.py")
print("3. Test end-to-end functionality")
print("=" * 60)