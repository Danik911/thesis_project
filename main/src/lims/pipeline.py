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
import re
import time
from typing import Any, Optional

from langfuse import get_client, observe
from pydantic import BaseModel, Field

from main.src.lims.classifier import TestTypeClassifier
from main.src.lims.config import LIMSConfig
from main.src.lims.focused_extractor import extract_text_from_pdf, focused_extract
from main.src.lims.merger import MergeResult, merge_layers
from main.src.lims.provenance import ComponentSource
from main.src.lims.test_type import ClassificationResult, TestType

logger = logging.getLogger(__name__)


_HIGH_RISK_PATH_PATTERNS = (
    r"components\[\d+\]\.result_type$",
    r"components\[\d+\]\.analysis$",
    r"calc_variables\[\d+\]\.analysis$",
    r"calculations\[\d+\]\.analysis$",
    r"calculations\[\d+\]\.source_code$",
)


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

    def _enforce_extraction_quality_gate(
        self,
        extraction_result: dict[str, Any],
        filename: str,
        *,
        require_validated_override: bool | None = None,
    ) -> None:
        """Fail loudly when extraction quality does not meet gate criteria."""
        if not self.config.extraction_quality_gate_enabled:
            return

        quality_metrics = extraction_result.get("quality_metrics") or {}
        null_ratio = float(
            quality_metrics.get(
                "critical_null_ratio",
                quality_metrics.get("null_ratio", 1.0),
            )
        )
        validated = bool(extraction_result.get("validated"))
        validation_error = extraction_result.get("validation_error")

        reasons: list[str] = []
        require_validated = (
            self.config.require_validated_extraction
            if require_validated_override is None
            else require_validated_override
        )

        if require_validated and not validated:
            reasons.append("validated=false")

        if null_ratio > self.config.extraction_max_null_ratio:
            reasons.append(
                "null_ratio="
                f"{null_ratio:.3f} exceeds max={self.config.extraction_max_null_ratio:.3f}"
            )

        if reasons:
            trace = extraction_result.get("extraction_trace") or {}
            diag = {
                "filename": filename,
                "quality_gate_enabled": self.config.extraction_quality_gate_enabled,
                "require_validated_extraction": require_validated,
                "configured_max_null_ratio": self.config.extraction_max_null_ratio,
                "validated": validated,
                "quality_metrics": quality_metrics,
                "validation_error": validation_error,
                "extraction_trace": {
                    "run_id": trace.get("run_id"),
                    "run_status": trace.get("run_status"),
                    "agent_name": trace.get("agent_name"),
                },
            }
            msg = (
                "Extraction quality gate failed: "
                + "; ".join(reasons)
                + f" | diagnostics={diag}"
            )
            raise ValueError(msg)

    def _evaluate_retrieval_quality(
        self,
        retrieval_metrics: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Evaluate retrieval quality against configured P1 thresholds."""
        if not self.config.retrieval_quality_gate_enabled:
            return True, []

        returned_count = int(retrieval_metrics.get("returned_count", 0))
        avg_distance = float(retrieval_metrics.get("avg_distance", 2.0))
        avg_token_overlap = float(retrieval_metrics.get("avg_token_overlap", 0.0))
        method_match_ratio = float(retrieval_metrics.get("method_match_ratio", 0.0))

        reasons: list[str] = []
        if returned_count < self.config.retrieval_min_results:
            reasons.append(
                "returned_count="
                f"{returned_count} < min_results={self.config.retrieval_min_results}"
            )
        if avg_distance > self.config.retrieval_max_distance:
            reasons.append(
                "avg_distance="
                f"{avg_distance:.3f} > max_distance={self.config.retrieval_max_distance:.3f}"
            )
        if avg_token_overlap < self.config.retrieval_min_avg_token_overlap:
            reasons.append(
                "avg_token_overlap="
                f"{avg_token_overlap:.3f} < min_overlap={self.config.retrieval_min_avg_token_overlap:.3f}"
            )

        method_family = retrieval_metrics.get("method_family")
        if method_family and method_match_ratio < self.config.retrieval_min_method_match_ratio:
            reasons.append(
                "method_match_ratio="
                f"{method_match_ratio:.3f} < min_method_match={self.config.retrieval_min_method_match_ratio:.3f}"
            )

        return len(reasons) == 0, reasons

    def _collect_low_confidence_high_risk_fields(
        self,
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Collect low-confidence edits on high-risk fields for HITL routing."""
        fields = provenance.get("fields") if isinstance(provenance, dict) else None
        if not isinstance(fields, dict):
            return []

        flagged: list[dict[str, Any]] = []
        for path, prov in fields.items():
            if not isinstance(prov, dict):
                continue

            if not any(re.search(pattern, path) for pattern in _HIGH_RISK_PATH_PATTERNS):
                continue

            source = str(prov.get("source", ""))
            if source not in {ComponentSource.EXTRACTED.value, ComponentSource.INFERRED.value}:
                continue

            confidence = float(prov.get("confidence", 0.0))
            if confidence < self.config.low_confidence_review_threshold:
                flagged.append({
                    "field_path": path,
                    "source": source,
                    "confidence": confidence,
                    "threshold": self.config.low_confidence_review_threshold,
                })

        return flagged

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

        try:
            # Two-layer extraction is intentionally partial and template-guided.
            # Full strict MDATemplate validation at this stage is advisory only.
            self._enforce_extraction_quality_gate(
                extraction_result,
                filename,
                require_validated_override=False,
            )
        except Exception:
            await self._transition_job(job_id, "FAILED")
            raise

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
                "quality_metrics": extraction_result.get("quality_metrics"),
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
            template_mda, extraction_result, classification, filename
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
            details={
                "suggestion_count": suggestion_count,
                "retrieval_metrics": augmented.get("retrieval_metrics") if augmented else None,
                "retrieval_quality_passed": augmented.get("retrieval_quality_passed") if augmented else None,
                "retrieval_quality_reasons": augmented.get("retrieval_quality_reasons") if augmented else None,
            },
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

        review_routing = {
            "requires_human_review": False,
            "low_confidence_high_risk_fields": [],
        }
        low_confidence_fields = self._collect_low_confidence_high_risk_fields(
            merge_result.provenance
        )
        if low_confidence_fields:
            review_routing = {
                "requires_human_review": True,
                "low_confidence_high_risk_fields": low_confidence_fields,
            }

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
                "review_routing": review_routing,
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
                job_id,
                classification,
                merge_result,
                stages,
                extraction_result,
                review_routing,
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
            "review_routing": review_routing,
            "retrieval_metrics": augmented.get("retrieval_metrics") if augmented else None,
        }

    @observe(name="lims-augment")
    async def _augment_gaps(
        self,
        template_mda: "MDATemplate",
        extraction_result: dict[str, Any],
        classification: ClassificationResult,
        filename: str,
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

        from main.src.lims.standards_loader import query_standards_with_metrics

        test_type = classification.test_type.value
        query_text = (
            f"{test_type} test method MDA template: "
            f"standard components, calculation patterns, "
            f"equipment groups, reagent lists"
        )

        # query_standards has its own @observe("rag-standards-query") — auto-nests here
        method_family = None
        method_match = re.search(
            r"\b[A-Z]{3}_[A-Z0-9]+(?:_[A-Z0-9]+){1,3}\b",
            filename.upper(),
        )
        if method_match:
            method_family = method_match.group(0)

        retrieval_payload = query_standards_with_metrics(
            query_text=query_text,
            collection_name=self.config.standards_collection,
            top_k=self.config.rag_standards_top_k,
            chroma_path=self.config.chromadb_path,
            method_family=method_family,
        )
        standards_results = retrieval_payload["results"]
        retrieval_metrics = retrieval_payload["metrics"]

        retrieval_quality_passed, retrieval_quality_reasons = self._evaluate_retrieval_quality(
            retrieval_metrics
        )
        if not retrieval_quality_passed:
            logger.warning(
                "Augmentation skipped due to retrieval quality gate: %s",
                retrieval_quality_reasons,
            )
            return {
                "suggestions": [],
                "retrieval_metrics": retrieval_metrics,
                "retrieval_quality_passed": False,
                "retrieval_quality_reasons": retrieval_quality_reasons,
            }

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

        augmented["retrieval_metrics"] = retrieval_metrics
        augmented["retrieval_quality_passed"] = True
        augmented["retrieval_quality_reasons"] = []

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
                    "retrieval_metrics": retrieval_metrics,
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

        try:
            # Single-layer path relies directly on extracted structure,
            # so strict validation requirement remains configurable.
            self._enforce_extraction_quality_gate(
                result,
                filename,
                require_validated_override=self.config.require_validated_extraction,
            )
        except Exception:
            if job_id:
                await self._transition_job(job_id, "FAILED")
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        stages.append(PipelineStageDetail(
            stage="EXTRACT_SINGLE_LAYER",
            duration_ms=duration_ms,
            summary=f"Single-layer extraction: validated={result.get('validated')}",
            details={
                "validated": result.get("validated"),
                "quality_metrics": result.get("quality_metrics"),
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
        review_routing: dict[str, Any],
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
            job.review_routing = review_routing
        except KeyError:
            logger.warning("Could not store results: job %s not found", job_id)
