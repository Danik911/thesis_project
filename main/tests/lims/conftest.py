"""Shared fixtures for LIMS tests."""

import pytest

from main.src.lims.mda_schema import (
    Analysis,
    AnalysisType,
    CalcVariable,
    CalcVariableReferenceType,
    Calculation,
    CalculationType,
    Component,
    MDATemplate,
    ResultType,
)


@pytest.fixture
def sample_mda_template() -> MDATemplate:
    """Minimal valid MDATemplate using ground truth patterns."""
    return MDATemplate(
        analyses=[
            Analysis(
                name="AND_ACS_DYE",
                reported_name="ACS Dye Binding",
                common_name="Dye Binding Identity",
                analysis_type=AnalysisType.ID,
            ),
        ],
        components=[
            Component(
                analysis="AND_ACS_DYE",
                component_name="ABSORBANCE_595",
                order_number=1,
                result_type=ResultType.N,
                uses_instrument=True,
                instrument_group="SPECTROPHOTOMETER",
            ),
            Component(
                analysis="AND_ACS_DYE",
                component_name="DYE_VOLUME_EXPECTED",
                order_number=2,
                result_type=ResultType.K,
                auto_calc=True,
            ),
        ],
        calc_variables=[
            CalcVariable(
                analysis="AND_ACS_DYE",
                component="DYE_VOLUME_EXPECTED",
                name="ABSORBANCE_595",
                reference_type=CalcVariableReferenceType.C,
            ),
        ],
        calculations=[
            Calculation(
                analysis="AND_ACS_DYE",
                component="DYE_VOLUME_EXPECTED",
                source_code="RESULT = ABSORBANCE_595 * 2.5",
                calculation_type=CalculationType.FORMULA,
                variables_used=["ABSORBANCE_595"],
            ),
        ],
    )


@pytest.fixture
def mock_extraction_result() -> dict:
    """Raw dict mimicking LlamaExtract output (pre-validation)."""
    return {
        "analyses": [
            {
                "name": "AND_ACS_DYE",
                "reported_name": "ACS Dye Binding",
                "common_name": "Dye Binding Identity",
                "analysis_type": "ID",
            }
        ],
        "components": [
            {
                "analysis": "AND_ACS_DYE",
                "component_name": "ABSORBANCE_595",
                "order_number": 1,
                "result_type": "N",
                "uses_instrument": True,
                "instrument_group": "SPECTROPHOTOMETER",
            }
        ],
        "calc_variables": [],
        "calculations": [],
    }