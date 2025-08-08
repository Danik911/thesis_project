"""
Centralized LLM Configuration for OpenAI/OpenRouter Model Selection

CRITICAL: NO FALLBACKS ALLOWED
- This configuration explicitly fails on errors
- No default values or fallback models
- Human consultation triggered on failures
- Full diagnostic information provided
"""

import os
from enum import Enum
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core import Settings


class ModelProvider(Enum):
    """Available model providers."""
    OPENAI = "openai"
    OPENROUTER = "openrouter"


class LLMConfig:
    """
    Centralized LLM configuration for model selection.
    
    CRITICAL RULES:
    - NO FALLBACK MODELS
    - NO DEFAULT VALUES ON FAILURE
    - FAIL EXPLICITLY WITH FULL DIAGNOSTICS
    - HUMAN CONSULTATION FOR UNCERTAINTIES
    """
    
    # Set provider from environment (default to OpenRouter for OSS migration)
    PROVIDER = ModelProvider(os.getenv("LLM_PROVIDER", "openrouter"))
    
    # Model configurations (NO FALLBACKS - single model per provider)
    MODELS = {
        ModelProvider.OPENAI: {
            "model": "gpt-4.1-mini-2025-04-14",  # Single model, no fallback
            "temperature": 0.1,
            "max_tokens": 2000,
        },
        ModelProvider.OPENROUTER: {
            "model": "openai/gpt-oss-120b",  # ONLY THIS MODEL - OSS 120B parameter model
            "temperature": 0.1,
            "max_tokens": 4000,  # Increased for complex pharmaceutical JSON responses
        }
    }
    
    @classmethod
    def get_llm(cls, **override_kwargs: Any) -> LLM:
        """
        Get configured LLM instance.
        
        CRITICAL: This method will FAIL EXPLICITLY if:
        - API key is missing
        - Model initialization fails
        - Any error occurs
        
        NO FALLBACKS OR DEFAULT VALUES ALLOWED.
        
        Args:
            **override_kwargs: Optional parameters to override defaults
            
        Returns:
            LLM: Configured LLM instance
            
        Raises:
            ValueError: If API key is missing
            RuntimeError: If LLM initialization fails
            Exception: Any other error (no masking)
        """
        config = cls.MODELS[cls.PROVIDER].copy()
        
        # Apply any overrides
        for key, value in override_kwargs.items():
            if value is not None:
                config[key] = value
        
        # Get the global callback manager from LlamaIndex Settings
        # This ensures Phoenix instrumentation is passed to the LLM
        callback_manager = Settings.callback_manager if hasattr(Settings, 'callback_manager') else None
        
        # Ensure Phoenix handler is registered if available
        if callback_manager and hasattr(callback_manager, 'handlers'):
            # Check if handlers list is empty
            if len(callback_manager.handlers) == 0:
                try:
                    # Try to add the Phoenix handler
                    from llama_index.callbacks.arize_phoenix import arize_phoenix_callback_handler
                    if arize_phoenix_callback_handler:
                        # arize_phoenix_callback_handler is a function that returns the handler
                        handler = arize_phoenix_callback_handler()  # CRITICAL FIX: Call the function to get handler
                        if handler not in callback_manager.handlers:
                            callback_manager.add_handler(handler)
                except ImportError:
                    pass  # Phoenix not available, continue without it
        
        try:
            if cls.PROVIDER == ModelProvider.OPENAI:
                # Import and initialize OpenAI
                from llama_index.llms.openai import OpenAI
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY not found in environment. "
                        "NO FALLBACK ALLOWED - Human consultation required."
                    )
                
                return OpenAI(
                    model=config["model"],
                    api_key=api_key,
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    callback_manager=callback_manager,  # Pass global callback manager
                )
                
            elif cls.PROVIDER == ModelProvider.OPENROUTER:
                # Import and initialize OpenRouter compatibility wrapper
                from src.llms.openrouter_compat import OpenRouterCompatLLM
                
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENROUTER_API_KEY not found in environment. "
                        "NO FALLBACK ALLOWED - Human consultation required."
                    )
                
                return OpenRouterCompatLLM(
                    model=config["model"],
                    openrouter_api_key=api_key,
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    callback_manager=callback_manager,  # Pass global callback manager
                )
                
            else:
                raise ValueError(
                    f"Unknown provider: {cls.PROVIDER}. "
                    f"NO FALLBACK ALLOWED - Configuration error."
                )
                
        except ImportError as e:
            # FAIL EXPLICITLY - no masking
            raise RuntimeError(
                f"Failed to import LLM provider {cls.PROVIDER}: {e}\n"
                f"Full stack trace provided for debugging.\n"
                f"NO FALLBACK ALLOWED - Human consultation required."
            ) from e
            
        except Exception as e:
            # FAIL EXPLICITLY - no masking or fallback
            raise RuntimeError(
                f"Failed to initialize LLM with provider {cls.PROVIDER}: {e}\n"
                f"Configuration: {config}\n"
                f"NO FALLBACK ALLOWED - Human consultation required."
            ) from e
    
    @classmethod
    def get_provider_info(cls) -> dict[str, Any]:
        """
        Get information about current provider configuration.
        
        Returns:
            dict: Provider information including model and settings
        """
        return {
            "provider": cls.PROVIDER.value,
            "configuration": cls.MODELS[cls.PROVIDER],
            "api_key_env_var": (
                "OPENAI_API_KEY" if cls.PROVIDER == ModelProvider.OPENAI 
                else "OPENROUTER_API_KEY"
            ),
            "api_key_present": bool(
                os.getenv("OPENAI_API_KEY") if cls.PROVIDER == ModelProvider.OPENAI
                else os.getenv("OPENROUTER_API_KEY")
            ),
        }
    
    @classmethod
    def validate_configuration(cls) -> tuple[bool, str]:
        """
        Validate current LLM configuration.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check API key
            api_key_var = (
                "OPENAI_API_KEY" if cls.PROVIDER == ModelProvider.OPENAI 
                else "OPENROUTER_API_KEY"
            )
            
            if not os.getenv(api_key_var):
                return False, f"{api_key_var} not found in environment"
            
            # Try to import required modules
            if cls.PROVIDER == ModelProvider.OPENAI:
                from llama_index.llms.openai import OpenAI
            else:
                from src.llms.openrouter_compat import OpenRouterCompatLLM
            
            return True, "Configuration valid"
            
        except ImportError as e:
            return False, f"Import error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"