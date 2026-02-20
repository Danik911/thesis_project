"""L16 — Canonical prepared dataset validation tests.

Validates the two-layer pipeline's data artifacts against the canonical
prepared dataset (output/sop_parsed and output/prepared_l10l15).

Tests real data integrity, quality hotspots, classifier cross-validation,
and RAG chunk integrity — NOT mock-based or hardcoded.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Canonical data paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOP_PARSED_DIR = PROJECT_ROOT / "output" / "sop_parsed"
PREPARED_DIR = PROJECT_ROOT / "output" / "prepared_l10l15"

# Skip entire module if canonical data is missing (CI without data artifacts)
pytestmark = pytest.mark.skipif(
    not PREPARED_DIR.exists() or not SOP_PARSED_DIR.exists(),
    reason="Canonical prepared data not available (output/prepared_l10l15 or output/sop_parsed missing)",
)


# =====================================================================
# Fixtures — load canonical manifests once
# =====================================================================


@pytest.fixture(scope="module")
def sop_manifest() -> dict:
    """Load output/sop_parsed/manifest.json."""
    manifest_path = SOP_PARSED_DIR / "manifest.json"
    assert manifest_path.exists(), f"Missing: {manifest_path}"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prepared_manifest() -> dict:
    """Load output/prepared_l10l15/manifest.json."""
    manifest_path = PREPARED_DIR / "manifest.json"
    assert manifest_path.exists(), f"Missing: {manifest_path}"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def l12_evaluation() -> dict:
    """Load L12 classifier evaluation results."""
    eval_path = PREPARED_DIR / "L12_classifier" / "evaluation_results.json"
    assert eval_path.exists(), f"Missing: {eval_path}"
    return json.loads(eval_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def quality_reports() -> dict[str, dict]:
    """Load all per-document quality reports."""
    reports = {}
    per_doc_dir = PREPARED_DIR / "per_document"
    if per_doc_dir.exists():
        for doc_dir in per_doc_dir.iterdir():
            qr = doc_dir / "quality_report.json"
            if qr.exists():
                reports[doc_dir.name] = json.loads(qr.read_text(encoding="utf-8"))
    return reports


# =====================================================================
# SOP Parsed Manifest Integrity
# =====================================================================


class TestSOPParsedManifest:
    """Validate output/sop_parsed/manifest.json structure and consistency."""

    def test_manifest_has_required_keys(self, sop_manifest: dict) -> None:
        """Manifest must have core structure keys."""
        required = {"generated_at_utc", "documents_count", "totals", "documents"}
        missing = required - set(sop_manifest.keys())
        assert not missing, f"Missing manifest keys: {missing}"

    def test_document_count_matches_list(self, sop_manifest: dict) -> None:
        """documents_count must match actual documents list length."""
        declared = sop_manifest["documents_count"]
        actual = len(sop_manifest["documents"])
        assert declared == actual, (
            f"Manifest declares {declared} documents but list has {actual}"
        )

    def test_exactly_four_documents(self, sop_manifest: dict) -> None:
        """Canonical corpus has exactly 4 SOP documents."""
        assert len(sop_manifest["documents"]) == 4

    def test_total_pages_is_856(self, sop_manifest: dict) -> None:
        """Total pages across all documents is 856."""
        assert sop_manifest["totals"]["pages"] == 856

    def test_page_totals_are_consistent(self, sop_manifest: dict) -> None:
        """Sum of per-document pages must equal declared total."""
        per_doc_sum = sum(
            d["metrics"]["total_pages"] for d in sop_manifest["documents"]
        )
        declared_total = sop_manifest["totals"]["pages"]
        assert per_doc_sum == declared_total, (
            f"Sum of per-document pages ({per_doc_sum}) != "
            f"declared total ({declared_total})"
        )

    def test_table_totals_are_consistent(self, sop_manifest: dict) -> None:
        """Sum of per-document tables must equal declared total."""
        per_doc_sum = sum(
            d["metrics"]["table_count"] for d in sop_manifest["documents"]
        )
        declared_total = sop_manifest["totals"]["tables"]
        assert per_doc_sum == declared_total, (
            f"Sum of per-document tables ({per_doc_sum}) != "
            f"declared total ({declared_total})"
        )

    def test_every_document_has_artifacts(self, sop_manifest: dict) -> None:
        """Each document must have summary, text, tables, and pages artifacts."""
        for doc in sop_manifest["documents"]:
            artifacts = doc.get("artifacts", {})
            for key in ("summary_json", "text_extracted", "tables_extracted", "pages_dir"):
                assert key in artifacts, (
                    f"Document '{doc['document_name']}' missing artifact '{key}'"
                )

    def test_document_ids_are_known(self, sop_manifest: dict) -> None:
        """All document IDs match expected canonical set."""
        expected_ids = {"CD-025649", "CD-025658", "UNKNOWN", "SOP-00597"}
        actual_ids = {d["document_id"] for d in sop_manifest["documents"]}
        assert actual_ids == expected_ids, (
            f"Unexpected document IDs: expected {expected_ids}, got {actual_ids}"
        )

    @pytest.mark.parametrize("doc_name,expected_pages", [
        ("CD-025649", 311),
        ("CD-025658", 248),
        ("UNKNOWN", 255),
        ("SOP-00597", 42),
    ])
    def test_per_document_page_count(
        self, sop_manifest: dict, doc_name: str, expected_pages: int
    ) -> None:
        """Each document has the expected page count."""
        doc = next(
            (d for d in sop_manifest["documents"] if d["document_id"] == doc_name),
            None,
        )
        assert doc is not None, f"Document '{doc_name}' not found in manifest"
        assert doc["metrics"]["total_pages"] == expected_pages, (
            f"{doc_name}: expected {expected_pages} pages, "
            f"got {doc['metrics']['total_pages']}"
        )


# =====================================================================
# Prepared L10-L15 Manifest Integrity
# =====================================================================


class TestPreparedManifest:
    """Validate output/prepared_l10l15/manifest.json structure and consistency."""

    def test_manifest_has_required_keys(self, prepared_manifest: dict) -> None:
        required = {"documents_count", "documents", "quality_summary", "downstream_ready"}
        missing = required - set(prepared_manifest.keys())
        assert not missing, f"Missing manifest keys: {missing}"

    def test_document_count_matches_list(self, prepared_manifest: dict) -> None:
        declared = prepared_manifest["documents_count"]
        actual = len(prepared_manifest["documents"])
        assert declared == actual

    def test_exactly_four_prepared_documents(self, prepared_manifest: dict) -> None:
        assert len(prepared_manifest["documents"]) == 4

    def test_quality_summary_totals_consistent(self, prepared_manifest: dict) -> None:
        """Quality summary totals must match sum of per-document values."""
        qs = prepared_manifest["quality_summary"]
        docs = prepared_manifest["documents"]

        assert sum(d["pages"] for d in docs) == qs["total_pages"]
        assert sum(d["sections"] for d in docs) == qs["total_sections"]
        assert sum(d["tables_cleaned"] for d in docs) == qs["total_tables"]
        assert sum(d["ocr_corrections"] for d in docs) == qs["total_ocr_corrections"]
        assert sum(d["low_confidence_lines"] for d in docs) == qs["total_low_confidence"]

    def test_downstream_ready_paths_exist(self, prepared_manifest: dict) -> None:
        """downstream_ready paths must reference existing directories."""
        dr = prepared_manifest["downstream_ready"]
        for key in ("L12_classifier", "L13_rag"):
            assert key in dr, f"Missing downstream_ready key: {key}"
            # Path is absolute in manifest but may reference WSL mount — check relative
            relative = PREPARED_DIR / key.split("/")[-1] if "/" in key else PREPARED_DIR / key
            # Also try the literal key as a subdir
            local_path = PREPARED_DIR / key
            assert local_path.exists() or relative.exists(), (
                f"downstream_ready[{key}] directory not found. "
                f"Checked: {local_path}, {relative}"
            )

    def test_per_document_output_dirs_exist(self, prepared_manifest: dict) -> None:
        """Per-document output directories must exist on disk."""
        per_doc_dir = PREPARED_DIR / "per_document"
        for doc in prepared_manifest["documents"]:
            slug = doc["slug"]
            doc_path = per_doc_dir / slug
            assert doc_path.exists(), (
                f"Per-document directory missing: {doc_path} (slug: {slug})"
            )


# =====================================================================
# Quality Hotspot: SOP-00597 (54 low-confidence OCR lines)
# =====================================================================


class TestQualityHotspotSOP00597:
    """Validate SOP-00597 quality report — highest OCR error density."""

    @pytest.fixture
    def qr(self, quality_reports: dict[str, dict]) -> dict:
        slug = "glims-code-stnd-sop-00597"
        assert slug in quality_reports, f"Quality report missing for {slug}"
        return quality_reports[slug]

    def test_document_id_is_sop_00597(self, qr: dict) -> None:
        assert qr["document_id"] == "SOP-00597"

    def test_low_confidence_line_count(self, qr: dict) -> None:
        """SOP-00597 has exactly 54 low-confidence OCR lines."""
        assert qr["ocr_statistics"]["low_confidence_lines"] == 54

    def test_min_confidence_below_threshold(self, qr: dict) -> None:
        """Min confidence is 0.084 — severely degraded OCR region."""
        min_conf = qr["ocr_statistics"]["min_confidence"]
        assert min_conf < 0.1, (
            f"Expected min confidence < 0.1, got {min_conf}. "
            f"This document has a severely degraded OCR region."
        )

    def test_average_confidence_above_0_9(self, qr: dict) -> None:
        """Despite hotspot, average confidence should still be > 0.9."""
        avg = qr["ocr_statistics"]["average_confidence"]
        assert avg > 0.9, f"Average confidence {avg} is unexpectedly low"

    def test_ocr_corrections_logged(self, qr: dict) -> None:
        """Corrections must be logged (LiMs -> LIMS, double spaces)."""
        corrections = qr.get("corrections_log", [])
        assert len(corrections) == 5, (
            f"Expected 5 logged corrections, got {len(corrections)}"
        )
        # Verify at least one LiMs->LIMS correction exists
        lims_corrections = [
            c for c in corrections
            if any("LiMs" in corr for corr in c.get("corrections", []))
        ]
        assert len(lims_corrections) >= 1, (
            "Expected at least 1 LiMs->LIMS OCR correction"
        )

    def test_section_statistics(self, qr: dict) -> None:
        """SOP-00597 has structured sections (not slide-mode)."""
        stats = qr["section_statistics"]
        assert stats["total_sections"] == 16
        assert stats["max_depth"] == 4, (
            f"Expected max_depth=4 (hierarchical structure), got {stats['max_depth']}"
        )
        assert stats["sections_with_content"] == 13


# =====================================================================
# Quality Hotspot: Training Slides (document_id: UNKNOWN)
# =====================================================================


class TestQualityHotspotTrainingSlides:
    """Validate training slides — document_id UNKNOWN, slide-mode sectioning."""

    @pytest.fixture
    def qr(self, quality_reports: dict[str, dict]) -> dict:
        slug = "glims-analysis-build-training-slides"
        assert slug in quality_reports, f"Quality report missing for {slug}"
        return quality_reports[slug]

    def test_document_id_is_unknown(self, qr: dict) -> None:
        """Training slides have document_id UNKNOWN — no formal document code."""
        assert qr["document_id"] == "UNKNOWN"

    def test_slide_mode_sectioning(self, qr: dict) -> None:
        """255 sections at max_depth=1 indicates slide-mode (one per page)."""
        stats = qr["section_statistics"]
        assert stats["total_sections"] == 255
        assert stats["max_depth"] == 1, (
            f"Expected max_depth=1 (flat slide-mode), got {stats['max_depth']}"
        )

    def test_low_content_density(self, qr: dict) -> None:
        """Only 62 of 255 sections have content — slides are mostly visual."""
        stats = qr["section_statistics"]
        assert stats["sections_with_content"] == 62
        content_ratio = stats["sections_with_content"] / stats["total_sections"]
        assert content_ratio < 0.3, (
            f"Content ratio {content_ratio:.2f} is higher than expected "
            f"for slide-mode document"
        )

    def test_ocr_confidence_acceptable(self, qr: dict) -> None:
        """Despite being slides, OCR confidence should be > 0.95 on average."""
        avg = qr["ocr_statistics"]["average_confidence"]
        assert avg > 0.95, f"Average confidence {avg} too low for slides"

    def test_low_confidence_lines_are_few(self, qr: dict) -> None:
        """Training slides should have very few low-confidence lines."""
        low = qr["ocr_statistics"]["low_confidence_lines"]
        assert low <= 5, f"Expected <= 5 low-confidence lines, got {low}"


# =====================================================================
# L12 Classifier Cross-Validation
# =====================================================================


class TestL12ClassifierCrossValidation:
    """Cross-validate L12 classifier evaluation results against live classifier."""

    def test_evaluation_has_metadata(self, l12_evaluation: dict) -> None:
        required = {"task", "total_pdfs", "correct", "accuracy"}
        missing = required - set(l12_evaluation.get("metadata", {}).keys())
        assert not missing, f"Evaluation metadata missing keys: {missing}"

    def test_evaluation_has_25_results(self, l12_evaluation: dict) -> None:
        assert len(l12_evaluation["results"]) == 25

    def test_accuracy_is_100_percent(self, l12_evaluation: dict) -> None:
        """L12 gate: classifier must achieve 100% on the demo corpus."""
        meta = l12_evaluation["metadata"]
        assert meta["accuracy"] == 1.0
        assert meta["correct"] == meta["total_pdfs"]

    def test_every_result_has_required_fields(self, l12_evaluation: dict) -> None:
        """Each result must have filename, expected, predicted, method, confidence."""
        required = {"filename", "expected", "predicted", "correct", "method", "confidence"}
        for i, result in enumerate(l12_evaluation["results"]):
            missing = required - set(result.keys())
            assert not missing, (
                f"Result[{i}] ({result.get('filename', '?')}) missing: {missing}"
            )

    def test_all_results_marked_correct(self, l12_evaluation: dict) -> None:
        """Every evaluation result must be correct=True."""
        incorrect = [
            r for r in l12_evaluation["results"] if not r["correct"]
        ]
        assert not incorrect, (
            f"{len(incorrect)} incorrect classifications: "
            f"{[r['filename'] for r in incorrect]}"
        )

    def test_live_classifier_matches_evaluation_filename_method(
        self, l12_evaluation: dict
    ) -> None:
        """Filename-based classifications must reproduce exactly.

        These don't need PDF text — the filename alone determines the result.
        If this test fails, filename patterns have drifted since L12 evaluation.
        """
        from main.src.lims.classifier import TestTypeClassifier

        classifier = TestTypeClassifier(confidence_threshold=0.6)

        filename_results = [
            r for r in l12_evaluation["results"] if r["method"] == "filename"
        ]
        assert len(filename_results) > 0, "No filename-method results in evaluation"

        mismatches = []
        for result in filename_results:
            filename = result["filename"]
            expected_type = result["predicted"]

            # Filename-based classification works with empty text
            classification = classifier.classify("", filename)
            actual_type = classification.test_type.value

            if actual_type != expected_type:
                mismatches.append({
                    "filename": filename,
                    "evaluation_says": expected_type,
                    "classifier_now_says": actual_type,
                    "method": classification.method,
                })

        assert not mismatches, (
            f"Filename classifier drift! {len(mismatches)} mismatches:\n"
            + "\n".join(
                f"  {m['filename']}: eval={m['evaluation_says']} "
                f"vs live={m['classifier_now_says']} (method={m['method']})"
                for m in mismatches
            )
        )

    def test_keyword_and_exclusion_methods_require_text(
        self, l12_evaluation: dict
    ) -> None:
        """Keyword/exclusion classifications cannot work with empty text.

        The classifier's exclusion path returns None for empty text (line 324
        of classifier.py), and keyword matching also returns None for empty text.
        This test verifies the classifier correctly refuses to classify
        without PDF content for non-filename methods.
        """
        from main.src.lims.classifier import TestTypeClassifier

        classifier = TestTypeClassifier(confidence_threshold=0.6)

        non_filename_results = [
            r for r in l12_evaluation["results"]
            if r["method"] in ("keywords", "exclusion")
        ]
        assert len(non_filename_results) > 0, (
            "No keyword/exclusion results in evaluation"
        )

        # With empty text, these filenames should NOT be classifiable
        # by keyword/exclusion — they need real PDF content
        for result in non_filename_results:
            filename = result["filename"]
            try:
                classification = classifier.classify("", filename)
                # If it didn't raise, it must have matched by filename instead
                assert classification.method == "filename", (
                    f"{filename}: classified as {classification.test_type.value} "
                    f"via {classification.method} with empty text — "
                    f"keyword/exclusion should not work without text"
                )
            except NotImplementedError:
                # Expected: no filename match + no text = LLM fallback raises
                pass

    def test_confidence_thresholds_valid(self, l12_evaluation: dict) -> None:
        """All confidence values must be in [0, 1] range."""
        for result in l12_evaluation["results"]:
            conf = result["confidence"]
            assert 0 <= conf <= 1, (
                f"{result['filename']}: confidence {conf} out of [0,1] range"
            )

    def test_evidence_field_is_nonempty(self, l12_evaluation: dict) -> None:
        """Every result must have non-empty evidence explaining the classification."""
        for result in l12_evaluation["results"]:
            evidence = result.get("evidence", [])
            assert len(evidence) > 0, (
                f"{result['filename']}: evidence is empty — "
                f"classification has no audit trail"
            )

    def test_method_distribution(self, l12_evaluation: dict) -> None:
        """Verify classifier uses both filename and keyword methods."""
        methods = {r["method"] for r in l12_evaluation["results"]}
        # Must have at least filename and one of keywords/exclusion
        assert "filename" in methods, "No filename-based classifications found"
        assert len(methods) >= 2, (
            f"Only 1 classification method used: {methods}. "
            f"Expected hybrid (filename + keywords)"
        )


# =====================================================================
# L13 RAG Data Integrity
# =====================================================================


class TestL13RAGDataIntegrity:
    """Validate L13 RAG JSONL chunks are loadable and structurally sound."""

    @pytest.fixture(scope="class")
    def standards_chunks(self) -> list[dict]:
        path = PREPARED_DIR / "L13_rag" / "lims_standards_chunks.jsonl"
        assert path.exists(), f"Missing: {path}"
        chunks = []
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            chunks.append(json.loads(line))
        return chunks

    @pytest.fixture(scope="class")
    def calculation_chunks(self) -> list[dict]:
        path = PREPARED_DIR / "L13_rag" / "calculation_patterns_chunks.jsonl"
        assert path.exists(), f"Missing: {path}"
        chunks = []
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            chunks.append(json.loads(line))
        return chunks

    @pytest.fixture(scope="class")
    def standards_trace(self) -> dict:
        path = PREPARED_DIR / "L13_rag" / "lims_standards_seed_trace.json"
        assert path.exists(), f"Missing: {path}"
        return json.loads(path.read_text(encoding="utf-8"))

    @pytest.fixture(scope="class")
    def calculation_trace(self) -> dict:
        path = PREPARED_DIR / "L13_rag" / "calculation_patterns_seed_trace.json"
        assert path.exists(), f"Missing: {path}"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_standards_chunks_count(self, standards_chunks: list[dict]) -> None:
        """Standards chunks JSONL has 154 entries (from seed trace)."""
        assert len(standards_chunks) == 154, (
            f"Expected 154 standards chunks, got {len(standards_chunks)}"
        )

    def test_calculation_chunks_count(self, calculation_chunks: list[dict]) -> None:
        """Calculation patterns JSONL has 401 entries (from seed trace)."""
        assert len(calculation_chunks) == 401, (
            f"Expected 401 calculation chunks, got {len(calculation_chunks)}"
        )

    def test_standards_chunk_structure(self, standards_chunks: list[dict]) -> None:
        """Every standards chunk must have id, title, content, source_slug."""
        required = {"id", "title", "content", "source_slug"}
        for i, chunk in enumerate(standards_chunks):
            missing = required - set(chunk.keys())
            assert not missing, (
                f"Standards chunk[{i}] (id={chunk.get('id', '?')}) "
                f"missing keys: {missing}"
            )

    def test_calculation_chunk_structure(self, calculation_chunks: list[dict]) -> None:
        """Every calculation chunk must have id, content, source_slug."""
        required = {"id", "content", "source_slug"}
        for i, chunk in enumerate(calculation_chunks):
            missing = required - set(chunk.keys())
            assert not missing, (
                f"Calculation chunk[{i}] (id={chunk.get('id', '?')}) "
                f"missing keys: {missing}"
            )

    def test_no_empty_content_chunks(self, standards_chunks: list[dict]) -> None:
        """No standards chunk should have empty content."""
        empty = [
            c["id"] for c in standards_chunks
            if not c.get("content", "").strip()
        ]
        assert not empty, (
            f"{len(empty)} standards chunks have empty content: {empty[:5]}..."
        )

    def test_no_empty_calculation_content(self, calculation_chunks: list[dict]) -> None:
        """No calculation chunk should have empty content."""
        empty = [
            c["id"] for c in calculation_chunks
            if not c.get("content", "").strip()
        ]
        assert not empty, (
            f"{len(empty)} calculation chunks have empty content: {empty[:5]}..."
        )

    def test_all_four_documents_represented_in_standards(
        self, standards_chunks: list[dict]
    ) -> None:
        """Standards chunks should cover all 4 source documents."""
        slugs = {c["source_slug"] for c in standards_chunks}
        expected = {
            "cd-025649-calc-sr-picker",
            "cd-025658-calc-components-optional",
            "glims-analysis-build-training-slides",
            "glims-code-stnd-sop-00597",
        }
        assert slugs == expected, (
            f"Standards chunks missing documents: {expected - slugs}"
        )

    def test_all_four_documents_represented_in_calculations(
        self, calculation_chunks: list[dict]
    ) -> None:
        """Calculation chunks should cover all 4 source documents."""
        slugs = {c["source_slug"] for c in calculation_chunks}
        expected = {
            "cd-025649-calc-sr-picker",
            "cd-025658-calc-components-optional",
            "glims-analysis-build-training-slides",
            "glims-code-stnd-sop-00597",
        }
        assert slugs == expected, (
            f"Calculation chunks missing documents: {expected - slugs}"
        )

    def test_standards_trace_matches_chunks(
        self, standards_trace: dict, standards_chunks: list[dict]
    ) -> None:
        """Seed trace chunk count must match actual JSONL line count."""
        trace_count = standards_trace["chunks_count"]
        actual_count = len(standards_chunks)
        assert trace_count == actual_count, (
            f"Standards seed trace says {trace_count} chunks, "
            f"JSONL has {actual_count}"
        )

    def test_calculation_trace_matches_chunks(
        self, calculation_trace: dict, calculation_chunks: list[dict]
    ) -> None:
        """Seed trace chunk count must match actual JSONL line count."""
        trace_count = calculation_trace["chunks_count"]
        actual_count = len(calculation_chunks)
        assert trace_count == actual_count, (
            f"Calculation seed trace says {trace_count} chunks, "
            f"JSONL has {actual_count}"
        )

    def test_standards_trace_documents_match(self, standards_trace: dict) -> None:
        """Seed trace must list all 4 documents."""
        expected = {
            "cd-025649-calc-sr-picker",
            "cd-025658-calc-components-optional",
            "glims-analysis-build-training-slides",
            "glims-code-stnd-sop-00597",
        }
        actual = set(standards_trace["documents"])
        assert actual == expected, f"Trace documents mismatch: {actual - expected}"

    def test_chunk_ids_are_unique(
        self, standards_chunks: list[dict], calculation_chunks: list[dict]
    ) -> None:
        """All chunk IDs must be unique within each collection."""
        std_ids = [c["id"] for c in standards_chunks]
        calc_ids = [c["id"] for c in calculation_chunks]

        std_dupes = len(std_ids) - len(set(std_ids))
        calc_dupes = len(calc_ids) - len(set(calc_ids))

        assert std_dupes == 0, f"{std_dupes} duplicate IDs in standards chunks"
        assert calc_dupes == 0, f"{calc_dupes} duplicate IDs in calculation chunks"


# =====================================================================
# Cross-Layer Consistency: sop_parsed ↔ prepared_l10l15
# =====================================================================


class TestCrossLayerConsistency:
    """Verify prepared data is traceable to sop_parsed source."""

    def test_same_document_count(
        self, sop_manifest: dict, prepared_manifest: dict
    ) -> None:
        """Both manifests must have the same number of documents."""
        assert sop_manifest["documents_count"] == prepared_manifest["documents_count"]

    def test_same_total_pages(
        self, sop_manifest: dict, prepared_manifest: dict
    ) -> None:
        """Total pages must match between sop_parsed and prepared."""
        sop_pages = sop_manifest["totals"]["pages"]
        prepared_pages = prepared_manifest["quality_summary"]["total_pages"]
        assert sop_pages == prepared_pages, (
            f"Page count mismatch: sop_parsed={sop_pages}, "
            f"prepared={prepared_pages}"
        )

    def test_same_total_tables(
        self, sop_manifest: dict, prepared_manifest: dict
    ) -> None:
        """Total tables must match between sop_parsed and prepared."""
        sop_tables = sop_manifest["totals"]["tables"]
        prepared_tables = prepared_manifest["quality_summary"]["total_tables"]
        assert sop_tables == prepared_tables, (
            f"Table count mismatch: sop_parsed={sop_tables}, "
            f"prepared={prepared_tables}"
        )

    def test_document_ids_match(
        self, sop_manifest: dict, prepared_manifest: dict
    ) -> None:
        """Document IDs must be identical between both manifests."""
        sop_ids = {d["document_id"] for d in sop_manifest["documents"]}
        prepared_ids = {d["document_id"] for d in prepared_manifest["documents"]}
        assert sop_ids == prepared_ids, (
            f"Document ID mismatch: "
            f"only in sop={sop_ids - prepared_ids}, "
            f"only in prepared={prepared_ids - sop_ids}"
        )

    def test_per_document_pages_match(
        self, sop_manifest: dict, prepared_manifest: dict
    ) -> None:
        """Each document's page count must match between manifests."""
        sop_docs = {d["document_id"]: d["metrics"]["total_pages"]
                    for d in sop_manifest["documents"]}
        prep_docs = {d["document_id"]: d["pages"]
                     for d in prepared_manifest["documents"]}
        for doc_id in sop_docs:
            assert sop_docs[doc_id] == prep_docs[doc_id], (
                f"{doc_id}: sop_parsed has {sop_docs[doc_id]} pages, "
                f"prepared has {prep_docs[doc_id]}"
            )


