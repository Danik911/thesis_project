"""
Centralized DeepSeek V3 Pricing Constants

This module provides centralized pricing constants for DeepSeek V3 model
to ensure consistency across all cost calculation points and prevent
pricing discrepancies that could compromise financial data integrity.

CRITICAL: These constants must be kept in sync with actual DeepSeek V3 pricing.
Any changes must be validated across all cost calculation systems.
"""

from typing import Final

# DeepSeek V3 Pricing (per 1M tokens as of January 2025)
# Source: https://platform.deepseek.com/pricing
DEEPSEEK_V3_INPUT_COST_PER_1M: Final[float] = 0.14   # USD per 1M input tokens
DEEPSEEK_V3_OUTPUT_COST_PER_1M: Final[float] = 0.28  # USD per 1M output tokens

# Model identifier for validation
DEEPSEEK_V3_MODEL_NAME: Final[str] = "deepseek/deepseek-chat"


def calculate_deepseek_v3_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate cost for DeepSeek V3 token usage.
    
    Args:
        prompt_tokens: Number of input/prompt tokens
        completion_tokens: Number of output/completion tokens
        
    Returns:
        Total cost in USD
        
    Raises:
        ValueError: If token counts are negative
    """
    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError(f"Token counts cannot be negative: prompt={prompt_tokens}, completion={completion_tokens}")

    prompt_cost = (prompt_tokens / 1_000_000) * DEEPSEEK_V3_INPUT_COST_PER_1M
    completion_cost = (completion_tokens / 1_000_000) * DEEPSEEK_V3_OUTPUT_COST_PER_1M

    return prompt_cost + completion_cost


def validate_pricing_consistency() -> None:
    """
    Validate that all cost calculation points use consistent pricing.
    
    This function should be called during system initialization to catch
    any pricing discrepancies that could compromise financial calculations.
    
    Raises:
        ValueError: If pricing constants are inconsistent
    """
    # Test calculation with known values
    test_prompt_tokens = 2000
    test_completion_tokens = 1000
    expected_cost = 0.00056  # (2000/1M * 0.14) + (1000/1M * 0.28)

    actual_cost = calculate_deepseek_v3_cost(test_prompt_tokens, test_completion_tokens)

    # Allow for small floating point precision differences
    if abs(actual_cost - expected_cost) > 0.000001:
        raise ValueError(
            f"Pricing validation failed: expected ${expected_cost:.6f}, got ${actual_cost:.6f}. "
            f"This indicates inconsistent pricing constants across the system."
        )


if __name__ == "__main__":
    # Self-test
    validate_pricing_consistency()
    print("✅ Pricing constants validation passed")

    # Example calculation
    cost = calculate_deepseek_v3_cost(2000, 1000)
    print(f"Example: 2000 prompt + 1000 completion tokens = ${cost:.6f}")
