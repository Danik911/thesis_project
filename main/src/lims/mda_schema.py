"""MDA (Method Definition and Analysis) Pydantic v2 schemas.

Ground truth: ACS Dye-Binding Identity Test (LAB-2499) from LabWare LIMS build.
Covers 4 core sheets: Analysis (Sheet 1), Component (Sheet 2),
CalcVariable (Sheet 6), Calculation (Sheet 7).

Three-analysis pattern observed:
  - Primary:  AND_ACS_DYE      (type=ID, 9 components)
  - Control:  AND_ACS_DYE_CTL  (type=QC_SAMPLES, 7 components)
  - Metadata: AND_ACS_DYE_META (type=QC_SAMPLES, 9 components)

Total: 25 components across 3 analyses.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AnalysisType(str, Enum):
    """Primary analysis classification.

    Ground truth: only the primary analysis (AND_ACS_DYE) uses ID.
    CTL and META suffixed analyses use QC_SAMPLES.
    """

    ID = "ID"
    ASY = "ASY"
    IMP = "IMP"
    PHYS = "PHYS"
    QC_SAMPLES = "QC_SAMPLES"
    HPLC = "HPLC"
    RM = "RM"
    KF = "KF"


class ResultType(str, Enum):
    """Component result type — determines the data entry mechanism.

    Critical misclassification warnings:
      - "Direct Red 80 Solution Used" = K (IF/ELSE calc), NOT L
      - Petri Dish = K with S/R Pickers, NOT L
      - Timer = Instrument Group code, NOT N
      - Reagents are NOT decomposed into measurement steps
    """

    N = "N"  # Numeric entry (measurement with instrument)
    K = "K"  # Calculated (LIMS Basic formula, GOSUB, or conditional)
    L = "L"  # List selection (YES_NO_2, PASS_FAIL, etc.)
    T = "T"  # Free text entry
    D = "D"  # Date picker


class RoundType(str, Enum):
    """Rounding direction for numeric results."""

    F = "F"  # Floor
    T = "T"  # Truncate
    U = "U"  # Up (observed on volume components in ground truth)


class UnitCode(str, Enum):
    """Standardized LabWare unit codes."""

    NONE = "NONE"
    MG = "MG"
    ML = "ML"
    PERCENT = "PERCENT"
    AU = "AU"
    G = "G"
    MG_ML = "MG_ML"
    UG_ML = "UG_ML"
    CM = "CM"
    MM = "MM"
    MIN = "MIN"


class CalcVariableReferenceType(str, Enum):
    """How a CALC_VARIABLE resolves its reference.

    C = within the same analysis (component reference).
    A = cross-analysis reference (e.g., CTL Sponge Size -> primary Dye Volume).
    """

    C = "C"
    A = "A"


class CalcVariableReturnValue(str, Enum):
    """What the CALC_VARIABLE returns."""

    S = "S"  # Single value
    P = "P"  # Population
    A = "A"  # All


class CalcVariableScope(str, Enum):
    """Scope at which the variable resolves.

    CR = CurrentResult (within-analysis).
    CT = CurrentTest.
    B  = Batch (typical for cross-analysis references).
    """

    CR = "CR"
    CT = "CT"
    B = "B"


class CalcVariableFunction(str, Enum):
    """Aggregation function applied to the variable."""

    ENTRY = "ENTRY"
    AVE = "AVE"
    RSD = "RSD"


class CalculationType(str, Enum):
    """Classification for code-gen routing of LIMS Basic calculations."""

    FORMULA = "FORMULA"
    CONDITIONAL = "CONDITIONAL"
    INST_PICKER = "INST_PICKER"
    SR_PICKER = "SR_PICKER"
    GOSUB = "GOSUB"


# ---------------------------------------------------------------------------
# Sheet 1: Analysis
# ---------------------------------------------------------------------------


class Analysis(BaseModel):
    """Sheet 1 — top-level test method definition.

    Naming convention: {SITE_PREFIX}_{METHOD_ABBREV}[_{SUFFIX}]
    Examples: AND_ACS_DYE, AND_ACS_DYE_CTL, AND_ACS_DYE_META
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    name: str
    version: int = 1
    group_name: str = "ANDOVER"
    active: bool = True
    reported_name: str
    common_name: str
    analysis_type: AnalysisType
    description: str = ""
    worklist_link: Optional[str] = None

    # Configuration flags (defaults from ground truth)
    allow_component_entry: bool = True
    allow_overspec: bool = False
    allow_underspec: bool = False
    auto_authorize: bool = False
    auto_complete: bool = False
    auto_link: bool = False
    auto_print: bool = False
    batch_link: bool = False
    certify: bool = False
    complete_on_entry: bool = False
    dual_authorization: bool = False
    in_spec: bool = True
    link_on_entry: bool = False
    multi_result_set: bool = False
    prep_required: bool = False
    review_required: bool = False
    sample_split: bool = False
    schedule_available: bool = False
    sign_off_required: bool = False

    @field_validator("name")
    @classmethod
    def validate_site_prefix(cls, v: str) -> str:
        """Verify name starts with a valid site prefix (e.g., AND_ for Andover)."""
        if "_" not in v:
            raise ValueError(
                f"Analysis name '{v}' must contain a site prefix separated by '_' "
                f"(e.g., AND_ACS_DYE)"
            )
        return v

    @field_validator("analysis_type", mode="before")
    @classmethod
    def coerce_qc_samples(cls, v: str) -> str:
        """CTL and META suffixed analyses should use QC_SAMPLES type."""
        return v

    @model_validator(mode="after")
    def validate_qc_samples_suffix(self) -> "Analysis":
        """Analyses with CTL/META suffix must be QC_SAMPLES type."""
        if self.name.endswith(("_CTL", "_META")):
            if self.analysis_type != AnalysisType.QC_SAMPLES:
                raise ValueError(
                    f"Analysis '{self.name}' has CTL/META suffix but "
                    f"analysis_type={self.analysis_type!r}; expected QC_SAMPLES"
                )
        return self


