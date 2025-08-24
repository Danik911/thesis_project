#!/usr/bin/env python3
"""
Check Dependencies Script - Verify what packages are actually installed
"""

import subprocess
import sys

print("📦 Checking Installed Dependencies")
print("=" * 50)

# List of critical dependencies to check
critical_deps = [
    "arize-phoenix",
    "openinference-instrumentation-llama-index",
    "openinference-instrumentation-openai",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp",
    "llama-index-llms-openai",
    "openai",
    "python-dotenv"
]

print("\n🔍 Checking critical dependencies:")
for dep in critical_deps:
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", dep],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            # Extract version from pip show output
            lines = result.stdout.strip().split("\n")
            version_line = [line for line in lines if line.startswith("Version:")]
            version = version_line[0].split(":", 1)[1].strip() if version_line else "unknown"
            print(f"✅ {dep}: {version}")
        else:
            print(f"❌ {dep}: NOT INSTALLED")
    except Exception as e:
        print(f"❌ {dep}: ERROR - {e}")

print("\n📋 Checking if packages need installation:")
try:
    result = subprocess.run([sys.executable, "-m", "pip", "list"],
                          capture_output=True, text=True, check=False)
    if result.returncode == 0:
        installed_packages = result.stdout.lower()
        missing_packages = []
        for dep in critical_deps:
            if dep.lower() not in installed_packages:
                missing_packages.append(dep)

        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("\n💡 To install missing packages, run:")
            print("uv sync")
            print("# or manually:")
            for pkg in missing_packages:
                print(f"uv add {pkg}")
        else:
            print("✅ All critical packages appear to be installed")
    else:
        print(f"❌ Failed to list packages: {result.stderr}")

except Exception as e:
    print(f"❌ Error checking packages: {e}")

print("\n🏁 Dependency Check Complete")
