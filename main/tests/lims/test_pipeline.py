"""Tests for the TwoLayerPipeline orchestrator.

Validates pipeline stages, state transitions, single-layer fallback,
and end-to-end pipeline execution.

GAMP-5 Category 5: Custom pharmaceutical software component.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main.src.lims.job_store import (
    LIMSJobStatus,
    _jobs,
    create_job,
    get_job,
)
from main.src.lims.pipeline import TwoLayerPipeline
from main.src.lims.test_type import ClassificationResult, TestType


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the in-memory job store between tests."""
    _jobs.clear()
    yield
    _jobs.clear()


@pytest.fixture
def mock_config():
    """Mock LIMSConfig with required attributes."""
    config = MagicMock()
    config.llamaextract_api_key = "test-key"
    config.extraction_mode = "balanced"
    config.openrouter_api_key = ""  # No OpenRouter -> skip augmentation
    config.openrouter_model = "test/model"
    config.chromadb_path = "./chroma_db_lims"
    config.upload_dir = "./uploads/lims"
    config.output_dir = "./output/lims"
    config.standards_collection = "lims_standards"
    config.calculations_collection = "calculation_patterns"
    config.classification_mode = "hybrid"
    config.classification_confidence_threshold = 0.6
    config.rag_standards_top_k = 5
    config.rag_mda_top_k = 3
    return config


@pytest.fixture
def mock_pdf_text():
    """Fake PDF text that contains identity keywords."""
    return (
        "ACS Dye-Binding Identity Test Method\n"
        "1. Visual Inspection: Package double layered and sealed\n"
        "2. Sponge Color: White to Off-White\n"
        "3. Dye Volume for Sponge\n"
        "4. Supernatant comparison with Standard B\n"
        "5. Confirmation of ACS Identity\n"
    )


@pytest.fixture
def mock_extraction_result():
    """Mock result from extract_mda_from_pdf."""
    return {
        "raw_extraction": {
            "analyses": [
                {
                    "name": "SITE_IDENTITY",
                    "analysis_type": "ID",
                    "description": "Extracted from PDF",
                }
            ],
            "components": [
                {
                    "analysis": "SITE_IDENTITY",
                    "component_name": "Weight of Sponge(s)",
                    "result_type": "N",
                    "units": "MG",
                }
            ],
            "calc_variables": [],
            "calculations": [],
        },
        "mda_template": {
            "analyses": [
                {
                    "name": "SITE_IDENTITY",
                    "analysis_type": "ID",
                    "description": "Extracted from PDF",
                }
            ],
            "components": [
                {
                    "analysis": "SITE_IDENTITY",
                    "component_name": "Weight of Sponge(s)",
                    "result_type": "N",
                    "units": "MG",
                }
            ],
            "calc_variables": [],
            "calculations": [],
        },
        "validated": True,
        "validation_error": None,
        "extraction_trace": {"model": "test"},
    }


@pytest.fixture
def mock_other_pdf_text():
    """PDF text that does not match any known test type."""
    return (
        "General Laboratory Procedure\n"
        "This is a routine procedure for sample handling.\n"
        "Equipment calibration records are maintained.\n"
    )


# ---------------------------------------------------------------------------
# Classification tests
# ---------------------------------------------------------------------------


class TestClassification:
    def test_classify_identity_via_filename(self, mock_config):
        """Filename pattern _acs_ -> IDENTITY classification."""
        pipeline = TwoLayerPipeline(mock_config)
        classification = pipeline.classifier.classify(
            "Some PDF text", "AND_ACS_DYE_LAB-2499.pdf"
        )
        assert classification.test_type == TestType.IDENTITY
        assert classification.confidence > 0

    def test_classify_hplc_via_filename(self, mock_config):
        """Filename pattern _hplc_ -> HPLC classification."""
        pipeline = TwoLayerPipeline(mock_config)
        classification = pipeline.classifier.classify(
            "Some PDF text", "AND_HPLC_ASSAY.pdf"
        )
        assert classification.test_type == TestType.HPLC

    def test_classify_other_for_unknown(self, mock_config, mock_other_pdf_text):
        """Unknown text with generic filename -> OTHER."""
        pipeline = TwoLayerPipeline(mock_config)
        classification = pipeline.classifier.classify(
            mock_other_pdf_text, "generic_lab_procedure.pdf"
        )
        assert classification.test_type == TestType.OTHER


# ---------------------------------------------------------------------------
# Single-layer fallback
# ---------------------------------------------------------------------------


class TestSingleLayerFallback:
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    @patch("main.src.lims.pipeline.asyncio.to_thread", new_callable=AsyncMock)
    def test_other_falls_back_to_single_layer(
        self,
        mock_to_thread,
        mock_extract_text,
        mock_config,
        mock_other_pdf_text,
    ):
        """TestType.OTHER -> single_layer pipeline_type."""
        mock_extract_text.return_value = mock_other_pdf_text
        mock_to_thread.return_value = {
            "raw_extraction": {"analyses": [], "components": []},
            "mda_template": None,
            "validated": False,
            "validation_error": "test",
            "extraction_trace": {"model": "test"},
        }

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake content", "generic_procedure.pdf")
        )

        assert result["pipeline_type"] == "single_layer"
        assert result["test_type"] == "OTHER"
        assert "classification" in result
        assert "stage_details" in result


# ---------------------------------------------------------------------------
# Two-layer pipeline
# ---------------------------------------------------------------------------


