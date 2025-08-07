"""
OpenRouter LLM integration for LlamaIndex.

This module provides a custom LLM class that wraps OpenRouter API
to work with LlamaIndex without model name validation issues.
"""

import os
from typing import Any, Optional, Sequence
import requests
import json

from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
    MessageRole,
)
from llama_index.core.callbacks import CallbackManager
from llama_index.core.base.query_pipeline.query import QueryComponent


class OpenRouterLLM(BaseLLM):
    """Custom LLM class for OpenRouter API integration."""
    
    model: str = "meta-llama/llama-3.1-8b-instruct:free"
    api_key: Optional[str] = None
    api_base: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.1
    max_tokens: int = 2000
    
    def __init__(
        self,
        model: str = "meta-llama/llama-3.1-8b-instruct:free",
        api_key: Optional[str] = None,
        api_base: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        callback_manager: Optional[CallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize OpenRouter LLM."""
        super().__init__(
            model=model,
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens,
            callback_manager=callback_manager,
            **kwargs,
        )
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable.")
    
    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=8192,  # Default context window
            num_output=self.max_tokens,
            model_name=self.model,
            is_chat_model=True,
        )
    
    @property
    def _model_kwargs(self) -> dict:
        """Get model kwargs."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def _make_api_request(self, messages: list[dict], stream: bool = False) -> dict:
        """Make API request to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "GAMP-5 Test Generation"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        """Complete the prompt."""
        # Convert prompt to chat format
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self._make_api_request(messages)
            text = response["choices"][0]["message"]["content"]
            
            return CompletionResponse(
                text=text,
                raw=response,
            )
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}")
    
    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        """Stream complete the prompt."""
        raise NotImplementedError("Streaming not implemented for OpenRouter LLM")
    
    def chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Chat with the model."""
        # Convert ChatMessage objects to dict format
        message_dicts = []
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            message_dicts.append({
                "role": role,
                "content": msg.content
            })
        
        try:
            response = self._make_api_request(message_dicts)
            message = response["choices"][0]["message"]
            
            return ChatResponse(
                message=ChatMessage(
                    role=MessageRole(message["role"]),
                    content=message["content"],
                ),
                raw=response,
            )
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}")
    
    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        """Stream chat with the model."""
        raise NotImplementedError("Streaming not implemented for OpenRouter LLM")
    
    async def acomplete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        """Async complete."""
        return self.complete(prompt, formatted, **kwargs)
    
    async def astream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        """Async stream complete."""
        raise NotImplementedError("Async streaming not implemented")
    
    async def achat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Async chat."""
        return self.chat(messages, **kwargs)
    
    async def astream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        """Async stream chat."""
        raise NotImplementedError("Async streaming not implemented")
    
    def _as_query_component(self, **kwargs: Any) -> 'QueryComponent':
        """Return as query component."""
        # This is required by LlamaIndex but not used in our implementation
        return self