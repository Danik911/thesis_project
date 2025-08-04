#!/usr/bin/env python3
"""
Simple debug script to test categorization tool only
"""

import sys
import os

# Add main to path
main_path = os.path.join(os.path.dirname(__file__), 'main')
sys.path.insert(0, main_path)

try:
    from src.agents.categorization.agent import gamp_analysis_tool, confidence_tool
    print("✓ Successfully imported categorization tools")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test document content
content = """# Standard Off-the-Shelf Temperature Monitoring System

## System Description
This is a standard commercial off-the-shelf (COTS) temperature monitoring system for pharmaceutical storage areas. The system uses vendor-supplied software without any customization or configuration beyond standard installation parameters.

## Key Features
- Standard temperature sensors with pre-configured ranges
- Vendor-supplied monitoring software used as-is
- Pre-built reporting templates from vendor
- Standard alert thresholds (no custom business logic)
- Out-of-the-box compliance features

## Requirements
1. Monitor temperature in cold storage units
2. Record readings every 5 minutes
3. Generate standard compliance reports
4. Send email alerts for out-of-range conditions
5. Maintain electronic records per 21 CFR Part 11

## GAMP Category Justification
This system clearly falls under GAMP Category 3 as it is:
- Commercial off-the-shelf software
- No customization or custom code
- Standard configuration only
- Uses vendor's standard functionality
- No bespoke interfaces or modifications"""

print("=== TESTING GAMP ANALYSIS TOOL ===")
try:
    analysis_result = gamp_analysis_tool(content)
    print(f"✓ Analysis completed")
    print(f"Predicted category: {analysis_result['predicted_category']}")
    
    # Check Category 3 indicators specifically
    cat3_analysis = analysis_result['all_categories_analysis'][3]
    print(f"\nCategory 3 Analysis:")
    print(f"  Strong indicators: {cat3_analysis['strong_indicators']}")
    print(f"  Strong count: {cat3_analysis['strong_count']}")
    print(f"  Exclusions: {cat3_analysis['exclusion_factors']}")
    print(f"  Exclusion count: {cat3_analysis['exclusion_count']}")
    
    # Check scoring
    if 'category_scores' in analysis_result['evidence']:
        scores = analysis_result['evidence']['category_scores']
        print(f"\nCategory scores:")
        for cat, score in scores.items():
            print(f"  Category {cat}: {score}")
    
except Exception as e:
    print(f"✗ Analysis error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== TESTING CONFIDENCE TOOL ===")
try:
    confidence = confidence_tool(analysis_result)
    print(f"✓ Confidence calculated: {confidence}")
    print(f"Confidence percentage: {confidence * 100:.1f}%")
    
    if confidence < 0.5:
        print("⚠️  WARNING: Very low confidence detected!")
        
except Exception as e:
    print(f"✗ Confidence error: {e}")
    import traceback
    traceback.print_exc()