"""Titration (Karl Fischer) test template skeleton.

Ground truth: FRE_KF_SINGLE / FRE_KF_META from FRE_KF_Config_w_Calcs.xlsx.
2 analyses, 11 components, 6 calc_variables, 7 calculations.

Karl Fischer water content determination per Ph. Eur. 2.5.12 / USP <921>.

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
PRIMARY = "SITE_KF"
META = "SITE_KF_META"


@TemplateLibrary.register(TestType.TITRATION)
class TitrationTemplate(TestTypeTemplate):
    """Karl Fischer titration template — 2 analyses, 11 components."""

    test_type = TestType.TITRATION

    def get_components(self) -> list[TemplateComponent]:
        return [
            # Fixed: analysis types
            TemplateComponent(
                sheet="analyses", field_path="analyses[0].analysis_type",
                value="KF", is_variable=False,
            ),
            TemplateComponent(
                sheet="analyses", field_path="analyses[1].analysis_type",
                value="QC_SAMPLES", is_variable=False,
            ),
            # Fixed: result types for primary components
            TemplateComponent(
                sheet="components", field_path="components[0].result_type",
                value="K", is_variable=False,
            ),
            TemplateComponent(
                sheet="components", field_path="components[3].result_type",
                value="K", is_variable=False,
            ),
            # Variable: water content limits from PDF
            TemplateComponent(
                sheet="components", field_path="components[3].maximum",
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
            group_name="FREIBURG",
            reported_name="Karl Fischer Single",
            common_name="WATER",
            analysis_type=AnalysisType.KF,
            description=(
                "Ph. Eur. 2.5.12, Water: semi-micro determination; "
                "USP <921>, water determination"
            ),
        ),
        Analysis(
            name=META,
            version=1,
            group_name="FREIBURG",
            reported_name="KF Meta",
            common_name="QC_SAMPLES",
            analysis_type=AnalysisType.QC_SAMPLES,
            description=(
                "Ph. Eur. 2.5.12, Water: semi-micro determination; "
                "USP <921>, water determination - Meta Data"
            ),
        ),
    ]


# =====================================================================
# Component definitions (Sheet 2) — 11 total
# =====================================================================
def _build_components() -> list[Component]:
    return [
        # ---- PRIMARY analysis: FRE_KF_SINGLE (7 components) ----
        Component(
            analysis=PRIMARY,
            component_name="Contract Testing/Balance interfaced",
            order_number=1,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Method Version",
            order_number=2,
            result_type=ResultType.T,
            units="NONE",
            auto_calc=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Raw data available",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            optional=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Water RESULT",
            order_number=4,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=False,
            reportable=True,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Water (JP) RESULT - INHOUSE",
            order_number=5,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            optional=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Water (JP) RESULT - CONTRACT",
            order_number=6,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=False,
            optional=True,
            reportable=False,
        ),
        Component(
            analysis=PRIMARY,
            component_name="Water (JP) RESULT",
            order_number=7,
            result_type=ResultType.K,
            units="PERCENT",
            auto_calc=True,
            optional=True,
            reportable=False,
        ),
        # ---- META analysis: FRE_KF_META (4 components) ----
        Component(
            analysis=META,
            component_name="Data Sheet Reference",
            order_number=1,
            result_type=ResultType.T,
            units="NONE",
            auto_calc=True,
            reportable=False,
        ),
        Component(
            analysis=META,
            component_name="Method Version",
            order_number=2,
            result_type=ResultType.T,
            units="NONE",
            auto_calc=True,
            reportable=False,
        ),
        Component(
            analysis=META,
            component_name="Karl Fischer Titrator ID",
            order_number=3,
            result_type=ResultType.K,
            units="NONE",
            auto_calc=False,
            instrument_group="KF",
            reportable=False,
        ),
        Component(
            analysis=META,
            component_name="Raw data see",
            order_number=5,
            result_type=ResultType.L,
            units="NONE",
            auto_calc=True,
            list_key="FRE_RAW_DATA_SEE",
            reportable=False,
        ),
    ]


# =====================================================================
# CalcVariable definitions (Sheet 6) — 6 total
# =====================================================================
def _build_calc_variables() -> list[CalcVariable]:
    return [
        # Water (JP) RESULT variables
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT",
            name="contract",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Contract Testing/Balance interfaced",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT",
            name="contractRslt",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Water (JP) RESULT - CONTRACT",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT",
            name="inHouseRslt",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Water (JP) RESULT - INHOUSE",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # Water (JP) RESULT - CONTRACT variable
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT - CONTRACT",
            name="Contract",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Contract Testing/Balance interfaced",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        # Water (JP) RESULT - INHOUSE variables
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT - INHOUSE",
            name="Contract",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Contract Testing/Balance interfaced",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
        CalcVariable(
            analysis=PRIMARY,
            component="Water (JP) RESULT - INHOUSE",
            name="resWater",
            reference_type=CalcVariableReferenceType.C,
            reference_analysis=PRIMARY,
            attribute_1="Water RESULT",
            return_value=CalcVariableReturnValue.S,
            scope=CalcVariableScope.CR,
            function=CalcVariableFunction.ENTRY,
        ),
    ]


# =====================================================================
# Calculation definitions (Sheet 7) — 7 total
# =====================================================================
def _build_calculations() -> list[Calculation]:
    return [
        # ---- META ----
        Calculation(
            analysis=META,
            component="Karl Fischer Titrator ID",
            source_code=(
                "/*Calls the Instrument Picker subroutine\n"
                "GoSub CALC_INST_PICKER"
            ),
            calculation_type=CalculationType.INST_PICKER,
        ),
        # ---- PRIMARY ----
        Calculation(
            analysis=PRIMARY,
            component="Contract Testing/Balance interfaced",
            source_code=(
                "/*Calls the Contract Test subroutine\n"
                "' Turns components optional when test is performed by contract laboratory\n"
                "' and only final results need to be recorded for the test.*/\n"
                "\n"
                'returnAnswer = ""\n'
                'strtitle = "Contract Testing/Balance interfaced?"\n'
                "GoSub CALC_COMPONENTS_OPTIONAL\n"
                "RETURN returnAnswer"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        Calculation(
            analysis=PRIMARY,
            component="Raw data available",
            source_code=(
                "Prompts for Date and modifies to site-preferred date format\n"
                "\n"
                'selectedDate = PromptForDate("", )\n'
                "selectedDate = STR(selectedDate)\n"
                'selectedDate = StringReplace(selectedDate, " 12:00:00 AM", "")\n'
                'status = ArrayFromCSVString(selectedDate, "-", , "F", "dateArr")\n'
                "\n"
                'finalDate = dateArr[2] & "-" & dateArr[1] & "-" & dateArr[3]\n'
                "\n"
                "RETURN finalDate"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        Calculation(
            analysis=PRIMARY,
            component="Water RESULT",
            source_code=(
                "' Call CALC_LIST_ALLOW_USER_ENTRY subroutine\n"
                'listName = "FRE_LOE_0_05"\n'
                "GOSUB CALC_LIST_ALLOW_USER_ENTRY\n"
                "RETURN rsltFinal"
            ),
            calculation_type=CalculationType.GOSUB,
        ),
        Calculation(
            analysis=PRIMARY,
            component="Water (JP) RESULT",
            source_code=(
                "If contract testing yes, pull contractRslt, else pull inHouseRslt\n"
                "\n"
                'IF (contract = "Yes") THEN\n'
                "    rsltFinal = contractRslt\n"
                'ELSEIF (contract = "No") THEN\n'
                "    rsltFinal = inHouseRslt\n"
                "ELSE\n"
                '    rsltFinal = ""\n'
                "ENDIF\n"
                "\n"
                "RETURN rsltFinal"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["contract", "contractRslt", "inHouseRslt"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Water (JP) RESULT - CONTRACT",
            source_code=(
                'IF (Contract = "Yes") THEN\n'
                "    ' Calls subroutine for choice of list selection or manual numeric result entry\n"
                '    listName = "FRE_LOE_CONFORMS"\n'
                "    GoSub CALC_LIST_ALLOW_USER_ENTRY\n"
                "    RETURN rsltFinal\n"
                "ELSE\n"
                '    RETURN "N/A"\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Contract"],
        ),
        Calculation(
            analysis=PRIMARY,
            component="Water (JP) RESULT - INHOUSE",
            source_code=(
                'IF (Contract = "No") THEN\n'
                "    ' In-house calculation path\n"
                "    rsltFinal = resWater\n"
                "    RETURN rsltFinal\n"
                "ELSE\n"
                '    RETURN "N/A"\n'
                "ENDIF"
            ),
            calculation_type=CalculationType.CONDITIONAL,
            variables_used=["Contract", "resWater"],
        ),
    ]
