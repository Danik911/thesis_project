"""
Test Phoenix Enhanced Observability Implementation Fix

This test validates that the Phoenix enhanced observability implementation correctly uses
the Phoenix Python Client instead of GraphQL, and that all method names and parameters
are correctly aligned between components.

Tests:
1. Phoenix Enhanced Client initialization and connection
2. Method name consistency between components
3. Parameter passing correctness
4. Error handling without fallbacks
5. Integration with unified workflow
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add main to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_phoenix_enhanced_imports():
    """Test that Phoenix enhanced imports work correctly."""
    try:
        from src.monitoring.phoenix_enhanced import (
            AutomatedTraceAnalyzer,
            ComplianceViolation,
            PhoenixEnhancedClient,
            TraceAnalysisResult,
            WorkflowEventFlowVisualizer,
        )
        logger.info("✅ Phoenix enhanced imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Phoenix enhanced imports failed: {e}")
        return False


def test_unified_workflow_imports():
    """Test that unified workflow imports Phoenix components correctly."""
    try:
        # Check that the import statement in the file is correct
        import inspect

        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        source = inspect.getsource(UnifiedTestGenerationWorkflow)

        # Verify correct imports are present
        assert "PhoenixEnhancedClient" in source
        assert "AutomatedTraceAnalyzer" in source
        assert "PhoenixGraphQLClient" not in source  # Old import should be removed

        logger.info("✅ Unified workflow imports fixed correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Unified workflow imports failed: {e}")
        return False


@patch("src.monitoring.phoenix_enhanced.PHOENIX_AVAILABLE", False)
def test_phoenix_client_graceful_failure():
    """Test that Phoenix client fails gracefully when phoenix is not available."""
    try:
        from src.monitoring.phoenix_enhanced import PhoenixEnhancedClient

        # Should raise exception when Phoenix not available
        try:
            client = PhoenixEnhancedClient()
            logger.error("❌ Phoenix client should have failed when not available")
            return False
        except Exception as e:
            if "Phoenix client not available" in str(e):
                logger.info("✅ Phoenix client fails gracefully when not available")
                return True
            logger.error(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False


@patch("src.monitoring.phoenix_enhanced.PHOENIX_AVAILABLE", True)
@patch("phoenix.client.Client")
def test_phoenix_client_initialization(mock_client_class):
    """Test Phoenix client initialization with mocked dependencies."""
    try:
        from src.monitoring.phoenix_enhanced import PhoenixEnhancedClient

        # Mock the Phoenix client
        mock_client = Mock()
        mock_client.get_spans.return_value = []
        mock_client_class.return_value = mock_client

        # Initialize client
        client = PhoenixEnhancedClient(
            phoenix_host="http://localhost:6006",
            api_key="test_key"
        )

        # Verify initialization
        assert client.phoenix_host == "http://localhost:6006"
        assert client.api_key == "test_key"

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            endpoint="http://localhost:6006",
            api_key="test_key"
        )

        logger.info("✅ Phoenix client initialization test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Phoenix client initialization test failed: {e}")
        return False


@patch("src.monitoring.phoenix_enhanced.PHOENIX_AVAILABLE", True)
@patch("phoenix.client.Client")
async def test_method_name_consistency(mock_client_class):
    """Test that method names are consistent between analyzer and workflow."""
    try:
        from src.monitoring.phoenix_enhanced import (
            AutomatedTraceAnalyzer,
            PhoenixEnhancedClient,
        )

        # Mock the Phoenix client
        mock_client = Mock()
        mock_client.get_spans.return_value = []
        mock_client_class.return_value = mock_client

        # Initialize components
        phoenix_client = PhoenixEnhancedClient()
        analyzer = AutomatedTraceAnalyzer(phoenix_client)

        # Check that the method exists and is callable
        assert hasattr(analyzer, "generate_compliance_dashboard")
        assert callable(analyzer.generate_compliance_dashboard)

        # Check method signature
        import inspect
        sig = inspect.signature(analyzer.generate_compliance_dashboard)
        params = list(sig.parameters.keys())

        # Should have 'hours' parameter, not 'hours_back'
        assert "hours" in params or len(params) == 1  # hours with default

        logger.info("✅ Method name consistency test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Method name consistency test failed: {e}")
        return False


@patch("src.monitoring.phoenix_enhanced.PHOENIX_AVAILABLE", True)
@patch("phoenix.client.Client")
async def test_compliance_analysis_no_fallbacks(mock_client_class):
    """Test that compliance analysis fails explicitly without fallbacks."""
    try:
        from src.monitoring.phoenix_enhanced import (
            AutomatedTraceAnalyzer,
            PhoenixEnhancedClient,
        )

        # Mock the Phoenix client to raise an error
        mock_client = Mock()
        mock_client.get_spans.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        # Initialize components
        phoenix_client = PhoenixEnhancedClient()
        analyzer = AutomatedTraceAnalyzer(phoenix_client)

        # This should fail explicitly, not return fallback values
        try:
            violations = await analyzer.analyze_compliance_violations(hours=1)
            logger.error("❌ Should have failed explicitly, not returned result")
            return False
        except Exception as e:
            if "Failed to analyze compliance violations" in str(e):
                logger.info("✅ Compliance analysis fails explicitly without fallbacks")
                return True
            logger.error(f"❌ Wrong error type: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ No fallbacks test setup failed: {e}")
        return False


@patch("src.monitoring.phoenix_enhanced.PHOENIX_AVAILABLE", True)
@patch("phoenix.client.Client")
async def test_dashboard_generation_no_fallbacks(mock_client_class):
    """Test that dashboard generation fails explicitly without fallbacks."""
    try:
        from src.monitoring.phoenix_enhanced import (
            AutomatedTraceAnalyzer,
            PhoenixEnhancedClient,
        )

        # Mock the Phoenix client to raise an error
        mock_client = Mock()
        mock_client.get_spans.side_effect = Exception("Dashboard creation failed")
        mock_client_class.return_value = mock_client

        # Initialize components
        phoenix_client = PhoenixEnhancedClient()
        analyzer = AutomatedTraceAnalyzer(phoenix_client)

        # This should fail explicitly, not return fallback values
        try:
            dashboard_path = await analyzer.generate_compliance_dashboard(hours=1)
            logger.error("❌ Should have failed explicitly, not returned result")
            return False
        except Exception as e:
            if "Failed to generate compliance dashboard" in str(e):
                logger.info("✅ Dashboard generation fails explicitly without fallbacks")
                return True
            logger.error(f"❌ Wrong error type: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Dashboard no fallbacks test setup failed: {e}")
        return False


def test_workflow_integration_syntax():
    """Test that workflow integration has correct syntax and method calls."""
    try:
        import ast
        import inspect

        from src.core.unified_workflow import UnifiedTestGenerationWorkflow

        # Get source code
        source = inspect.getsource(UnifiedTestGenerationWorkflow)

        # Parse the source code
        tree = ast.parse(source)

        # Look for the complete_workflow method
        complete_workflow_method = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "complete_workflow":
                complete_workflow_method = node
                break

        if complete_workflow_method is None:
            logger.error("❌ complete_workflow method not found")
            return False

        # Check for correct method calls in the source
        method_calls = []
        for node in ast.walk(complete_workflow_method):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                method_calls.append(node.func.attr)

        # Should have generate_compliance_dashboard, not create_compliance_dashboard
        if "generate_compliance_dashboard" in method_calls:
            logger.info("✅ Workflow uses correct method name: generate_compliance_dashboard")
        else:
            logger.error("❌ Workflow missing generate_compliance_dashboard method call")
            return False

        # Should not have old GraphQL methods
        forbidden_methods = ["query_workflow_traces", "analyze_trace"]
        for method in forbidden_methods:
            if method in method_calls:
                logger.error(f"❌ Workflow still uses old method: {method}")
                return False

        logger.info("✅ Workflow integration syntax correct")
        return True
    except Exception as e:
        logger.error(f"❌ Workflow integration syntax test failed: {e}")
        return False


async def run_all_tests():
    """Run all Phoenix enhanced observability tests."""
    tests = [
        ("Import Tests", test_phoenix_enhanced_imports),
        ("Unified Workflow Imports", test_unified_workflow_imports),
        ("Phoenix Client Graceful Failure", test_phoenix_client_graceful_failure),
        ("Phoenix Client Initialization", test_phoenix_client_initialization),
        ("Method Name Consistency", test_method_name_consistency),
        ("Compliance Analysis No Fallbacks", test_compliance_analysis_no_fallbacks),
        ("Dashboard Generation No Fallbacks", test_dashboard_generation_no_fallbacks),
        ("Workflow Integration Syntax", test_workflow_integration_syntax)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("PHOENIX ENHANCED OBSERVABILITY FIX TEST RESULTS")
    logger.info("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1

    logger.info(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Phoenix Enhanced Observability fix is working!")
        return True
    logger.error(f"❌ {total - passed} tests failed - Fix needs more work")
    return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())
