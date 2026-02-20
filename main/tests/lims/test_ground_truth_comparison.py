"""L16 — Ground truth XLSX structure comparison tests.

Links template output to real LabWare XLSX exports. Hardcoded expected values
derived from parsed XLSX ground truth files:
  - IDENTITY:  AND_ACS_DYE-LAB-2499.xlsx     (3 analyses, 25 components)
  - HPLC:      AND_BCMA_CEX-LAB-38176.xlsx    (4 analyses, 59 components)
  - LOD:       AND_USP_LOD_Config_w_Calcs.xlsx (2 analyses, 14 components)
  - TITRATION: FRE_KF_Config_w_Calcs.xlsx     (2 analyses, 11 components)

Structure-only comparison: counts and types, not field-by-field matching.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

from collections import Counter

import pytest

from main.src.lims.mda_schema import MDATemplate, ResultType
from main.src.lims.templates import TemplateLibrary
from main.src.lims.test_type import TestType


# =====================================================================
# Ground Truth Data — hardcoded from parsed XLSX
# =====================================================================

GROUND_TRUTH: dict = {
    TestType.IDENTITY: {
        "source_xlsx": "AND_ACS_DYE-LAB-2499.xlsx",
        "analysis_count": 3,
        "component_count": 25,
        "calc_variable_count": 6,
        "calculation_count": 11,
        "analysis_names": ["SITE_IDENTITY", "SITE_IDENTITY_CTL", "SITE_IDENTITY_META"],
        "per_analysis_components": {
            "SITE_IDENTITY": 9,
            "SITE_IDENTITY_CTL": 7,
            "SITE_IDENTITY_META": 9,
        },
        "analysis_types": {
            "SITE_IDENTITY": "ID",
            "SITE_IDENTITY_CTL": "QC_SAMPLES",
            "SITE_IDENTITY_META": "QC_SAMPLES",
        },
        "result_type_distribution": {
            ResultType.L: 8,
            ResultType.N: 4,
            ResultType.K: 11,
            ResultType.D: 1,
            ResultType.T: 1,
        },
    },
    TestType.HPLC: {
        "source_xlsx": "AND_BCMA_CEX-LAB-38176.xlsx",
        "analysis_count": 4,
        "component_count": 59,
        "calc_variable_count": 48,
        "calculation_count": 30,
        "analysis_names": ["SITE_HPLC", "SITE_HPLC_M", "SITE_HPLC_REF", "SITE_HPLC_SD"],
        "per_analysis_components": {
            "SITE_HPLC": 13,
            "SITE_HPLC_M": 7,
            "SITE_HPLC_REF": 21,
            "SITE_HPLC_SD": 18,
        },
        "analysis_types": {
            "SITE_HPLC": "HPLC",
            "SITE_HPLC_M": "QC_SAMPLES",
            "SITE_HPLC_REF": "QC_SAMPLES",
            "SITE_HPLC_SD": "QC_SAMPLES",
        },
        "result_type_distribution": {
            ResultType.K: 30,
            ResultType.N: 21,
            ResultType.L: 6,
            ResultType.D: 1,
            ResultType.T: 1,
        },
    },
    TestType.LOD: {
        "source_xlsx": "AND_USP_LOD_Config_w_Calcs.xlsx",
        "analysis_count": 2,
        "component_count": 14,
        "calc_variable_count": 4,
        "calculation_count": 6,
        "analysis_names": ["SITE_LOD", "SITE_LOD_META"],
        "per_analysis_components": {
            "SITE_LOD": 8,
            "SITE_LOD_META": 6,
        },
        "analysis_types": {
            "SITE_LOD": "RM",
            "SITE_LOD_META": "QC_SAMPLES",
        },
        "result_type_distribution": {
            ResultType.K: 6,
            ResultType.N: 6,
            ResultType.D: 1,
            ResultType.T: 1,
        },
    },
    TestType.TITRATION: {
        "source_xlsx": "FRE_KF_Config_w_Calcs.xlsx",
        "analysis_count": 2,
        "component_count": 11,
        "calc_variable_count": 6,
        "calculation_count": 7,
        "analysis_names": ["SITE_KF", "SITE_KF_META"],
        "per_analysis_components": {
            "SITE_KF": 7,
            "SITE_KF_META": 4,
        },
        "analysis_types": {
            "SITE_KF": "KF",
            "SITE_KF_META": "QC_SAMPLES",
        },
        "result_type_distribution": {
            ResultType.K: 7,
            ResultType.T: 3,
            ResultType.L: 1,
        },
    },
}

ALL_TEMPLATE_TYPES = [TestType.IDENTITY, TestType.HPLC, TestType.LOD, TestType.TITRATION]


# =====================================================================
# IDENTITY Ground Truth Tests
# =====================================================================


class TestIdentityGroundTruth:
    """Verify IDENTITY template matches AND_ACS_DYE-LAB-2499.xlsx ground truth."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(TestType.IDENTITY)
        return tpl.to_mda_template()

    def test_per_analysis_component_count(self, mda: MDATemplate) -> None:
        """Verify component breakdown: PRIMARY=9, CTL=7, META=9 (total 25)."""
        gt = GROUND_TRUTH[TestType.IDENTITY]["per_analysis_components"]
        actual = Counter(c.analysis for c in mda.components)
        for analysis_name, expected_count in gt.items():
            assert actual[analysis_name] == expected_count, (
                f"{analysis_name}: expected {expected_count}, got {actual[analysis_name]}"
            )

    def test_analysis_types_match(self, mda: MDATemplate) -> None:
        """Verify each analysis has correct AnalysisType from XLSX."""
        gt = GROUND_TRUTH[TestType.IDENTITY]["analysis_types"]
        for analysis in mda.analyses:
            expected_type = gt[analysis.name]
            assert analysis.analysis_type == expected_type, (
                f"{analysis.name}: expected {expected_type}, got {analysis.analysis_type}"
            )

    def test_result_type_distribution(self, mda: MDATemplate) -> None:
        """Verify L=8, N=4, K=11, D=1, T=1 match XLSX ground truth."""
        gt = GROUND_TRUTH[TestType.IDENTITY]["result_type_distribution"]
        actual = Counter(c.result_type for c in mda.components)
        for rt, expected_count in gt.items():
            assert actual[rt] == expected_count, (
                f"ResultType.{rt.value}: expected {expected_count}, got {actual[rt]}"
            )


