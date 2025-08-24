#!/usr/bin/env uv run python
"""
FDA Part 11 Q&A Questions for Context Provider Agent Testing

This module contains targeted questions designed to test the Context Provider Agent's
ability to retrieve relevant information from the FDA Part 11 document and demonstrate
comprehensive Phoenix observability tracing.
"""

from typing import Any


class FDApart11Questions:
    """Container for FDA Part 11 test questions with expected answer validation."""

    @staticmethod
    def get_test_questions() -> list[dict[str, Any]]:
        """
        Get comprehensive list of FDA Part 11 test questions.
        
        Returns:
            List of question dictionaries with metadata for testing and validation
        """
        return [
            {
                "id": "q1_scope_narrow_interpretation",
                "category": "Scope and Application",
                "question": "What is FDA's narrow interpretation of Part 11 scope and when does Part 11 apply to electronic records?",
                "expected_concepts": [
                    "narrow interpretation",
                    "electronic format in place of paper format",
                    "predicate rule requirements",
                    "rely on electronic records",
                    "business practices"
                ],
                "context_depth": "comprehensive",
                "search_sections": ["scope", "application", "narrow_interpretation", "electronic_records"],
                "gamp_category": "4",
                "test_strategy": {
                    "validation_type": "regulatory_scope_analysis",
                    "focus_area": "part11_scope_definition"
                },
                "expected_confidence_min": 0.75,
                "complexity": "medium"
            },

            {
                "id": "q2_validation_enforcement_discretion",
                "category": "Validation Requirements",
                "question": "What is FDA's current enforcement approach regarding validation requirements for computerized systems under Part 11?",
                "expected_concepts": [
                    "enforcement discretion",
                    "validation of computerized systems",
                    "predicate rule requirements",
                    "risk assessment",
                    "justified and documented"
                ],
                "context_depth": "detailed",
                "search_sections": ["validation", "enforcement", "computerized_systems", "risk_assessment"],
                "gamp_category": "4",
                "test_strategy": {
                    "validation_type": "validation_approach_analysis",
                    "focus_area": "enforcement_discretion"
                },
                "expected_confidence_min": 0.80,
                "complexity": "high"
            },

            {
                "id": "q3_audit_trail_requirements",
                "category": "Audit Trail and Security",
                "question": "Under what circumstances does FDA exercise enforcement discretion for audit trail requirements, and what controls should still be maintained?",
                "expected_concepts": [
                    "audit trail",
                    "computer-generated, time-stamped",
                    "enforcement discretion",
                    "predicate rule requirements",
                    "trustworthiness and integrity"
                ],
                "context_depth": "comprehensive",
                "search_sections": ["audit_trail", "security", "enforcement", "integrity"],
                "gamp_category": "4",
                "test_strategy": {
                    "validation_type": "audit_trail_analysis",
                    "focus_area": "security_controls"
                },
                "expected_confidence_min": 0.70,
                "complexity": "high"
            },

            {
                "id": "q4_legacy_systems_criteria",
                "category": "Legacy Systems",
                "question": "What are the specific criteria that legacy systems must meet to qualify for Part 11 enforcement discretion?",
                "expected_concepts": [
                    "legacy systems",
                    "operational before August 20, 1997",
                    "predicate rule requirements",
                    "documented evidence",
                    "fit for intended use"
                ],
                "context_depth": "detailed",
                "search_sections": ["legacy_systems", "criteria", "enforcement", "operational"],
                "gamp_category": "3",
                "test_strategy": {
                    "validation_type": "legacy_system_analysis",
                    "focus_area": "grandfathering_criteria"
                },
                "expected_confidence_min": 0.85,
                "complexity": "medium"
            },

            {
                "id": "q5_electronic_signatures_definition",
                "category": "Electronic Signatures",
                "question": "How does Part 11 define electronic signatures and what makes them equivalent to handwritten signatures?",
                "expected_concepts": [
                    "electronic signatures",
                    "equivalent of handwritten signatures",
                    "initials and other general signings",
                    "predicate rules",
                    "approved, reviewed, and verified"
                ],
                "context_depth": "standard",
                "search_sections": ["electronic_signatures", "handwritten", "equivalent", "predicate_rules"],
                "gamp_category": "5",
                "test_strategy": {
                    "validation_type": "signature_equivalence_analysis",
                    "focus_area": "electronic_signature_definition"
                },
                "expected_confidence_min": 0.75,
                "complexity": "medium"
            },

            {
                "id": "q6_records_copying_inspection",
                "category": "Record Management",
                "question": "What are FDA's expectations for providing copies of electronic records during inspections under the current guidance?",
                "expected_concepts": [
                    "copies of records",
                    "enforcement discretion",
                    "reasonable and useful access",
                    "inspection",
                    "predicate rules"
                ],
                "context_depth": "standard",
                "search_sections": ["copies", "records", "inspection", "access"],
                "gamp_category": "4",
                "test_strategy": {
                    "validation_type": "inspection_readiness_analysis",
                    "focus_area": "record_copying_requirements"
                },
                "expected_confidence_min": 0.70,
                "complexity": "low"
            }
        ]

    @staticmethod
    def get_question_by_id(question_id: str) -> dict[str, Any]:
        """Get specific question by ID."""
        questions = FDApart11Questions.get_test_questions()
        for q in questions:
            if q["id"] == question_id:
                return q
        raise ValueError(f"Question with ID '{question_id}' not found")

    @staticmethod
    def get_questions_by_category(category: str) -> list[dict[str, Any]]:
        """Get all questions in a specific category."""
        questions = FDApart11Questions.get_test_questions()
        return [q for q in questions if q["category"] == category]

    @staticmethod
    def get_questions_by_complexity(complexity: str) -> list[dict[str, Any]]:
        """Get questions filtered by complexity level."""
        questions = FDApart11Questions.get_test_questions()
        return [q for q in questions if q["complexity"] == complexity]

    @staticmethod
    def validate_answer_quality(question: dict[str, Any], retrieved_content: str) -> dict[str, Any]:
        """
        Validate if retrieved content contains expected concepts from the question.
        
        Args:
            question: Question dictionary with expected_concepts
            retrieved_content: Content retrieved by the agent
            
        Returns:
            Validation results with concept coverage analysis
        """
        expected_concepts = question.get("expected_concepts", [])
        content_lower = retrieved_content.lower()

        found_concepts = []
        missing_concepts = []

        for concept in expected_concepts:
            # Check for concept or related terms
            concept_lower = concept.lower()
            if concept_lower in content_lower:
                found_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        coverage_percentage = len(found_concepts) / len(expected_concepts) * 100 if expected_concepts else 100

        return {
            "question_id": question["id"],
            "expected_concepts_count": len(expected_concepts),
            "found_concepts_count": len(found_concepts),
            "found_concepts": found_concepts,
            "missing_concepts": missing_concepts,
            "coverage_percentage": coverage_percentage,
            "meets_expectations": coverage_percentage >= 70.0,  # 70% threshold
            "quality_assessment": (
                "excellent" if coverage_percentage >= 90 else
                "good" if coverage_percentage >= 80 else
                "acceptable" if coverage_percentage >= 70 else
                "poor"
            )
        }


if __name__ == "__main__":
    # Example usage and validation
    questions = FDApart11Questions.get_test_questions()
    print(f"📋 FDA Part 11 Test Questions: {len(questions)} questions loaded")

    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q['category']}] {q['id']}")
        print(f"   Question: {q['question']}")
        print(f"   Expected concepts: {len(q['expected_concepts'])}")
        print(f"   Complexity: {q['complexity']}")
        print(f"   Min confidence: {q['expected_confidence_min']}")
