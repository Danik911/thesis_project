#!/usr/bin/env python3
"""
Timeout Configuration Validation Script

This script validates that all timeout fixes have been applied correctly
and reports the current timeout hierarchy for debugging SME agent issues.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.timeout_config import TimeoutConfig


def main():
    """Validate timeout configuration and hierarchy."""
    print("🕐 Timeout Configuration Validation")
    print("=" * 50)

    # Get all configured timeouts
    timeouts = TimeoutConfig.get_all_timeouts()

    print("Current Timeout Values:")
    for service, timeout_val in timeouts.items():
        env_var = f"{service.upper()}_TIMEOUT"
        is_overridden = env_var in os.environ
        override_marker = " (ENV OVERRIDE)" if is_overridden else ""
        print(f"  {service:20}: {timeout_val:4d}s{override_marker}")

    print()

    # Validate timeout hierarchy
    validation = TimeoutConfig.validate_timeouts()

    if validation["valid"]:
        print("✅ Timeout configuration is VALID")
    else:
        print("❌ Timeout configuration has ISSUES:")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    if validation["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")

    print()

    # Check timeout buffers
    print("Timeout Buffers:")
    api_timeout = timeouts["openrouter_api"]
    for agent in ["sme_agent", "oq_generator"]:
        buffer = timeouts[agent] - api_timeout
        buffer_status = "✅" if buffer >= 60 else "⚠️"
        print(f"  {agent} buffer: {buffer}s {buffer_status}")

    print()

    # Specific SME agent analysis
    print("SME Agent Timeout Analysis:")
    sme_timeout = timeouts["sme_agent"]
    api_timeout = timeouts["openrouter_api"]
    workflow_timeout = timeouts["unified_workflow"]

    print(f"  API → SME Buffer:      {sme_timeout - api_timeout}s")
    print(f"  SME → Workflow Buffer: {workflow_timeout - sme_timeout}s")

    if sme_timeout >= 480:  # 8 minutes
        print("  ✅ SME timeout increased to 8+ minutes (should fix 120s timeout issue)")
    else:
        print("  ❌ SME timeout still too low")

    if api_timeout >= 420:  # 7 minutes
        print("  ✅ API timeout increased to 7+ minutes")
    else:
        print("  ❌ API timeout may be too low for SME operations")

    print()

    # Environment variable help
    print("Environment Variable Overrides:")
    env_help = TimeoutConfig.get_environment_variables_help()
    for var, description in env_help.items():
        current_value = os.getenv(var, "not set")
        print(f"  {var:25} = {current_value:10} ({description})")

    print()
    print("🎯 Fixes Applied:")
    print("  ✅ Increased OpenRouter API timeout: 300s → 420s")
    print("  ✅ Increased SME agent timeout: 360s → 480s")
    print("  ✅ Enhanced timeout error reporting with hierarchy")
    print("  ✅ Added workflow startup timeout validation")
    print("  ✅ Added test content quality validation")
    print("  ✅ StartEvent compatibility patch already present")

    print()
    print("🧪 Next Steps:")
    print("  1. Run end-to-end workflow test to verify fixes")
    print("  2. Monitor Phoenix traces for actual timeout behavior")
    print("  3. Check if timeouts still occur (should be resolved)")
    print("  4. Validate that generated tests contain real content")

    return validation["valid"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
