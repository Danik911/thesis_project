"""Simplified extraction schema for LIMS extraction APIs.

LlamaExtract Cloud API requires simple JSON-compatible schemas — no enums,
no custom validators, no model validators. This module provides a flat
extraction schema that maps to the full MDATemplate after extraction.

For L7 migration work, this schema remains the canonical extraction contract for
the current `llamaextract` runtime path and can be reused by future
`llamaparse_v2` structuring orchestration.

The fields mirror MDATemplate but use plain str/int/float/bool/Optional types.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedAnalysis(BaseModel):
    """Simplified Analysis for extraction (no enums/validators)."""

    name: str = Field(default="", description="LabWare analysis name, e.g. AND_ACS_DYE, AND_ACS_DYE_CTL, AND_ACS_DYE_META")
    version: int = 1
    group_name: str = ""
    active: bool = True
    reported_name: str = ""
    common_name: str = ""
    analysis_type: str = Field(
        default="",
        description="One of: ID, ASY, IMP, PHYS, QC_SAMPLES, HPLC, RM, KF",
    )
    description: str = ""
    worklist_link: str | None = None


class ExtractedComponent(BaseModel):
    """Simplified Component for extraction (no enums/validators)."""

    analysis: str = Field(default="", description="Parent analysis name; must match one analysis.name")
    component_name: str = Field(default="", description="Component label used in LabWare result entry")
    version: int = 1
    order_number: int = 0
    result_type: str = Field(
        default="",
        description="Result type code: N numeric, K calculated/auto-populated, L list, T text, D date",
    )
    units: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    uses_instrument: bool = Field(default=False, description="True when value is measured by instrument")
    instrument_group: str | None = None
    auto_calc: bool = Field(default=False, description="True for K/calculated components")
    list_key: str | None = Field(default=None, description="List dictionary key for L components, e.g. YES_NO_2, PASS_FAIL")
    sr_picker: str | None = None
    round_type: str | None = None  # Was RoundType enum
    places: int | None = None
    reportable: bool = True
    optional: bool = False
    allow_out_of_range: bool = False


class ExtractedCalcVariable(BaseModel):
    """Simplified CalcVariable for extraction (no enums/validators)."""

    analysis: str = Field(default="", description="Analysis owning this calculation variable")
    component: str = Field(default="", description="Component using this variable")
    name: str = ""
    version: int = 1
    reference_type: str = Field(
        default="",
        description="C for within-analysis reference, A for cross-analysis reference",
    )
    reference_analysis: str | None = None
    reference_component: str | None = None
    attribute_1: str | None = None
    return_value: str = Field(default="S", description="Return value mode, typically S")
    scope: str = Field(default="CR", description="Scope code, typically CR or B")
    function: str = Field(default="ENTRY", description="Function code, e.g. ENTRY, AVE, RSD")


class ExtractedCalculation(BaseModel):
    """Simplified Calculation for extraction (no enums/validators)."""

    analysis: str = Field(default="", description="Analysis owning this calculation")
    component: str = Field(default="", description="Component calculated by this formula")
    version: int = 1
    description: str = ""
    source_code: str = Field(default="", description="LIMS Basic source code or formula text")
    calculation_type: str = Field(
        default="FORMULA",
        description="FORMULA, CONDITIONAL, INST_PICKER, SR_PICKER, or GOSUB",
    )
    variables_used: list[str] = []


class MDAExtractionSchema(BaseModel):
    """Simplified MDATemplate for LlamaExtract — no enums, no validators.

    After extraction, the raw dict can be validated against the full
    MDATemplate from mda_schema.py for strict compliance checking.
    """

    analyses: list[ExtractedAnalysis] = []
    components: list[ExtractedComponent] = []
    calc_variables: list[ExtractedCalcVariable] = []
    calculations: list[ExtractedCalculation] = []
