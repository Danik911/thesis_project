"""
Cerebras Provider for GPT-OSS Models
Provides OpenAI-compatible interface for Cerebras-hosted GPT-OSS models.
"""

import os
from typing import Any, Dict, Optional
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai.utils import resolve_openai_credentials
from openai import OpenAI as OpenAIClient


class CerebrasLLM(OpenAI):
    """
    Cerebras-compatible LLM provider that bypasses OpenAI model validation.
    Uses Cerebras API endpoints with GPT-OSS models.
    """
    
    def __init__(
        self,
        model: str = "gpt-oss-120b",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Cerebras LLM with GPT-OSS models.
        
        Args:
            model: Model name (gpt-oss-120b or gpt-oss-20b)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            api_key: Cerebras API key (or from env CEREBRAS_API_KEY)
            api_base: Cerebras API base URL
        """
        # Use Cerebras defaults if not provided
        if api_base is None:
            api_base = os.getenv("OPENAI_API_BASE", "https://api.cerebras.ai/v1")
        
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CEREBRAS_API_KEY")
        
        # Initialize with a dummy valid OpenAI model to pass validation
        super().__init__(
            model="gpt-3.5-turbo",  # Dummy model to pass validation
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            api_base=api_base,
            **kwargs
        )
        
        # Now set the actual model after initialization
        self._actual_model = model
        self.model = model
        
        # Override the client to use Cerebras endpoint
        self._client = OpenAIClient(
            base_url=api_base,
            api_key=api_key,
            timeout=kwargs.get("timeout", 600),
            max_retries=kwargs.get("max_retries", 3)
        )
    
    def _get_model_name(self) -> str:
        """Return the actual Cerebras model name."""
        return self._actual_model
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Model metadata."""
        return {
            **super().metadata,
            "model_name": self._actual_model,
            "provider": "cerebras",
            "context_window": 131072,  # 131K context for GPT-OSS
            "is_function_calling_model": True,
        }


def get_cerebras_llm(
    model: Optional[str] = None,
    use_original_openai: bool = False
) -> OpenAI:
    """
    Factory function to get either Cerebras or OpenAI LLM based on configuration.
    
    Args:
        model: Optional model override
        use_original_openai: If True, use original OpenAI instead of Cerebras
        
    Returns:
        LLM instance configured for either Cerebras or OpenAI
    """
    if use_original_openai:
        # Use original OpenAI
        return OpenAI(
            model=model or "gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY_ORIGINAL"),
            api_base="https://api.openai.com/v1",
            temperature=0.1
        )
    else:
        # Use Cerebras with GPT-OSS
        return CerebrasLLM(
            model=model or os.getenv("LLM_MODEL", "gpt-oss-120b"),
            api_key=os.getenv("CEREBRAS_API_KEY") or os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.cerebras.ai/v1"),
            temperature=0.1
        )