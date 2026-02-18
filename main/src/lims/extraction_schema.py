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

from typing import List, Optional

from pydantic import BaseModel


class ExtractedAnalysis(BaseModel):
    """Simplified Analysis for extraction (no enums/validators)."""

    name: str = ""
    version: int = 1
    group_name: str = ""
    active: bool = True
    reported_name: str = ""
    common_name: str = ""
    analysis_type: str = ""  # Was AnalysisType enum
    description: str = ""
    worklist_link: Optional[str] = None


class ExtractedComponent(BaseModel):
    """Simplified Component for extraction (no enums/validators)."""

    analysis: str = ""
    component_name: str = ""
    version: int = 1
    order_number: int = 0
    result_type: str = ""  # Was ResultType enum
    units: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    uses_instrument: bool = False
    instrument_group: Optional[str] = None
    auto_calc: bool = False
    list_key: Optional[str] = None
    sr_picker: Optional[str] = None
    round_type: Optional[str] = None  # Was RoundType enum
    places: Optional[int] = None
    reportable: bool = True
    optional: bool = False
    allow_out_of_range: bool = False


class ExtractedCalcVariable(BaseModel):
    """Simplified CalcVariable for extraction (no enums/validators)."""

    analysis: str = ""
    component: str = ""
    name: str = ""
    version: int = 1
    reference_type: str = ""  # Was CalcVariableReferenceType enum
    reference_analysis: Optional[str] = None
    reference_component: Optional[str] = None
    attribute_1: Optional[str] = None
    return_value: str = "S"  # Was CalcVariableReturnValue enum
    scope: str = "CR"  # Was CalcVariableScope enum
    function: str = "ENTRY"  # Was CalcVariableFunction enum


class ExtractedCalculation(BaseModel):
    """Simplified Calculation for extraction (no enums/validators)."""

    analysis: str = ""
    component: str = ""
    version: int = 1
    description: str = ""
    source_code: str = ""
    calculation_type: str = "FORMULA"  # Was CalculationType enum
    variables_used: List[str] = []


class MDAExtractionSchema(BaseModel):
    """Simplified MDATemplate for LlamaExtract — no enums, no validators.

    After extraction, the raw dict can be validated against the full
    MDATemplate from mda_schema.py for strict compliance checking.
    """

    analyses: List[ExtractedAnalysis] = []
    components: List[ExtractedComponent] = []
    calc_variables: List[ExtractedCalcVariable] = []
    calculations: List[ExtractedCalculation] = []
