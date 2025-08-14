"""
Open-Source LLM Provider Factory

Provides a unified interface for multiple open-source LLM providers including
OpenRouter, Cerebras, Together AI, and Fireworks. Implements ZERO FALLBACK
policy - all failures are explicit with full diagnostic information.

NO FALLBACKS: This module will NEVER mask failures or provide automatic fallbacks.
All errors are reported explicitly for regulatory compliance.
"""

import logging
import os
from enum import Enum
from typing import Any

from llama_index.llms.openai import OpenAI
from openai import OpenAI as OpenAIClient


class OSSProvider(Enum):
    """Supported open-source model providers."""
    OPENROUTER = "openrouter"
    CEREBRAS = "cerebras"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    OPENAI = "openai"  # For comparison testing


class OSSModelFactory:
    """
    Factory for creating LLM instances with different open-source providers.
    
    NO FALLBACKS: If a provider fails, the error is raised immediately with
    full diagnostic information. No automatic switching between providers.
    """

    # Provider configuration
    PROVIDER_CONFIG = {
        OSSProvider.OPENROUTER: {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "openai/gpt-oss-120b",
            "cost_per_m_input": 0.09,
            "cost_per_m_output": 0.45,
            "max_tps": 290,
            "context_window": 131072,
            "env_key": "OPENROUTER_API_KEY"
        },
        OSSProvider.CEREBRAS: {
            "base_url": "https://api.cerebras.ai/v1",
            "default_model": "gpt-oss-120b",
            "cost_per_m_input": 0.25,
            "cost_per_m_output": 0.69,
            "max_tps": 3000,
            "context_window": 131072,
            "env_key": "CEREBRAS_API_KEY"
        },
        OSSProvider.TOGETHER: {
            "base_url": "https://api.together.xyz/v1",
            "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "cost_per_m_input": 0.15,
            "cost_per_m_output": 0.60,
            "max_tps": 170,
            "context_window": 131072,
            "env_key": "TOGETHER_API_KEY"
        },
        OSSProvider.FIREWORKS: {
            "base_url": "https://api.fireworks.ai/inference/v1",
            "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "cost_per_m_input": 0.15,
            "cost_per_m_output": 0.60,
            "max_tps": 260,
            "context_window": 131072,
            "env_key": "FIREWORKS_API_KEY"
        },
        OSSProvider.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o-mini",
            "cost_per_m_input": 10.0,
            "cost_per_m_output": 30.0,
            "max_tps": 100,
            "context_window": 128000,
            "env_key": "OPENAI_API_KEY"
        }
    }

    def __init__(self, verbose: bool = False):
        """
        Initialize the OSS model factory.
        
        Args:
            verbose: Enable detailed logging
        """
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

        # Track usage for cost analysis
        self.usage_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "errors": []
        }

    def create_llm(
        self,
        provider: OSSProvider | str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        api_key: str | None = None,
        **kwargs
    ) -> OpenAI:
        """
        Create an LLM instance for the specified provider.
        
        NO FALLBACKS: If provider initialization fails, raises exception immediately.
        
        Args:
            provider: The OSS provider to use
            model: Optional model override (uses provider default if not specified)
            temperature: Sampling temperature (0.1 for deterministic)
            max_tokens: Maximum tokens to generate
            api_key: Optional API key override (uses env variable if not specified)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured OpenAI-compatible LLM instance
            
        Raises:
            ValueError: If provider is not supported
            RuntimeError: If API key is missing or provider initialization fails
        """
        # Convert string to enum if needed
        if isinstance(provider, str):
            try:
                provider = OSSProvider(provider.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported provider: {provider}. "
                    f"Supported providers: {[p.value for p in OSSProvider]}"
                )

        # Get provider configuration
        config = self.PROVIDER_CONFIG[provider]

        # Get API key (NO FALLBACK - fail if missing)
        if api_key is None:
            api_key = os.getenv(config["env_key"])
            if not api_key:
                raise RuntimeError(
                    f"API key missing for {provider.value}. "
                    f"Set {config['env_key']} environment variable or provide api_key parameter. "
                    f"NO FALLBACK: Cannot proceed without valid API key."
                )

        # Use default model if not specified
        if model is None:
            model = config["default_model"]
            if self.verbose:
                self.logger.info(f"Using default model for {provider.value}: {model}")

        # Log provider selection (for audit trail)
        self.logger.info(
            f"Creating LLM with provider={provider.value}, model={model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        try:
            # Special handling for non-OpenAI providers (bypass model validation)
            if provider in [OSSProvider.CEREBRAS, OSSProvider.OPENROUTER, OSSProvider.TOGETHER, OSSProvider.FIREWORKS]:
                # Initialize with dummy model to pass validation
                llm = OpenAI(
                    model="gpt-3.5-turbo",  # Dummy for validation
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key,
                    api_base=config["base_url"],
                    **kwargs
                )
                # Override with actual model
                llm.model = model
                llm._model_name = model  # Some versions use this

                # Replace client with properly configured one
                llm._client = OpenAIClient(
                    base_url=config["base_url"],
                    api_key=api_key,
                    timeout=kwargs.get("timeout", 600),
                    max_retries=kwargs.get("max_retries", 3)
                )
                # Override the client's model too
                llm._client._default_model = model
            else:
                # Standard OpenAI initialization
                llm = OpenAI(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key,
                    api_base=config["base_url"],
                    **kwargs
                )

            # Add provider metadata
            llm._provider = provider.value
            llm._cost_per_m_input = config["cost_per_m_input"]
            llm._cost_per_m_output = config["cost_per_m_output"]

            return llm

        except Exception as e:
            # NO FALLBACK - report error with full diagnostics
            error_msg = (
                f"Failed to initialize {provider.value} provider.\n"
                f"Provider: {provider.value}\n"
                f"Model: {model}\n"
                f"API Base: {config['base_url']}\n"
                f"Error: {e!s}\n"
                f"NO FALLBACK: Manual intervention required."
            )
            self.logger.error(error_msg)
            self.usage_stats["errors"].append({
                "provider": provider.value,
                "model": model,
                "error": str(e)
            })
            raise RuntimeError(error_msg) from e

    def create_from_env(self) -> OpenAI:
        """
        Create LLM instance from environment variables.
        
        Environment variables:
            LLM_PROVIDER: Provider name (openrouter, cerebras, etc.)
            LLM_MODEL_OSS: Model name (optional, uses provider default)
            LLM_TEMPERATURE: Temperature (optional, default 0.1)
            LLM_MAX_TOKENS: Max tokens (optional)
            
        Returns:
            Configured LLM instance
            
        Raises:
            RuntimeError: If required environment variables are missing
        """
        provider_str = os.getenv("LLM_PROVIDER")
        if not provider_str:
            raise RuntimeError(
                "LLM_PROVIDER environment variable not set. "
                "Set to one of: openrouter, cerebras, together, fireworks, openai"
            )

        return self.create_llm(
            provider=provider_str,
            model=os.getenv("LLM_MODEL_OSS"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")) if os.getenv("LLM_MAX_TOKENS") else None
        )

    def estimate_cost(
        self,
        provider: OSSProvider | str,
        input_tokens: int,
        output_tokens: int
    ) -> dict[str, float]:
        """
        Estimate cost for a given token usage.
        
        Args:
            provider: The provider to estimate for
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary with cost breakdown
        """
        if isinstance(provider, str):
            provider = OSSProvider(provider.lower())

        config = self.PROVIDER_CONFIG[provider]

        input_cost = (input_tokens / 1_000_000) * config["cost_per_m_input"]
        output_cost = (output_tokens / 1_000_000) * config["cost_per_m_output"]
        total_cost = input_cost + output_cost

        return {
            "provider": provider.value,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "cost_per_m_input": config["cost_per_m_input"],
            "cost_per_m_output": config["cost_per_m_output"]
        }

    def compare_providers(
        self,
        input_tokens: int = 1000,
        output_tokens: int = 2000
    ) -> dict[str, dict[str, Any]]:
        """
        Compare costs across all providers.
        
        Args:
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            
        Returns:
            Comparison dictionary with all providers
        """
        comparison = {}

        for provider in OSSProvider:
            cost_data = self.estimate_cost(provider, input_tokens, output_tokens)
            config = self.PROVIDER_CONFIG[provider]

            comparison[provider.value] = {
                **cost_data,
                "max_tps": config["max_tps"],
                "context_window": config["context_window"],
                "savings_vs_openai": None
            }

        # Calculate savings vs OpenAI
        openai_cost = comparison["openai"]["total_cost"]
        for provider in comparison:
            if provider != "openai":
                provider_cost = comparison[provider]["total_cost"]
                savings_pct = ((openai_cost - provider_cost) / openai_cost) * 100
                comparison[provider]["savings_vs_openai"] = round(savings_pct, 1)

        return comparison

    def get_usage_stats(self) -> dict[str, Any]:
        """Get current usage statistics."""
        return self.usage_stats.copy()


def get_oss_llm(
    provider: str | None = None,
    model: str | None = None,
    **kwargs
) -> OpenAI:
    """
    Convenience function to get an OSS LLM instance.
    
    Args:
        provider: Provider name (uses LLM_PROVIDER env if not specified)
        model: Model name (uses provider default if not specified)
        **kwargs: Additional parameters for the LLM
        
    Returns:
        Configured LLM instance
    """
    factory = OSSModelFactory()

    if provider:
        return factory.create_llm(provider, model, **kwargs)
    return factory.create_from_env()


if __name__ == "__main__":
    # Example usage and cost comparison
    factory = OSSModelFactory(verbose=True)

    print("\n=== Provider Cost Comparison ===")
    print("For 1000 input tokens + 2000 output tokens:\n")

    comparison = factory.compare_providers(1000, 2000)

    for provider, data in comparison.items():
        print(f"{provider.upper()}:")
        print(f"  Total Cost: ${data['total_cost']:.6f}")
        print(f"  Max TPS: {data['max_tps']}")
        print(f"  Context: {data['context_window']:,} tokens")
        if data["savings_vs_openai"]:
            print(f"  Savings vs OpenAI: {data['savings_vs_openai']}%")
        print()

    # Test provider initialization (if API keys are set)
    try:
        print("\n=== Testing Provider Initialization ===")

        # Try to create from environment
        if os.getenv("LLM_PROVIDER"):
            llm = factory.create_from_env()
            print(f"✓ Successfully created LLM from environment: {llm._provider}")
        else:
            print("LLM_PROVIDER not set, skipping environment test")

    except Exception as e:
        print(f"✗ Provider initialization failed: {e}")
