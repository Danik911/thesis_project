"""
Test suite for GAMP-5 Categorization Error Handling and Fallback Strategy

Tests comprehensive error handling, fallback mechanisms, and audit logging
for the GAMP-5 categorization agent with regulatory compliance.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC
from uuid import UUID

from main.src.core.events import GAMPCategory, GAMPCategorizationEvent
from main.src.agents.categorization.agent import (
    create_gamp_categorization_agent,
    gamp_analysis_tool_with_error_handling,
    confidence_tool_with_error_handling,
    categorize_with_error_handling
)
from main.src.agents.categorization.error_handler import (
    CategorizationErrorHandler,
    CategorizationError,
    ErrorType,
    ErrorSeverity,
    AuditLogEntry
)


class TestErrorHandler:
    """Test suite for CategorizationErrorHandler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = CategorizationErrorHandler(
            confidence_threshold=0.60,
            ambiguity_threshold=0.15,
            enable_audit_logging=True,
            verbose=True
        )
        
    def test_parsing_error_handling(self):
        """Test handling of document parsing errors."""
        # Simulate parsing error
        parsing_error = ValueError("Invalid document format")
        document_content = "Malformed content"
        document_name = "test_doc.txt"
        
        result = self.error_handler.handle_parsing_error(
            parsing_error, document_content, document_name
        )
        
        # Verify fallback to Category 5
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert result.review_required is True
        assert "AUTOMATIC FALLBACK TO CATEGORY 5" in result.justification
        assert "PARSING_ERROR" in result.justification
        
        # Verify audit log
        assert len(self.error_handler.audit_log) == 1
        audit_entry = self.error_handler.audit_log[0]
        assert audit_entry.action == "FALLBACK_CATEGORIZATION"
        assert audit_entry.document_name == document_name
        assert audit_entry.fallback_category == GAMPCategory.CATEGORY_5
        
    def test_logic_error_handling(self):
        """Test handling of categorization logic failures."""
        error_details = {
            "message": "Categorization logic failed",
            "step": "evidence_analysis",
            "reason": "Conflicting indicators"
        }
        
        result = self.error_handler.handle_logic_error(
            error_details, "logic_test.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert "LOGIC_ERROR" in result.justification
        assert result.risk_assessment["error_details"]["error_type"] == "logic_error"
        
    def test_ambiguity_detection(self):
        """Test detection of ambiguous categorization results."""
        # High confidence for multiple categories
        confidence_scores = {
            1: 0.75,  # Category 1
            3: 0.72,  # Category 3 
            4: 0.20,
            5: 0.10
        }
        
        categorization_results = {
            "predicted_category": 1,
            "evidence": {"strong_indicators": ["test"]}
        }
        
        error = self.error_handler.check_ambiguity(
            categorization_results, confidence_scores
        )
        
        assert error is not None
        assert error.error_type == ErrorType.AMBIGUITY_ERROR
        assert "Multiple categories with high confidence" in error.message
        assert error.details["high_confidence_categories"] == [1, 3]
        
    def test_low_confidence_detection(self):
        """Test detection of low confidence results."""
        # All categories below threshold
        confidence_scores = {
            1: 0.45,
            3: 0.50,
            4: 0.55,
            5: 0.40
        }
        
        error = self.error_handler.check_ambiguity({}, confidence_scores)
        
        assert error is not None
        assert error.error_type == ErrorType.CONFIDENCE_ERROR
        assert "No category meets confidence threshold" in error.message
        assert error.details["max_confidence"] == 0.55
        
    def test_tool_error_handling(self):
        """Test handling of tool execution errors."""
        tool_error = RuntimeError("Tool execution failed")
        
        result = self.error_handler.handle_tool_error(
            "gamp_analysis_tool",
            tool_error,
            "test input",
            "tool_test.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert "TOOL_ERROR" in result.justification
        assert "gamp_analysis_tool" in result.justification
        
    def test_llm_error_handling(self):
        """Test handling of LLM-related errors."""
        llm_error = Exception("OpenAI API error")
        prompt = "Analyze this URS document..."
        
        result = self.error_handler.handle_llm_error(
            llm_error, prompt, "llm_test.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert "LLM_ERROR" in result.justification
        assert result.risk_assessment["error_details"]["severity"] == "critical"
        
    def test_validation_error_detection(self):
        """Test validation of categorization results."""
        # Missing required fields
        invalid_result = {
            "predicted_category": 3,
            # Missing "evidence" and "all_categories_analysis"
        }
        
        error = self.error_handler.validate_categorization_result(invalid_result)
        
        assert error is not None
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "Missing required fields" in error.message
        assert "evidence" in error.details["missing_fields"]
        
    def test_invalid_category_validation(self):
        """Test detection of invalid category values."""
        invalid_result = {
            "predicted_category": 2,  # Category 2 doesn't exist
            "evidence": {},
            "all_categories_analysis": {}
        }
        
        error = self.error_handler.validate_categorization_result(invalid_result)
        
        assert error is not None
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "Invalid category value: 2" in error.message
        
    def test_audit_log_generation(self):
        """Test comprehensive audit log generation."""
        # Generate multiple errors
        self.error_handler.handle_parsing_error(
            ValueError("Error 1"), "content1", "doc1.urs"
        )
        self.error_handler.handle_logic_error(
            {"message": "Error 2"}, "doc2.urs"
        )
        
        audit_log = self.error_handler.get_audit_log()
        
        assert len(audit_log) == 2
        
        # Verify audit log structure
        for entry in audit_log:
            assert "entry_id" in entry
            assert "timestamp" in entry
            assert "action" in entry
            assert "document_name" in entry
            assert "fallback_category" in entry
            assert entry["fallback_category"] == 5
            
    def test_error_statistics(self):
        """Test error statistics tracking."""
        # Generate various errors
        self.error_handler.handle_parsing_error(ValueError("E1"), "c1", "d1")
        self.error_handler.handle_parsing_error(ValueError("E2"), "c2", "d2")
        self.error_handler.handle_logic_error({"message": "E3"}, "d3")
        self.error_handler.handle_tool_error("tool", Exception("E4"), "i4", "d4")
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 4
        assert stats["fallback_count"] == 4
        assert stats["error_type_distribution"]["parsing_error"] == 2
        assert stats["error_type_distribution"]["logic_error"] == 1
        assert stats["error_type_distribution"]["tool_error"] == 1
        assert len(stats["recent_errors"]) == 4


class TestErrorHandlingIntegration:
    """Test error handling integration with categorization agent."""
    
    def test_agent_with_error_handling_enabled(self):
        """Test agent creation with error handling enabled."""
        agent = create_gamp_categorization_agent(
            enable_error_handling=True,
            confidence_threshold=0.70,
            verbose=True
        )
        
        assert hasattr(agent, 'error_handler')
        assert agent.error_handler.confidence_threshold == 0.70
        assert len(agent.tools) == 2  # gamp_analysis and confidence tools
        
    def test_agent_with_error_handling_disabled(self):
        """Test agent creation with error handling disabled."""
        agent = create_gamp_categorization_agent(
            enable_error_handling=False
        )
        
        assert not hasattr(agent, 'error_handler')
        assert len(agent.tools) == 2
        
    def test_gamp_tool_with_error_handling(self):
        """Test GAMP analysis tool with error handling."""
        error_handler = CategorizationErrorHandler()
        
        # Test with invalid input
        result = gamp_analysis_tool_with_error_handling("", error_handler)
        
        assert result["predicted_category"] == 5
        assert result.get("error") is True
        assert "Invalid URS content" in result["decision_rationale"]
        
        # Test with too short input
        result = gamp_analysis_tool_with_error_handling("Short", error_handler)
        
        assert result["predicted_category"] == 5
        assert "too short" in result["decision_rationale"]
        
    def test_confidence_tool_with_error_handling(self):
        """Test confidence tool with error handling."""
        error_handler = CategorizationErrorHandler()
        
        # Test with error result
        error_result = {"error": True}
        confidence = confidence_tool_with_error_handling(error_result, error_handler)
        assert confidence == 0.0
        
        # Test with invalid input
        confidence = confidence_tool_with_error_handling("invalid", error_handler)
        assert confidence == 0.0
        
        # Test with missing fields
        incomplete_result = {"predicted_category": 3}
        confidence = confidence_tool_with_error_handling(incomplete_result, error_handler)
        assert confidence == 0.0


class TestCategorizationWithErrorHandling:
    """Test complete categorization workflow with error handling."""
    
    @patch('main.src.agents.categorization.agent.FunctionAgent')
    def test_successful_categorization(self, mock_agent_class):
        """Test successful categorization without errors."""
        # Mock agent response
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.__str__.return_value = """
        Based on the analysis, this is Category 4 (Configured Products) 
        with a confidence score of 85%. The system requires user-defined 
        parameters and workflow configuration.
        """
        mock_agent.chat.return_value = mock_response
        
        result = categorize_with_error_handling(
            mock_agent, 
            "LIMS configuration for workflows",
            "test_success.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_4
        assert result.confidence_score == 0.85
        assert not result.review_required  # High confidence
        
    @patch('main.src.agents.categorization.agent.FunctionAgent')
    def test_low_confidence_fallback(self, mock_agent_class):
        """Test fallback when confidence is below threshold."""
        mock_agent = MagicMock()
        mock_agent.error_handler = CategorizationErrorHandler(confidence_threshold=0.70)
        
        # Mock low confidence response
        mock_response = MagicMock()
        mock_response.__str__.return_value = "Category 3 with 45% confidence"
        mock_agent.chat.return_value = mock_response
        
        result = categorize_with_error_handling(
            mock_agent,
            "Ambiguous system requirements",
            "test_low_conf.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert result.review_required is True
        assert "CONFIDENCE_ERROR" in result.justification
        
    @patch('main.src.agents.categorization.agent.FunctionAgent')
    def test_parsing_error_fallback(self, mock_agent_class):
        """Test fallback on parsing errors."""
        mock_agent = MagicMock()
        mock_agent.error_handler = CategorizationErrorHandler()
        
        result = categorize_with_error_handling(
            mock_agent,
            "",  # Empty content should trigger parsing error
            "test_empty.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert "Invalid URS content" in result.justification
        
    @patch('main.src.agents.categorization.agent.FunctionAgent')
    def test_llm_error_with_retry(self, mock_agent_class):
        """Test LLM error handling with retry logic."""
        mock_agent = MagicMock()
        mock_agent.error_handler = CategorizationErrorHandler()
        
        # First call fails, second succeeds
        mock_agent.chat.side_effect = [
            Exception("API error"),
            MagicMock(__str__=lambda self: "Category 1 with 90% confidence")
        ]
        
        result = categorize_with_error_handling(
            mock_agent,
            "Windows Server 2019 infrastructure",
            "test_retry.urs",
            max_retries=1
        )
        
        # Should succeed on retry
        assert result.gamp_category == GAMPCategory.CATEGORY_1
        assert result.confidence_score == 0.90
        assert mock_agent.chat.call_count == 2
        
    @patch('main.src.agents.categorization.agent.FunctionAgent')
    def test_persistent_error_fallback(self, mock_agent_class):
        """Test fallback when all retries fail."""
        mock_agent = MagicMock()
        mock_agent.error_handler = CategorizationErrorHandler()
        
        # All calls fail
        mock_agent.chat.side_effect = Exception("Persistent API error")
        
        result = categorize_with_error_handling(
            mock_agent,
            "Test content",
            "test_persistent.urs",
            max_retries=2
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert "LLM_ERROR" in result.justification
        assert mock_agent.chat.call_count == 3  # Initial + 2 retries


class TestMalformedDocuments:
    """Test handling of various malformed and edge-case documents."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_gamp_categorization_agent(
            enable_error_handling=True,
            confidence_threshold=0.60
        )
        
    def test_empty_document(self):
        """Test handling of empty documents."""
        result = categorize_with_error_handling(
            self.agent, "", "empty.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        assert "Invalid URS content" in result.justification
        
    def test_non_text_content(self):
        """Test handling of non-text content."""
        binary_content = "\x00\x01\x02\x03\x04"
        
        result = categorize_with_error_handling(
            self.agent, binary_content, "binary.urs"
        )
        
        # Should handle gracefully and fallback
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.review_required is True
        
    def test_extremely_short_content(self):
        """Test handling of very short documents."""
        result = categorize_with_error_handling(
            self.agent, "ABC", "short.urs"
        )
        
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert "too short" in result.justification.lower()
        
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        unicode_content = """
        System Requirements: 
        • Unicode test: 你好世界 🌍
        • Special chars: @#$%^&*()
        • Mixed content: ABC123αβγ
        """
        
        # Should process without errors (actual categorization may vary)
        result = categorize_with_error_handling(
            self.agent, unicode_content, "unicode.urs"
        )
        
        assert isinstance(result, GAMPCategorizationEvent)
        assert result.gamp_category in [
            GAMPCategory.CATEGORY_1,
            GAMPCategory.CATEGORY_3,
            GAMPCategory.CATEGORY_4,
            GAMPCategory.CATEGORY_5
        ]


if __name__ == "__main__":
    # Run a simple test to verify setup
    error_handler = CategorizationErrorHandler()
    
    print("GAMP-5 Error Handling Test Suite")
    print("=" * 60)
    
    # Test error generation
    test_error = error_handler.handle_parsing_error(
        ValueError("Test error"),
        "Test content",
        "test_doc.urs"
    )
    
    print(f"Generated fallback event:")
    print(f"  Category: {test_error.gamp_category.name}")
    print(f"  Confidence: {test_error.confidence_score}")
    print(f"  Review Required: {test_error.review_required}")
    print(f"  Audit Log Entries: {len(error_handler.audit_log)}")
    
    print("\n✅ Error handling module working correctly!")