# ---------------------------------------------------------------------------
# Sheet 2: Component
# ---------------------------------------------------------------------------


class Component(BaseModel):
    """Sheet 2 — individual test parameter within an Analysis.

    Classification rules (PDF pattern -> ResultType):
      - Visual yes/no         -> L (YES_NO_2 list)
      - Measurement + instr   -> N (uses_instrument=True)
      - Value from formula    -> K (auto_calc=True, LIMS Basic)
      - Equipment selection   -> K (GOSUB CALC_INST_PICKER)
      - Reagent/std selection -> K (GOSUB CALC_SR_PICKER)
      - Date entry            -> D
      - Free text             -> T
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    analysis: str
    component_name: str
    version: int = 1
    order_number: int
    result_type: ResultType
    units: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    # Instrument & calculation
    uses_instrument: bool = False
    instrument_group: Optional[str] = None
    auto_calc: bool = False
    list_key: Optional[str] = None

    # S/R Pickers (for equipment/reagent selection components)
    sr_picker: Optional[str] = None

    # Rounding
    round_type: Optional[RoundType] = None
    places: Optional[int] = None

    # Reporting
    reportable: bool = True
    optional: bool = False
    allow_out_of_range: bool = False

    @model_validator(mode="after")
    def validate_result_type_constraints(self) -> "Component":
        """Enforce result type constraints from ground truth.

        L-type requires a list_key.
        N-type with uses_instrument should have an instrument_group.

        Note: K-type does NOT require auto_calc=True. Many K-type components
        use GOSUB triggers (INST_PICKER, SR_PICKER, CALC_COMPONENTS_OPTIONAL)
        rather than auto-calc. The cross-sheet integrity check in MDATemplate
        ensures every K-type component has at least one Calculation entry.
        """
        if self.result_type == ResultType.L and not self.list_key:
            raise ValueError(
                f"Component '{self.component_name}': result_type=L requires "
                f"a list_key (e.g., YES_NO_2, PASS_FAIL)"
            )
        return self


# ---------------------------------------------------------------------------
# Sheet 6: CalcVariable
# ---------------------------------------------------------------------------


class CalcVariable(BaseModel):
    """Sheet 6 — variable used in LIMS Basic calculations.

    Cross-analysis pattern:
      reference_type=C: within same analysis (scope=CR typically)
      reference_type=A: cross-analysis ref (scope=B for batch-level)

    Example: Sponge Size lives in CTL analysis; primary analysis
    references it via reference_type=A, scope=B to compute Dye Volume.
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    analysis: str
    component: str
    name: str
    version: int = 1
    reference_type: CalcVariableReferenceType
    reference_analysis: Optional[str] = None
    reference_component: Optional[str] = None
    attribute_1: Optional[str] = None
    return_value: CalcVariableReturnValue = CalcVariableReturnValue.S
    scope: CalcVariableScope = CalcVariableScope.CR
    function: CalcVariableFunction = CalcVariableFunction.ENTRY

    @model_validator(mode="after")
    def validate_cross_analysis_reference(self) -> "CalcVariable":
        """Cross-analysis references (type=A) must specify the target analysis."""
        if self.reference_type == CalcVariableReferenceType.A:
            if not self.reference_analysis:
                raise ValueError(
                    f"CalcVariable '{self.name}' on {self.analysis}/{self.component}: "
                    f"reference_type=A requires reference_analysis to be set"
                )
        return self


