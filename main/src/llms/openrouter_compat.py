"""
OpenRouter LLM Compatibility Wrapper for LlamaIndex.

This module provides a compatibility wrapper that inherits from OpenAI's LLM
to pass LlamaIndex's Pydantic validation while routing requests to OpenRouter.
"""

import json
import os
import time
import uuid
from collections.abc import Sequence
from typing import Any

import requests
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
    MessageRole,
)
from llama_index.core.callbacks import CallbackManager, CBEventType, EventPayload
from llama_index.llms.openai import OpenAI

# Import OpenTelemetry for direct span creation
try:
    from openinference.semconv.trace import SpanAttributes
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    # Get tracer for OpenRouter LLM
    tracer = trace.get_tracer("openrouter_compat_llm")
    OTEL_AVAILABLE = True
except ImportError:
    tracer = None
    OTEL_AVAILABLE = False

# Import configurable timeout support
from src.config.timeout_config import TimeoutConfig


class OpenRouterCompatLLM(OpenAI):
    """
    OpenRouter compatibility wrapper that inherits from OpenAI LLM.
    
    This class passes LlamaIndex's Pydantic validation by inheriting from
    the OpenAI class, but overrides all API calls to use OpenRouter instead.
    
    CRITICAL: NO FALLBACKS - This wrapper fails explicitly if OpenRouter fails.
    """

    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
        openrouter_api_key: str | None = None,
        api_base: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.1,
        max_tokens: int = 30000,  # Increased to 30000 to prevent JSON truncation of 25 test cases
        callback_manager: CallbackManager | None = None,
        **kwargs: Any,
    ):
        """
        Initialize OpenRouter compatibility wrapper.
        
        Args:
            model: OpenRouter model identifier 
            openrouter_api_key: OpenRouter API key
            api_base: OpenRouter API base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            callback_manager: Callback manager for tracing
            **kwargs: Additional arguments
            
        Raises:
            ValueError: If OpenRouter API key is missing (NO FALLBACKS)
        """
        # Get OpenRouter API key first (before parent init)
        openrouter_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")

        if not openrouter_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable. "
                "NO FALLBACK ALLOWED - Human consultation required."
            )

        # Initialize parent OpenAI class with dummy OpenAI key to pass validation
        # The actual API calls will be overridden to use OpenRouter
        dummy_openai_key = "sk-dummy-key-for-llamaindex-validation"

        super().__init__(
            model="gpt-4",  # Use valid OpenAI model name for validation
            api_key=dummy_openai_key,
            temperature=temperature,
            max_tokens=max_tokens,
            callback_manager=callback_manager,
            **kwargs,
        )

        # Store OpenRouter settings after parent initialization
        self._openrouter_api_key = openrouter_key
        self._openrouter_api_base = api_base
        self._openrouter_model = model

        # Override with actual OpenRouter model after initialization
        self.model = model

    def _calculate_tokens(self, text: str) -> int:
        """
        Estimate token count using simple approximation.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count (1 token ≈ 4 characters)
        """
        return max(1, len(text) // 4)

    def _emit_llm_event(self, event_type: CBEventType, payload: dict) -> None:
        """
        Emit LLM callback event if callback manager exists.
        
        Args:
            event_type: Type of callback event
            payload: Event payload data
        """
        if self.callback_manager is not None:
            if event_type == CBEventType.LLM:
                if "template" in payload:  # Start event
                    self.callback_manager.on_event_start(event_type, payload)
                else:  # End event
                    self.callback_manager.on_event_end(event_type, payload)

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata for OpenRouter model."""
        return LLMMetadata(
            context_window=128000,  # OpenRouter models typically support large context
            num_output=self.max_tokens,
            model_name=self.model,
            is_chat_model=True,
        )

    def _make_openrouter_request(self, messages: list[dict], stream: bool = False) -> dict:
        """
        Make API request to OpenRouter.
        
        Args:
            messages: List of messages in OpenAI format
            stream: Whether to stream the response
            
        Returns:
            Response data from OpenRouter API
            
        Raises:
            RuntimeError: If API request fails (NO FALLBACKS)
        """
        headers = {
            "Authorization": f"Bearer {self._openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "GAMP-5 Pharmaceutical Test Generation"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }

        # Get configurable timeout with logging
        api_timeout = TimeoutConfig.get_timeout("openrouter_api")

        try:
            response = requests.post(
                f"{self._openrouter_api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=api_timeout  # Now configurable via environment
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"OpenRouter API request timed out after {api_timeout} seconds. "
                f"Configure with OPENROUTER_API_TIMEOUT environment variable. "
                f"Current timeout hierarchy - API: {api_timeout}s, "
                f"SME Agent: {TimeoutConfig.get_timeout('sme_agent')}s, "
                f"OQ Generator: {TimeoutConfig.get_timeout('oq_generator')}s. "
                f"NO FALLBACK ALLOWED - Human consultation required."
            ) from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"OpenRouter API request failed: {e}. "
                f"NO FALLBACK ALLOWED - Human consultation required."
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"OpenRouter API error: {e}. "
                f"NO FALLBACK ALLOWED - Human consultation required."
            ) from e

    def complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        """Complete the prompt using OpenRouter API with OpenTelemetry tracing."""
        # Convert prompt to chat format for OpenRouter
        messages = [{"role": "user", "content": prompt}]

        # Create OpenTelemetry span for Phoenix
        span = None
        if OTEL_AVAILABLE and tracer:
            span = tracer.start_span("llm.completion")
            # Set Phoenix/OpenInference attributes
            span.set_attribute(SpanAttributes.LLM_MODEL_NAME, self.model)
            span.set_attribute(SpanAttributes.LLM_PROVIDER, "openrouter")
            span.set_attribute(SpanAttributes.LLM_SYSTEM, "OpenRouter")
            span.set_attribute(SpanAttributes.LLM_PROMPTS, [prompt])
            span.set_attribute(SpanAttributes.INPUT_VALUE, prompt)
            # Set invocation parameters as a JSON string (OpenInference convention)
            span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS, json.dumps({
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "provider": "openrouter"
            }))

        # Emit start event for callbacks
        event_id = str(uuid.uuid4())
        start_payload = {
            EventPayload.TEMPLATE: prompt,
            EventPayload.MODEL_NAME: self.model,
            EventPayload.PROMPT: prompt,
            "event_id": event_id,
            "model_dict": {
                "model_name": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        }
        self._emit_llm_event(CBEventType.LLM, start_payload)

        try:
            start_time = time.time()
            response_data = self._make_openrouter_request(messages)
            latency = time.time() - start_time

            text = response_data["choices"][0]["message"]["content"]

            # Calculate token usage
            prompt_tokens = self._calculate_tokens(prompt)
            completion_tokens = self._calculate_tokens(text)
            total_tokens = prompt_tokens + completion_tokens

            # Update OpenTelemetry span with response
            if span:
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, text)
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, prompt_tokens)
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, completion_tokens)
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, total_tokens)
                span.set_attribute("llm.latency_ms", latency * 1000)
                span.set_status(Status(StatusCode.OK))

            # Create response object
            response = CompletionResponse(
                text=text,
                raw=response_data,
            )

            # Emit end event for callbacks
            end_payload = {
                EventPayload.RESPONSE: response,
                EventPayload.PROMPT: prompt,
                "event_id": event_id,
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                }
            }
            self._emit_llm_event(CBEventType.LLM, end_payload)

            return response
        except Exception as e:
            # Set error status on span
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)

            # Emit error event for callbacks
            error_payload = {
                EventPayload.EXCEPTION: str(e),
                "event_id": event_id,
            }
            self._emit_llm_event(CBEventType.LLM, error_payload)
            raise RuntimeError(f"OpenRouter completion failed: {e}") from e
        finally:
            # End the span
            if span:
                span.end()

    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        """Stream complete the prompt (not implemented)."""
        raise NotImplementedError(
            "Streaming not implemented for OpenRouter compatibility wrapper. "
            "Use non-streaming methods only."
        )

    def chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Chat with the model using OpenRouter API with OpenTelemetry tracing."""
        # Convert ChatMessage objects to dict format for OpenRouter
        message_dicts = []
        messages_text = ""
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            message_dicts.append({
                "role": role,
                "content": msg.content
            })
            messages_text += f"{role}: {msg.content}\n"

        # Create OpenTelemetry span for Phoenix
        span = None
        if OTEL_AVAILABLE and tracer:
            span = tracer.start_span("llm.chat")
            # Set Phoenix/OpenInference attributes
            span.set_attribute(SpanAttributes.LLM_MODEL_NAME, self.model)
            span.set_attribute(SpanAttributes.LLM_PROVIDER, "openrouter")
            span.set_attribute(SpanAttributes.LLM_SYSTEM, "OpenRouter")

            # Set messages as input
            span.set_attribute(SpanAttributes.INPUT_VALUE, messages_text)
            # Set messages in OpenInference format
            span.set_attribute(SpanAttributes.LLM_INPUT_MESSAGES,
                             [{"role": m["role"], "content": m["content"]} for m in message_dicts])
            # Set invocation parameters as a JSON string (OpenInference convention)
            span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS, json.dumps({
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "provider": "openrouter"
            }))

        # Emit start event for callbacks
        event_id = str(uuid.uuid4())
        start_payload = {
            EventPayload.MESSAGES: list(messages),
            EventPayload.MODEL_NAME: self.model,
            "event_id": event_id,
            "model_dict": {
                "model_name": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        }
        self._emit_llm_event(CBEventType.LLM, start_payload)

        try:
            start_time = time.time()
            response_data = self._make_openrouter_request(message_dicts)
            latency = time.time() - start_time

            message_data = response_data["choices"][0]["message"]

            # Calculate token usage
            input_tokens = self._calculate_tokens(messages_text)
            output_tokens = self._calculate_tokens(message_data["content"])
            total_tokens = input_tokens + output_tokens

            # Update OpenTelemetry span with response
            if span:
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, message_data["content"])
                span.set_attribute(SpanAttributes.LLM_OUTPUT_MESSAGES,
                                 [{"role": message_data["role"], "content": message_data["content"]}])
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, input_tokens)
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, output_tokens)
                span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, total_tokens)
                span.set_attribute("llm.latency_ms", latency * 1000)
                span.set_status(Status(StatusCode.OK))

            # Create response object
            response = ChatResponse(
                message=ChatMessage(
                    role=MessageRole(message_data["role"]),
                    content=message_data["content"],
                ),
                raw=response_data,
            )

            # Emit end event for callbacks
            end_payload = {
                EventPayload.RESPONSE: response,
                EventPayload.MESSAGES: list(messages),
                "event_id": event_id,
                "token_usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }
            }
            self._emit_llm_event(CBEventType.LLM, end_payload)

            return response
        except Exception as e:
            # Set error status on span
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)

            # Emit error event for callbacks
            error_payload = {
                EventPayload.EXCEPTION: str(e),
                "event_id": event_id,
            }
            self._emit_llm_event(CBEventType.LLM, error_payload)
            raise RuntimeError(f"OpenRouter chat failed: {e}") from e
        finally:
            # End the span
            if span:
                span.end()

    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        """Stream chat with the model (not implemented)."""
        raise NotImplementedError(
            "Streaming not implemented for OpenRouter compatibility wrapper. "
            "Use non-streaming methods only."
        )

    async def acomplete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        """Async complete using OpenRouter API."""
        # Reuse the synchronous implementation for now
        # This ensures the same instrumentation is applied
        return self.complete(prompt, formatted, **kwargs)

    async def astream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        """Async stream complete (not implemented)."""
        raise NotImplementedError(
            "Async streaming not implemented for OpenRouter compatibility wrapper."
        )

    async def achat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Async chat using OpenRouter API."""
        # Reuse the synchronous implementation for now
        # This ensures the same instrumentation is applied
        return self.chat(messages, **kwargs)

    async def astream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        """Async stream chat (not implemented)."""
        raise NotImplementedError(
            "Async streaming not implemented for OpenRouter compatibility wrapper."
        )

    def _as_query_component(self, **kwargs: Any) -> Any:
        """Return as query component."""
        # Return self to maintain compatibility
        return self

    def __str__(self) -> str:
        """String representation."""
        return f"OpenRouterCompatLLM(model={self.model}, api_base={self._openrouter_api_base})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"OpenRouterCompatLLM("
            f"model='{self.model}', "
            f"temperature={self.temperature}, "
            f"max_tokens={self.max_tokens}, "
            f"api_base='{self._openrouter_api_base}'"
            f")"
        )


# Factory function for creating OpenRouter compatible LLM
def create_openrouter_compat_llm(
    model: str = "openai/gpt-oss-120b",
    temperature: float = 0.1,
    max_tokens: int = 30000,
    **kwargs: Any
) -> OpenRouterCompatLLM:
    """
    Factory function to create OpenRouter compatible LLM.
    
    Args:
        model: OpenRouter model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional arguments
        
    Returns:
        OpenRouterCompatLLM instance
        
    Raises:
        ValueError: If configuration is invalid (NO FALLBACKS)
    """
    return OpenRouterCompatLLM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
