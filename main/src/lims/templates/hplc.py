"""HPLC (CEX-HPLC) test template skeleton.

Ground truth: AND_BCMA_CEX / AND_BCMA_CEX_M / AND_BCMA_CEX_REF / AND_BCMA_CEX_SD (LAB-38176).
4 analyses, 59 components, 48 calc_variables, 28 calculations.

Cation Exchange HPLC — most complex template type.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

from main.src.lims.mda_schema import (
    Analysis,
    AnalysisType,
    Calculation,
    CalculationType,
    CalcVariable,
    CalcVariableFunction,
    CalcVariableReferenceType,
    CalcVariableReturnValue,
    CalcVariableScope,
    Component,
    MDATemplate,
    ResultType,
    RoundType,
)
from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType

# ---------------------------------------------------------------------------
# Analysis name constants
# ---------------------------------------------------------------------------
PRIMARY = "SITE_HPLC"
M = "SITE_HPLC_M"
REF = "SITE_HPLC_REF"
SD = "SITE_HPLC_SD"


@TemplateLibrary.register(TestType.HPLC)
class HPLCTemplate(TestTypeTemplate):
    """CEX-HPLC template — 4 analyses, 59 components."""

    test_type = TestType.HPLC

    def get_components(self) -> list[TemplateComponent]:
        return [
            # Fixed: analysis types
            TemplateComponent(
                sheet="analyses", field_path="analyses[0].analysis_type",
                value="HPLC", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[1].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[2].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[3].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            # Fixed: K-type result types for calculated components
            TemplateComponent(
                sheet="components", field_path="components[0].result_type",
                value="K", is_variable=False,
            ),
            # Variable: sample concentration (from PDF)
            TemplateComponent(
                sheet="components", field_path="components[0].minimum",
                value=None, is_variable=True,
            ),
            TemplateComponent(
                sheet="components", field_path="components[0].maximum",
                value=None, is_variable=True,
            ),
            # Variable: detector sensitivity limits (from PDF)
            TemplateComponent(
                sheet="components", field_path="sd_components.detector_sensitivity.minimum",
                value=None, is_variable=True,
            ),
            TemplateComponent(
                sheet="components", field_path="sd_components.detector_sensitivity.maximum",
                value=None, is_variable=True,
            ),
        ]

    def to_mda_template(self) -> MDATemplate:
        return MDATemplate(
            analyses=_build_analyses(),
            components=_build_components(),
            calc_variables=_build_calc_variables(),
            calculations=_build_calculations(),
        )


# =====================================================================
# Analysis definitions (Sheet 1)
# =====================================================================
def _build_analyses() -> list[Analysis]:
    return [
        Analysis(
            name=PRIMARY,
            version=1,
            group_name="ANDOVER",
            reported_name="CEX-HPLC",
            common_name="HPLC",
            analysis_type=AnalysisType.HPLC,
            description="Cation Exchange High Performance Liquid Chromatography (CEX-HPLC) Assay",
        ),
        Analysis(
            name=M,
            version=1,
            group_name="ANDOVER",
            reported_name="CEX-HPLC Meta",
            common_name="HPLC",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="CEX-HPLC Assay, Metadata",
        ),
        Analysis(
            name=REF,
            version=1,
            group_name="ANDOVER",
            reported_name="CEX-HPLC Ref",
            common_name="HPLC",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="CEX-HPLC Assay, Reference",
        ),
        Analysis(
            name=SD,
            version=1,
            group_name="ANDOVER",
            reported_name="Sensitivity Detect",
            common_name="HPLC",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="CEX-HPLC Assay, Sensitivity of Detection",
        ),
    ]


# =====================================================================
# Component definitions (Sheet 2) — 59 total
# =====================================================================
def _build_components() -> list[Component]:
    return [
        # ==== PRIMARY analysis: 13 components ====
        Component(
            analysis=PRIMARY,
            component_name="Sample Concentration",
            order_number=1,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=False,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Concentration Reference",
            order_number=2,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Final Volume",
            order_number=3,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sample Volume, Qty Exp",
            order_number=4,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sample Volume, Qty Act",
            order_number=5,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Mobile Phase A, Qty Exp",
            order_number=6,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Mobile Phase A, Qty Act",
            order_number=7,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Final Sample Concentration",
            order_number=8,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sample Profile Acceptable",
            order_number=9,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="PASS_FAIL",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="% BCMA mAb",
            order_number=10,
            result_type=ResultType.N,
            units="PERCENT",
            places=3,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="% BCMA mAb reported",
            order_number=11,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            round_type=RoundType.U,
            places=1,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="% Anti-BCMA/Anti-CD3 mAb Clip",
            order_number=12,
            result_type=ResultType.N,
            units="PERCENT",
            places=3,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="% Anti-BCMA/ Anti-CD3 mAb Clip reported",
            order_number=13,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            round_type=RoundType.U,
            places=1,
            reportable=True,
        ),
        # ==== M (Meta) analysis: 7 components ====
        Component(
            analysis=M,
            component_name="Date Performed",
            order_number=1,
            result_type=ResultType.D,
            units="NONE",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=M,
            component_name="Method / Version",
            order_number=2,
            result_type=ResultType.T,
            units="NONE",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=M,
            component_name="Pipette",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="PIPETTE",
            places=0,
            reportable=True,
            num_replicates=2,
        ),
        Component(
            analysis=M,
            component_name="Mobile Phase A",
            order_number=4,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_CX_1_PH_5_6_MP",
            reportable=True,
        ),
        Component(
            analysis=M,
            component_name="Mobile Phase B",
            order_number=5,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_CX_1_PH_102_MP",
            reportable=True,
        ),
        Component(
            analysis=M,
            component_name="Column",
            order_number=6,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_BCMA_CEX_COL",
            reportable=True,
        ),
        Component(
            analysis=M,
            component_name="Is Assay Valid?",
            order_number=7,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="AND_META_INV_VAL",
            reportable=True,
        ),
        # ==== REF analysis: 21 components ====
        Component(
            analysis=REF,
            component_name="Reference Material",
            order_number=1,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_BCMA_REF",
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Reference Material Concentration",
            order_number=2,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Final Volume",
            order_number=3,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Reference Material, Qty Exp",
            order_number=4,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Reference Material, Qty Act",
            order_number=5,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Mobile Phase A, Qty Exp",
            order_number=6,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Mobile Phase A, Qty Act",
            order_number=7,
            result_type=ResultType.N,
            units="UL",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Final Reference Material Concentration",
            order_number=8,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="SYS INJ 1 BCMA mAb Main",
            order_number=9,
            result_type=ResultType.N,
            units="PERCENT",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="SYS INJ 2 BCMA mAb Main",
            order_number=10,
            result_type=ResultType.N,
            units="PERCENT",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="SYS INJ 3 BCMA mAb Main",
            order_number=11,
            result_type=ResultType.N,
            units="PERCENT",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="BRKT INJ BCMA mAb Main",
            order_number=12,
            result_type=ResultType.N,
            units="PERCENT",
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Blank Injection Free of interfering Peak",
            order_number=13,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="PASS_FAIL",
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Suitability Profiles comparable to SOP",
            order_number=14,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="PASS_FAIL",
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Mean SYS BCMA mAb Main",
            order_number=15,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="STD DEV SYS BCMA mAb Mean",
            order_number=16,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="% Anti-BCMA/ Anti-CD3 mAb %RSD,SS",
            order_number=17,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="All Reference Profiles acceptable",
            order_number=18,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="PASS_FAIL",
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="Mean of 4 Ref Injections mAb Main",
            order_number=19,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="STD DEV of 4 Ref Injections mAb Main",
            order_number=20,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=REF,
            component_name="% Anti-BCMA/ Anti-CD3 mAb %RSD, AAC",
            order_number=21,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        # ==== SD (Sensitivity of Detection) analysis: 18 components ====
        Component(
            analysis=SD,
            component_name="Reference Material",
            order_number=1,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_BCMA_REF",
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Reference Material Concentration",
            order_number=2,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=True,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Final Volume Dilution 1",
            order_number=3,
            result_type=ResultType.N,
            units="UL",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Final Concentration Dil 1",
            order_number=4,
            result_type=ResultType.N,
            units="MG_ML",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Reference Material, Qty Exp",
            order_number=5,
            result_type=ResultType.K,
            units="UL",
            minimum=10.0,
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Reference Material, Qty Act",
            order_number=6,
            result_type=ResultType.N,
            units="UL",
            minimum=10.0,
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Mobile Phase, Qty Exp",
            order_number=7,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Mobile Phase, Qty Act",
            order_number=8,
            result_type=ResultType.N,
            units="UL",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Final Volume Dilution 2",
            order_number=9,
            result_type=ResultType.N,
            units="UL",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Final Concentration Dil 2",
            order_number=10,
            result_type=ResultType.K,
            units="MG_ML",
            auto_calc=True,
            places=1,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Dilution 1, Qty Exp",
            order_number=11,
            result_type=ResultType.K,
            units="UL",
            minimum=10.0,
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Dilution 1, Qty Act",
            order_number=12,
            result_type=ResultType.N,
            units="UL",
            minimum=10.0,
            places=0,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Mobile Phase 2, Qty Exp",
            order_number=13,
            result_type=ResultType.K,
            units="UL",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Mobile Phase 2, Qty Act",
            order_number=14,
            result_type=ResultType.N,
            units="UL",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Peak B Area of DSS",
            order_number=15,
            result_type=ResultType.N,
            units="PEAK_AREA",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Peak B Area 3 SS INJ",
            order_number=16,
            result_type=ResultType.N,
            units="PEAK_AREA",
            places=1,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Detector Sensitivity (%)",
            order_number=17,
            result_type=ResultType.K,
            units="PERCENT",
            minimum=0.6,
            maximum=1.2,
            auto_calc=True,
            round_type=RoundType.U,
            places=1,
            reportable=True,
        ),
        Component(
            analysis=SD,
            component_name="Detector Sensitivity (%) Acceptable",
            order_number=18,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="PASS_FAIL",
            reportable=True,
        ),
    ]


# =====================================================================
# CalcVariable definitions (Sheet 6) — 48 total
# =====================================================================
def _build_calc_variables() -> list[CalcVariable]:
    return [
        # ---- PRIMARY (9 variables) ----
        CalcVariable(
            analysis=PRIMARY,
            component="% Anti-BCMA/ Anti-CD3 mAb Clip reported",
            name="Bispec",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="% Anti-BCMA/Anti-CD3 mAb Clip",
            return_value=CalcVariableReturnValue.P,
            scope=CalcVariableScope.CT,
            function=CalcVariableFunction.AVE,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="% BCMA mAb reported",
            name="BCMA",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="% BCMA mAb",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Final Sample Concentration",
            name="Conc",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Sample Concentration",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Final Sample Concentration",
            name="FormVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Mobile Phase A, Qty Act",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Final Sample Concentration",
            name="SampVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Sample Volume, Qty Act",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Mobile Phase A, Qty Exp",
            name="SampVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Sample Volume, Qty Exp",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Mobile Phase A, Qty Exp",
            name="Vol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Final Volume",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Sample Volume, Qty Exp",
            name="Conc",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Sample Concentration",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Sample Volume, Qty Exp",
            name="Vol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Final Volume",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # ---- REF (26 variables) ----
        CalcVariable(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD, AAC",
            name="MeanS",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Mean of 4 Ref Injections mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD, AAC",
            name="StdD",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="STD DEV of 4 Ref Injections mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD,SS",
            name="MeanS",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Mean SYS BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD,SS",
            name="StdD",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="STD DEV SYS BCMA mAb Mean",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Final Reference Material Concentration",
            name="Conc",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Reference Material Concentration",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Final Reference Material Concentration",
            name="FormVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Mobile Phase A, Qty Act",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Final Reference Material Concentration",
            name="RefVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Reference Material, Qty Act",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean SYS BCMA mAb Main",
            name="SYS1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 1 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean SYS BCMA mAb Main",
            name="SYS2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 2 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean SYS BCMA mAb Main",
            name="SYS3",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 3 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean of 4 Ref Injections mAb Main",
            name="SYS1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 1 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean of 4 Ref Injections mAb Main",
            name="SYS2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 2 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean of 4 Ref Injections mAb Main",
            name="SYS3",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 3 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mean of 4 Ref Injections mAb Main",
            name="SYS4",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="BRKT INJ BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mobile Phase A, Qty Exp",
            name="RefVol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Reference Material, Qty Exp",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Mobile Phase A, Qty Exp",
            name="Vol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Final Volume",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Reference Material Concentration",
            name="strSR",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Reference Material",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Reference Material, Qty Exp",
            name="Conc",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Reference Material Concentration",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="Reference Material, Qty Exp",
            name="Vol",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="Final Volume",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV SYS BCMA mAb Mean",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 1 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV SYS BCMA mAb Mean",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 2 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV SYS BCMA mAb Mean",
            name="var3",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 3 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV of 4 Ref Injections mAb Main",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 1 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV of 4 Ref Injections mAb Main",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 2 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV of 4 Ref Injections mAb Main",
            name="var3",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="SYS INJ 3 BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=REF,
            component="STD DEV of 4 Ref Injections mAb Main",
            name="var4",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=REF,
            attribute_1="BRKT INJ BCMA mAb Main",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # ---- SD (13 variables) ----
        CalcVariable(
            analysis=SD,
            component="Detector Sensitivity (%)",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Peak B Area of DSS",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Detector Sensitivity (%)",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Peak B Area 3 SS INJ",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Dilution 1, Qty Exp",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Concentration Dil 2",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Dilution 1, Qty Exp",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Volume Dilution 2",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Dilution 1, Qty Exp",
            name="var3",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Concentration Dil 1",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Mobile Phase 2, Qty Exp",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Volume Dilution 2",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Mobile Phase 2, Qty Exp",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Dilution 1, Qty Exp",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Mobile Phase, Qty Exp",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Volume Dilution 1",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Mobile Phase, Qty Exp",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Reference Material, Qty Exp",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Reference Material Concentration",
            name="strSR",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Reference Material",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Reference Material, Qty Exp",
            name="Conc",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Reference Material Concentration",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Reference Material, Qty Exp",
            name="var1",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Concentration Dil 1",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=SD,
            component="Reference Material, Qty Exp",
            name="var2",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=SD,
            attribute_1="Final Volume Dilution 1",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
    ]


# =====================================================================
# Calculation definitions (Sheet 7) — 28 total
# =====================================================================
def _build_calculations() -> list[Calculation]:
    return [
        # ---- PRIMARY (7 calculations) ----
        Calculation(
            analysis=PRIMARY,
            component="% Anti-BCMA/ Anti-CD3 mAb Clip reported",
            source_code=(
                "Bispec = val(RoundOddUp(Bispec, 1))\n"
                "IF (Bispec <= 0.3) THEN\n"
                'Return "NMT 0.3"\n'
                "ELSE\n"
                "Return Bispec\n"
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Bispec"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="% BCMA mAb reported",
            source_code=(
                "BCMA = val(RoundOddUp(BCMA, 1))\n"
                "IF (BCMA <= 0.3) THEN\n"
                'Return "NMT 0.3"\n'
                "ELSE\n"
                "Return BCMA\n"
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["BCMA"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Concentration Reference",
            source_code=(
                "smpnum = select sample.sample_number\n"
                "tstnum = select test.test_number\n"
                "rsltnum = select result.result_number\n"
                "intLot1 = select sample.t_ph_related_lot\n"
                "strSampleType = select Sample.C_Sample_Type\n"
                "intLot2 = select sample.lot\n"
                "prodGrade = select sample.product_grade\n"
                "prodStage = select sample.stage\n"
                "prodSpecType = select sample.spec_type\n"
                'IF (strSampleType = "ADH") THEN\n'
                'Msgbox("Please manually enter concentration reference information.")\n'
                "status = ConvertResultToText(smpnum, tstnum,rsltnum)\n"
                "GOSUB RESULT_ENTRY_REFRESH\n"
                "Return\n"
                'ELSEIF (strSampleType = "STB") THEN\n'
                'strAnalysisName = "AND_CONC_ASSAY_SUM"\n'
                "strProtocol = SELECT sample.protocol\n"
                "strTestArticle = SELECT sample.formulation\n"
                "strCondition = SELECT sample.condition\n"
                "strLevel = SELECT SAMPLE.PROTOCOL_LEVEL\n"
                'q = "select distinct t.batch"\n'
                "q = q + \" from sample s, test t, time_zero tz\"\n"
                "q = q + \" where t.analysis = '\" + strAnalysisName + \"' \"\n"
                "q = q + \" and t.status = 'A'\"\n"
                "q = q + \" and s.sample_number = t.sample_number\"\n"
                "q = q + \" and tz.OBJECT_ID = s.sample_number\"\n"
                "q = q + \" and tz.protocol = '\" + strProtocol + \"'\"\n"
                "q = q + \" and tz.test_article = '\" + strTestArticle + \"'\"\n"
                "q = q + \" and tz.condition = '\" + strCondition + \"'\"\n"
                "q = q + \" and tz.level_name = '\" + strLevel + \"'\"\n"
                "ELSE\n"
                'q = "Select distinct t.batch"\n'
                'q = q + " from sample s, test t"\n'
                'q = q + " where s.sample_number = t.sample_number"\n'
                "q = q + \" and s.stage = '\" + prodStage + \"'\"\n"
                "q = q + \" and s.lot = '\" + intLot2 + \"'\"\n"
                "q = q + \" and s.product_grade = '\" + prodGrade + \"'\"\n"
                "q = q + \" and s.spec_type = '\" + prodSpecType + \"'\"\n"
                "q = q + \" and t.Analysis = 'AND_CONC_ASSAY_SUM'\"\n"
                "q = q + \" and t.status = 'A' \"\n"
                "ENDIF\n"
                "'Perform the query\n"
                'status = SQL(q, "tempArray")\n'
                "'Get the sample concentration reference\n"
                "ProtConcRef = tempArray[1,1]\n"
                "IF (IsEmpty(ProtConcRef)) OR (IsNull(ProtConcRef)) THEN\n"
                'Msgbox("Protein Concentration Assay Reference # not found, '
                'ensure result has been entered, peer reviewed and approved")\n'
                'Return ""\n'
                "ENDIF\n"
                "Return ProtConcRef"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        Calculation(
            analysis=PRIMARY,
            component="Final Sample Concentration",
            source_code="Return ((Conc * SampVol) / (SampVol + FormVol))",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Conc", "SampVol", "FormVol"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Mobile Phase A, Qty Exp",
            source_code="Return (Vol - SampVol)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Vol", "SampVol"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Sample Concentration",
            source_code=(
                "smpNum = select sample.sample_number\n"
                "testNum = select test.test_number\n"
                "rsltNum = select result.result_number\n"
                "smpType = select sample.c_sample_type\n"
                'IF (smpType = "PRD" OR smpType = "RAW") THEN\n'
                'strAnalysisName = "AND_CONC_ASSAY_SUM"\n'
                'strResultName = "Average Concentration"\n'
                "gosub CALC_TEST_RESULT\n"
                "protConc = arrResultValue[1,1]\n"
                "RETURN protConc\n"
                'ELSEIF (smpType = "STB") THEN\n'
                'strAnalysisName = "AND_CONC_ASSAY_SUM"\n'
                'strResultName = "Average Concentration"\n'
                "flagTimeZero = TRUE\n"
                "gosub CALC_STAB_RESULT\n"
                "protConc = arrResultValue[1,1]\n"
                "IF (IsEmpty(protConc)) OR (IsNull(protConc)) THEN\n"
                'Msgbox("T0 protein concentration not found.")\n'
                'Return ""\n'
                "ENDIF\n"
                "RETURN protConc\n"
                "ELSE\n"
                'msgbox("Sample is a Special Test Request sample.")\n'
                "status = ConvertResultToNumeric(smpNum, testNum, rsltNum)\n"
                "GOSUB RESULT_ENTRY_REFRESH\n"
                "RETURN\n"
                "ENDIF"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        Calculation(
            analysis=PRIMARY,
            component="Sample Volume, Qty Exp",
            source_code="Return ((Vol * 1.0) / Conc)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Vol", "Conc"],
        ),
        # ---- M (Meta) (4 calculations) ----
        Calculation(
            analysis=M,
            component="Column",
            source_code=(
                "g_sr_list = \"'BCMA_CEX_COL'\"\n"
                "gosub CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=M,
            component="Mobile Phase A",
            source_code=(
                "g_sr_list = \"'CX_1_PH_5_6_MP'\"\n"
                "gosub CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=M,
            component="Mobile Phase B",
            source_code=(
                "g_sr_list = \"'CX_1_PH_102_MP'\"\n"
                "gosub CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=M,
            component="Pipette",
            source_code=(
                "g_na = true\n"
                "'g_inst_group = \"PIPETTE\"\n"
                "gosub CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        # ---- REF (10 calculations) ----
        Calculation(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD, AAC",
            source_code=(
                "rsltnum = SELECT result.result_number\n"
                "Res = (StdD / MeanS) * 100\n"
                "Res1 = Val(RoundOddUp(Res,0))\n"
                "IF (Res1 > 5) THEN\n"
                "status = OutOfSpec(rsltnum)\n"
                "ELSE\n"
                "status = InSpec(rsltnum)\n"
                "ENDIF\n"
                "Return Res1"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["StdD", "MeanS"],
        ),
        Calculation(
            analysis=REF,
            component="% Anti-BCMA/ Anti-CD3 mAb %RSD,SS",
            source_code=(
                "rsltnum = SELECT result.result_number\n"
                "Res = (StdD / MeanS) * 100\n"
                "Res1 = Val(RoundOddUp(Res,0))\n"
                "IF (Res1 > 5) THEN\n"
                "status = OutOfSpec(rsltnum)\n"
                "ELSE\n"
                "status = InSpec(rsltnum)\n"
                "ENDIF\n"
                "Return Res1"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["StdD", "MeanS"],
        ),
        Calculation(
            analysis=REF,
            component="Final Reference Material Concentration",
            source_code="Return ((Conc * RefVol) / (RefVol + FormVol))",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Conc", "RefVol", "FormVol"],
        ),
        Calculation(
            analysis=REF,
            component="Mean SYS BCMA mAb Main",
            source_code=(
                "Res = (SYS1 + SYS2 + SYS3 ) / 3\n"
                "Return Res"
            ),
            calculation_type=CalculationType.FORMULA,
            variables_used=["SYS1", "SYS2", "SYS3"],
        ),
        Calculation(
            analysis=REF,
            component="Mean of 4 Ref Injections mAb Main",
            source_code=(
                "Res = (SYS1 + SYS2 + SYS3 + SYS4) / 4\n"
                "Return Res"
            ),
            calculation_type=CalculationType.FORMULA,
            variables_used=["SYS1", "SYS2", "SYS3", "SYS4"],
        ),
        Calculation(
            analysis=REF,
            component="Mobile Phase A, Qty Exp",
            source_code="Return (Vol - RefVol)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Vol", "RefVol"],
        ),
        Calculation(
            analysis=REF,
            component="Reference Material",
            source_code=(
                "g_sr_list = \"'BCMA_REF'\"\n"
                "gosub CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=REF,
            component="Reference Material Concentration",
            source_code=(
                'strResult = "Protein Concentration"\n'
                'strValueName = "ENTRY"\n'
                "gosub CALC_SR_RESULT"
            ),
            calculation_type=CalculationType.GOSUB,
            variables_used=["strSR"],
        ),
        Calculation(
            analysis=REF,
            component="Reference Material, Qty Exp",
            source_code="RETURN ((Vol * 1.0) / Conc)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["Vol", "Conc"],
        ),
        Calculation(
            analysis=REF,
            component="STD DEV SYS BCMA mAb Mean",
            source_code=(
                "array[1,1] = var1\n"
                "array[1,2] = var2\n"
                "array[1,3] = var3\n"
                "x = Std(array)\n"
                "Return x"
            ),
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2", "var3"],
        ),
        Calculation(
            analysis=REF,
            component="STD DEV of 4 Ref Injections mAb Main",
            source_code=(
                "array[1,1] = var1\n"
                "array[1,2] = var2\n"
                "array[1,3] = var3\n"
                "array[1,4] = var4\n"
                "x = Std(array)\n"
                "Return x"
            ),
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2", "var3", "var4"],
        ),
        # ---- SD (7 calculations) ----
        Calculation(
            analysis=SD,
            component="Detector Sensitivity (%)",
            source_code="Return ((var1 / var2) * 100)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2"],
        ),
        Calculation(
            analysis=SD,
            component="Dilution 1, Qty Exp",
            source_code="Return ((var1 * var2) / var3)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2", "var3"],
        ),
        Calculation(
            analysis=SD,
            component="Final Concentration Dil 2",
            source_code="Return 0.1",
            calculation_type=CalculationType.FORMULA,
        ),
        Calculation(
            analysis=SD,
            component="Mobile Phase 2, Qty Exp",
            source_code="Return (var1 - var2)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2"],
        ),
        Calculation(
            analysis=SD,
            component="Mobile Phase, Qty Exp",
            source_code="Return (var1 - var2)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2"],
        ),
        Calculation(
            analysis=SD,
            component="Reference Material",
            source_code=(
                "g_sr_list = \"'BCMA_REF'\"\n"
                "gosub CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=SD,
            component="Reference Material Concentration",
            source_code=(
                'strResult = "Protein Concentration"\n'
                'strValueName = "ENTRY"\n'
                "gosub CALC_SR_RESULT"
            ),
            calculation_type=CalculationType.GOSUB,
            variables_used=["strSR"],
        ),
        Calculation(
            analysis=SD,
            component="Reference Material, Qty Exp",
            source_code="Return ((var1 * var2) / Conc)",
            calculation_type=CalculationType.FORMULA,
            variables_used=["var1", "var2", "Conc"],
        ),
    ]
