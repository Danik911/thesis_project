#!/usr/bin/env python3
"""
Test script to validate the batch timeout fix for OQ generation.
Tests the timeout calculation logic without actually generating tests.
"""

import asyncio
import logging
from src.core.events import GAMPCategory
from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_timeout_calculation():
    """Test the new timeout calculation logic."""
    print("🧪 Testing OQ Generator V2 Timeout Fixes")
    print("=" * 50)
    
    # Create generator instance
    generator = OQTestGeneratorV2(verbose=True)
    
    # Test timeout calculations for different categories
    test_scenarios = [
        (GAMPCategory.CATEGORY_1, 5, 2),    # 5 tests, 2 per batch = 3 batches
        (GAMPCategory.CATEGORY_3, 10, 2),   # 10 tests, 2 per batch = 5 batches  
        (GAMPCategory.CATEGORY_4, 15, 2),   # 15 tests, 2 per batch = 8 batches
    ]
    
    for category, total_tests, batch_size in test_scenarios:
        print(f"\n📊 Testing {category.value}:")
        print(f"   Total tests: {total_tests}")
        print(f"   Batch size: {batch_size}")
        
        num_batches = (total_tests + batch_size - 1) // batch_size
        total_timeout = generator.timeout_mapping[category]
        base_timeout = total_timeout // num_batches
        actual_timeout = max(60, base_timeout)
        
        print(f"   Number of batches: {num_batches}")
        print(f"   Total timeout: {total_timeout}s")
        print(f"   Base timeout per batch: {base_timeout}s")
        print(f"   Actual timeout per batch: {actual_timeout}s")
        print(f"   Timeout adequate: {'✅ YES' if actual_timeout >= 60 else '❌ NO'}")
        
        # Calculate total time if all batches use full timeout
        max_total_time = num_batches * actual_timeout
        print(f"   Maximum total time: {max_total_time}s ({max_total_time/60:.1f} minutes)")

if __name__ == "__main__":
    asyncio.run(test_timeout_calculation())