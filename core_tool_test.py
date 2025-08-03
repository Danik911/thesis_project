#!/usr/bin/env python3
"""
Test just the core gamp_analysis_tool with the fix
"""

import sys
import os

# Add main to path
main_path = os.path.join(os.path.dirname(__file__), 'main')
sys.path.insert(0, main_path)

# Test document content
test_content = """# Standard Off-the-Shelf Temperature Monitoring System

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

def test_core_analysis():
    """Test the core analysis tool"""
    
    try:
        from src.agents.categorization.agent import gamp_analysis_tool, confidence_tool
        print("✅ Successfully imported tools")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    print("\n🔍 TESTING CORE GAMP ANALYSIS TOOL")
    print("="*50)
    
    try:
        # Run analysis
        result = gamp_analysis_tool(test_content)
        
        print(f"✅ Analysis completed")
        print(f"📊 Predicted category: {result['predicted_category']}")
        
        # Focus on Category 3 results
        cat3_data = result['all_categories_analysis'][3]
        print(f"\n📋 Category 3 Analysis:")
        print(f"   Strong indicators ({cat3_data['strong_count']}): {cat3_data['strong_indicators']}")
        print(f"   Weak indicators ({cat3_data['weak_count']}): {cat3_data['weak_indicators']}")
        print(f"   Exclusions ({cat3_data['exclusion_count']}): {cat3_data['exclusion_factors']}")
        
        # Check all scores
        if 'category_scores' in result['evidence']:
            print(f"\n📈 All Category Scores:")
            for cat, score in result['evidence']['category_scores'].items():
                print(f"   Category {cat}: {score}")
        
        print(f"\n💭 Decision: {result['decision_rationale']}")
        
        # Test confidence
        confidence = confidence_tool(result)
        print(f"\n🎯 Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
        
        # Evaluation
        success_criteria = {
            'correct_category': result['predicted_category'] == 3,
            'has_strong_indicators': cat3_data['strong_count'] >= 2,
            'minimal_exclusions': cat3_data['exclusion_count'] <= 1,  # Allow 1 in case of edge cases
            'good_confidence': confidence >= 0.70  # 70% minimum
        }
        
        print(f"\n🏆 EVALUATION:")
        all_passed = True
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} {criterion.replace('_', ' ').title()}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 SUCCESS! The fix resolved the confidence issue.")
            print(f"   Category 3 document now gets {confidence*100:.1f}% confidence")
            print(f"   (vs. the original 22% false negative)")
        else:
            print(f"\n⚠️  Some issues remain - may need further refinement")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_core_analysis()
    print(f"\n{'='*50}")
    print(f"RESULT: {'SUCCESS' if success else 'NEEDS MORE WORK'}")
    print(f"{'='*50}")