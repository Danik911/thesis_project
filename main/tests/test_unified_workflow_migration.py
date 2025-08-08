"""
Test to verify UnifiedTestGenerationWorkflow migration to centralized LLM config.

CRITICAL: This test verifies NO FALLBACKS policy is maintained.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.config.llm_config import LLMConfig


def test_unified_workflow_uses_centralized_llm_config():
    """Test that UnifiedTestGenerationWorkflow uses LLMConfig.get_llm()."""
    
    # Mock the LLMConfig.get_llm method
    mock_llm = MagicMock()
    
    with patch.object(LLMConfig, 'get_llm', return_value=mock_llm) as mock_get_llm:
        # Initialize workflow without providing an LLM
        workflow = UnifiedTestGenerationWorkflow()
        
        # Verify LLMConfig.get_llm was called
        mock_get_llm.assert_called_once()
        
        # Verify the workflow is using the LLM from LLMConfig
        assert workflow.llm == mock_llm
        
        print("SUCCESS: UnifiedTestGenerationWorkflow correctly uses centralized LLM config")


def test_unified_workflow_respects_provided_llm():
    """Test that UnifiedTestGenerationWorkflow uses provided LLM when given."""
    
    # Create a mock LLM
    provided_llm = MagicMock()
    
    with patch.object(LLMConfig, 'get_llm') as mock_get_llm:
        # Initialize workflow with a provided LLM
        workflow = UnifiedTestGenerationWorkflow(llm=provided_llm)
        
        # Verify LLMConfig.get_llm was NOT called
        mock_get_llm.assert_not_called()
        
        # Verify the workflow is using the provided LLM
        assert workflow.llm == provided_llm
        
        print("SUCCESS: UnifiedTestGenerationWorkflow correctly uses provided LLM")


def test_unified_workflow_no_fallback_on_llm_error():
    """Test that workflow fails explicitly when LLM config raises an error."""
    
    # Mock LLMConfig.get_llm to raise an error (simulating missing API key)
    with patch.object(LLMConfig, 'get_llm', side_effect=ValueError("OPENROUTER_API_KEY not found")):
        # Verify that initialization fails with no fallback
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY not found"):
            workflow = UnifiedTestGenerationWorkflow()
        
        print("SUCCESS: UnifiedTestGenerationWorkflow fails explicitly with no fallback")


if __name__ == "__main__":
    # Run tests directly
    test_unified_workflow_uses_centralized_llm_config()
    test_unified_workflow_respects_provided_llm()
    test_unified_workflow_no_fallback_on_llm_error()
    print("\nAll migration tests passed!")