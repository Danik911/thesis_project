"""
Test script to verify that all imports in unified_workflow.py resolve correctly.
"""

def test_core_imports():
    """Test core module imports."""
    try:
        from src.core.events import (
            AgentRequestEvent,
            AgentResultEvent,
            AgentResultsEvent,
            ErrorRecoveryEvent,
            GAMPCategorizationEvent,
            GAMPCategory,
            OQTestSuiteEvent,
            OQValidationResultEvent,
            URSIngestionEvent,
            WorkflowCompletionEvent,
        )
        print("✓ Core events import successful")
    except ImportError as e:
        print(f"✗ Core events import failed: {e}")
        return False

    try:
        from src.core.models import (
            AgentExecRequest,
            AgentResult,
            ContextData,
            DocumentMetadata,
            MonitoringConfiguration,
            OQTestCase,
            OQTestSuite,
            OutputConfiguration,
            QualityThresholds,
            TestPlan,
            ValidationReport,
            ValidationResult,
            WorkflowConfiguration,
        )
        print("✓ Core models import successful")
    except ImportError as e:
        print(f"✗ Core models import failed: {e}")
        return False

    try:
        from src.core.error_handler import (
            ErrorHandler,
            RecoveryStrategy,
            ValidationError,
            WorkflowError,
            WorkflowErrorType,
        )
        print("✓ Error handler import successful")
    except ImportError as e:
        print(f"✗ Error handler import failed: {e}")
        return False

    try:
        from src.core.monitoring import (
            MonitoringEventType,
            PerformanceMetrics,
            WorkflowMonitor,
        )
        print("✓ Monitoring import successful")
    except ImportError as e:
        print(f"✗ Monitoring import failed: {e}")
        return False

    try:
        from src.core.output_management import FileCreationResult, OutputManager
        print("✓ Output management import successful")
    except ImportError as e:
        print(f"✗ Output management import failed: {e}")
        return False

    try:
        from src.core.event_logger import EventLogger
        print("✓ Event logger import successful")
    except ImportError as e:
        print(f"✗ Event logger import failed: {e}")
        return False

    return True


def test_agent_imports():
    """Test agent imports."""
    try:
        from src.agents.categorization.agent import GAMPCategorizationAgent
        from src.agents.categorization.workflow import GAMPCategorizationWorkflow
        from src.agents.oq_generator.generator import OQGeneratorAgent
        from src.agents.parallel.context_provider import ContextProviderAgent
        from src.agents.parallel.research_agent import ResearchAgent
        from src.agents.parallel.sme_agent import SMEAgent
        print("✓ Agent imports successful")
        return True
    except ImportError as e:
        print(f"✗ Agent imports failed: {e}")
        return False


def test_unified_workflow_import():
    """Test the main unified workflow import."""
    try:
        from src.core.unified_workflow import (
            UnifiedTestGenerationWorkflow,
            run_pharmaceutical_workflow,
        )
        print("✓ Unified workflow import successful")
        return True
    except ImportError as e:
        print(f"✗ Unified workflow import failed: {e}")
        return False


def main():
    """Run all import tests."""
    print("Testing import resolution for unified workflow...")
    print("=" * 60)

    all_passed = True

    # Test core imports
    if not test_core_imports():
        all_passed = False

    print()

    # Test agent imports
    if not test_agent_imports():
        all_passed = False

    print()

    # Test unified workflow import
    if not test_unified_workflow_import():
        all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("🎉 ALL IMPORTS SUCCESSFUL - Unified workflow can be loaded!")
        return 0
    print("❌ SOME IMPORTS FAILED - Additional fixes needed")
    return 1


if __name__ == "__main__":
    exit(main())
