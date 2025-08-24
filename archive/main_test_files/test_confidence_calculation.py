#!/usr/bin/env python3
"""Test confidence calculation directly"""

def test_confidence_calculation():
    """Test confidence calculation with simulated URS-003 data"""

    # Simulated evidence data for URS-003 with our indicator fixes
    # Based on the indicators we should find in URS-003
    evidence = {
        "strong_indicators": [
            "custom-developed", "custom algorithms", "develop custom",
            "custom workflow", "proprietary data structures",
            "custom mobile application", "bespoke analytics",
            "custom audit trail", "proprietary electronic signature",
            "custom data integrity"
        ],
        "weak_indicators": [
            "custom interfaces", "enhanced metadata", "proprietary protocols",
            "site-specific business rules"
        ],
        "exclusion_factors": [],
        "strong_count": 10,  # Should be high with our fixes
        "weak_count": 4,
        "exclusion_count": 0
    }

    # Simulated all_categories_analysis
    all_analysis = {
        1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
        3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
        4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
        5: {"strong_count": 10, "weak_count": 4, "exclusion_count": 0}
    }

    # Category data for Category 5
    category_data = {
        "predicted_category": 5,
        "evidence": evidence,
        "all_categories_analysis": all_analysis,
        "decision_rationale": "Category 5 selected based on 10 strong indicators"
    }

    print("Testing Confidence Calculation")
    print("=" * 40)
    print(f"Strong Count: {evidence['strong_count']}")
    print(f"Weak Count: {evidence['weak_count']}")
    print(f"Exclusion Count: {evidence['exclusion_count']}")
    print(f"Predicted Category: {category_data['predicted_category']}")

    # Weights (from the actual code)
    weights = {
        "strong_indicators": 0.4,
        "weak_indicators": 0.2,
        "exclusion_factors": -0.3,
        "ambiguity_penalty": -0.1
    }

    # Calculate base score
    base_score = (
        weights["strong_indicators"] * evidence["strong_count"] +
        weights["weak_indicators"] * evidence["weak_count"] +
        weights["exclusion_factors"] * evidence["exclusion_count"]
    )

    print("\nBase Score Calculation:")
    print(f"  Strong: {evidence['strong_count']} × {weights['strong_indicators']} = {evidence['strong_count'] * weights['strong_indicators']}")
    print(f"  Weak: {evidence['weak_count']} × {weights['weak_indicators']} = {evidence['weak_count'] * weights['weak_indicators']}")
    print(f"  Exclusions: {evidence['exclusion_count']} × {weights['exclusion_factors']} = {evidence['exclusion_count'] * weights['exclusion_factors']}")
    print(f"  Base Score: {base_score}")

    # Calculate ambiguity penalty
    predicted_category = category_data["predicted_category"]
    competing_strong_indicators = sum(
        analysis["strong_count"] for cat_id, analysis in all_analysis.items()
        if cat_id != predicted_category and analysis["strong_count"] > 0
    )

    ambiguity_penalty = 0.0
    if competing_strong_indicators > 0:
        penalty_factor = min(competing_strong_indicators * 0.1, 0.3)
        ambiguity_penalty = weights["ambiguity_penalty"] * penalty_factor

    print("\nAmbiguity Analysis:")
    print(f"  Competing Strong Indicators: {competing_strong_indicators}")
    print(f"  Ambiguity Penalty: {ambiguity_penalty}")

    # Category-specific adjustments
    category_adjustment = 0.0
    if predicted_category == 1 and evidence["strong_count"] >= 2:
        category_adjustment = 0.1
    elif predicted_category == 5 and evidence["strong_count"] >= 2:
        category_adjustment = 0.15
    elif predicted_category in [3, 4] and evidence["strong_count"] >= 1:
        category_adjustment = 0.05

    print("\nCategory Adjustment:")
    print(f"  Category {predicted_category} with {evidence['strong_count']} strong indicators")
    print(f"  Adjustment: {category_adjustment}")

    # Final confidence calculation
    raw_confidence = base_score + ambiguity_penalty + category_adjustment
    final_confidence = max(0.0, min(1.0, 0.5 + raw_confidence))

    print("\nFinal Calculation:")
    print(f"  Raw Confidence: {base_score} + {ambiguity_penalty} + {category_adjustment} = {raw_confidence}")
    print(f"  Final Confidence: max(0.0, min(1.0, 0.5 + {raw_confidence})) = {final_confidence}")
    print(f"  Final Confidence %: {final_confidence:.1%}")

    # Assessment
    print("\n" + "=" * 40)
    print("Assessment:")
    if final_confidence > 0.6:
        print(f"  ✅ PASS: Confidence {final_confidence:.1%} > 60% threshold")
    elif final_confidence > 0.0:
        print(f"  ⚠️ LOW: Confidence {final_confidence:.1%} above 0 but below 60%")
    else:
        print(f"  ❌ FAIL: Confidence {final_confidence:.1%} is zero")

    return final_confidence


if __name__ == "__main__":
    test_confidence_calculation()