# ---------------------------------------------------------------------------
# Sheet 7: Calculation
# ---------------------------------------------------------------------------


class Calculation(BaseModel):
    """Sheet 7 — LIMS Basic calculation code attached to a component.

    calculation_type classifies the code for routing:
      FORMULA      -> arithmetic expression
      CONDITIONAL  -> IF/THEN/ELSE logic
      INST_PICKER  -> GOSUB CALC_INST_PICKER
      SR_PICKER    -> GOSUB CALC_SR_PICKER
      GOSUB        -> other GOSUB calls
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    analysis: str
    component: str
    version: int = 1
    description: str = ""
    source_code: str
    calculation_type: CalculationType = CalculationType.FORMULA
    variables_used: List[str] = []

    @field_validator("source_code")
    @classmethod
    def validate_source_code_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Calculation source_code must not be empty")
        return v


# ---------------------------------------------------------------------------
# Root Model: MDATemplate
# ---------------------------------------------------------------------------


class MDATemplate(BaseModel):
    """Complete MDA template — 4 core sheets with cross-sheet integrity.

    Ground truth (ACS Dye-Binding): 3 analyses, 25 components,
    calc_variables and calculations for K-type components.
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    analyses: List[Analysis] = []
    components: List[Component] = []
    calc_variables: List[CalcVariable] = []
    calculations: List[Calculation] = []

    @model_validator(mode="after")
    def validate_cross_sheet_integrity(self) -> "MDATemplate":
        """Cross-sheet referential integrity validators."""
        analysis_names = {a.name for a in self.analyses}

        # 1. Every component must reference a valid analysis
        for comp in self.components:
            if comp.analysis not in analysis_names:
                raise ValueError(
                    f"Component '{comp.component_name}' references analysis "
                    f"'{comp.analysis}' which does not exist. "
                    f"Valid analyses: {sorted(analysis_names)}"
                )

        # 2. Every K-type component should have at least one calculation
        k_components = {
            (c.analysis, c.component_name)
            for c in self.components
            if c.result_type == ResultType.K
        }
        calc_components = {
            (c.analysis, c.component) for c in self.calculations
        }
        orphan_k = k_components - calc_components
        if orphan_k:
            raise ValueError(
                f"K-type components without calculations: {sorted(orphan_k)}. "
                f"Every K-type component must have at least one Calculation."
            )

        # 3. CalcVariable references must resolve to existing analyses
        for cv in self.calc_variables:
            if cv.analysis not in analysis_names:
                raise ValueError(
                    f"CalcVariable '{cv.name}' on analysis '{cv.analysis}' — "
                    f"analysis does not exist."
                )
            if (
                cv.reference_type == CalcVariableReferenceType.A
                and cv.reference_analysis
                and cv.reference_analysis not in analysis_names
            ):
                raise ValueError(
                    f"CalcVariable '{cv.name}' cross-references analysis "
                    f"'{cv.reference_analysis}' which does not exist."
                )

        # 4. Calculation references must point to valid analyses
        for calc in self.calculations:
            if calc.analysis not in analysis_names:
                raise ValueError(
                    f"Calculation for component '{calc.component}' references "
                    f"analysis '{calc.analysis}' which does not exist."
                )

        return self
