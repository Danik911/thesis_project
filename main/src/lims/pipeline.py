"""Two-Layer Pipeline orchestrator.

Orchestrates the full pipeline:
1. CLASSIFY: Detect test type via hybrid rules + keywords
2. TEMPLATE: Load curated skeleton for that test type
3. EXTRACT: Full LlamaExtract extraction (focused on variable fields at merge)
4. AUGMENT: Fill gaps from standards RAG + LLM
5. MERGE: Combine layers with provenance tracking
6. REVIEW: Ready for SME review

For TestType.OTHER: delegates to single-layer pipeline (backward compat).

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC for known test types.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional

from langfuse import get_client, observe
from pydantic import BaseModel, Field

from main.src.lims.classifier import TestTypeClassifier
from main.src.lims.config import LIMSConfig
from main.src.lims.focused_extractor import extract_text_from_pdf, focused_extract
from main.src.lims.merger import MergeResult, merge_layers
from main.src.lims.test_type import ClassificationResult, TestType

logger = logging.getLogger(__name__)


class PipelineStageDetail(BaseModel):
    """Record of what happened at each pipeline stage."""

    stage: str
    duration_ms: int
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)


class TwoLayerPipeline:
    """Orchestrates the two-layer extraction pipeline.

    For known test types (HPLC, LOD, Titration, Identity):
        Classify -> Template -> Extract -> Augment -> Merge -> Review

    For TestType.OTHER:
        Single-layer pipeline (existing flow) for backward compatibility.
    """

    def __init__(self, config: LIMSConfig) -> None:
        self.config = config
        self.classifier = TestTypeClassifier(
            confidence_threshold=config.classification_confidence_threshold
        )

    @observe(name="lims-two-layer-pipeline", capture_input=False, capture_output=False)
    async def run(
        self,
        pdf_content: bytes,
        filename: str,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the full two-layer pipeline.

        Args:
            pdf_content: Raw PDF bytes.
            filename: Original PDF filename.
            job_id: Optional job ID for state machine transitions.

        Returns:
            Dict with: classification, mda_template, provenance,
            conflicts, stage_details, pipeline_type, trace_id.

        Raises:
            ValueError: If classification or extraction fails.
            Exception: All errors propagate with full diagnostics.
        """
        # Log metadata manually (capture_input=False to avoid serializing PDF bytes)
        _lf = get_client()
        if _lf:
            _lf.update_current_span(
                input={"filename": filename, "job_id": job_id, "file_size": len(pdf_content)},
            )

        stages: list[PipelineStageDetail] = []

        # Stage 1: CLASSIFY
        start = time.perf_counter()
        await self._transition_job(job_id, "CLASSIFYING")

        pdf_text = extract_text_from_pdf(pdf_content)

        classification = self.classifier.classify(pdf_text, filename)

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="CLASSIFY",
            duration_ms=duration_ms,
            summary=(
                f"Classified as {classification.test_type.value} "
                f"(confidence: {classification.confidence:.2f}, "
                f"method: {classification.method})"
            ),
            details=classification.model_dump(),
        ))

        logger.info(
            "Pipeline stage CLASSIFY: %s (confidence=%.2f, method=%s) for '%s'",
            classification.test_type.value,
            classification.confidence,
            classification.method,
            filename,
        )

        # Check for OTHER -> single-layer fallback
        if classification.test_type == TestType.OTHER:
            return await self._single_layer_fallback(
                pdf_content, filename, job_id, classification, stages
            )

        # Stage 2: LOAD TEMPLATE
        start = time.perf_counter()
        await self._transition_job(job_id, "LOADING_TEMPLATE")

        from main.src.lims.templates import TemplateLibrary

        template = TemplateLibrary.get_template_for_type(classification.test_type)
        template_mda = template.to_mda_template()

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="TEMPLATE",
            duration_ms=duration_ms,
            summary=(
                f"Loaded {classification.test_type.value} template: "
                f"{len(template_mda.analyses)} analyses, "
                f"{len(template_mda.components)} components, "
                f"{len(template.get_variable_fields())} variable fields"
            ),
            details={
                "test_type": classification.test_type.value,
                "analysis_count": len(template_mda.analyses),
                "component_count": len(template_mda.components),
                "variable_fields": template.get_variable_fields(),
                "fixed_fields": template.get_fixed_fields(),
            },
        ))

        logger.info(
            "Pipeline stage TEMPLATE: loaded %s template "
            "(%d analyses, %d components, %d variable fields)",
            classification.test_type.value,
            len(template_mda.analyses),
            len(template_mda.components),
            len(template.get_variable_fields()),
        )

        # Stage 3: FOCUSED EXTRACT
        start = time.perf_counter()
        await self._transition_job(job_id, "EXTRACTING")

        extraction_result = await focused_extract(
            pdf_content, filename, template, self.config
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="EXTRACT",
            duration_ms=duration_ms,
            summary=(
                f"Extraction complete: validated={extraction_result.get('validated')}"
            ),
            details={
                "validated": extraction_result.get("validated"),
                "validation_error": extraction_result.get("validation_error"),
                "extraction_trace": extraction_result.get("extraction_trace"),
            },
        ))

        logger.info(
            "Pipeline stage EXTRACT: validated=%s for '%s'",
            extraction_result.get("validated"),
            filename,
        )

        # Stage 4: AUGMENT
        start = time.perf_counter()
        await self._transition_job(job_id, "AUGMENTING")

        augmented = await self._augment_gaps(
            template_mda, extraction_result, classification
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        suggestion_count = (
            len(augmented.get("suggestions", []))
            if augmented
            else 0
        )
        stages.append(PipelineStageDetail(
            stage="AUGMENT",
            duration_ms=duration_ms,
            summary=f"Augmentation: {suggestion_count} suggestions generated",
            details={"suggestion_count": suggestion_count},
        ))

        logger.info(
            "Pipeline stage AUGMENT: %d suggestions for '%s'",
            suggestion_count,
            filename,
        )

        # Stage 5: MERGE
        start = time.perf_counter()
        await self._transition_job(job_id, "MERGING")

        extracted_data = extraction_result.get("mda_template") or extraction_result.get(
            "normalized_extraction", {}
        )

        merge_result = merge_layers(
            template_mda=template_mda,
            extracted_data=extracted_data,
            augmented_data=augmented,
            test_type=classification.test_type,
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="MERGE",
            duration_ms=duration_ms,
            summary=(
                f"Merge complete: {len(merge_result.conflicts)} conflicts, "
                f"validation={'PASSED' if merge_result.validation_passed else 'FAILED'}, "
                f"stats={merge_result.stats}"
            ),
            details={
                "conflicts_count": len(merge_result.conflicts),
                "validation_passed": merge_result.validation_passed,
                "validation_error": merge_result.validation_error,
                "stats": merge_result.stats,
            },
        ))

        logger.info(
            "Pipeline stage MERGE: %d conflicts, validation=%s, stats=%s",
            len(merge_result.conflicts),
            merge_result.validation_passed,
            merge_result.stats,
        )

        # Stage 6: PENDING_REVIEW
        await self._transition_job(job_id, "PENDING_REVIEW")

        # Store results on job if available
        if job_id:
            self._store_results_on_job(
                job_id, classification, merge_result, stages, extraction_result
            )

        stages.append(PipelineStageDetail(
            stage="REVIEW",
            duration_ms=0,
            summary="MDA ready for SME review",
        ))

        # Capture Langfuse trace ID for frontend visibility
        _lf = get_client()
        trace_id = _lf.get_current_trace_id() if _lf else None

        return {
            "classification": classification.model_dump(),
            "mda_template": merge_result.mda_template,
            "provenance": merge_result.provenance,
            "conflicts": [c.model_dump() for c in merge_result.conflicts],
            "stage_details": [s.model_dump() for s in stages],
            "pipeline_type": "two_layer",
            "test_type": classification.test_type.value,
            "extraction_trace": extraction_result.get("extraction_trace"),
            "raw_extraction": extraction_result.get("raw_extraction"),
            "validated": merge_result.validation_passed,
            "validation_error": merge_result.validation_error,
            "trace_id": trace_id,
        }

    @observe(name="lims-augment")
    async def _augment_gaps(
        self,
        template_mda: "MDATemplate",
        extraction_result: dict[str, Any],
        classification: ClassificationResult,
    ) -> dict[str, Any] | None:
        """Fill gaps from standards RAG + LLM.

        Queries ChromaDB for relevant standards, then asks LLM to suggest
        values for fields that are still empty after extraction.

        Returns:
            Dict with "suggestions" key, or None if augmentation is skipped.
        """
        if not self.config.openrouter_api_key:
            logger.info(
                "Augmentation skipped: LIMS_OPENROUTER_API_KEY not configured"
            )
            return None

        from main.src.lims.standards_loader import query_standards

        test_type = classification.test_type.value
        query_text = (
            f"{test_type} test method MDA template: "
            f"standard components, calculation patterns, "
            f"equipment groups, reagent lists"
        )

        # query_standards has its own @observe("rag-standards-query") — auto-nests here
        standards_results = query_standards(
            query_text=query_text,
            collection_name=self.config.standards_collection,
            top_k=self.config.rag_standards_top_k,
            chroma_path=self.config.chromadb_path,
        )

        standards_context = "\n\n".join(
            f"--- {r.get('title', 'Untitled')} ---\n{r.get('content', '')}"
            for r in standards_results
        )

        extracted_data = extraction_result.get("mda_template") or extraction_result.get(
            "normalized_extraction", {}
        )

        from main.src.lims.prompts.augmentation_prompt import (
            AUGMENTATION_SYSTEM_PROMPT,
        )

        user_prompt = (
            f"Test type: {test_type}\n\n"
            f"Template analyses: {len(template_mda.analyses)}\n"
            f"Template components: {len(template_mda.components)}\n\n"
            f"Extraction result:\n{json.dumps(extracted_data, indent=2, default=str)[:3000]}\n\n"
            f"Standards context:\n{standards_context[:3000]}\n\n"
            "Identify gaps in the extraction and suggest values from the standards. "
            "Return JSON with a 'suggestions' array."
        )

        from openai import OpenAI

        client = OpenAI(
            api_key=self.config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model=self.config.openrouter_model,
            messages=[
                {"role": "system", "content": AUGMENTATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        response_text = response.choices[0].message.content or "{}"
        augmented = json.loads(response_text)

        if "suggestions" not in augmented:
            augmented = {"suggestions": []}

        suggestion_count = len(augmented.get("suggestions", []))

        # Log LLM call metadata on this observation
        _lf = get_client()
        if _lf:
            _lf.update_current_span(
                input={"test_type": test_type, "model": self.config.openrouter_model},
                output={
                    "suggestion_count": suggestion_count,
                    "rag_results_count": len(standards_results),
                    "response_length": len(response_text),
                },
            )

        logger.info(
            "Augmentation LLM returned %d suggestions",
            suggestion_count,
        )
        return augmented

    async def _single_layer_fallback(
        self,
        pdf_content: bytes,
        filename: str,
        job_id: str | None,
        classification: ClassificationResult,
        stages: list[PipelineStageDetail],
    ) -> dict[str, Any]:
        """Run the existing single-layer extraction for TestType.OTHER.

        Replicates the current extract_pdf flow:
        1. Run LlamaExtract extraction
        2. Optionally trigger MDA generation workflow

        Args:
            pdf_content: Raw PDF bytes.
            filename: Original filename.
            job_id: Optional job ID for state transitions.
            classification: The classification result (OTHER).
            stages: Stage details list to append to.

        Returns:
            Pipeline result dict with pipeline_type="single_layer".
        """
        logger.info(
            "TestType.OTHER for '%s' — running single-layer pipeline",
            filename,
        )

        from main.src.lims.pdf_extractor import extract_mda_from_pdf

        start = time.perf_counter()
        await self._transition_job(job_id, "EXTRACTING")

        result = await asyncio.to_thread(
            extract_mda_from_pdf,
            pdf_content=pdf_content,
            filename=filename,
            config=self.config,
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="EXTRACT_SINGLE_LAYER",
            duration_ms=duration_ms,
            summary=f"Single-layer extraction: validated={result.get('validated')}",
            details={
                "validated": result.get("validated"),
                "extraction_trace": result.get("extraction_trace"),
            },
        ))

        mda_generation: dict[str, Any] | None = None
        if self.config.openrouter_api_key:
            try:
                if job_id:
                    await self._transition_job(job_id, "GENERATING")

                from main.src.lims.mda_generator import MDAGenerationWorkflow

                workflow = MDAGenerationWorkflow()
                gen_result = await workflow.run(
                    raw_extraction=result.get("raw_extraction", {}),
                    config=self.config,
                )
                mda_generation = gen_result

                if job_id:
                    await self._transition_job(job_id, "PENDING_REVIEW")

            except Exception as e:
                logger.exception(
                    "MDA generation failed in single-layer pipeline: %s", e
                )
                mda_generation = {"generation_error": f"{type(e).__name__}: {e}"}
                if job_id:
                    await self._transition_job(job_id, "FAILED")
        else:
            if job_id:
                from main.src.lims.job_store import get_job

                job = get_job(job_id)
                job.raw_extraction = result.get("raw_extraction")
                job.extraction_trace = result.get("extraction_trace")
                if result.get("mda_template"):
                    job.mda_template = result["mda_template"]

                await self._transition_job(job_id, "PENDING_REVIEW")

        return {
            "classification": classification.model_dump(),
            "mda_template": result.get("mda_template"),
            "raw_extraction": result.get("raw_extraction"),
            "extraction_trace": result.get("extraction_trace"),
            "validated": result.get("validated"),
            "validation_error": result.get("validation_error"),
            "mda_generation": mda_generation,
            "stage_details": [s.model_dump() for s in stages],
            "pipeline_type": "single_layer",
            "test_type": "OTHER",
        }

    async def _transition_job(
        self, job_id: str | None, status_name: str
    ) -> None:
        """Transition job state if job_id is provided.

        Uses deferred import to avoid circular imports.
        """
        if job_id is None:
            return

        from main.src.lims.job_store import LIMSJobStatus, update_status

        new_status = LIMSJobStatus(status_name)
        update_status(job_id, new_status)

    def _store_results_on_job(
        self,
        job_id: str,
        classification: ClassificationResult,
        merge_result: MergeResult,
        stages: list[PipelineStageDetail],
        extraction_result: dict[str, Any],
    ) -> None:
        """Store pipeline results on the job record."""
        from main.src.lims.job_store import get_job

        try:
            job = get_job(job_id)
            job.classification = classification.model_dump()
            job.mda_template = merge_result.mda_template
            job.provenance = merge_result.provenance
            job.conflicts = [c.model_dump() for c in merge_result.conflicts]
            job.stage_details = [s.model_dump() for s in stages]
            job.raw_extraction = extraction_result.get("raw_extraction")
            job.extraction_trace = extraction_result.get("extraction_trace")
            job.validated = merge_result.validation_passed
            job.validation_error = merge_result.validation_error
        except KeyError:
            logger.warning("Could not store results: job %s not found", job_id)
