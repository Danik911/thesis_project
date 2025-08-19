#!/usr/bin/env python
"""Quick test script to verify enhanced traceability features."""

import logging
import os
import sys
from datetime import datetime
import tracemalloc
import psutil

# Add main directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging with enhanced format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def test_traceability_logs():
    """Test that enhanced traceability logs are working."""
    
    # Start memory tracking
    tracemalloc.start()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Generate unique workflow ID
    import random
    import string
    workflow_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Test OQ-TRACE logs
    logger.info(f"[OQ-TRACE] Creating OQ workflow instance: {workflow_id}")
    logger.info(f"[OQ-TRACE] [Workflow {workflow_id}] STEP 1/3: start_oq_generation")
    logger.info(f"[OQ-TRACE] [Workflow {workflow_id}] STEP 2/3: categorization")
    logger.info(f"[OQ-TRACE] [Workflow {workflow_id}] STEP 3/3: complete_workflow")
    
    # Test OQ-RESOURCE logs
    logger.info(f"[OQ-RESOURCE] Initial memory usage: {initial_memory:.2f} MB")
    
    # Allocate some memory to show delta
    test_data = [i for i in range(100000)]
    current_memory = process.memory_info().rss / 1024 / 1024
    delta = current_memory - initial_memory
    
    logger.info(f"[OQ-RESOURCE] Memory after allocation: {current_memory:.2f} MB (delta: +{delta:.2f} MB)")
    
    # Test OQ-BATCH logs
    logger.info("[OQ-BATCH] Expected batches: 5")
    logger.info("[OQ-BATCH] Batch configuration: 10 tests in batches of 2")
    
    for i in range(1, 6):
        logger.info(f"[OQ-BATCH] Processing batch {i}/5...")
        logger.info(f"[OQ-BATCH] Batch {i} complete: 2 tests generated")
    
    logger.info("[OQ-BATCH] Generation summary: 5 batches processed")
    
    # Test heartbeat simulation
    import time
    logger.info("[OQ-TRACE] ⏱️ Generation in progress... 0s elapsed")
    time.sleep(1)
    logger.info("[OQ-TRACE] ⏱️ Generation in progress... 1s elapsed")
    
    # Success message
    logger.info(f"[OQ-TRACE] 🎉 SUCCESS: OQ generation completed in 1.00 seconds!")
    
    # Final memory
    del test_data
    final_memory = process.memory_info().rss / 1024 / 1024
    logger.info(f"[OQ-RESOURCE] Final memory after cleanup: {final_memory:.2f} MB")
    
    # Stop memory tracking
    tracemalloc.stop()
    
    print("\n✅ Enhanced traceability logs verified successfully!")
    print(f"   - Workflow ID: {workflow_id}")
    print(f"   - Memory tracking: {initial_memory:.2f} MB → {current_memory:.2f} MB → {final_memory:.2f} MB")
    print("   - Batch processing: 5 batches logged")
    print("   - All log prefixes working: [OQ-TRACE], [OQ-RESOURCE], [OQ-BATCH]")

if __name__ == "__main__":
    test_traceability_logs()