"""Identity test template skeleton — ACS Dye-Binding pattern.

Ground truth: AND_ACS_DYE / AND_ACS_DYE_CTL / AND_ACS_DYE_META (LAB-2499).
3 analyses, 25 components, 6 calc_variables, 10 calculations.

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
PRIMARY = "SITE_IDENTITY"
CTL = "SITE_IDENTITY_CTL"
META = "SITE_IDENTITY_META"


@TemplateLibrary.register(TestType.IDENTITY)
class IdentityTemplate(TestTypeTemplate):
    """ACS Dye-Binding Identity template — 3 analyses, 25 components."""

    test_type = TestType.IDENTITY

    # ------------------------------------------------------------------
    # TemplateComponent metadata (variable vs fixed classification)
    # ------------------------------------------------------------------
    def get_components(self) -> list[TemplateComponent]:
        return [
            # --- Fixed fields (LIMS convention) ---
            TemplateComponent(
                sheet="analyses", field_path="analyses[0].analysis_type",
                value="ID", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[1].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[2].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            # Component result types are fixed LIMS convention
            TemplateComponent(
                sheet="components", field_path="components[0].result_type",
                value="L", is_variable=False,
            ),
            TemplateComponent(
                sheet="components", field_path="components[4].result_type",
                value="N", is_variable=False,
            ),
            TemplateComponent(
                sheet="components", field_path="components[5].result_type",
                value="K", is_variable=False,
            ),
            # --- Variable fields (from PDF) ---
            TemplateComponent(
                sheet="analyses", field_path="analyses[0].description",
                value="", is_variable=True,
            ),
            TemplateComponent(
                sheet="components", field_path="components[4].minimum",
                value=None, is_variable=True,
            ),
            TemplateComponent(
                sheet="components", field_path="components[4].maximum",
                value=None, is_variable=True,
            ),
        ]

    # ------------------------------------------------------------------
    # Full MDATemplate builder
    # ------------------------------------------------------------------
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
            reported_name="ACS Dye Binding",
            common_name="ID",
            analysis_type=AnalysisType.ID,
            description="Dye-Binding Identity Test for Absorbable Collagen Sponge (ACS)",
        ),
        Analysis(
            name=CTL,
            version=1,
            group_name="ANDOVER",
            reported_name="ACS Dye Binding Ctl",
            common_name="ID",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="Dye-Binding Identity Test for ACS - Control",
        ),
        Analysis(
            name=META,
            version=1,
            group_name="ANDOVER",
            reported_name="ACS Dye Binding Meta",
            common_name="ID",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="Dye-Binding Identity Test for ACS - Meta Data",
        ),
    ]


# =====================================================================
# Component definitions (Sheet 2) — 25 total
# =====================================================================
def _build_components() -> list[Component]:
    return [
        # ---- PRIMARY analysis (9 components) ----
        Component(
            analysis=PRIMARY,
            component_name="Package: Double layered and sealed?",
            order_number=1,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sponge Color: White to Off-White?",
            order_number=2,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sponge Shape: Rectangular?",
            order_number=3,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Sponge Packing: Dry?",
            order_number=4,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Weight of Sponge(s)",
            order_number=5,
            result_type=ResultType.N,
            units="MG",
            uses_instrument=True,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Dye Volume for Sponge(s), Expected",
            order_number=6,
            result_type=ResultType.K,
            units="ML",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Dye Volume for Sponge(s), Actual",
            order_number=7,
            result_type=ResultType.N,
            units="ML",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Is Supernatant Less Intense than Std B?",
            order_number=8,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Confirmation of ACS Identity",
            order_number=9,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=True,
            places=1,
            reportable=True,
        ),
        # ---- CTL analysis (7 components) ----
        Component(
            analysis=CTL,
            component_name="Sponge Size",
            order_number=1,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=False,
            list_key="AND_SPONGE_SIZE",
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Petri Dish used for Sample",
            order_number=2,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_PETRI_100, AND_PETRI_150",
            places=0,
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Direct Red Solution Used for Binding",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Weight of Collagen Control",
            order_number=4,
            result_type=ResultType.N,
            units="MG",
            uses_instrument=True,
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Dye Volume for Control, Expected",
            order_number=5,
            result_type=ResultType.K,
            units="ML",
            auto_calc=True,
            round_type=RoundType.U,
            places=0,
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Dye Volume for Control, Actual",
            order_number=6,
            result_type=ResultType.N,
            units="ML",
            reportable=True,
        ),
        Component(
            analysis=CTL,
            component_name="Ctl Supernatant Less Intense than Std B?",
            order_number=7,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="YES_NO_2",
            reportable=True,
        ),
        # ---- META analysis (9 components) ----
        Component(
            analysis=META,
            component_name="Date Performed",
            order_number=1,
            result_type=ResultType.D,
            units="NONE",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Method/Version",
            order_number=2,
            result_type=ResultType.T,
            units="NONE",
            auto_calc=True,
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Timer",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="TIMER",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Balance",
            order_number=4,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="BAL",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="0.5 M Acetic Acid",
            order_number=5,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_HAC_0_5M",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="1 mm Direct Red 80 Solution",
            order_number=6,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_DRED80_1MM",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="0.75 mM Direct Red 80 Solution",
            order_number=7,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_DRED80750U",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Type I Collagen Control",
            order_number=8,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_COLLAGEN_1",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Is Assay Valid?",
            order_number=9,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="AND_META_INV_VAL",
            reportable=True,
        ),
    ]


# =====================================================================
# CalcVariable definitions (Sheet 6) — 6 total
# =====================================================================
def _build_calc_variables() -> list[CalcVariable]:
    return [
        # PRIMARY: Confirmation of ACS Identity
        CalcVariable(
            analysis=PRIMARY,
            component="Confirmation of ACS Identity",
            name="Sample",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Is Supernatant Less Intense than Std B?",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # PRIMARY: Dye Volume for Sponge(s), Expected
        CalcVariable(
            analysis=PRIMARY,
            component="Dye Volume for Sponge(s), Expected",
            name="Size",
            reference_type=CalcVariableReferenceType.A,
            reference_analysis=CTL,
            attribute_1="Sponge Size",
            return_value=CalcVariableReturnValue.A,
            scope=CalcVariableScope.B,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Dye Volume for Sponge(s), Expected",
            name="Weight",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Weight of Sponge(s)",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # CTL: Direct Red Solution Used for Binding
        CalcVariable(
            analysis=CTL,
            component="Direct Red Solution Used for Binding",
            name="Size",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=CTL,
            attribute_1="Sponge Size",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # CTL: Dye Volume for Control, Expected
        CalcVariable(
            analysis=CTL,
            component="Dye Volume for Control, Expected",
            name="Size",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=CTL,
            attribute_1="Sponge Size",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=CTL,
            component="Dye Volume for Control, Expected",
            name="Weight",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=CTL,
            attribute_1="Weight of Collagen Control",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
    ]


# =====================================================================
# Calculation definitions (Sheet 7) — 10 total
# =====================================================================
def _build_calculations() -> list[Calculation]:
    return [
        # ---- PRIMARY ----
        Calculation(
            analysis=PRIMARY,
            component="Confirmation of ACS Identity",
            source_code=(
                'IF (Sample = "YES") THEN\n'
                'RETURN "Pass"\n'
                "ELSE\n"
                'RETURN "Fail"\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Sample"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Dye Volume for Sponge(s), Expected",
            source_code=(
                "Calculation based on size of sponge tested\n"
                "IF (IsEmpty(Size[1])) THEN\n"
                'RETURN ""\n'
                'ELSEIF ((Size[1] = "1_BY_2") OR (Size[1] = "HALF_BY_2")) THEN\n'
                "RETURN 20 * Weight / 100\n"
                'ELSEIF (Size[1]= "3_BY_4") THEN\n'
                "RETURN 15 * Weight / 100\n"
                "ELSE ' Should never happen unless list modified\n"
                'RETURN ""\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Size", "Weight"],
        ),
        # ---- CTL ----
        Calculation(
            analysis=CTL,
            component="Direct Red Solution Used for Binding",
            source_code=(
                "Calculation based on size of sponge tested\n"
                'IF ((Size = "1_BY_2") OR (Size = "HALF_BY_2")) THEN\n'
                'RETURN "0.75 mM Direct Red 80 Solution"\n'
                'ELSEIF (Size = "3_BY_4") THEN\n'
                'RETURN "1 mm Direct Red 80 Solution"\n'
                "ELSE ' Should never happen unless list modified\n"
                'RETURN ""\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Size"],
        ),
        Calculation(
            analysis=CTL,
            component="Dye Volume for Control, Expected",
            source_code=(
                "Calculation based on size of sponge tested\n"
                'IF ((Size = "1_BY_2") OR (Size = "HALF_BY_2")) THEN\n'
                "RETURN 20 * Weight / 100\n"
                'ELSEIF (Size = "3_BY_4") THEN\n'
                "RETURN 15 * Weight / 100\n"
                "ELSE ' Should never happen unless list modified\n"
                'RETURN ""\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Size", "Weight"],
        ),
        Calculation(
            analysis=CTL,
            component="Petri Dish used for Sample",
            source_code=(
                "g_sr_list = \"'PETRI_150', 'PETRI_100', 'PETRI_60'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        # ---- META ----
        Calculation(
            analysis=META,
            component="0.5 M Acetic Acid",
            source_code=(
                "g_sr_list = \"'HAC_0_5M'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=META,
            component="0.75 mM Direct Red 80 Solution",
            source_code=(
                "g_na = true\n"
                "'g_sr_list = \"'DRED80750U'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=META,
            component="1 mm Direct Red 80 Solution",
            source_code=(
                "g_sr_list = \"'DRED80_1MM'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Balance",
            source_code=(
                'g_inst_group = "BAL"\n'
                "GOSUB CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Timer",
            source_code=(
                'g_inst_group = "TIMER"\n'
                "GOSUB CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Type I Collagen Control",
            source_code=(
                "g_sr_list = \"'COLLAGEN_1'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
    ]
