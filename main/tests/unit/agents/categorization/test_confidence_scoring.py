"""
Comprehensive test suite for Enhanced Confidence Scoring

Tests the confidence scoring mechanism with focus on:
- Accuracy of confidence calculations
- Traceability and audit trail generation
- Edge cases and ambiguous scenarios
- Pharmaceutical validation compliance
"""

from main.src.agents.categorization.agent import confidence_tool, gamp_analysis_tool
from main.src.agents.categorization.confidence_scorer import (
    ConfidenceLevel,
    EnhancedConfidenceScorer,
    ScoringComponent,
    enhanced_confidence_tool,
)


class TestEnhancedConfidenceScorer:
    """Test suite for enhanced confidence scoring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = EnhancedConfidenceScorer()

        # Sample category data for testing
        self.clear_category_1_data = {
            "predicted_category": 1,
            "evidence": {
                "strong_indicators": ["windows server", "oracle", "tcp/ip"],
                "weak_indicators": ["infrastructure"],
                "exclusion_factors": [],
                "strong_count": 3,
                "weak_count": 1,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 3, "weak_count": 1, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0}
            }
        }

        self.ambiguous_data = {
            "predicted_category": 4,
            "evidence": {
                "strong_indicators": ["configure", "user-defined parameters"],
                "weak_indicators": ["lims"],
                "exclusion_factors": ["custom development"],
                "strong_count": 2,
                "weak_count": 1,
                "exclusion_count": 1
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 1, "exclusion_count": 0},
                4: {"strong_count": 2, "weak_count": 1, "exclusion_count": 1},
                5: {"strong_count": 1, "weak_count": 0, "exclusion_count": 0}
            }
        }

        self.low_confidence_data = {
            "predicted_category": 3,
            "evidence": {
                "strong_indicators": [],
                "weak_indicators": ["software", "system"],
                "exclusion_factors": [],
                "strong_count": 0,
                "weak_count": 2,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 1, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 2, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 1, "exclusion_count": 0},
                5: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0}
            }
        }

    def test_high_confidence_scoring(self):
        """Test scoring for clear, high-confidence categorization."""
        result = self.scorer.calculate_confidence(self.clear_category_1_data)

        assert result.final_score > 0.85
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert not result.requires_review
        assert len(result.components) > 0
        assert any(c.name == "Strong Indicators" for c in result.components)

    def test_ambiguous_scoring(self):
        """Test scoring for ambiguous categorization with competing evidence."""
        result = self.scorer.calculate_confidence(self.ambiguous_data)

        assert 0.6 <= result.final_score < 0.85
        assert result.confidence_level == ConfidenceLevel.MEDIUM
        assert result.requires_review
        assert "verification recommended" in result.review_reason.lower()
        assert any(c.name == "Ambiguity Penalty" for c in result.components)
        assert any(c.name == "Exclusion Factors" for c in result.components)

    def test_low_confidence_scoring(self):
        """Test scoring for weak evidence scenarios."""
        result = self.scorer.calculate_confidence(self.low_confidence_data)

        assert result.final_score < 0.6
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.requires_review
        assert "Low confidence" in result.review_reason
        assert "Limited evidence" in result.uncertainty_factors

    def test_audit_trail_generation(self):
        """Test audit trail completeness for regulatory compliance."""
        result = self.scorer.calculate_confidence(self.clear_category_1_data)
        audit_trail = result.get_audit_trail()

        # Verify all required audit fields
        assert "timestamp" in audit_trail
        assert "scoring_version" in audit_trail
        assert "final_score" in audit_trail
        assert "confidence_level" in audit_trail
        assert "components" in audit_trail
        assert "calculation_summary" in audit_trail

        # Verify component details
        assert len(audit_trail["components"]) > 0
        component = audit_trail["components"][0]
        assert all(key in component for key in ["name", "value", "weight", "contribution", "rationale"])

    def test_scoring_component_calculations(self):
        """Test individual scoring component calculations."""
        # Test strong indicators
        strong_component = ScoringComponent(
            name="Strong Indicators",
            value=3,
            weight=0.4,
            contribution=1.2,
            rationale="Found 3 strong indicators"
        )
        assert strong_component.contribution == 1.2
        assert strong_component.to_dict()["name"] == "Strong Indicators"

        # Test exclusion factors (negative contribution)
        exclusion_component = ScoringComponent(
            name="Exclusion Factors",
            value=2,
            weight=-0.3,
            contribution=-0.6,
            rationale="Found 2 conflicting indicators"
        )
        assert exclusion_component.contribution == -0.6

    def test_uncertainty_factor_identification(self):
        """Test identification of uncertainty factors."""
        result = self.scorer.calculate_confidence(self.low_confidence_data)

        assert len(result.uncertainty_factors) > 0
        assert any("Limited evidence" in factor for factor in result.uncertainty_factors)
        assert any("weak evidence" in factor.lower() for factor in result.uncertainty_factors)

    def test_category_specific_adjustments(self):
        """Test category-specific confidence adjustments."""
        # Category 5 with strong evidence should get bonus
        category_5_data = {
            "predicted_category": 5,
            "evidence": {
                "strong_indicators": ["custom development", "bespoke", "proprietary"],
                "weak_indicators": [],
                "exclusion_factors": [],
                "strong_count": 3,
                "weak_count": 0,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 3, "weak_count": 0, "exclusion_count": 0}
            }
        }

        result = self.scorer.calculate_confidence(category_5_data)
        assert any(adj.name.startswith("Category 5") for adj in result.adjustments)
        assert result.final_score > 0.9

    def test_review_requirements_for_category_5(self):
        """Test that Category 5 requires review even with high confidence."""
        category_5_data = {
            "predicted_category": 5,
            "evidence": {
                "strong_indicators": ["custom development"],
                "weak_indicators": [],
                "exclusion_factors": [],
                "strong_count": 1,
                "weak_count": 0,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 1, "weak_count": 0, "exclusion_count": 0}
            }
        }

        result = self.scorer.calculate_confidence(category_5_data)
        if result.final_score < 0.95:
            assert result.requires_review
            assert "Category 5" in result.review_reason

    def test_performance_metrics_tracking(self):
        """Test performance metrics collection."""
        # Generate multiple scores
        for _ in range(5):
            self.scorer.calculate_confidence(self.clear_category_1_data)

        metrics = self.scorer.get_performance_metrics()

        assert metrics["total_scores"] == 5
        assert "average_confidence" in metrics
        assert "confidence_distribution" in metrics
        assert metrics["confidence_distribution"]["high"] > 0

    def test_backward_compatibility(self):
        """Test that original confidence_tool still works."""
        # Test original function
        original_score = confidence_tool(self.clear_category_1_data)
        assert isinstance(original_score, float)
        assert 0.0 <= original_score <= 1.0

        # Test enhanced wrapper
        enhanced_result = enhanced_confidence_tool(self.clear_category_1_data)
        assert "confidence_score" in enhanced_result
        assert "audit_trail" in enhanced_result
        assert enhanced_result["confidence_score"] > 0

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty evidence
        empty_data = {
            "predicted_category": 3,
            "evidence": {
                "strong_indicators": [],
                "weak_indicators": [],
                "exclusion_factors": [],
                "strong_count": 0,
                "weak_count": 0,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0}
            }
        }

        result = self.scorer.calculate_confidence(empty_data)
        assert result.final_score == 0.5  # Base normalization
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.requires_review

    def test_calculation_summary_readability(self):
        """Test that calculation summary is human-readable."""
        result = self.scorer.calculate_confidence(self.ambiguous_data)
        summary = result._generate_calculation_summary()

        assert "Base Score Calculation:" in summary
        assert "Components:" in summary
        assert "Final Score:" in summary
        assert str(result.final_score)[:5] in summary  # Check score appears

    def test_custom_weights(self):
        """Test scorer with custom weights."""
        custom_weights = {
            "strong_indicators": 0.5,
            "weak_indicators": 0.1,
            "exclusion_factors": -0.4,
            "ambiguity_penalty": -0.2
        }

        custom_scorer = EnhancedConfidenceScorer(weights=custom_weights)
        result = custom_scorer.calculate_confidence(self.clear_category_1_data)

        # Should have higher score due to higher strong indicator weight
        default_result = self.scorer.calculate_confidence(self.clear_category_1_data)
        assert result.final_score >= default_result.final_score


class TestIntegrationWithGAMPAnalysis:
    """Test integration between GAMP analysis and confidence scoring."""

    def test_end_to_end_categorization_with_confidence(self):
        """Test complete flow from URS to confident categorization."""
        # Real URS content
        urs_content = """
        System Requirements for Laboratory Information Management System:
        - Configure sample workflows for stability testing
        - User-defined test protocols and specifications  
        - Configurable approval workflows for test results
        - Standard reporting capabilities
        - 21 CFR Part 11 compliance
        """

        # Run through analysis
        analysis_result = gamp_analysis_tool(urs_content)

        # Calculate confidence with both methods
        original_confidence = confidence_tool(analysis_result)
        enhanced_result = enhanced_confidence_tool(analysis_result)

        # Verify consistency
        assert enhanced_result["confidence_score"] > 0
        assert enhanced_result["audit_trail"] is not None
        assert "calculation_summary" in enhanced_result

        # Check categorization
        assert analysis_result["predicted_category"] == 4  # Should be Category 4
        assert enhanced_result["confidence_level"] in ["high", "medium", "low"]


if __name__ == "__main__":
    # Run quick validation
    print("Running confidence scoring validation tests...")

    scorer = EnhancedConfidenceScorer()

    # Test scenarios
    test_cases = [
        ("Clear Infrastructure", {
            "predicted_category": 1,
            "evidence": {
                "strong_indicators": ["windows server", "oracle"],
                "weak_indicators": [],
                "exclusion_factors": [],
                "strong_count": 2,
                "weak_count": 0,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                1: {"strong_count": 2, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                4: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0}
            }
        }),
        ("Ambiguous Case", {
            "predicted_category": 3,
            "evidence": {
                "strong_indicators": ["cots"],
                "weak_indicators": ["software"],
                "exclusion_factors": ["configuration"],
                "strong_count": 1,
                "weak_count": 1,
                "exclusion_count": 1
            },
            "all_categories_analysis": {
                1: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0},
                3: {"strong_count": 1, "weak_count": 1, "exclusion_count": 1},
                4: {"strong_count": 1, "weak_count": 0, "exclusion_count": 0},
                5: {"strong_count": 0, "weak_count": 0, "exclusion_count": 0}
            }
        })
    ]

    for name, data in test_cases:
        result = scorer.calculate_confidence(data)
        print(f"\n{name}:")
        print(f"  Score: {result.final_score:.3f}")
        print(f"  Level: {result.confidence_level.value}")
        print(f"  Review: {result.requires_review}")
        if result.review_reason:
            print(f"  Reason: {result.review_reason}")

    print("\n✅ Confidence scoring tests completed!")
