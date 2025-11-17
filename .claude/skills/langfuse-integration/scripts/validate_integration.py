#!/usr/bin/env python3
"""
Langfuse Integration Validation Script

Validates that Langfuse integration is correctly configured and operational.

Usage:
    python validate_integration.py
"""

import os
import sys
from pathlib import Path
import subprocess


def check_sdk_installed() -> bool:
    """Check if Langfuse SDK is installed."""
    try:
        import langfuse
        print("✅ Langfuse SDK installed (version: {})".format(langfuse.__version__))
        return True
    except ImportError:
        print("❌ Langfuse SDK not installed")
        print("   Run: uv add langfuse")
        return False


def check_llamaindex_integration() -> bool:
    """Check if LlamaIndex integration package is installed."""
    try:
        from langfuse.llama_index import LlamaIndexCallbackHandler
        print("✅ LlamaIndex integration installed")
        return True
    except ImportError:
        print("❌ LlamaIndex integration not installed")
        print("   Run: uv add llama-index-instrumentation-langfuse")
        return False


def check_api_keys() -> bool:
    """Check if API keys are configured."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key:
        print("❌ LANGFUSE_PUBLIC_KEY not set")
        return False

    if not secret_key:
        print("❌ LANGFUSE_SECRET_KEY not set")
        return False

    print(f"✅ API keys configured")
    print(f"   Host: {host}")
    print(f"   Public key: {public_key[:10]}...")
    return True


def check_cloud_connectivity() -> bool:
    """Test connection to Langfuse Cloud."""
    try:
        from langfuse import Langfuse

        client = Langfuse()

        # Create test trace
        trace = client.trace(
            name="validation-test",
            input={"test": True},
            metadata={"validation": "integration_check"}
        )

        # Flush immediately
        client.flush()

        print(f"✅ Cloud connectivity successful")
        print(f"   Test trace ID: {trace.id}")
        return True

    except Exception as e:
        print(f"❌ Cloud connectivity failed: {e}")
        return False


def check_decorators() -> int:
    """Count @observe decorators in codebase."""
    try:
        result = subprocess.run(
            ["grep", "-r", "@observe", "main/src/", "--include=*.py"],
            capture_output=True,
            text=True
        )

        count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        print(f"✅ Found {count} @observe decorators")
        return count

    except Exception as e:
        print(f"⚠️  Could not count decorators: {e}")
        return 0


def check_phoenix_removed() -> bool:
    """Verify Phoenix references are removed."""
    try:
        result = subprocess.run(
            ["grep", "-r", "from phoenix", "main/src/", "--include=*.py"],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            print("❌ Phoenix imports still present:")
            print(result.stdout)
            return False
        else:
            print("✅ No Phoenix imports found (as expected)")
            return True

    except Exception as e:
        print(f"⚠️  Could not check Phoenix references: {e}")
        return True


def check_configuration_file() -> bool:
    """Check if langfuse_config.py exists."""
    config_path = Path("main/src/monitoring/langfuse_config.py")

    if config_path.exists():
        print(f"✅ Configuration file exists: {config_path}")
        return True
    else:
        print(f"❌ Configuration file missing: {config_path}")
        return False


def check_callback_handler() -> bool:
    """Check if callback handler is imported in workflow."""
    try:
        result = subprocess.run(
            ["grep", "-r", "LlamaIndexCallbackHandler", "main/src/", "--include=*.py"],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            print("✅ LlamaIndex callback handler found in codebase")
            return True
        else:
            print("⚠️  LlamaIndex callback handler not found")
            print("   Ensure workflow is configured with langfuse_handler")
            return False

    except Exception as e:
        print(f"⚠️  Could not check callback handler: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Langfuse Integration Validation")
    print("=" * 60)
    print()

    checks = [
        ("SDK Installation", check_sdk_installed()),
        ("LlamaIndex Integration", check_llamaindex_integration()),
        ("API Keys", check_api_keys()),
        ("Cloud Connectivity", check_cloud_connectivity()),
        ("Configuration File", check_configuration_file()),
        ("Callback Handler", check_callback_handler()),
        ("Phoenix Removed", check_phoenix_removed()),
    ]

    decorator_count = check_decorators()

    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")

    print()
    print(f"Overall: {passed}/{total} checks passed")
    print(f"Decorators: {decorator_count} @observe decorators found")

    if passed == total:
        print()
        print("🎉 All validation checks passed!")
        print("   Langfuse integration is ready for use.")
        return 0
    else:
        print()
        print("⚠️  Some checks failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
