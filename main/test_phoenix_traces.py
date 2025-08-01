#!/usr/bin/env uv run python
"""
Minimal Phoenix trace generation test to verify observability infrastructure.

This script creates a simple workflow with instrumentation to verify that
Phoenix is properly receiving and displaying traces.
"""

import time
import logging
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phoenix_instrumentation():
    """Test Phoenix instrumentation with minimal workflow."""
    logger.info("=== Phoenix Instrumentation Test ===")
    
    try:
        # Initialize Phoenix
        from src.monitoring.phoenix_config import setup_phoenix, PhoenixConfig
        
        config = PhoenixConfig(
            enable_tracing=True,
            enable_local_ui=True,
            enable_openai_instrumentation=True,
            enable_chromadb_instrumentation=True,
        )
        
        phoenix_manager = setup_phoenix(config)
        logger.info(f"Phoenix initialized: {phoenix_manager._initialized}")
        
        # Get tracer for manual trace creation
        tracer = phoenix_manager.get_tracer("test_workflow")
        
        # Create test spans
        with tracer.start_as_current_span("test_workflow_execution") as workflow_span:
            workflow_span.set_attribute("workflow.type", "test")
            workflow_span.set_attribute("workflow.pharmaceutical.compliant", True)
            workflow_span.set_attribute("compliance.gamp5.workflow", True)
            
            logger.info("Created workflow span")
            
            # Create nested spans
            with tracer.start_as_current_span("test_llm_operation") as llm_span:
                llm_span.set_attribute("llm.model", "gpt-4o-mini")
                llm_span.set_attribute("llm.operation", "categorization")
                llm_span.set_attribute("llm.tokens.input", 100)
                llm_span.set_attribute("llm.tokens.output", 50)
                
                time.sleep(0.1)  # Simulate processing
                logger.info("Created LLM span")
            
            with tracer.start_as_current_span("test_vector_operation") as vector_span:
                vector_span.set_attribute("vector_db.operation", "query")
                vector_span.set_attribute("compliance.gamp5.vector_operation", True)
                vector_span.set_attribute("chromadb.query.n_results", 5)
                
                time.sleep(0.05)  # Simulate vector query
                logger.info("Created vector DB span")
        
        # Force flush traces
        logger.info("Flushing traces to Phoenix...")
        phoenix_manager.tracer_provider.force_flush(timeout_millis=5000)
        
        logger.info("✅ Phoenix instrumentation test completed")
        logger.info(f"Phoenix UI should be available at: http://localhost:6006")
        logger.info("Check the UI for traces in the next 30 seconds...")
        
        # Keep alive for trace viewing
        time.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phoenix instrumentation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phoenix_instrumentation()
    sys.exit(0 if success else 1)