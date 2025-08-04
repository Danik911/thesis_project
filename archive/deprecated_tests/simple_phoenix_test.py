"""
Simple Phoenix test without Unicode characters.
Tests basic functionality and trace capture.
"""

import time
import logging
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_phoenix_tracing():
    """Setup Phoenix tracing with OTLP exporter."""
    logger.info("Setting up Phoenix tracing...")
    
    # Create resource with service info
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: "pharmaceutical-test-system",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "testing"
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:6006/v1/traces",
        timeout=10
    )
    
    # Add batch processor
    processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=1000,
        max_export_batch_size=32,
        export_timeout_millis=5000
    )
    provider.add_span_processor(processor)
    
    # Set as global provider
    trace.set_tracer_provider(provider)
    
    logger.info("Phoenix tracing configured successfully")
    return provider

def generate_test_traces():
    """Generate test traces to verify Phoenix is working."""
    tracer = trace.get_tracer("test-tracer")
    
    logger.info("Generating test traces...")
    
    # Generate multiple traces
    for i in range(5):
        with tracer.start_as_current_span(f"test-workflow-{i}") as workflow_span:
            workflow_span.set_attribute("workflow.type", "pharmaceutical_test")
            workflow_span.set_attribute("workflow.id", f"test-{i}")
            workflow_span.set_attribute("gamp.category", 5)
            
            # Simulate categorization
            with tracer.start_as_current_span("categorization") as cat_span:
                cat_span.set_attribute("confidence.score", 0.95)
                cat_span.set_attribute("gamp.category", 5)
                time.sleep(0.1)  # Simulate work
                
            # Simulate agent work
            with tracer.start_as_current_span("agent-coordination") as agent_span:
                agent_span.set_attribute("agent.count", 3)
                agent_span.set_attribute("agent.types", ["context", "sme", "research"])
                time.sleep(0.1)  # Simulate work
                
        logger.info(f"Generated trace {i+1}/5")
    
    logger.info("All test traces generated")

def verify_phoenix_api():
    """Verify Phoenix API is accessible."""
    import requests
    
    logger.info("Verifying Phoenix API...")
    
    try:
        # Check Phoenix health
        response = requests.get("http://localhost:6006/", timeout=5)
        if response.status_code == 200:
            logger.info("Phoenix server is accessible")
        else:
            logger.warning(f"Phoenix returned status: {response.status_code}")
            
        # Check GraphQL endpoint
        graphql_query = {
            "query": """
            query {
                projects {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
            """
        }
        
        response = requests.post(
            "http://localhost:6006/graphql",
            json=graphql_query,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                logger.warning(f"GraphQL errors: {data['errors']}")
            else:
                logger.info("GraphQL API is functional")
        else:
            logger.warning(f"GraphQL returned status: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Phoenix API check failed: {e}")

def main():
    """Run the simple Phoenix test."""
    logger.info("=" * 60)
    logger.info("SIMPLE PHOENIX TEST")
    logger.info("=" * 60)
    
    # Setup tracing
    provider = setup_phoenix_tracing()
    
    # Generate traces
    generate_test_traces()
    
    # Force flush
    logger.info("Flushing traces to Phoenix...")
    provider.force_flush()
    time.sleep(2)  # Give Phoenix time to process
    
    # Verify API
    verify_phoenix_api()
    
    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("Check Phoenix UI at: http://localhost:6006")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()