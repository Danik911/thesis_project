#!/usr/bin/env python3
"""
Test script for the GAMP-5 compliant event logging system.

This script demonstrates the comprehensive event streaming logging
capabilities and validates GAMP-5 compliance features.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent / "main"))

from src.shared import get_config, setup_event_logging
from src.shared.config import LogLevel
from src.shared.event_logging_integration import GAMP5EventLoggingWorkflow


async def test_basic_event_logging():
    """Test basic event logging functionality."""
    print("🧪 Testing Basic Event Logging Functionality")
    print("-" * 50)

    # Configure logging for testing
    config = get_config()
    config.logging.log_level = LogLevel.DEBUG
    config.logging.log_directory = "logs/test_events"
    config.gamp5_compliance.enable_compliance_logging = True
    config.event_streaming.enable_event_streaming = True

    # Setup event logging
    try:
        event_handler = setup_event_logging(config)
        print("✅ Event logging system initialized successfully")

        # Test configuration validation
        issues = config.validate()
        if issues:
            print(f"⚠️  Configuration issues found: {issues}")
        else:
            print("✅ Configuration validation passed")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize event logging: {e}")
        return False


async def test_workflow_integration():
    """Test workflow integration with event logging."""
    print("\n🔄 Testing Workflow Integration")
    print("-" * 50)

    try:
        # Create workflow with event logging
        workflow = GAMP5EventLoggingWorkflow(enable_logging=True)

        # Prepare test data
        test_data = {
            "document_name": "test_system_urs.md",
            "document_version": "1.0",
            "author": "test_engineer",
            "urs_content": "Sample URS content for testing event logging system"
        }

        print("🚀 Running workflow with event logging...")
        result = await workflow.run(data=test_data)

        if result and result.get("workflow_completed"):
            print("✅ Workflow completed successfully with event logging")

            # Display results
            print(f"  - Validation Status: {result.get('validation_status', 'Unknown')}")
            print(f"  - Compliance Score: {result.get('compliance_score', 0):.1%}")
            print(f"  - Issues Found: {len(result.get('issues_found', []))}")

            # Get statistics
            if hasattr(workflow, "event_handler") and workflow.event_handler:
                stats = workflow.event_handler.get_statistics()
                print("\n📊 Event Processing Statistics:")
                print(f"  - Events Processed: {stats['events_processed']}")
                print(f"  - Events Filtered: {stats['events_filtered']}")
                print(f"  - Runtime: {stats['runtime_seconds']:.2f}s")
                print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")

                # Get compliance statistics
                compliance_stats = workflow.event_handler.compliance_logger.get_audit_statistics()
                print("\n🔒 GAMP-5 Compliance Statistics:")
                print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
                print(f"  - Audit Files: {compliance_stats['audit_file_count']}")
                print(f"  - Storage Size: {compliance_stats['total_size_mb']:.2f} MB")
                print(f"  - Standards: {', '.join(compliance_stats['compliance_standards'])}")
                print(f"  - Tamper Evident: {compliance_stats['tamper_evident']}")
                print(f"  - Retention: {compliance_stats['retention_days']} days")

            return True
        print("❌ Workflow failed or returned invalid result")
        return False

    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_log_file_generation():
    """Test that log files are properly generated."""
    print("\n📁 Testing Log File Generation")
    print("-" * 50)

    log_directories = [
        "logs/test_events",
        "logs/audit",
        "logs/validation"
    ]

    files_found = 0
    total_size = 0

    for log_dir in log_directories:
        log_path = Path(log_dir)
        if log_path.exists():
            print(f"✅ Directory exists: {log_dir}")

            # Count files in directory
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl"))
            if log_files:
                print(f"  📄 Found {len(log_files)} log files:")
                for log_file in log_files:
                    file_size = log_file.stat().st_size
                    files_found += 1
                    total_size += file_size
                    print(f"    - {log_file.name} ({file_size} bytes)")
            else:
                print(f"  ⚠️  No log files found in {log_dir}")
        else:
            print(f"❌ Directory missing: {log_dir}")

    print("\n📊 Log File Summary:")
    print(f"  - Total Files: {files_found}")
    print(f"  - Total Size: {total_size} bytes ({total_size/1024:.2f} KB)")

    return files_found > 0


def test_compliance_features():
    """Test GAMP-5 compliance features."""
    print("\n🔒 Testing GAMP-5 Compliance Features")
    print("-" * 50)

    tests_passed = 0
    total_tests = 5

    # Test 1: Configuration validation
    try:
        config = get_config()
        if config.gamp5_compliance.enable_compliance_logging:
            print("✅ Compliance logging enabled")
            tests_passed += 1
        else:
            print("❌ Compliance logging disabled")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

    # Test 2: ALCOA+ principles
    try:
        alcoa_principles = [
            "attributable", "legible", "contemporaneous",
            "original", "accurate"
        ]
        config = get_config()
        compliance_config = config.gamp5_compliance

        alcoa_enabled = all([
            compliance_config.ensure_attributable,
            compliance_config.ensure_legible,
            compliance_config.ensure_contemporaneous,
            compliance_config.ensure_original,
            compliance_config.ensure_accurate
        ])

        if alcoa_enabled:
            print("✅ ALCOA+ principles enabled")
            tests_passed += 1
        else:
            print("❌ Some ALCOA+ principles disabled")
    except Exception as e:
        print(f"❌ ALCOA+ test failed: {e}")

    # Test 3: Audit trail configuration
    try:
        config = get_config()
        if config.gamp5_compliance.enable_audit_trail:
            print("✅ Audit trail enabled")
            tests_passed += 1
        else:
            print("❌ Audit trail disabled")
    except Exception as e:
        print(f"❌ Audit trail test failed: {e}")

    # Test 4: Tamper evidence
    try:
        config = get_config()
        if config.gamp5_compliance.enable_tamper_evident:
            print("✅ Tamper evidence enabled")
            tests_passed += 1
        else:
            print("❌ Tamper evidence disabled")
    except Exception as e:
        print(f"❌ Tamper evidence test failed: {e}")

    # Test 5: Retention policy
    try:
        config = get_config()
        retention_days = config.gamp5_compliance.audit_retention_days
        if retention_days >= 2555:  # 7 years minimum for pharma
            print(f"✅ Retention policy valid: {retention_days} days")
            tests_passed += 1
        else:
            print(f"❌ Retention policy too short: {retention_days} days")
    except Exception as e:
        print(f"❌ Retention policy test failed: {e}")

    print(f"\n📊 Compliance Test Results: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests


async def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🔬 GAMP-5 Event Logging System - Comprehensive Test Suite")
    print("=" * 70)

    test_results = []

    # Test 1: Basic functionality
    result = await test_basic_event_logging()
    test_results.append(("Basic Event Logging", result))

    # Test 2: Workflow integration
    result = await test_workflow_integration()
    test_results.append(("Workflow Integration", result))

    # Test 3: Log file generation
    result = test_log_file_generation()
    test_results.append(("Log File Generation", result))

    # Test 4: Compliance features
    result = test_compliance_features()
    test_results.append(("Compliance Features", result))

    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUITE SUMMARY")
    print("=" * 70)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} | {status}")
        if result:
            passed += 1

    print("-" * 70)
    print(f"Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Event logging system is working correctly!")
        print("\n📁 Generated files can be found in:")
        print("  - logs/test_events/     (structured event logs)")
        print("  - logs/audit/           (GAMP-5 audit trails)")
        print("  - logs/validation/      (validation logs)")
        return True
    print("⚠️  SOME TESTS FAILED - Please check the implementation")
    return False


async def main():
    """Main test function."""
    try:
        success = await run_comprehensive_test()

        if success:
            print("\n✅ Event logging system test completed successfully")
            print("🔍 You can examine the generated log files for detailed event data")
            sys.exit(0)
        else:
            print("\n❌ Event logging system test failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
