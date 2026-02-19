"""Unit tests for L10 provenance and test type foundation models."""

import pytest
from pydantic import ValidationError

from main.src.lims.provenance import ComponentSource, FieldProvenance, ProvenanceMap
from main.src.lims.test_type import ClassificationResult, TestType as LimsTestType


def test_component_source_has_five_values() -> None:
    assert len(ComponentSource) == 5
    assert {source.value for source in ComponentSource} == {
        "TEMPLATE",
        "EXTRACTED",
        "INFERRED",
        "SME_REQUIRED",
        "SME_MODIFIED",
    }


def test_field_provenance_confidence_in_range() -> None:
    model = FieldProvenance(source=ComponentSource.TEMPLATE, confidence=0.75)
    assert model.confidence == 0.75


@pytest.mark.parametrize("bad_confidence", [-0.01, 1.01])
def test_field_provenance_confidence_out_of_range_raises(bad_confidence: float) -> None:
    with pytest.raises(ValidationError):
        FieldProvenance(source=ComponentSource.EXTRACTED, confidence=bad_confidence)


def test_provenance_map_summary_counts_by_source() -> None:
    provenance = ProvenanceMap()
    provenance.set_provenance(
        "analyses[0].name",
        ComponentSource.TEMPLATE,
        confidence=1.0,
        detail="template skeleton",
    )
    provenance.set_provenance(
        "components[0].result_type",
        ComponentSource.EXTRACTED,
        confidence=0.88,
        detail="PDF page 3",
    )
    provenance.set_provenance(
        "components[1].result_type",
        ComponentSource.EXTRACTED,
        confidence=0.82,
        detail="PDF page 4",
    )

    assert provenance.get_provenance("analyses[0].name") is not None
    assert provenance.summary() == {"TEMPLATE": 1, "EXTRACTED": 2}


def test_test_type_has_five_values() -> None:
    assert len(LimsTestType) == 5
    assert {test_type.value for test_type in LimsTestType} == {
        "HPLC",
        "LOD",
        "TITRATION",
        "IDENTITY",
        "OTHER",
    }


def test_classification_result_validates_confidence() -> None:
    model = ClassificationResult(
        test_type=LimsTestType.HPLC,
        confidence=0.91,
        method="hybrid",
        evidence=["method title contains 'HPLC'"],
        pdf_filename="method.pdf",
    )
    assert model.test_type == LimsTestType.HPLC
    assert model.confidence == 0.91


@pytest.mark.parametrize("bad_confidence", [-1.0, 2.0])
def test_classification_result_confidence_out_of_range_raises(
    bad_confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        ClassificationResult(
            test_type=LimsTestType.OTHER,
            confidence=bad_confidence,
            method="rules",
        )