# =====================================================================
# HPLC Ground Truth Tests
# =====================================================================


class TestHPLCGroundTruth:
    """Verify HPLC template matches AND_BCMA_CEX-LAB-38176.xlsx ground truth."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(TestType.HPLC)
        return tpl.to_mda_template()

    def test_per_analysis_component_count(self, mda: MDATemplate) -> None:
        """Verify component breakdown: PRIMARY=13, M=7, REF=21, SD=18 (total 59)."""
        gt = GROUND_TRUTH[TestType.HPLC]["per_analysis_components"]
        actual = Counter(c.analysis for c in mda.components)
        for analysis_name, expected_count in gt.items():
            assert actual[analysis_name] == expected_count, (
                f"{analysis_name}: expected {expected_count}, got {actual[analysis_name]}"
            )

    def test_analysis_types_match(self, mda: MDATemplate) -> None:
        """Verify HPLC primary + 3 QC_SAMPLES."""
        gt = GROUND_TRUTH[TestType.HPLC]["analysis_types"]
        for analysis in mda.analyses:
            expected_type = gt[analysis.name]
            assert analysis.analysis_type == expected_type, (
                f"{analysis.name}: expected {expected_type}, got {analysis.analysis_type}"
            )

    def test_result_type_distribution(self, mda: MDATemplate) -> None:
        """Verify K=30, N=21, L=6, D=1, T=1 match XLSX ground truth."""
        gt = GROUND_TRUTH[TestType.HPLC]["result_type_distribution"]
        actual = Counter(c.result_type for c in mda.components)
        for rt, expected_count in gt.items():
            assert actual[rt] == expected_count, (
                f"ResultType.{rt.value}: expected {expected_count}, got {actual[rt]}"
            )


# =====================================================================
# LOD Ground Truth Tests
# =====================================================================


class TestLODGroundTruth:
    """Verify LOD template matches AND_USP_LOD_Config_w_Calcs.xlsx ground truth."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(TestType.LOD)
        return tpl.to_mda_template()

    def test_per_analysis_component_count(self, mda: MDATemplate) -> None:
        """Verify component breakdown: PRIMARY=8, META=6 (total 14)."""
        gt = GROUND_TRUTH[TestType.LOD]["per_analysis_components"]
        actual = Counter(c.analysis for c in mda.components)
        for analysis_name, expected_count in gt.items():
            assert actual[analysis_name] == expected_count, (
                f"{analysis_name}: expected {expected_count}, got {actual[analysis_name]}"
            )

    def test_analysis_types_match(self, mda: MDATemplate) -> None:
        """Verify RM primary + QC_SAMPLES meta."""
        gt = GROUND_TRUTH[TestType.LOD]["analysis_types"]
        for analysis in mda.analyses:
            expected_type = gt[analysis.name]
            assert analysis.analysis_type == expected_type, (
                f"{analysis.name}: expected {expected_type}, got {analysis.analysis_type}"
            )

    def test_result_type_distribution(self, mda: MDATemplate) -> None:
        """Verify K=6, N=6, D=1, T=1 match XLSX ground truth."""
        gt = GROUND_TRUTH[TestType.LOD]["result_type_distribution"]
        actual = Counter(c.result_type for c in mda.components)
        for rt, expected_count in gt.items():
            assert actual[rt] == expected_count, (
                f"ResultType.{rt.value}: expected {expected_count}, got {actual[rt]}"
            )


