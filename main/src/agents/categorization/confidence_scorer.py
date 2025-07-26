"""
Enhanced Confidence Scoring Module for GAMP-5 Categorization

This module provides advanced confidence scoring with detailed traceability
for pharmaceutical validation compliance (21 CFR Part 11, GAMP-5).

Features:
- Detailed scoring breakdown for audit trails
- Calibrated confidence scores
- Uncertainty quantification
- Traceable decision rationale
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Confidence level categories for decision support."""
    HIGH = "high"          # ≥ 0.85 - Automatic classification
    MEDIUM = "medium"      # 0.60-0.85 - Flag for review
    LOW = "low"           # < 0.60 - Human intervention required


@dataclass
class ScoringComponent:
    """Individual component of confidence scoring for traceability."""
    name: str
    value: float
    weight: float
    contribution: float
    rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "contribution": self.contribution,
            "rationale": self.rationale
        }


@dataclass
class ConfidenceScoreResult:
    """Complete confidence scoring result with full traceability."""
    final_score: float
    confidence_level: ConfidenceLevel
    components: List[ScoringComponent] = field(default_factory=list)
    adjustments: List[ScoringComponent] = field(default_factory=list)
    uncertainty_factors: List[str] = field(default_factory=list)
    requires_review: bool = False
    review_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    scoring_version: str = "2.0"
    
    def get_audit_trail(self) -> Dict[str, Any]:
        """Generate complete audit trail for regulatory compliance."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "scoring_version": self.scoring_version,
            "final_score": self.final_score,
            "confidence_level": self.confidence_level.value,
            "requires_review": self.requires_review,
            "review_reason": self.review_reason,
            "components": [c.to_dict() for c in self.components],
            "adjustments": [a.to_dict() for a in self.adjustments],
            "uncertainty_factors": self.uncertainty_factors,
            "calculation_summary": self._generate_calculation_summary()
        }
    
    def _generate_calculation_summary(self) -> str:
        """Generate human-readable calculation summary."""
        summary_parts = [
            f"Base Score Calculation:",
            f"  Components:"
        ]
        
        for comp in self.components:
            summary_parts.append(
                f"    - {comp.name}: {comp.value} × {comp.weight} = {comp.contribution:.3f}"
            )
        
        base_total = sum(c.contribution for c in self.components)
        summary_parts.append(f"  Base Total: {base_total:.3f}")
        
        if self.adjustments:
            summary_parts.append(f"\nAdjustments:")
            for adj in self.adjustments:
                summary_parts.append(
                    f"  - {adj.name}: {adj.contribution:+.3f} ({adj.rationale})"
                )
        
        summary_parts.append(f"\nFinal Score: {self.final_score:.3f}")
        summary_parts.append(f"Confidence Level: {self.confidence_level.value.upper()}")
        
        return "\n".join(summary_parts)


class EnhancedConfidenceScorer:
    """
    Enhanced confidence scoring system for GAMP-5 categorization.
    
    Provides detailed, traceable confidence scores with full audit trail
    capability for pharmaceutical validation compliance.
    """
    
    # Default weights based on pharmaceutical validation best practices
    DEFAULT_WEIGHTS = {
        'strong_indicators': 0.4,
        'weak_indicators': 0.2,
        'exclusion_factors': -0.3,
        'ambiguity_penalty': -0.1,
        'evidence_quality': 0.15,
        'consistency_bonus': 0.05
    }
    
    # Confidence thresholds aligned with GAMP-5 risk levels
    CONFIDENCE_THRESHOLDS = {
        'high': 0.85,      # Low risk - automatic classification
        'medium': 0.60,    # Medium risk - review recommended
        'low': 0.0         # High risk - manual intervention required
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 calibration_data: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced confidence scorer.
        
        Args:
            weights: Custom scoring weights (uses defaults if None)
            calibration_data: Historical performance data for calibration
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.calibration_data = calibration_data or {}
        self.scoring_history: List[ConfidenceScoreResult] = []
    
    def calculate_confidence(
        self, 
        category_data: Dict[str, Any],
        include_advanced_features: bool = True
    ) -> ConfidenceScoreResult:
        """
        Calculate confidence score with detailed traceability.
        
        Args:
            category_data: Output from gamp_analysis_tool
            include_advanced_features: Whether to include advanced scoring features
            
        Returns:
            ConfidenceScoreResult with complete scoring breakdown
        """
        result = ConfidenceScoreResult(final_score=0.0, confidence_level=ConfidenceLevel.LOW)
        
        # Extract evidence
        evidence = category_data["evidence"]
        all_analysis = category_data["all_categories_analysis"]
        predicted_category = category_data["predicted_category"]
        
        # 1. Calculate base components
        result.components.extend(self._calculate_base_components(evidence))
        
        # 2. Calculate ambiguity penalty
        ambiguity_component = self._calculate_ambiguity_penalty(
            predicted_category, all_analysis
        )
        if ambiguity_component:
            result.components.append(ambiguity_component)
        
        # 3. Add advanced features if enabled
        if include_advanced_features:
            # Evidence quality assessment
            quality_component = self._assess_evidence_quality(evidence)
            if quality_component:
                result.adjustments.append(quality_component)
            
            # Consistency check
            consistency_component = self._check_consistency(evidence, predicted_category)
            if consistency_component:
                result.adjustments.append(consistency_component)
        
        # 4. Category-specific adjustments
        category_adjustment = self._get_category_adjustment(predicted_category, evidence)
        if category_adjustment:
            result.adjustments.append(category_adjustment)
        
        # 5. Calculate final score
        base_score = sum(c.contribution for c in result.components)
        adjustment_score = sum(a.contribution for a in result.adjustments)
        raw_score = base_score + adjustment_score
        
        # Normalize to [0, 1] range
        result.final_score = max(0.0, min(1.0, 0.5 + raw_score))
        
        # 6. Apply calibration if available
        if self.calibration_data:
            result.final_score = self._apply_calibration(result.final_score, predicted_category)
        
        # 7. Determine confidence level and review requirements
        result.confidence_level = self._determine_confidence_level(result.final_score)
        result.requires_review, result.review_reason = self._check_review_requirements(
            result, evidence, predicted_category
        )
        
        # 8. Identify uncertainty factors
        result.uncertainty_factors = self._identify_uncertainty_factors(
            evidence, all_analysis, predicted_category
        )
        
        # Store in history for performance tracking
        self.scoring_history.append(result)
        
        return result
    
    def _calculate_base_components(self, evidence: Dict[str, Any]) -> List[ScoringComponent]:
        """Calculate base scoring components."""
        components = []
        
        # Strong indicators
        if evidence['strong_count'] > 0:
            components.append(ScoringComponent(
                name="Strong Indicators",
                value=evidence['strong_count'],
                weight=self.weights['strong_indicators'],
                contribution=evidence['strong_count'] * self.weights['strong_indicators'],
                rationale=f"Found {evidence['strong_count']} strong indicator(s): {', '.join(evidence['strong_indicators'][:3])}"
            ))
        
        # Weak indicators
        if evidence['weak_count'] > 0:
            components.append(ScoringComponent(
                name="Weak Indicators",
                value=evidence['weak_count'],
                weight=self.weights['weak_indicators'],
                contribution=evidence['weak_count'] * self.weights['weak_indicators'],
                rationale=f"Found {evidence['weak_count']} supporting indicator(s)"
            ))
        
        # Exclusion factors
        if evidence['exclusion_count'] > 0:
            components.append(ScoringComponent(
                name="Exclusion Factors",
                value=evidence['exclusion_count'],
                weight=self.weights['exclusion_factors'],
                contribution=evidence['exclusion_count'] * self.weights['exclusion_factors'],
                rationale=f"Found {evidence['exclusion_count']} conflicting indicator(s): {', '.join(evidence['exclusion_factors'][:2])}"
            ))
        
        return components
    
    def _calculate_ambiguity_penalty(
        self, 
        predicted_category: int, 
        all_analysis: Dict[int, Dict[str, Any]]
    ) -> Optional[ScoringComponent]:
        """Calculate penalty for ambiguous categorization."""
        competing_strong = sum(
            analysis["strong_count"] 
            for cat_id, analysis in all_analysis.items()
            if cat_id != predicted_category and analysis["strong_count"] > 0
        )
        
        if competing_strong > 0:
            penalty_factor = min(competing_strong * 0.1, 0.3)
            contribution = self.weights['ambiguity_penalty'] * penalty_factor
            
            competing_categories = [
                str(cat_id) for cat_id, analysis in all_analysis.items()
                if cat_id != predicted_category and analysis["strong_count"] > 0
            ]
            
            return ScoringComponent(
                name="Ambiguity Penalty",
                value=penalty_factor,
                weight=self.weights['ambiguity_penalty'],
                contribution=contribution,
                rationale=f"Competing evidence for category/categories: {', '.join(competing_categories)}"
            )
        
        return None
    
    def _assess_evidence_quality(self, evidence: Dict[str, Any]) -> Optional[ScoringComponent]:
        """Assess quality of evidence for advanced scoring."""
        quality_score = 0.0
        rationale_parts = []
        
        # Check evidence diversity
        total_indicators = evidence['strong_count'] + evidence['weak_count']
        if total_indicators >= 3:
            quality_score += 0.5
            rationale_parts.append("diverse evidence")
        
        # Check for clear signals (high strong/weak ratio)
        if evidence['strong_count'] > 0 and evidence['weak_count'] > 0:
            ratio = evidence['strong_count'] / (evidence['strong_count'] + evidence['weak_count'])
            if ratio > 0.7:
                quality_score += 0.5
                rationale_parts.append(f"clear signal (ratio: {ratio:.2f})")
        
        if quality_score > 0:
            return ScoringComponent(
                name="Evidence Quality",
                value=quality_score,
                weight=self.weights.get('evidence_quality', 0.15),
                contribution=quality_score * self.weights.get('evidence_quality', 0.15),
                rationale=f"High quality evidence: {', '.join(rationale_parts)}"
            )
        
        return None
    
    def _check_consistency(self, evidence: Dict[str, Any], predicted_category: int) -> Optional[ScoringComponent]:
        """Check for internal consistency in categorization."""
        consistency_score = 0.0
        rationale_parts = []
        
        # Check if exclusions align with category
        if predicted_category in [1, 3, 4] and evidence['exclusion_count'] == 0:
            consistency_score += 1.0
            rationale_parts.append("no conflicting indicators")
        elif predicted_category == 5 and evidence['exclusion_count'] > 0:
            consistency_score += 0.5
            rationale_parts.append("exclusions support custom category")
        
        if consistency_score > 0:
            return ScoringComponent(
                name="Consistency Bonus",
                value=consistency_score,
                weight=self.weights.get('consistency_bonus', 0.05),
                contribution=consistency_score * self.weights.get('consistency_bonus', 0.05),
                rationale=f"Consistent categorization: {', '.join(rationale_parts)}"
            )
        
        return None
    
    def _get_category_adjustment(self, predicted_category: int, evidence: Dict[str, Any]) -> Optional[ScoringComponent]:
        """Apply category-specific confidence adjustments."""
        adjustment = 0.0
        rationale = ""
        
        if predicted_category == 1 and evidence['strong_count'] >= 2:
            adjustment = 0.1
            rationale = "Strong infrastructure evidence"
        elif predicted_category == 5 and evidence['strong_count'] >= 2:
            adjustment = 0.15
            rationale = "Clear custom development indicators"
        elif predicted_category in [3, 4] and evidence['strong_count'] >= 1:
            adjustment = 0.05
            rationale = "Adequate commercial software evidence"
        
        if adjustment > 0:
            return ScoringComponent(
                name=f"Category {predicted_category} Adjustment",
                value=1.0,
                weight=adjustment,
                contribution=adjustment,
                rationale=rationale
            )
        
        return None
    
    def _apply_calibration(self, raw_score: float, category: int) -> float:
        """Apply calibration based on historical performance data."""
        # Placeholder for calibration logic
        # In practice, this would use isotonic regression or similar
        return raw_score
    
    def _determine_confidence_level(self, score: float) -> ConfidenceLevel:
        """Determine confidence level based on score."""
        if score >= self.CONFIDENCE_THRESHOLDS['high']:
            return ConfidenceLevel.HIGH
        elif score >= self.CONFIDENCE_THRESHOLDS['medium']:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _check_review_requirements(
        self, 
        result: ConfidenceScoreResult,
        evidence: Dict[str, Any],
        predicted_category: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if human review is required."""
        reasons = []
        
        # Low confidence always requires review
        if result.confidence_level == ConfidenceLevel.LOW:
            reasons.append("Low confidence score")
        
        # Medium confidence may require review
        elif result.confidence_level == ConfidenceLevel.MEDIUM:
            reasons.append("Medium confidence - verification recommended")
        
        # High-risk categories require review even with high confidence
        if predicted_category == 5 and result.final_score < 0.95:
            reasons.append("Category 5 (custom) requires validation")
        
        # Significant ambiguity
        if any(c.name == "Ambiguity Penalty" and c.contribution < -0.1 for c in result.components):
            reasons.append("Significant ambiguity detected")
        
        # Many exclusion factors
        if evidence['exclusion_count'] >= 3:
            reasons.append(f"High exclusion count ({evidence['exclusion_count']})")
        
        requires_review = len(reasons) > 0
        review_reason = "; ".join(reasons) if reasons else None
        
        return requires_review, review_reason
    
    def _identify_uncertainty_factors(
        self,
        evidence: Dict[str, Any],
        all_analysis: Dict[int, Dict[str, Any]],
        predicted_category: int
    ) -> List[str]:
        """Identify factors contributing to uncertainty."""
        factors = []
        
        # Limited evidence
        total_evidence = evidence['strong_count'] + evidence['weak_count']
        if total_evidence < 2:
            factors.append("Limited evidence available")
        
        # Competing categories
        competing = [
            cat_id for cat_id, analysis in all_analysis.items()
            if cat_id != predicted_category and analysis["strong_count"] > 0
        ]
        if competing:
            factors.append(f"Competing evidence for categories: {competing}")
        
        # Exclusion factors present
        if evidence['exclusion_count'] > 0:
            factors.append(f"Conflicting indicators present: {evidence['exclusion_factors']}")
        
        # Weak evidence dominance
        if evidence['weak_count'] > evidence['strong_count'] * 2:
            factors.append("Predominantly weak evidence")
        
        return factors
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from scoring history."""
        if not self.scoring_history:
            return {"message": "No scoring history available"}
        
        total_scores = len(self.scoring_history)
        avg_confidence = sum(r.final_score for r in self.scoring_history) / total_scores
        
        level_distribution = {
            "high": sum(1 for r in self.scoring_history if r.confidence_level == ConfidenceLevel.HIGH),
            "medium": sum(1 for r in self.scoring_history if r.confidence_level == ConfidenceLevel.MEDIUM),
            "low": sum(1 for r in self.scoring_history if r.confidence_level == ConfidenceLevel.LOW)
        }
        
        review_rate = sum(1 for r in self.scoring_history if r.requires_review) / total_scores
        
        return {
            "total_scores": total_scores,
            "average_confidence": avg_confidence,
            "confidence_distribution": level_distribution,
            "review_rate": review_rate,
            "scoring_version": self.scoring_history[-1].scoring_version if self.scoring_history else "2.0"
        }


# Backward compatibility wrapper
def enhanced_confidence_tool(category_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced confidence tool with full traceability.
    
    Wrapper function that provides backward compatibility while adding
    enhanced features for pharmaceutical validation compliance.
    """
    scorer = EnhancedConfidenceScorer()
    result = scorer.calculate_confidence(category_data)
    
    return {
        "confidence_score": result.final_score,
        "confidence_level": result.confidence_level.value,
        "requires_review": result.requires_review,
        "review_reason": result.review_reason,
        "audit_trail": result.get_audit_trail(),
        "calculation_summary": result._generate_calculation_summary()
    }