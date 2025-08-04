#!/usr/bin/env python3
"""Minimal test of GAMP analysis tool with our fixes"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up minimal environment to avoid import errors
import os
os.environ.setdefault("OPENAI_API_KEY", "dummy")

# URS-003 content for testing
URS003_CONTENT = """
## URS-003: Manufacturing Execution System (MES)
**Target Category**: 5 (Clear)
**System Type**: Custom Batch Record Management System

### 1. Introduction
This URS defines requirements for a custom MES to manage electronic batch records for sterile injectable products.

### 2. Functional Requirements
- **URS-MES-001**: System shall be custom-developed to integrate with proprietary equipment.
- **URS-MES-002**: Custom algorithms required for:
  - Dynamic in-process control limits based on multivariate analysis
  - Real-time batch genealogy tracking across multiple unit operations
  - Proprietary yield optimization calculations
- **URS-MES-003**: Develop custom interfaces for:
  - 12 different equipment types with proprietary protocols
  - Integration with custom warehouse management system
  - Real-time data exchange with proprietary PAT systems
- **URS-MES-004**: Custom workflow engine to handle:
  - Parallel processing paths unique to our manufacturing process
  - Complex exception handling for deviations
  - Site-specific business rules not supported by commercial packages
- **URS-MES-005**: Develop proprietary data structures for:
  - Multi-level bill of materials with conditional components
  - Process parameters with complex interdependencies
- **URS-MES-006**: Custom mobile application for shop floor data entry.
- **URS-MES-007**: Bespoke analytics module for real-time process monitoring.

### 3. Regulatory Requirements
- **URS-MES-008**: Custom audit trail implementation with enhanced metadata.
- **URS-MES-009**: Develop proprietary electronic signature workflow.
- **URS-MES-010**: Custom data integrity checks beyond standard validations.
"""

def test_gamp_analysis():
    """Test the GAMP analysis tool directly"""
    
    try:
        from src.agents.categorization.agent import gamp_analysis_tool, confidence_tool
        
        print("Testing GAMP Analysis Tool with URS-003")
        print("Expected: Category 5")
        print("=" * 60)
        
        # Step 1: Run GAMP analysis
        print("\n1. Running GAMP Analysis...")
        result = gamp_analysis_tool(URS003_CONTENT)
        
        print(f"   Predicted Category: {result['predicted_category']}")
        print(f"   Decision Rationale: {result['decision_rationale']}")
        
        # Show Category 5 evidence
        cat5_evidence = result['all_categories_analysis'][5]
        print(f"\n   Category 5 Evidence:")
        print(f"   - Strong Count: {cat5_evidence['strong_count']}")
        print(f"   - Strong Indicators: {cat5_evidence['strong_indicators']}")
        print(f"   - Weak Count: {cat5_evidence['weak_count']}")
        print(f"   - Weak Indicators: {cat5_evidence['weak_indicators']}")
        
        # Step 2: Calculate confidence
        print(f"\n2. Calculating Confidence...")
        confidence = confidence_tool(result)
        print(f"   Confidence Score: {confidence:.3f} ({confidence:.1%})")
        
        # Step 3: Assessment
        print(f"\n3. Assessment:")
        if result['predicted_category'] == 5:
            print("   ✅ CATEGORY: Correctly predicted Category 5")
        else:
            print(f"   ❌ CATEGORY: Wrong prediction - got {result['predicted_category']}, expected 5")
            
        if confidence > 0.6:
            print(f"   ✅ CONFIDENCE: Good confidence {confidence:.1%} > 60%")
        elif confidence > 0.0:
            print(f"   ⚠️ CONFIDENCE: Low confidence {confidence:.1%} (0% < conf < 60%)")
        else:
            print(f"   ❌ CONFIDENCE: Zero confidence {confidence:.1%}")
            
        # Overall result
        print(f"\n" + "=" * 60)
        if result['predicted_category'] == 5 and confidence > 0.0:
            print("🎉 SUCCESS: Fix appears to be working!")
        else:
            print("❌ ISSUES REMAIN: Need further debugging")
            
        return result, confidence
        
    except ImportError as e:
        print(f"Import error: {e}")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    test_gamp_analysis()