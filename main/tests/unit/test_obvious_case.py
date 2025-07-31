#!/usr/bin/env python3
"""
Test obvious categorization cases that should work without issues.
"""

import asyncio
from src.core.categorization_workflow import run_categorization_workflow


async def test_obvious_cases():
    """Test that obvious cases can be categorized without fallbacks."""
    
    print("🧪 Testing Obvious GAMP Categorization Cases")
    print("=" * 50)
    
    # Test Case 1: Infrastructure/Operating System (Category 1)
    print("\n📋 Test 1: Infrastructure Software (Category 1)")
    obvious_category_1 = """
    Windows Server 2019 Operating System
    Used as the base operating system for pharmaceutical manufacturing systems.
    Standard Microsoft OS with no customization.
    """
    
    try:
        result = await run_categorization_workflow(
            urs_content=obvious_category_1,
            document_name="windows_server_os.md"
        )
        print(f"✅ Category: {result['summary']['category']}, Confidence: {result['summary']['confidence']:.1%}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test Case 2: Commercial Software (Category 3)  
    print("\n📋 Test 2: Commercial Software (Category 3)")
    obvious_category_3 = """
    SAP ERP System for Pharmaceutical Manufacturing
    Standard SAP software package used for manufacturing resource planning.
    Configured but not customized for pharmaceutical operations.
    Includes standard modules for inventory, production, and quality management.
    """
    
    try:
        result = await run_categorization_workflow(
            urs_content=obvious_category_3,
            document_name="sap_erp_system.md"
        )
        print(f"✅ Category: {result['summary']['category']}, Confidence: {result['summary']['confidence']:.1%}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        
    # Test Case 3: Custom Application (Category 5)
    print("\n📋 Test 3: Custom Application (Category 5)")
    obvious_category_5 = """
    Custom Pharmaceutical Batch Management System
    Developed in-house specifically for pharmaceutical batch processing.
    Includes custom algorithms for batch optimization and compliance reporting.
    Integrated with proprietary manufacturing equipment and laboratory systems.
    Requires full validation lifecycle per GAMP-5 guidelines.
    """
    
    try:
        result = await run_categorization_workflow(
            urs_content=obvious_category_5,
            document_name="custom_batch_system.md"
        )
        print(f"✅ Category: {result['summary']['category']}, Confidence: {result['summary']['confidence']:.1%}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n" + "=" * 50)
    print("🎯 Test Summary: Obvious cases should be categorized with high confidence")
    print("❌ Any failures indicate the agent needs improvement for clear cases")


if __name__ == "__main__":
    asyncio.run(test_obvious_cases())