"""
Unit tests for OpenRouter cost tracking utility.

Tests token usage extraction and cost calculation for GAMP-5 audit trail compliance.
"""

import pytest
from src.utils.cost_tracker import (
    TokenUsage,
    CostDetails,
    OPENROUTER_PRICING,
    calculate_cost,
    extract_usage_from_response,
    format_cost_for_display,
    get_model_pricing,
    is_model_supported,
)


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_basic_token_usage(self):
        """Test basic token usage creation."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.native_prompt_tokens is None
        assert usage.native_completion_tokens is None

    def test_token_usage_with_native_tokens(self):
        """Test token usage with native tokens."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            native_prompt_tokens=120,
            native_completion_tokens=55
        )
        assert usage.native_prompt_tokens == 120
        assert usage.native_completion_tokens == 55

    def test_get_billable_input_tokens_with_native(self):
        """Test billable input returns native tokens when available."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            native_prompt_tokens=120,
            native_completion_tokens=55
        )
        assert usage.get_billable_input_tokens() == 120

    def test_get_billable_input_tokens_without_native(self):
        """Test billable input returns standard tokens when native unavailable."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        assert usage.get_billable_input_tokens() == 100

    def test_get_billable_output_tokens_with_native(self):
        """Test billable output returns native tokens when available."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            native_prompt_tokens=120,
            native_completion_tokens=55
        )
        assert usage.get_billable_output_tokens() == 55

    def test_get_billable_output_tokens_without_native(self):
        """Test billable output returns standard tokens when native unavailable."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        assert usage.get_billable_output_tokens() == 50


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_deepseek_free(self):
        """Test cost calculation for DeepSeek (free model)."""
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            native_prompt_tokens=1200,
            native_completion_tokens=550
        )
        cost = calculate_cost(usage, "deepseek/deepseek-chat")

        assert cost.total_cost_usd == 0.0
        assert cost.input_cost_usd == 0.0
        assert cost.output_cost_usd == 0.0
        assert cost.model == "deepseek/deepseek-chat"
        # Should use native tokens for calculation
        assert cost.input_tokens == 1200
        assert cost.output_tokens == 550

    def test_calculate_cost_unknown_model_raises(self):
        """Test that unknown model raises ValueError (NO FALLBACK)."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        with pytest.raises(ValueError) as exc_info:
            calculate_cost(usage, "unknown/model")

        assert "Unknown model for pricing" in str(exc_info.value)
        assert "NO FALLBACK ALLOWED" in str(exc_info.value)

    def test_calculate_cost_uses_standard_tokens_when_no_native(self):
        """Test that standard tokens are used when native not available."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        cost = calculate_cost(usage, "deepseek/deepseek-chat")

        assert cost.input_tokens == 100
        assert cost.output_tokens == 50


class TestExtractUsageFromResponse:
    """Tests for extract_usage_from_response function."""

    def test_extract_usage_complete(self):
        """Test extracting complete usage data from response."""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "native_prompt_tokens": 120,
                "native_completion_tokens": 55
            }
        }

        usage = extract_usage_from_response(response)

        assert usage is not None
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.native_prompt_tokens == 120
        assert usage.native_completion_tokens == 55

    def test_extract_usage_without_native_tokens(self):
        """Test extracting usage without native tokens."""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        usage = extract_usage_from_response(response)

        assert usage is not None
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.native_prompt_tokens is None
        assert usage.native_completion_tokens is None

    def test_extract_usage_missing_returns_none(self):
        """Test that missing usage returns None (not raises)."""
        response = {"choices": [{"message": {"content": "Hello"}}]}

        usage = extract_usage_from_response(response)

        assert usage is None

    def test_extract_usage_empty_response(self):
        """Test empty response returns None."""
        usage = extract_usage_from_response({})
        assert usage is None


class TestPricingData:
    """Tests for pricing data and helper functions."""

    def test_deepseek_models_in_pricing(self):
        """Test that DeepSeek models are in pricing dict."""
        assert "deepseek/deepseek-chat" in OPENROUTER_PRICING
        assert "deepseek/deepseek-chat-v3" in OPENROUTER_PRICING
        assert "deepseek/deepseek-chat-v3.1" in OPENROUTER_PRICING

    def test_get_model_pricing_exists(self):
        """Test get_model_pricing for existing model."""
        pricing = get_model_pricing("deepseek/deepseek-chat")
        assert pricing is not None
        assert "input" in pricing
        assert "output" in pricing

    def test_get_model_pricing_not_exists(self):
        """Test get_model_pricing for unknown model."""
        pricing = get_model_pricing("unknown/model")
        assert pricing is None

    def test_is_model_supported_true(self):
        """Test is_model_supported for known model."""
        assert is_model_supported("deepseek/deepseek-chat") is True

    def test_is_model_supported_false(self):
        """Test is_model_supported for unknown model."""
        assert is_model_supported("unknown/model") is False


class TestFormatCostForDisplay:
    """Tests for format_cost_for_display function."""

    def test_format_cost_basic(self):
        """Test basic cost formatting."""
        cost = CostDetails(
            input_cost_usd=0.0,
            output_cost_usd=0.0,
            total_cost_usd=0.0,
            model="deepseek/deepseek-chat",
            input_tokens=1000,
            output_tokens=500
        )

        formatted = format_cost_for_display(cost)

        assert "deepseek/deepseek-chat" in formatted
        assert "1,000 tokens" in formatted
        assert "500 tokens" in formatted
        assert "$0.000000" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
