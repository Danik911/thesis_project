"""
OpenRouter Cost Tracking Utility for Pharmaceutical Test Generation System.

This module provides token usage extraction and cost calculation for OpenRouter API calls.
Implements GAMP-5 compliant audit trail with accurate token tracking.

CRITICAL: NO FALLBACK LOGIC - all errors are explicit for regulatory compliance.

Features:
- Token usage extraction from OpenRouter responses
- Native token tracking (what OpenRouter bills)
- Cost calculation with model-specific pricing
- Audit trail logging for pharmaceutical compliance
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """
    Token usage data from OpenRouter response.

    OpenRouter provides both standard tokens (OpenAI-compatible) and native tokens
    (what the underlying model provider actually counts). Native tokens are what
    OpenRouter bills for.

    Attributes:
        prompt_tokens: Standard prompt token count
        completion_tokens: Standard completion token count
        total_tokens: Standard total token count
        native_prompt_tokens: Native prompt tokens (OpenRouter billing basis)
        native_completion_tokens: Native completion tokens (OpenRouter billing basis)
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    native_prompt_tokens: int | None = None
    native_completion_tokens: int | None = None

    def get_billable_input_tokens(self) -> int:
        """Get the tokens used for billing input (native if available)."""
        return self.native_prompt_tokens if self.native_prompt_tokens is not None else self.prompt_tokens

    def get_billable_output_tokens(self) -> int:
        """Get the tokens used for billing output (native if available)."""
        return self.native_completion_tokens if self.native_completion_tokens is not None else self.completion_tokens


@dataclass
class CostDetails:
    """
    Cost calculation details for OpenRouter API call.

    Attributes:
        input_cost_usd: Cost for input tokens in USD
        output_cost_usd: Cost for output tokens in USD
        total_cost_usd: Total cost in USD
        model: Model name used for pricing lookup
        input_tokens: Input tokens used in calculation
        output_tokens: Output tokens used in calculation
    """
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    model: str
    input_tokens: int
    output_tokens: int


# OpenRouter pricing per 1M tokens (USD)
# Source: https://openrouter.ai/models
# Last updated: 2025-11-28
# NOTE: DeepSeek V3 is currently FREE on OpenRouter
OPENROUTER_PRICING = {
    # DeepSeek models (FREE tier)
    "deepseek/deepseek-chat": {"input": 0.0, "output": 0.0},
    "deepseek/deepseek-chat-v3": {"input": 0.0, "output": 0.0},
    "deepseek/deepseek-chat-v3.1": {"input": 0.0, "output": 0.0},
    "deepseek/deepseek-coder": {"input": 0.0, "output": 0.0},
    # Add more models as needed for future pricing
    # Example paid models (for reference):
    # "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
    # "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
}


def calculate_cost(usage: TokenUsage, model: str) -> CostDetails:
    """
    Calculate cost from token usage for a specific model.

    Uses native tokens when available for accurate billing calculation.

    Args:
        usage: Token usage data from response
        model: Model name for pricing lookup

    Returns:
        CostDetails with calculated costs

    Raises:
        ValueError: If model is not found in pricing dict. NO FALLBACK -
                   add model to OPENROUTER_PRICING dict if needed.
    """
    pricing = OPENROUTER_PRICING.get(model)

    if pricing is None:
        # NO FALLBACK - explicit error for unknown model
        available_models = list(OPENROUTER_PRICING.keys())
        raise ValueError(
            f"Unknown model for pricing: '{model}'. "
            f"NO FALLBACK ALLOWED - Add model to OPENROUTER_PRICING dict in cost_tracker.py. "
            f"Available models: {available_models}"
        )

    # Use native tokens if available (what OpenRouter actually bills)
    input_tokens = usage.get_billable_input_tokens()
    output_tokens = usage.get_billable_output_tokens()

    # Calculate cost (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    cost_details = CostDetails(
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total_cost,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )

    # Log for audit trail (GAMP-5 compliance)
    logger.info(
        f"[COST_TRACKING] Model: {model}, "
        f"Input tokens: {input_tokens}, Output tokens: {output_tokens}, "
        f"Cost: ${total_cost:.6f} USD "
        f"(Native tokens used: {usage.native_prompt_tokens is not None})"
    )

    return cost_details


def extract_usage_from_response(response: dict[str, Any]) -> TokenUsage | None:
    """
    Extract token usage from OpenRouter API response.

    OpenRouter includes usage data when `"usage": {"include": True}` is set
    in the request. This function extracts both standard and native tokens.

    Args:
        response: Raw response dict from OpenRouter API

    Returns:
        TokenUsage with token counts, or None if usage data not present.

    Note:
        Returns None instead of raising an error if usage is missing,
        as some OpenRouter responses may not include usage data (e.g., streaming).
        The caller should handle None appropriately with a warning.
    """
    usage = response.get("usage")

    if not usage:
        # Log warning for audit trail - missing usage is notable but not fatal
        logger.warning(
            "[COST_TRACKING] No usage data in OpenRouter response. "
            "Was 'usage.include' enabled in the request? "
            "Token counts will not be available for this call."
        )
        return None

    # Extract standard tokens (always present in usage block)
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    # Extract native tokens (OpenRouter billing basis, may not always be present)
    native_prompt_tokens = usage.get("native_prompt_tokens")
    native_completion_tokens = usage.get("native_completion_tokens")

    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        native_prompt_tokens=native_prompt_tokens,
        native_completion_tokens=native_completion_tokens
    )

    # Log for audit trail
    logger.debug(
        f"[COST_TRACKING] Extracted usage - "
        f"Prompt: {prompt_tokens} (native: {native_prompt_tokens}), "
        f"Completion: {completion_tokens} (native: {native_completion_tokens}), "
        f"Total: {total_tokens}"
    )

    return token_usage


def format_cost_for_display(cost: CostDetails) -> str:
    """
    Format cost details for human-readable display.

    Args:
        cost: CostDetails to format

    Returns:
        Formatted string with cost breakdown
    """
    return (
        f"Model: {cost.model}\n"
        f"Input: {cost.input_tokens:,} tokens (${cost.input_cost_usd:.6f})\n"
        f"Output: {cost.output_tokens:,} tokens (${cost.output_cost_usd:.6f})\n"
        f"Total: ${cost.total_cost_usd:.6f} USD"
    )


def get_model_pricing(model: str) -> dict[str, float] | None:
    """
    Get pricing information for a specific model.

    Args:
        model: Model name to look up

    Returns:
        Dict with 'input' and 'output' prices per 1M tokens, or None if not found
    """
    return OPENROUTER_PRICING.get(model)


def is_model_supported(model: str) -> bool:
    """
    Check if a model is in the supported pricing list.

    Args:
        model: Model name to check

    Returns:
        True if model has pricing data, False otherwise
    """
    return model in OPENROUTER_PRICING
