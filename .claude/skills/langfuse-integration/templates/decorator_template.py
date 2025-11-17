"""
Langfuse Decorator Templates for Pharmaceutical Test Generation

Copy-paste templates for common instrumentation patterns.
"""

from langfuse import observe, get_current_observation, get_current_trace
from datetime import datetime, timezone


# Template 1: Basic Function Tracing
@observe()
def basic_function(param1: str, param2: int) -> dict:
    """Basic function with automatic input/output capture."""
    result = {"status": "success", "data": []}
    return result


# Template 2: Async Function Tracing
@observe()
async def async_function(param1: str) -> dict:
    """Async function with automatic tracing."""
    result = await some_async_operation(param1)
    return result


# Template 3: LLM Generation Tracing
@observe(name="llm-generation", as_type="generation")
async def llm_generation(prompt: str) -> str:
    """LLM call with token usage tracking."""
    response = await llm.acomplete(prompt)

    # Update token usage for DeepSeek
    obs = get_current_observation()
    if obs and hasattr(response, 'usage'):
        obs.update(usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        })

    return response.text


# Template 4: GAMP-5 Categorization
@observe(name="gamp5-categorization")
async def gamp5_categorization(urs_content: str) -> dict:
    """Categorization with compliance metadata."""
    category = await classify(urs_content)
    confidence = calculate_confidence(category)

    obs = get_current_observation()
    if obs:
        obs.update(metadata={
            "compliance.gamp5.applicable": True,
            "compliance.gamp5.category": category,
            "compliance.gamp5.confidence": confidence,
            "compliance.timestamp": datetime.now(timezone.utc).isoformat()
        })

    return {"category": category, "confidence": confidence}


# Template 5: Workflow Entry Point with ALCOA+ Attributes
@observe(name="workflow-entry-point")
async def workflow_entry_point(
    user_id: str,
    urs_file: str,
    job_id: str
) -> dict:
    """Set trace-level compliance attributes."""
    trace = get_current_trace()
    if trace:
        trace.update(
            user_id=user_id,
            session_id=job_id,
            tags=["pharmaceutical", "gamp5", "alcoa-plus"],
            metadata={
                "compliance.gamp5.applicable": True,
                "compliance.alcoa_plus.attributable": True,
                "compliance.alcoa_plus.contemporaneous": True,
                "user.clerk_id": user_id,
                "job.id": job_id,
                "session.timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    result = await process_workflow(urs_file)
    return result


# Template 6: Error Handling (No Fallbacks)
@observe()
async def function_with_error_handling(data: dict) -> dict:
    """Explicit error capture without fallback logic."""
    try:
        validated_data = validate(data)

        if not validated_data:
            raise ValueError("Validation failed")

        result = await process(validated_data)
        return result

    except ValueError as e:
        obs = get_current_observation()
        if obs:
            obs.update(metadata={
                "error.type": "ValidationError",
                "error.message": str(e)
            })
        raise  # Always re-raise


# Template 7: Retry Logic with Visibility
@observe()
async def function_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Retry logic with trace metadata."""
    obs = get_current_observation()

    for attempt in range(max_retries):
        try:
            response = await call_api(prompt)

            if obs:
                obs.update(metadata={
                    "retry.attempt": attempt + 1,
                    "retry.success": True
                })

            return response

        except RateLimitError as e:
            if obs:
                obs.update(metadata={
                    f"retry.attempt_{attempt + 1}.error": "RateLimitError",
                    f"retry.attempt_{attempt + 1}.message": str(e)
                })

            if attempt == max_retries - 1:
                raise

            await asyncio.sleep(2 ** attempt)

    raise RuntimeError("Retry logic failed")