# =====================================================================
# TITRATION Ground Truth Tests
# =====================================================================


class TestTitrationGroundTruth:
    """Verify TITRATION template matches FRE_KF_Config_w_Calcs.xlsx ground truth."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(TestType.TITRATION)
        return tpl.to_mda_template()

    def test_per_analysis_component_count(self, mda: MDATemplate) -> None:
        """Verify component breakdown: PRIMARY=7, META=4 (total 11)."""
        gt = GROUND_TRUTH[TestType.TITRATION]["per_analysis_components"]
        actual = Counter(c.analysis for c in mda.components)
        for analysis_name, expected_count in gt.items():
            assert actual[analysis_name] == expected_count, (
                f"{analysis_name}: expected {expected_count}, got {actual[analysis_name]}"
            )

    def test_analysis_types_match(self, mda: MDATemplate) -> None:
        """Verify KF primary + QC_SAMPLES meta."""
        gt = GROUND_TRUTH[TestType.TITRATION]["analysis_types"]
        for analysis in mda.analyses:
            expected_type = gt[analysis.name]
            assert analysis.analysis_type == expected_type, (
                f"{analysis.name}: expected {expected_type}, got {analysis.analysis_type}"
            )

    def test_result_type_distribution(self, mda: MDATemplate) -> None:
        """Verify K=7, T=3, L=1 match XLSX ground truth."""
        gt = GROUND_TRUTH[TestType.TITRATION]["result_type_distribution"]
        actual = Counter(c.result_type for c in mda.components)
        for rt, expected_count in gt.items():
            assert actual[rt] == expected_count, (
                f"ResultType.{rt.value}: expected {expected_count}, got {actual[rt]}"
            )


# =====================================================================
# Cross-Cutting Ground Truth Coverage Tests
# =====================================================================


class TestGroundTruthCoverage:
    """Cross-cutting validation: every registered type has ground truth data."""

    @pytest.mark.parametrize("test_type", ALL_TEMPLATE_TYPES)
    def test_all_types_have_ground_truth(self, test_type: TestType) -> None:
        """Every registered template type has ground truth data."""
        assert test_type in GROUND_TRUTH, f"No ground truth for {test_type.value}"

    @pytest.mark.parametrize("test_type", ALL_TEMPLATE_TYPES)
    def test_all_types_produce_valid_mda(self, test_type: TestType) -> None:
        """Every template produces a valid MDATemplate (Pydantic passes)."""
        tpl = TemplateLibrary.get_template_for_type(test_type)
        mda = tpl.to_mda_template()
        assert isinstance(mda, MDATemplate)

    @pytest.mark.parametrize("test_type", ALL_TEMPLATE_TYPES)
    def test_total_counts_match(self, test_type: TestType) -> None:
        """Analysis, component, calc_variable, and calculation totals match GT."""
        gt = GROUND_TRUTH[test_type]
        tpl = TemplateLibrary.get_template_for_type(test_type)
        mda = tpl.to_mda_template()
        assert len(mda.analyses) == gt["analysis_count"], (
            f"analyses: expected {gt['analysis_count']}, got {len(mda.analyses)}"
        )
        assert len(mda.components) == gt["component_count"], (
            f"components: expected {gt['component_count']}, got {len(mda.components)}"
        )
        assert len(mda.calc_variables) == gt["calc_variable_count"], (
            f"calc_variables: expected {gt['calc_variable_count']}, got {len(mda.calc_variables)}"
        )
        assert len(mda.calculations) == gt["calculation_count"], (
            f"calculations: expected {gt['calculation_count']}, got {len(mda.calculations)}"
        )

    @pytest.mark.parametrize("test_type", ALL_TEMPLATE_TYPES)
    def test_analysis_names_match(self, test_type: TestType) -> None:
        """Template analysis names match XLSX ground truth names."""
        gt = GROUND_TRUTH[test_type]
        tpl = TemplateLibrary.get_template_for_type(test_type)
        mda = tpl.to_mda_template()
        actual_names = sorted(a.name for a in mda.analyses)
        expected_names = sorted(gt["analysis_names"])
        assert actual_names == expected_names

    @pytest.mark.parametrize("test_type", ALL_TEMPLATE_TYPES)
    def test_no_orphan_components(self, test_type: TestType) -> None:
        """Every component references a valid analysis name."""
        tpl = TemplateLibrary.get_template_for_type(test_type)
        mda = tpl.to_mda_template()
        analysis_names = {a.name for a in mda.analyses}
        for comp in mda.components:
            assert comp.analysis in analysis_names, (
                f"Component '{comp.component_name}' references "
                f"unknown analysis '{comp.analysis}'"
            )
