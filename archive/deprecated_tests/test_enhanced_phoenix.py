#!/usr/bin/env uv run python
"""
Test script for enhanced Phoenix observability.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main"))

from src.monitoring.phoenix_enhanced import (
    setup_enhanced_phoenix_observability,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_enhanced_phoenix():
    """Test enhanced Phoenix observability features."""
    try:
        logger.info("Testing enhanced Phoenix observability...")

        # Test 1: Setup enhanced observability
        logger.info("1. Setting up enhanced Phoenix observability...")
        enhanced_phoenix = await setup_enhanced_phoenix_observability()
        logger.info(f"✅ Setup completed. Capabilities: {enhanced_phoenix['capabilities']}")

        # Test 2: Test GraphQL API access
        logger.info("2. Testing GraphQL API access...")
        client = enhanced_phoenix["graphql_client"]

        # Query compliance metrics
        compliance_metrics = await client.query_compliance_metrics(timeframe_hours=1)
        logger.info(f"✅ Retrieved compliance metrics: {compliance_metrics.get('total_spans', 0)} spans analyzed")

        # Query workflow traces
        traces = await client.query_workflow_traces(workflow_type="UnifiedTestGenerationWorkflow", hours=1)
        logger.info(f"✅ Retrieved {len(traces)} workflow traces")

        # Test 3: Automated compliance analysis
        logger.info("3. Testing automated compliance analysis...")
        analyzer = enhanced_phoenix["analyzer"]

        violations = await analyzer.analyze_compliance_violations(hours=1)
        logger.info(f"✅ Found {len(violations)} compliance violations")

        if violations:
            for violation in violations[:3]:  # Show first 3
                logger.warning(f"   - {violation.severity}: {violation.violation_type} - {violation.description}")

        # Generate compliance report
        report = await analyzer.generate_compliance_report()
        logger.info(f"✅ Generated compliance report - Status: {report['report_metadata']['regulatory_status']}")
        logger.info(f"   - Compliance rate: {report['compliance_summary']['compliance_rate_percent']:.1f}%")
        logger.info(f"   - Critical violations: {report['violations_summary']['critical_violations']}")

        # Test 4: Create compliance dashboard
        logger.info("4. Creating compliance dashboard...")
        visualizer = enhanced_phoenix["visualizer"]

        dashboard_path = await visualizer.create_compliance_dashboard()
        logger.info(f"✅ Compliance dashboard created: {dashboard_path}")

        # Test 5: Create event flow diagram (if we have traces)
        if traces:
            logger.info("5. Creating event flow diagram...")
            trace_id = traces[0].trace_id
            flow_diagram_path = await visualizer.create_workflow_flow_diagram(trace_id)
            logger.info(f"✅ Event flow diagram created: {flow_diagram_path}")
        else:
            logger.info("5. Skipping event flow diagram - no traces available")

        logger.info("🎉 All enhanced Phoenix observability tests passed!")

        # Print summary
        print("\n" + "="*60)
        print("ENHANCED PHOENIX OBSERVABILITY TEST SUMMARY")
        print("="*60)
        print("GraphQL API Access: ✅ Working")
        print(f"Compliance Metrics: ✅ {compliance_metrics.get('total_spans', 0)} spans")
        print(f"Workflow Traces: ✅ {len(traces)} traces")
        print(f"Compliance Violations: ⚠️ {len(violations)} found")
        print(f"Regulatory Status: {report['report_metadata']['regulatory_status']}")
        print(f"Compliance Rate: {report['compliance_summary']['compliance_rate_percent']:.1f}%")
        print(f"Dashboard: ✅ {dashboard_path}")
        if traces:
            print(f"Event Flow: ✅ {flow_diagram_path}")
        print("="*60)

        return True

    except Exception as e:
        logger.error(f"❌ Enhanced Phoenix test failed: {e}")
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_phoenix())
    sys.exit(0 if success else 1)
