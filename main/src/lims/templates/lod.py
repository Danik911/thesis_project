"""LOD (Loss on Drying) test template skeleton.

Ground truth: AND_LOD_CW_U / AND_LOD_CW_U_META (USP Constant Weight).
2 analyses, 14 components, 4 calc_variables, 6 calculations.

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
)
from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType

# ---------------------------------------------------------------------------
# Analysis name constants
# ---------------------------------------------------------------------------
PRIMARY = "SITE_LOD"
META = "SITE_LOD_META"


@TemplateLibrary.register(TestType.LOD)
class LODTemplate(TestTypeTemplate):
    """Loss on Drying template — 2 analyses, 14 components."""

    test_type = TestType.LOD

    def get_components(self) -> list[TemplateComponent]:
        return [
            # Fixed: analysis types
            TemplateComponent(
                sheet="analyses", field_path="analyses[0].analysis_type",
                value="RM", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[1].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            # Fixed: component result types
            TemplateComponent(
                sheet="components", field_path="components[0].result_type",
                value="K", is_variable=False,
            ),
            TemplateComponent(
                sheet="components", field_path="components[1].result_type",
                value="N", is_variable=False,
            ),
            # Variable: drying temperature (from PDF)
            TemplateComponent(
                sheet="components", field_path="components[1].minimum",
                value=None, is_variable=True,
            ),
            TemplateComponent(
                sheet="components", field_path="components[1].maximum",
                value=None, is_variable=True,
            ),
            # Variable: pass/fail limits from PDF
            TemplateComponent(
                sheet="components", field_path="components[7].maximum",
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
            reported_name="Loss on Drying CW",
            common_name="PHYSICAL",
            analysis_type=AnalysisType.RM,
            description="Loss on Drying, Constant Weight, USP",
            batch_link=True,
        ),
        Analysis(
            name=META,
            version=1,
            group_name="ANDOVER",
            reported_name="LOD CW Meta",
            common_name="PHYSICAL",
            analysis_type=AnalysisType.QC_SAMPLES,
            description="Loss on Drying Test, Constant Weight, USP - Meta Data",
            batch_link=True,
        ),
    ]


# =====================================================================
# Component definitions (Sheet 2) — 14 total
# =====================================================================
def _build_components() -> list[Component]:
    return [
        # ---- PRIMARY analysis (8 components) ----
        Component(
            analysis=PRIMARY,
            component_name="Contract test?",
            order_number=1,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Drying Temperature",
            order_number=2,
            result_type=ResultType.N,
            units="DEG_C",
            auto_calc=True,
            optional=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Tare Drying Time",
            order_number=3,
            result_type=ResultType.N,
            units="HR",
            places=1,
            auto_calc=True,
            optional=True,
            reportable=False,
            num_replicates=2,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Tare Weight",
            order_number=4,
            result_type=ResultType.N,
            units="G",
            places=1,
            uses_instrument=True,
            auto_calc=False,
            optional=True,
            reportable=False,
            num_replicates=2,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Gross Weight",
            order_number=5,
            result_type=ResultType.N,
            units="G",
            places=1,
            uses_instrument=True,
            auto_calc=True,
            optional=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Drying Time",
            order_number=6,
            result_type=ResultType.N,
            units="HR",
            places=1,
            auto_calc=False,
            optional=True,
            reportable=False,
            num_replicates=2,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Dry Weight",
            order_number=7,
            result_type=ResultType.N,
            units="G",
            places=1,
            uses_instrument=True,
            auto_calc=True,
            optional=True,
            reportable=False,
            num_replicates=2,
        ),
        Component(
            analysis=PRIMARY,
            component_name="% Loss on Drying",
            order_number=8,
            result_type=ResultType.K,
            units="PERCENT",
            places=1,
            auto_calc=False,
            reportable=True,
        ),
        # ---- META analysis (6 components) ----
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
            component_name="Oven",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="OVEN",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Thermometer",
            order_number=4,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="THERMOMETER",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Timer",
            order_number=5,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="TIMER",
            reportable=True,
        ),
        Component(
            analysis=META,
            component_name="Desiccator Reagent",
            order_number=6,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            sr_picker="AND_H2SO4, AND_P_5OXIDE",
            reportable=True,
        ),
    ]


# =====================================================================
# CalcVariable definitions (Sheet 6) — 4 total
# =====================================================================
def _build_calc_variables() -> list[CalcVariable]:
    return [
        CalcVariable(
            analysis=PRIMARY,
            component="% Loss on Drying",
            name="conTest",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Contract test?",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="% Loss on Drying",
            name="postWeight",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Dry Weight",
            return_value=CalcVariableReturnValue.A,
            scope=CalcVariableScope.CT,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="% Loss on Drying",
            name="preWeight",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Gross Weight",
            return_value=CalcVariableReturnValue.P,
            scope=CalcVariableScope.CT,
            function=CalcVariableFunction.AVE,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="% Loss on Drying",
            name="tareWeight",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Tare Weight",
            return_value=CalcVariableReturnValue.A,
            scope=CalcVariableScope.CT,
            function=CalcVariableFunction.ENTRY,
        ),
    ]


# =====================================================================
# Calculation definitions (Sheet 7) — 6 total
# =====================================================================
def _build_calculations() -> list[Calculation]:
    return [
        # ---- PRIMARY ----
        Calculation(
            analysis=PRIMARY,
            component="% Loss on Drying",
            source_code=(
                "Determine the % LOD if the constant weight criteria is met\n"
                'IF (conTest = "Yes") THEN\n'
                'retVal = PromptForNumber(, , , "Enter a result")\n'
                "RETURN retVal\n"
                "ENDIF\n"
                "\n"
                "PostCount = Len(postWeight)\n"
                "TareCount = Len(tareWeight)\n"
                "IF (IsEmpty(postWeight[PostCount]) OR "
                "IsEmpty(postWeight[PostCount - 1]) OR "
                "IsEmpty(preWeight) OR IsEmpty(tareWeight[TareCount])) THEN\n"
                'RETURN ""\n'
                "ENDIF\n"
                "\n"
                "'Calculate Weight difference for Constant Weight criteria\n"
                "Tare = tareWeight[TareCount]\n"
                "Post = postWeight[PostCount]\n"
                "IF (preWeight = Tare) THEN\n"
                'MsgBox("Divide by Zero Error")\n'
                'RETURN ""\n'
                "ENDIF\n"
                "\n"
                "currentDiffWeight = Abs((postWeight[PostCount] - "
                "postWeight[PostCount - 1]) / (preWeight - Tare))\n"
                "\n"
                "'Compared value of >= 0.00055 accounts for non-rounded currentDiffWeight\n"
                "IF (currentDiffWeight >= 0.00055) THEN\n"
                'MsgBox("Please replicate the applicable components '
                'and continue to constant weight.")\n'
                'RETURN ""\n'
                "ENDIF\n"
                "\n"
                "retval = (preWeight - Post) / (preWeight - Tare) * 100\n"
                "\n"
                "RETURN retval"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["conTest", "postWeight", "preWeight", "tareWeight"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Contract test?",
            source_code=(
                "GOSUB CALC_COMPONENTS_OPTIONAL\n"
                "RETURN returnAnswer"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        # ---- META ----
        Calculation(
            analysis=META,
            component="Desiccator Reagent",
            source_code=(
                "g_na = true\n"
                "' g_sr_list = \"'H2SO4','P_5OXIDE'\"\n"
                "GOSUB CALC_SR_PICKER"
            ),
            calculation_type=CalculationType.SR_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Oven",
            source_code=(
                "g_na = true\n"
                "' g_inst_group = \"OVEN\"\n"
                "GOSUB CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Thermometer",
            source_code=(
                "g_na = true\n"
                "' g_inst_group = \"THERM\"\n"
                "GOSUB CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        Calculation(
            analysis=META,
            component="Timer",
            source_code=(
                "g_na = true\n"
                "' g_inst_group = \"TIMER\"\n"
                "GOSUB CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
    ]
