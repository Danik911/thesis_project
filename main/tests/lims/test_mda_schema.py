"""Tests for MDA Pydantic schema validation and cross-sheet integrity."""

import pytest
from pydantic import ValidationError

from main.src.lims.mda_schema import (
    Analysis,
    AnalysisType,
    Component,
    MDATemplate,
    ResultType,
)


class TestMDATemplateRoundtrip:
    def test_serialize_deserialize(self, sample_mda_template):
        data = sample_mda_template.model_dump()
        restored = MDATemplate.model_validate(data)
        assert restored.model_dump() == data

    def test_json_roundtrip(self, sample_mda_template):
        json_str = sample_mda_template.model_dump_json()
        restored = MDATemplate.model_validate_json(json_str)
        assert restored == sample_mda_template


class TestComponentValidators:
    def test_k_type_requires_auto_calc(self):
        with pytest.raises(ValidationError, match="auto_calc"):
            Component(
                analysis="AND_ACS_DYE",
                component_name="BAD_K",
                order_number=1,
                result_type=ResultType.K,
                auto_calc=False,
            )

    def test_l_type_requires_list_key(self):
        with pytest.raises(ValidationError, match="list_key"):
            Component(
                analysis="AND_ACS_DYE",
                component_name="BAD_L",
                order_number=1,
                result_type=ResultType.L,
                list_key=None,
            )

    def test_valid_k_type(self):
        comp = Component(
            analysis="AND_ACS_DYE",
            component_name="GOOD_K",
            order_number=1,
            result_type=ResultType.K,
            auto_calc=True,
        )
        assert comp.auto_calc is True


class TestCrossSheetIntegrity:
    def test_orphan_k_component_detected(self):
        with pytest.raises(ValidationError, match="without calculations"):
            MDATemplate(
                analyses=[
                    Analysis(
                        name="AND_TEST",
                        reported_name="Test",
                        common_name="Test",
                        analysis_type=AnalysisType.ID,
                    )
                ],
                components=[
                    Component(
                        analysis="AND_TEST",
                        component_name="CALC_COMP",
                        order_number=1,
                        result_type=ResultType.K,
                        auto_calc=True,
                    )
                ],
                calc_variables=[],
                calculations=[],
            )

    def test_component_references_nonexistent_analysis(self):
        with pytest.raises(ValidationError, match="does not exist"):
            MDATemplate(
                analyses=[
                    Analysis(
                        name="AND_TEST",
                        reported_name="Test",
                        common_name="Test",
                        analysis_type=AnalysisType.ID,
                    )
                ],
                components=[
                    Component(
                        analysis="AND_NONEXISTENT",
                        component_name="BAD_REF",
                        order_number=1,
                        result_type=ResultType.N,
                    )
                ],
                calc_variables=[],
                calculations=[],
            )

    def test_analysis_naming_convention(self):
        with pytest.raises(ValidationError, match="site prefix"):
            Analysis(
                name="NOUNDERSCORE",
                reported_name="Test",
                common_name="Test",
                analysis_type=AnalysisType.ID,
            )