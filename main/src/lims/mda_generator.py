"""MDA generation workflow: extraction + RAG -> LLM -> preliminary MDATemplate.

Uses LlamaIndex Workflow + @step pattern from thesis unified_workflow.py.
LLM via OpenRouter (OpenAI-compatible SDK).

GAMP-5 Category 5: Custom pharmaceutical software component.
No fallback logic — all errors propagate with full diagnostics.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from openai import OpenAI

from .config import LIMSConfig
from .mda_schema import MDATemplate
from .prompts.mda_generation_prompt import MDA_GENERATION_SYSTEM_PROMPT
from .rag_loader import query_similar_templates

logger = logging.getLogger(__name__)


class MDAGenerationWorkflow(Workflow):
    """Generate a preliminary MDA from raw extraction + RAG context.

    Flow:
      1. Receive raw_extraction dict and LIMSConfig from StartEvent
      2. Query ChromaDB for similar MDA templates (RAG)
      3. Build LLM prompt with extraction data + RAG context
      4. Call LLM via OpenRouter (OpenAI-compatible)
      5. Parse and validate response as MDATemplate
      6. Return validated template in StopEvent
    """

    @step
    async def generate_mda(self, ctx: Context, ev: StartEvent) -> StopEvent:
        """RAG lookup + LLM generation -> validated MDATemplate."""
        raw_extraction: dict[str, Any] = ev.get("raw_extraction", {})
        config: LIMSConfig = ev.get("config")

        if not config:
            raise ValueError(
                "LIMSConfig is required. Pass config=get_lims_config() in StartEvent."
            )

        if not config.openrouter_api_key:
            raise ValueError(
                "LIMS_OPENROUTER_API_KEY is not set. "
                "Add it to .env.local to enable MDA generation."
            )

        # Serialize extraction for prompt (truncate to 3000 chars for token budget)
        extraction_summary = json.dumps(raw_extraction, indent=2, default=str)[:3000]

        logger.info(
            "Starting MDA generation (extraction: %d chars, model: %s)",
            len(extraction_summary),
            config.openrouter_model,
        )

        # 1. Query ChromaDB for similar MDA templates
        rag_failure: str | None = None
        rag_examples: list[str] = []
        try:
            rag_examples = query_similar_templates(
                extraction_text=extraction_summary,
                top_k=2,
                chroma_path=config.chromadb_path,
            )
            logger.info("RAG returned %d similar templates", len(rag_examples))
        except RuntimeError as e:
            # RuntimeError = collection not seeded yet — transparent degradation
            rag_failure = f"RAG unavailable: {e}"
            logger.warning(rag_failure)

        rag_context = (
            "\n---\n".join(rag_examples)
            if rag_examples
            else "No example templates available."
        )

        # 2. Build LLM prompt
        user_prompt = (
            f"## Raw Extraction Data\n```json\n{extraction_summary}\n```\n\n"
            f"## Similar MDA Templates (RAG)\n{rag_context}\n\n"
            f"Generate a complete MDATemplate JSON with all 4 sheets "
            f"(analyses, components, calc_variables, calculations).\n"
            f"Follow the naming conventions and result type rules strictly."
        )

        # 3. Call LLM via OpenRouter (OpenAI-compatible)
        client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        logger.info("Calling OpenRouter model: %s", config.openrouter_model)

        response = client.chat.completions.create(
            model=config.openrouter_model,
            messages=[
                {"role": "system", "content": MDA_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError(
                f"LLM returned empty response. Model: {config.openrouter_model}, "
                f"finish_reason: {response.choices[0].finish_reason}"
            )

        logger.info(
            "LLM response received: %d chars, finish_reason=%s",
            len(raw_content),
            response.choices[0].finish_reason,
        )

        # 4. Parse JSON response
        try:
            raw_mda = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON: {e}\n"
                f"First 500 chars of response: {raw_content[:500]}"
            ) from e

        # 5. Validate with Pydantic MDATemplate
        mda = MDATemplate.model_validate(raw_mda)

        logger.info(
            "MDA generation complete: %d analyses, %d components, "
            "%d calc_variables, %d calculations",
            len(mda.analyses),
            len(mda.components),
            len(mda.calc_variables),
            len(mda.calculations),
        )

        return StopEvent(result={
            "mda_template": mda.model_dump(),
            "validated": True,
            "rag_examples_used": len(rag_examples),
            "rag_failure": rag_failure,
            "model_used": config.openrouter_model,
        })
