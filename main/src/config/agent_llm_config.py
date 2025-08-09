"""
Agent-specific LLM configuration.
OSS models (DeepSeek) for all agents except OQ generation which uses OpenAI.
"""

import os
from typing import Any
from enum import Enum
from dotenv import load_dotenv

from llama_index.core.llms import LLM

# Load environment variables
load_dotenv()


class AgentType(Enum):
    """Types of agents in the system."""
    CATEGORIZATION = "categorization"
    CONTEXT_PROVIDER = "context_provider"
    RESEARCH = "research"
    SME = "sme"
    OQ_GENERATOR = "oq_generator"


class AgentLLMConfig:
    """
    Agent-specific LLM configuration.
    
    Strategy:
    - OSS (DeepSeek) for all agents except OQ generation
    - OpenAI for OQ generation only (better at structured output)
    """
    
    @classmethod
    def get_llm_for_agent(cls, agent_type: AgentType, **override_kwargs: Any) -> LLM:
        """
        Get the appropriate LLM for a specific agent.
        
        Args:
            agent_type: The type of agent requesting the LLM
            **override_kwargs: Optional parameter overrides
            
        Returns:
            Configured LLM instance
        """
        
        # OQ Generator uses OpenAI for better structured output
        if agent_type == AgentType.OQ_GENERATOR:
            return cls._get_openai_llm(**override_kwargs)
        
        # All other agents use OSS (DeepSeek)
        return cls._get_oss_llm(**override_kwargs)
    
    @classmethod
    def _get_openai_llm(cls, **override_kwargs: Any) -> LLM:
        """Get OpenAI LLM for OQ generation - using GPT-4 Turbo."""
        from llama_index.llms.openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found for OQ generation")
        
        config = {
            "model": "gpt-4-turbo-preview",  # Use GPT-4 Turbo for reliable generation
            "temperature": 0.1,
            "max_tokens": 4096,  # OpenAI's limit
        }
        
        # Apply overrides
        config.update(override_kwargs)
        
        return OpenAI(
            api_key=api_key,
            **config
        )
    
    @classmethod
    def _get_oss_llm(cls, **override_kwargs: Any) -> LLM:
        """Get OSS (DeepSeek) LLM for other agents."""
        from src.llms.openrouter_compat import OpenRouterCompatLLM
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found for OSS agents")
        
        config = {
            "model": "deepseek/deepseek-chat",
            "temperature": 0.1,
            "max_tokens": 30000,  # DeepSeek can handle more tokens
        }
        
        # Apply overrides
        config.update(override_kwargs)
        
        return OpenRouterCompatLLM(
            openrouter_api_key=api_key,
            **config
        )
    
    @classmethod
    def get_agent_config_info(cls) -> dict:
        """Get information about agent LLM configuration."""
        return {
            "strategy": "OSS for all agents including OQ generation",
            "oss_model": "deepseek/deepseek-chat",
            "oq_model": "deepseek/deepseek-chat",
            "oss_api_key_present": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
            "agent_assignments": {
                "categorization": "OSS (DeepSeek)",
                "context_provider": "OSS (DeepSeek)",
                "research": "OSS (DeepSeek)",
                "sme": "OSS (DeepSeek)",
                "oq_generator": "OSS (DeepSeek)"
            }
        }