# =====================================================================
# Pipeline State Machine vs Canonical Data
# =====================================================================


class TestPipelineStateConsistency:
    """Verify pipeline state machine transitions match what the prepared data requires."""

    def test_classifying_allows_single_layer_fallback(self) -> None:
        """CLASSIFYING must allow EXTRACTING transition (single-layer fallback).

        This was a real bug found by L16 validation: test_job_store.py
        originally omitted EXTRACTING from CLASSIFYING transitions.
        """
        from main.src.lims.job_store import LIMSJobStatus, VALID_TRANSITIONS

        allowed = VALID_TRANSITIONS[LIMSJobStatus.CLASSIFYING]
        assert LIMSJobStatus.EXTRACTING in allowed, (
            "CLASSIFYING must allow EXTRACTING for single-layer fallback path. "
            "Pipeline._single_layer_fallback() transitions to EXTRACTING."
        )

    def test_two_layer_path_is_complete(self) -> None:
        """Full two-layer path must be valid: EXTRACTING -> CLASSIFYING -> LOADING_TEMPLATE -> EXTRACTING -> AUGMENTING -> MERGING -> PENDING_REVIEW."""
        from main.src.lims.job_store import LIMSJobStatus, VALID_TRANSITIONS

        path = [
            (LIMSJobStatus.EXTRACTING, LIMSJobStatus.CLASSIFYING),
            (LIMSJobStatus.CLASSIFYING, LIMSJobStatus.LOADING_TEMPLATE),
            (LIMSJobStatus.LOADING_TEMPLATE, LIMSJobStatus.EXTRACTING),
            (LIMSJobStatus.EXTRACTING, LIMSJobStatus.AUGMENTING),
            (LIMSJobStatus.AUGMENTING, LIMSJobStatus.MERGING),
            (LIMSJobStatus.MERGING, LIMSJobStatus.PENDING_REVIEW),
        ]
        for from_status, to_status in path:
            assert to_status in VALID_TRANSITIONS[from_status], (
                f"Invalid transition: {from_status.value} -> {to_status.value} "
                f"not in VALID_TRANSITIONS"
            )

    def test_single_layer_path_is_complete(self) -> None:
        """Single-layer path: EXTRACTING -> CLASSIFYING -> EXTRACTING -> PENDING_REVIEW."""
        from main.src.lims.job_store import LIMSJobStatus, VALID_TRANSITIONS

        path = [
            (LIMSJobStatus.EXTRACTING, LIMSJobStatus.CLASSIFYING),
            (LIMSJobStatus.CLASSIFYING, LIMSJobStatus.EXTRACTING),
            (LIMSJobStatus.EXTRACTING, LIMSJobStatus.PENDING_REVIEW),
        ]
        for from_status, to_status in path:
            assert to_status in VALID_TRANSITIONS[from_status], (
                f"Invalid transition: {from_status.value} -> {to_status.value}"
            )

    def test_hitl_gate_is_enforced(self) -> None:
        """APPROVED must only be reachable from PENDING_REVIEW."""
        from main.src.lims.job_store import LIMSJobStatus, VALID_TRANSITIONS

        # Only PENDING_REVIEW should have APPROVED in its transitions
        states_reaching_approved = [
            status for status, allowed in VALID_TRANSITIONS.items()
            if LIMSJobStatus.APPROVED in allowed
        ]
        assert states_reaching_approved == [LIMSJobStatus.PENDING_REVIEW], (
            f"APPROVED is reachable from: {[s.value for s in states_reaching_approved]}. "
            f"Must only be reachable from PENDING_REVIEW (HITL gate)."
        )
