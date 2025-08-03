#!/usr/bin/env python3
"""
Debug script to test categorization agent with the simple Category 3 document
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))

from main.src.agents.categorization.agent import gamp_analysis_tool, confidence_tool

# Read the test document
with open('main/simple_category3.md', 'r') as f:
    content = f.read()

print("=== DOCUMENT CONTENT ===")
print(content)
print("\n" + "="*50 + "\n")

# Test the analysis tool
print("=== GAMP ANALYSIS TOOL RESULTS ===")
try:
    analysis_result = gamp_analysis_tool(content)
    print(f"Predicted category: {analysis_result['predicted_category']}")
    print(f"Evidence: {analysis_result['evidence']}")
    print(f"All categories analysis: {analysis_result['all_categories_analysis']}")
    print(f"Decision rationale: {analysis_result['decision_rationale']}")
    print(f"Summary: {analysis_result['summary']}")
    
    print("\n=== DETAILED CATEGORY ANALYSIS ===")
    for category_num, analysis in analysis_result['all_categories_analysis'].items():
        print(f"\nCategory {category_num}:")
        print(f"  Strong indicators ({analysis['strong_count']}): {analysis['strong_indicators']}")
        print(f"  Weak indicators ({analysis['weak_count']}): {analysis['weak_indicators']}")
        print(f"  Exclusions ({analysis['exclusion_count']}): {analysis['exclusion_factors']}")
        if 'category_scores' in analysis_result['evidence']:
            print(f"  Score: {analysis_result['evidence']['category_scores'].get(category_num, 'N/A')}")
    
    print("\n=== CONFIDENCE CALCULATION ===")
    confidence = confidence_tool(analysis_result)
    print(f"Confidence score: {confidence}")
    print(f"Confidence percentage: {confidence * 100:.1f}%")
    
    print("\n=== DEBUGGING INFO ===")
    print(f"Winning score: {analysis_result['evidence'].get('winning_score', 'N/A')}")
    print(f"Category scores: {analysis_result['evidence'].get('category_scores', 'N/A')}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()