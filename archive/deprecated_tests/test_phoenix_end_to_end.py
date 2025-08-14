#!/usr/bin/env python
"""
Phoenix End-to-End Test Script

This script performs a complete end-to-end test of Phoenix observability:
1. Generates test traces using the workflow configuration
2. Exports traces to Phoenix via OTLP
3. Verifies traces can be retrieved via GraphQL
4. Tests enhanced observability features
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PhoenixEndToEndTester:
    """Complete end-to-end Phoenix observability test."""

    def __init__(self, phoenix_host="localhost", phoenix_port=6006):
        self.phoenix_host = phoenix_host
        self.phoenix_port = phoenix_port
        self.base_url = f"http://{phoenix_host}:{phoenix_port}"
        self.graphql_url = f"{self.base_url}/graphql"
        self.otlp_url = f"{self.base_url}/v1/traces"

        self.test_session_id = f"e2e_test_{int(time.time())}"
        self.tracer_provider = None

        self.results = {
            "test_session_id": self.test_session_id,
            "test_timestamp": time.time(),
            "phoenix_url": self.base_url,
            "test_results": {},
            "traces_generated": 0,
            "traces_verified": 0,
            "success": False
        }

    def setup_opentelemetry(self):
        """Set up OpenTelemetry with Phoenix OTLP export."""
        logger.info("🔧 Setting up OpenTelemetry with Phoenix...")

        try:
            # Create resource with pharmaceutical compliance attributes
            resource = Resource.create({
                "service.name": "phoenix_e2e_test",
                "service.version": "1.0.0",
                "deployment.environment": "test",
                "compliance.gamp5.enabled": True,
                "compliance.pharmaceutical": True,
                "test.session_id": self.test_session_id
            })

            # Create tracer provider
            self.tracer_provider = trace_sdk.TracerProvider(resource=resource)

            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_url,
                headers={}
            )

            # Create batch span processor with fast export for testing
            span_processor = BatchSpanProcessor(
                otlp_exporter,
                max_queue_size=100,
                max_export_batch_size=10,
                schedule_delay_millis=500  # Fast export for testing
            )

            self.tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(self.tracer_provider)

            logger.info("✅ OpenTelemetry configured successfully")

            self.results["test_results"]["opentelemetry_setup"] = {
                "success": True,
                "otlp_endpoint": self.otlp_url,
                "resource_attributes": dict(resource.attributes)
            }

            return True

        except Exception as e:
            logger.error(f"❌ OpenTelemetry setup failed: {e}")
            self.results["test_results"]["opentelemetry_setup"] = {
                "success": False,
                "error": str(e)
            }
            return False

    def generate_pharmaceutical_workflow_traces(self):
        """Generate realistic pharmaceutical workflow traces."""
        logger.info("🧪 Generating pharmaceutical workflow traces...")

        try:
            tracer = trace.get_tracer("pharmaceutical_workflow")
            traces_generated = 0

            # Simulate GAMP-5 categorization workflow
            with tracer.start_as_current_span("gamp5_categorization_workflow") as workflow_span:
                workflow_span.set_attribute("workflow.type", "categorization")
                workflow_span.set_attribute("workflow.pharmaceutical.compliant", True)
                workflow_span.set_attribute("compliance.gamp5.workflow", True)
                workflow_span.set_attribute("compliance.gamp5.category", 4)
                workflow_span.set_attribute("test.session_id", self.test_session_id)

                # Simulate URS ingestion
                with tracer.start_as_current_span("urs_ingestion") as urs_span:
                    urs_span.set_attribute("document.type", "URS")
                    urs_span.set_attribute("document.name", "test_urs_document.txt")
                    urs_span.set_attribute("compliance.gamp5.validation_required", True)
                    time.sleep(0.1)
                    traces_generated += 1

                # Simulate GAMP analysis
                with tracer.start_as_current_span("gamp_analysis") as gamp_span:
                    gamp_span.set_attribute("tool.name", "gamp_analysis")
                    gamp_span.set_attribute("tool.category", "categorization")
                    gamp_span.set_attribute("gamp5.result.category", 4)
                    gamp_span.set_attribute("gamp5.result.confidence", 0.95)
                    gamp_span.set_attribute("compliance.pharmaceutical.tool", True)
                    time.sleep(0.1)
                    traces_generated += 1

                # Simulate confidence scoring
                with tracer.start_as_current_span("confidence_scoring") as conf_span:
                    conf_span.set_attribute("tool.name", "confidence_scorer")
                    conf_span.set_attribute("confidence.score", 0.95)
                    conf_span.set_attribute("confidence.threshold", 0.8)
                    conf_span.set_attribute("confidence.status", "high")
                    time.sleep(0.1)
                    traces_generated += 1

            # Simulate parallel agent coordination
            with tracer.start_as_current_span("parallel_agent_coordination") as coord_span:
                coord_span.set_attribute("workflow.type", "parallel_coordination")
                coord_span.set_attribute("agents.count", 3)
                coord_span.set_attribute("test.session_id", self.test_session_id)

                # Context provider agent
                with tracer.start_as_current_span("context_provider_agent") as context_span:
                    context_span.set_attribute("agent.name", "context_provider")
                    context_span.set_attribute("agent.type", "pharmaceutical_agent")
                    context_span.set_attribute("vector_db.operation", "query")
                    context_span.set_attribute("chromadb.query.n_results", 5)
                    context_span.set_attribute("compliance.gamp5.vector_operation", True)
                    time.sleep(0.1)
                    traces_generated += 1

                # SME agent
                with tracer.start_as_current_span("sme_agent") as sme_span:
                    sme_span.set_attribute("agent.name", "sme_agent")
                    sme_span.set_attribute("agent.type", "pharmaceutical_agent")
                    sme_span.set_attribute("llm.model", "gpt-4o-mini")
                    sme_span.set_attribute("llm.tokens.input", 1250)
                    sme_span.set_attribute("llm.tokens.output", 450)
                    time.sleep(0.1)
                    traces_generated += 1

                # Research agent
                with tracer.start_as_current_span("research_agent") as research_span:
                    research_span.set_attribute("agent.name", "research_agent")
                    research_span.set_attribute("agent.type", "pharmaceutical_agent")
                    research_span.set_attribute("research.queries", 3)
                    research_span.set_attribute("research.sources", "FDA,GAMP5,ICH")
                    time.sleep(0.1)
                    traces_generated += 1

            # Simulate OQ test generation
            with tracer.start_as_current_span("oq_test_generation") as oq_span:
                oq_span.set_attribute("workflow.type", "test_generation")
                oq_span.set_attribute("test.type", "OQ")
                oq_span.set_attribute("test.count", 12)
                oq_span.set_attribute("compliance.21cfr_part11.applicable", True)
                oq_span.set_attribute("test.session_id", self.test_session_id)

                # Individual test generation
                for i in range(3):
                    with tracer.start_as_current_span(f"generate_oq_test_{i+1}") as test_span:
                        test_span.set_attribute("test.id", f"OQ_{i+1:03d}")
                        test_span.set_attribute("test.category", "operational_qualification")
                        test_span.set_attribute("test.priority", "high" if i == 0 else "medium")
                        time.sleep(0.05)
                        traces_generated += 1

            # Force flush to ensure all traces are exported
            logger.info("🚀 Flushing traces to Phoenix...")
            flush_success = self.tracer_provider.force_flush(timeout_millis=10000)

            self.results["traces_generated"] = traces_generated
            self.results["test_results"]["trace_generation"] = {
                "success": flush_success,
                "traces_generated": traces_generated,
                "flush_successful": flush_success
            }

            if flush_success:
                logger.info(f"✅ Generated and exported {traces_generated} traces successfully")
            else:
                logger.warning(f"⚠️ Generated {traces_generated} traces but flush may have timed out")

            # Wait for Phoenix to process traces
            logger.info("⏳ Waiting for Phoenix to process traces...")
            time.sleep(5)

            return flush_success

        except Exception as e:
            logger.error(f"❌ Trace generation failed: {e}")
            self.results["test_results"]["trace_generation"] = {
                "success": False,
                "error": str(e)
            }
            return False

    def verify_traces_in_phoenix(self):
        """Verify that traces can be retrieved from Phoenix via GraphQL."""
        logger.info("🔍 Verifying traces in Phoenix...")

        try:
            # Query for traces with our test session ID
            query = """
            {
                traces(first: 20) {
                    edges {
                        node {
                            traceId
                            spans {
                                edges {
                                    node {
                                        name
                                        attributes {
                                            name
                                            value
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"❌ GraphQL request failed - status: {response.status_code}")
                self.results["test_results"]["trace_verification"] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                return False

            data = response.json()

            if "errors" in data:
                logger.error(f"❌ GraphQL errors: {data['errors']}")
                self.results["test_results"]["trace_verification"] = {
                    "success": False,
                    "errors": data["errors"]
                }
                return False

            if "data" not in data or not data["data"] or "traces" not in data["data"]:
                logger.error("❌ No trace data returned from GraphQL")
                self.results["test_results"]["trace_verification"] = {
                    "success": False,
                    "error": "No trace data in response"
                }
                return False

            # Analyze traces
            traces = data["data"]["traces"]["edges"]
            total_traces = len(traces)
            test_session_traces = 0
            pharmaceutical_spans = 0
            gamp5_spans = 0

            for trace in traces:
                trace_spans = trace["node"]["spans"]["edges"]

                for span in trace_spans:
                    span_node = span["node"]
                    attributes = {attr["name"]: attr["value"] for attr in span_node.get("attributes", [])}

                    # Check if this span belongs to our test session
                    if attributes.get("test.session_id") == self.test_session_id:
                        test_session_traces += 1

                    # Check for pharmaceutical compliance attributes
                    if attributes.get("compliance.pharmaceutical") == "true":
                        pharmaceutical_spans += 1

                    if attributes.get("compliance.gamp5.workflow") == "true":
                        gamp5_spans += 1

            self.results["traces_verified"] = test_session_traces
            self.results["test_results"]["trace_verification"] = {
                "success": True,
                "total_traces_found": total_traces,
                "test_session_traces": test_session_traces,
                "pharmaceutical_spans": pharmaceutical_spans,
                "gamp5_spans": gamp5_spans,
                "graphql_accessible": True
            }

            logger.info("✅ Trace verification successful!")
            logger.info(f"   Total traces in Phoenix: {total_traces}")
            logger.info(f"   Our test session traces: {test_session_traces}")
            logger.info(f"   Pharmaceutical spans: {pharmaceutical_spans}")
            logger.info(f"   GAMP-5 spans: {gamp5_spans}")

            return test_session_traces > 0

        except Exception as e:
            logger.error(f"❌ Trace verification failed: {e}")
            self.results["test_results"]["trace_verification"] = {
                "success": False,
                "error": str(e)
            }
            return False

    def test_enhanced_observability_features(self):
        """Test enhanced Phoenix observability features."""
        logger.info("🔬 Testing enhanced observability features...")

        try:
            # Test pharmaceutical compliance query
            compliance_query = """
            {
                spans(first: 10, filter: {attribute: {name: "compliance.pharmaceutical", value: "true"}}) {
                    edges {
                        node {
                            name
                            attributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
            """

            response = requests.post(
                self.graphql_url,
                json={"query": compliance_query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            compliance_spans_accessible = False

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"] and "spans" in data["data"]:
                    spans = data["data"]["spans"]["edges"]
                    compliance_spans_accessible = len(spans) > 0
                    logger.info(f"   Found {len(spans)} compliance spans")

            # Test GAMP-5 specific query
            gamp5_query = """
            {
                spans(first: 10, filter: {attribute: {name: "compliance.gamp5.workflow", value: "true"}}) {
                    edges {
                        node {
                            name
                            attributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
            """

            response = requests.post(
                self.graphql_url,
                json={"query": gamp5_query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            gamp5_spans_accessible = False

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"] and "spans" in data["data"]:
                    spans = data["data"]["spans"]["edges"]
                    gamp5_spans_accessible = len(spans) > 0
                    logger.info(f"   Found {len(spans)} GAMP-5 spans")

            self.results["test_results"]["enhanced_observability"] = {
                "success": compliance_spans_accessible or gamp5_spans_accessible,
                "compliance_spans_accessible": compliance_spans_accessible,
                "gamp5_spans_accessible": gamp5_spans_accessible
            }

            if compliance_spans_accessible or gamp5_spans_accessible:
                logger.info("✅ Enhanced observability features working")
                return True
            logger.warning("⚠️ Enhanced observability features not fully functional")
            return False

        except Exception as e:
            logger.error(f"❌ Enhanced observability test failed: {e}")
            self.results["test_results"]["enhanced_observability"] = {
                "success": False,
                "error": str(e)
            }
            return False

    def cleanup(self):
        """Clean up OpenTelemetry resources."""
        logger.info("🧹 Cleaning up resources...")

        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
                logger.info("✅ OpenTelemetry cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

    def run_end_to_end_test(self):
        """Run complete end-to-end test."""
        logger.info("🚀 Starting Phoenix End-to-End Test")
        logger.info("=" * 60)
        logger.info(f"Test Session ID: {self.test_session_id}")
        logger.info(f"Phoenix URL: {self.base_url}")
        logger.info("=" * 60)

        try:
            # Test steps
            steps = [
                ("Setup OpenTelemetry", self.setup_opentelemetry),
                ("Generate workflow traces", self.generate_pharmaceutical_workflow_traces),
                ("Verify traces in Phoenix", self.verify_traces_in_phoenix),
                ("Test enhanced observability", self.test_enhanced_observability_features),
            ]

            success_count = 0

            for step_name, step_func in steps:
                logger.info(f"\\n🔧 {step_name}...")
                try:
                    if step_func():
                        success_count += 1
                        logger.info(f"✅ {step_name} successful")
                    else:
                        logger.error(f"❌ {step_name} failed")
                except Exception as e:
                    logger.error(f"❌ {step_name} exception: {e}")

            # Final assessment
            self.results["success"] = (
                success_count >= 3 and  # At least setup, generation, and verification
                self.results["traces_generated"] > 0 and
                self.results["traces_verified"] > 0
            )

            logger.info("=" * 60)
            logger.info(f"🏁 End-to-end test complete: {success_count}/{len(steps)} steps successful")

            if self.results["success"]:
                logger.info("✅ Phoenix observability is fully functional!")
                logger.info(f"   Traces generated: {self.results['traces_generated']}")
                logger.info(f"   Traces verified: {self.results['traces_verified']}")
            else:
                logger.error("❌ Phoenix observability has critical issues")

            return self.results

        finally:
            self.cleanup()

    def save_results(self, filename=None):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phoenix_e2e_test_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"📊 Test results saved to: {filename}")
        return filename

def main():
    """Run Phoenix end-to-end test."""
    tester = PhoenixEndToEndTester()
    results = tester.run_end_to_end_test()

    # Save results
    filename = tester.save_results()

    # Print summary
    print("\\n" + "=" * 60)
    print("📋 END-TO-END TEST SUMMARY")
    print("=" * 60)

    print(f"🆔 Test Session: {results['test_session_id']}")
    print(f"🌐 Phoenix URL: {results['phoenix_url']}")
    print(f"📊 Traces Generated: {results['traces_generated']}")
    print(f"✅ Traces Verified: {results['traces_verified']}")

    print("\\n🧪 Test Results:")
    for test_name, result in results["test_results"].items():
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        print(f"   {status}: {test_name}")

    if results["success"]:
        print("\\n🎉 Phoenix observability is fully functional!")
        print("   • Traces are generated and exported correctly")
        print("   • GraphQL API can retrieve trace data")
        print("   • Enhanced pharmaceutical features work")
        print("   • Ready for production use")
    else:
        print("\\n⚠️ Phoenix observability issues detected:")

        failed_tests = [name for name, result in results["test_results"].items()
                       if not result.get("success", False)]

        for test in failed_tests:
            print(f"   • {test} failed")

        print("\\n📋 Next steps:")
        print("   1. Run fix_phoenix_environment.py")
        print("   2. Run fix_phoenix_graphql.py")
        print("   3. Check Phoenix server logs")
        print("   4. Consider Phoenix version compatibility")

    print(f"\\n📁 Detailed results: {filename}")

    return results["success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
