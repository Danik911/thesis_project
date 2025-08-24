"""
Test the working enhanced Phoenix observability.
"""

import asyncio
import logging

from main.src.monitoring.phoenix_enhanced import (
    AutomatedTraceAnalyzer,
    PhoenixEnhancedClient,
    WorkflowEventFlowVisualizer,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_observability():
    """Test the working enhanced observability features."""
    logger.info("Testing enhanced Phoenix observability...")

    try:
        # Initialize enhanced client
        logger.info("\n1. Initializing enhanced client...")
        client = PhoenixEnhancedClient()
        logger.info("SUCCESS: Enhanced client initialized")

        # Query workflow traces
        logger.info("\n2. Querying workflow traces...")
        traces = await client.query_workflow_traces(hours=24)
        logger.info(f"SUCCESS: Found {len(traces)} workflow traces")

        # Query compliance metrics
        logger.info("\n3. Querying compliance metrics...")
        metrics = await client.query_compliance_metrics(hours=24)
        logger.info(f"SUCCESS: Metrics - Total spans: {metrics['total_spans']}, Compliant: {metrics['compliant_spans']}")

        # Initialize analyzer
        logger.info("\n4. Testing compliance analyzer...")
        analyzer = AutomatedTraceAnalyzer(client)

        # Analyze traces
        if traces:
            violations = await analyzer.analyze_trace(traces[0])
            logger.info(f"Analyzed first trace, found {len(violations)} violations")

        # Generate dashboard
        logger.info("\n5. Generating compliance dashboard...")
        dashboard_path = await analyzer.generate_compliance_dashboard()
        logger.info(f"SUCCESS: Dashboard generated at {dashboard_path}")

        # Test visualizer
        logger.info("\n6. Testing event flow visualizer...")
        visualizer = WorkflowEventFlowVisualizer(client)
        if traces:
            flow_path = await visualizer.generate_event_flow_diagram(traces[0])
            logger.info(f"SUCCESS: Event flow generated at {flow_path}")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ENHANCED PHOENIX OBSERVABILITY TEST")
    logger.info("=" * 60)

    success = asyncio.run(test_enhanced_observability())

    if success:
        logger.info("\nALL TESTS PASSED!")
        logger.info("Enhanced observability is working correctly")
    else:
        logger.info("\nTESTS FAILED")

    logger.info("=" * 60)