class TestTwoLayerPipeline:
    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_full_run_produces_mda_with_provenance(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """All stages execute, result has provenance and MDA."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf")
        )

        assert result["pipeline_type"] == "two_layer"
        assert result["test_type"] == "IDENTITY"
        assert result["mda_template"] is not None
        assert result["provenance"] is not None
        assert "fields" in result["provenance"]
        assert len(result["provenance"]["fields"]) > 0

    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_stage_details_recorded(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """All 6 stages should have PipelineStageDetail entries."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf")
        )

        stage_names = [s["stage"] for s in result["stage_details"]]
        assert "CLASSIFY" in stage_names
        assert "TEMPLATE" in stage_names
        assert "EXTRACT" in stage_names
        assert "AUGMENT" in stage_names
        assert "MERGE" in stage_names
        assert "REVIEW" in stage_names

    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_job_state_transitions(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """Job transitions through CLASSIFYING -> ... -> PENDING_REVIEW."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        job_id = create_job("AND_ACS_DYE_LAB-2499.pdf")

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf", job_id)
        )

        # Job should be in PENDING_REVIEW after pipeline completes
        job = get_job(job_id)
        assert job.status == LIMSJobStatus.PENDING_REVIEW

    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_classification_in_result(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """Classification result is included in pipeline output."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf")
        )

        classification = result["classification"]
        assert classification["test_type"] == "IDENTITY"
        assert classification["confidence"] > 0
        assert "method" in classification

    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_conflicts_in_result(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
    ):
        """Conflicts list is included (possibly empty) in pipeline output."""
        mock_focused_extract.return_value = {
            "raw_extraction": {},
            "mda_template": {"analyses": [], "components": []},
            "validated": True,
            "extraction_trace": {},
        }
        mock_extract_text.return_value = mock_pdf_text

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf")
        )

        assert "conflicts" in result
        assert isinstance(result["conflicts"], list)


# ---------------------------------------------------------------------------
# Single-layer job state transitions
# ---------------------------------------------------------------------------


class TestSingleLayerJobState:
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    @patch("main.src.lims.pipeline.asyncio.to_thread", new_callable=AsyncMock)
    def test_single_layer_job_reaches_pending_review(
        self,
        mock_to_thread,
        mock_extract_text,
        mock_config,
        mock_other_pdf_text,
    ):
        """OTHER path without OpenRouter -> job reaches PENDING_REVIEW."""
        mock_extract_text.return_value = mock_other_pdf_text
        mock_to_thread.return_value = {
            "raw_extraction": {"analyses": [], "components": []},
            "mda_template": None,
            "validated": False,
            "validation_error": "test",
            "extraction_trace": {"model": "test"},
        }

        job_id = create_job("generic_procedure.pdf")

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake content", "generic_procedure.pdf", job_id)
        )

        assert result["pipeline_type"] == "single_layer"
        job = get_job(job_id)
        assert job.status == LIMSJobStatus.PENDING_REVIEW

    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    @patch("main.src.lims.pipeline.asyncio.to_thread", new_callable=AsyncMock)
    def test_other_falls_back_to_single_layer_with_job(
        self,
        mock_to_thread,
        mock_extract_text,
        mock_config,
        mock_other_pdf_text,
    ):
        """OTHER path transitions through CLASSIFYING -> EXTRACTING."""
        mock_extract_text.return_value = mock_other_pdf_text
        mock_to_thread.return_value = {
            "raw_extraction": {"analyses": [], "components": []},
            "mda_template": {"analyses": [], "components": []},
            "validated": False,
            "validation_error": "test",
            "extraction_trace": {"model": "test"},
        }

        job_id = create_job("generic_procedure.pdf")

        pipeline = TwoLayerPipeline(mock_config)
        asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake content", "generic_procedure.pdf", job_id)
        )

        # Job must have passed through EXTRACTING -> PENDING_REVIEW
        job = get_job(job_id)
        assert job.status == LIMSJobStatus.PENDING_REVIEW


class TestAugmentationErrorPropagation:
    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_augmentation_error_propagates(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """When augmentation raises, error propagates (not swallowed)."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        # Enable OpenRouter so augmentation is attempted
        mock_config.openrouter_api_key = "test-key"

        pipeline = TwoLayerPipeline(mock_config)

        with patch(
            "main.src.lims.pipeline.json.loads",
            side_effect=RuntimeError("Augmentation exploded"),
        ), patch("main.src.lims.pipeline.json.dumps", return_value="{}"):
            with pytest.raises(RuntimeError, match="Augmentation exploded"):
                asyncio.get_event_loop().run_until_complete(
                    pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE_LAB-2499.pdf")
                )


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    @patch("main.src.lims.pipeline.focused_extract", new_callable=AsyncMock)
    @patch("main.src.lims.pipeline.extract_text_from_pdf")
    def test_and_acs_dye_backward_compat(
        self,
        mock_extract_text,
        mock_focused_extract,
        mock_config,
        mock_pdf_text,
        mock_extraction_result,
    ):
        """AND_ACS_DYE.pdf -> IDENTITY -> valid MDA with template structure."""
        mock_extract_text.return_value = mock_pdf_text
        mock_focused_extract.return_value = mock_extraction_result

        pipeline = TwoLayerPipeline(mock_config)
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run(b"%PDF-1.4 fake", "AND_ACS_DYE.pdf")
        )

        assert result["pipeline_type"] == "two_layer"
        assert result["test_type"] == "IDENTITY"
        assert result["mda_template"] is not None

        # Should have identity template structure (3 analyses, 25+ components)
        mda = result["mda_template"]
        assert len(mda["analyses"]) == 3
        assert len(mda["components"]) >= 25
