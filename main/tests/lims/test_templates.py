"""Unit tests for L10 template base classes and L11 template implementations."""

import pytest

from main.src.lims.mda_schema import MDATemplate
from main.src.lims.provenance import ComponentSource
from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType as LimsTestType


# =====================================================================
# L10 — Base class tests (preserved from original)
# =====================================================================


class _DummyTemplate(TestTypeTemplate):
    test_type = LimsTestType.HPLC

    def get_components(self) -> list[TemplateComponent]:
        return [
            TemplateComponent(
                sheet="components",
                field_path="components[0].component_name",
                value="ASSAY",
                is_variable=False,
            ),
            TemplateComponent(
                sheet="components",
                field_path="components[1].target_value",
                value=None,
                is_variable=True,
            ),
        ]


def test_template_component_defaults_source_to_template() -> None:
    component = TemplateComponent(
        sheet="analyses",
        field_path="analyses[0].name",
        value="AND_ACS_DYE",
    )
    assert component.source == ComponentSource.TEMPLATE
    assert component.is_variable is False


def test_test_type_template_variable_and_fixed_fields() -> None:
    template = _DummyTemplate()
    assert template.get_fixed_fields() == ["components[0].component_name"]
    assert template.get_variable_fields() == ["components[1].target_value"]


def test_test_type_template_requires_get_components() -> None:
    template = TestTypeTemplate()
    with pytest.raises(NotImplementedError, match="must implement get_components"):
        template.get_components()


def test_test_type_template_requires_to_mda_template() -> None:
    template = _DummyTemplate()
    with pytest.raises(NotImplementedError, match="must implement to_mda_template"):
        template.to_mda_template()


def test_template_library_register_and_get_template() -> None:
    original_registry = TemplateLibrary._registry.copy()
    try:
        TemplateLibrary._registry.clear()

        @TemplateLibrary.register(LimsTestType.HPLC)
        class RegisteredTemplate(_DummyTemplate):
            pass

        instance = TemplateLibrary.get_template_for_type(LimsTestType.HPLC)
        assert isinstance(instance, RegisteredTemplate)
        assert TemplateLibrary.available_types() == [LimsTestType.HPLC]
    finally:
        TemplateLibrary._registry = original_registry


def test_template_library_unknown_type_raises() -> None:
    original_registry = TemplateLibrary._registry.copy()
    try:
        TemplateLibrary._registry.clear()
        with pytest.raises(ValueError, match="No template registered"):
            TemplateLibrary.get_template_for_type(LimsTestType.LOD)
    finally:
        TemplateLibrary._registry = original_registry


# =====================================================================
# L11 — All 4 templates registered
# =====================================================================


class TestTemplateRegistration:
    """Verify all 4 template types are registered in TemplateLibrary."""

    def test_all_four_types_registered(self) -> None:
        available = TemplateLibrary.available_types()
        for tt in [LimsTestType.HPLC, LimsTestType.IDENTITY, LimsTestType.LOD, LimsTestType.TITRATION]:
            assert tt in available, f"{tt.value} not registered"

    def test_hplc_returns_hplc_template(self) -> None:
        from main.src.lims.templates.hplc import HPLCTemplate
        instance = TemplateLibrary.get_template_for_type(LimsTestType.HPLC)
        assert isinstance(instance, HPLCTemplate)

    def test_identity_returns_identity_template(self) -> None:
        from main.src.lims.templates.identity import IdentityTemplate
        instance = TemplateLibrary.get_template_for_type(LimsTestType.IDENTITY)
        assert isinstance(instance, IdentityTemplate)

    def test_lod_returns_lod_template(self) -> None:
        from main.src.lims.templates.lod import LODTemplate
        instance = TemplateLibrary.get_template_for_type(LimsTestType.LOD)
        assert isinstance(instance, LODTemplate)

    def test_titration_returns_titration_template(self) -> None:
        from main.src.lims.templates.titration import TitrationTemplate
        instance = TemplateLibrary.get_template_for_type(LimsTestType.TITRATION)
        assert isinstance(instance, TitrationTemplate)


# =====================================================================
# L11 — Identity template (AND_ACS_DYE ground truth)
# =====================================================================


class TestIdentityTemplate:
    """Identity template: 3 analyses, 25 components, 6 calc_vars, 11 calcs."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.IDENTITY)
        return tpl.to_mda_template()

    def test_valid_mda(self, mda: MDATemplate) -> None:
        """Pydantic validation passes — cross-sheet integrity OK."""
        assert isinstance(mda, MDATemplate)

    def test_analysis_count(self, mda: MDATemplate) -> None:
        assert len(mda.analyses) == 3

    def test_analysis_names(self, mda: MDATemplate) -> None:
        names = {a.name for a in mda.analyses}
        assert names == {"SITE_IDENTITY", "SITE_IDENTITY_CTL", "SITE_IDENTITY_META"}

    def test_component_count(self, mda: MDATemplate) -> None:
        assert len(mda.components) == 25

    def test_calc_variable_count(self, mda: MDATemplate) -> None:
        assert len(mda.calc_variables) == 6

    def test_calculation_count(self, mda: MDATemplate) -> None:
        assert len(mda.calculations) == 11

    def test_primary_analysis_type(self, mda: MDATemplate) -> None:
        primary = next(a for a in mda.analyses if a.name == "SITE_IDENTITY")
        assert primary.analysis_type == "ID"

    def test_ctl_meta_are_qc_samples(self, mda: MDATemplate) -> None:
        for a in mda.analyses:
            if a.name.endswith(("_CTL", "_META")):
                assert a.analysis_type == "QC_SAMPLES"

    def test_variable_vs_fixed_fields(self) -> None:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.IDENTITY)
        variable = tpl.get_variable_fields()
        fixed = tpl.get_fixed_fields()
        assert len(variable) > 0
        assert len(fixed) > 0
        # No overlap
        assert not set(variable) & set(fixed)


# =====================================================================
# L11 — LOD template (AND_LOD_CW_U ground truth)
# =====================================================================


class TestLODTemplate:
    """LOD template: 2 analyses, 14 components, 4 calc_vars, 6 calcs."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.LOD)
        return tpl.to_mda_template()

    def test_valid_mda(self, mda: MDATemplate) -> None:
        assert isinstance(mda, MDATemplate)

    def test_analysis_count(self, mda: MDATemplate) -> None:
        assert len(mda.analyses) == 2

    def test_analysis_names(self, mda: MDATemplate) -> None:
        names = {a.name for a in mda.analyses}
        assert names == {"SITE_LOD", "SITE_LOD_META"}

    def test_component_count(self, mda: MDATemplate) -> None:
        assert len(mda.components) == 14

    def test_calc_variable_count(self, mda: MDATemplate) -> None:
        assert len(mda.calc_variables) == 4

    def test_calculation_count(self, mda: MDATemplate) -> None:
        assert len(mda.calculations) == 6

    def test_primary_analysis_type(self, mda: MDATemplate) -> None:
        primary = next(a for a in mda.analyses if a.name == "SITE_LOD")
        assert primary.analysis_type == "RM"

    def test_variable_vs_fixed_fields(self) -> None:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.LOD)
        variable = tpl.get_variable_fields()
        fixed = tpl.get_fixed_fields()
        assert len(variable) > 0
        assert len(fixed) > 0
        assert not set(variable) & set(fixed)


# =====================================================================
# L11 — HPLC template (AND_BCMA_CEX ground truth)
# =====================================================================


class TestHPLCTemplate:
    """HPLC template: 4 analyses, 59 components, 48 calc_vars, 30 calcs."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.HPLC)
        return tpl.to_mda_template()

    def test_valid_mda(self, mda: MDATemplate) -> None:
        assert isinstance(mda, MDATemplate)

    def test_analysis_count(self, mda: MDATemplate) -> None:
        assert len(mda.analyses) == 4

    def test_analysis_names(self, mda: MDATemplate) -> None:
        names = {a.name for a in mda.analyses}
        assert names == {"SITE_HPLC", "SITE_HPLC_M", "SITE_HPLC_REF", "SITE_HPLC_SD"}

    def test_component_count(self, mda: MDATemplate) -> None:
        assert len(mda.components) == 59

    def test_calc_variable_count(self, mda: MDATemplate) -> None:
        assert len(mda.calc_variables) == 48

    def test_calculation_count(self, mda: MDATemplate) -> None:
        assert len(mda.calculations) == 30

    def test_primary_analysis_type(self, mda: MDATemplate) -> None:
        primary = next(a for a in mda.analyses if a.name == "SITE_HPLC")
        assert primary.analysis_type == "HPLC"

    def test_has_40_plus_components(self, mda: MDATemplate) -> None:
        """Gate criteria: HPLC template has 40+ template components."""
        assert len(mda.components) >= 40

    def test_variable_vs_fixed_fields(self) -> None:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.HPLC)
        variable = tpl.get_variable_fields()
        fixed = tpl.get_fixed_fields()
        assert len(variable) > 0
        assert len(fixed) > 0
        assert not set(variable) & set(fixed)


# =====================================================================
# L11 — Titration template (FRE_KF ground truth)
# =====================================================================


class TestTitrationTemplate:
    """Titration template: 2 analyses, 11 components, 6 calc_vars, 7 calcs."""

    @pytest.fixture
    def mda(self) -> MDATemplate:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.TITRATION)
        return tpl.to_mda_template()

    def test_valid_mda(self, mda: MDATemplate) -> None:
        assert isinstance(mda, MDATemplate)

    def test_analysis_count(self, mda: MDATemplate) -> None:
        assert len(mda.analyses) == 2

    def test_analysis_names(self, mda: MDATemplate) -> None:
        names = {a.name for a in mda.analyses}
        assert names == {"SITE_KF", "SITE_KF_META"}

    def test_component_count(self, mda: MDATemplate) -> None:
        assert len(mda.components) == 11

    def test_calc_variable_count(self, mda: MDATemplate) -> None:
        assert len(mda.calc_variables) == 6

    def test_calculation_count(self, mda: MDATemplate) -> None:
        assert len(mda.calculations) == 7

    def test_primary_analysis_type(self, mda: MDATemplate) -> None:
        primary = next(a for a in mda.analyses if a.name == "SITE_KF")
        assert primary.analysis_type == "KF"

    def test_variable_vs_fixed_fields(self) -> None:
        tpl = TemplateLibrary.get_template_for_type(LimsTestType.TITRATION)
        variable = tpl.get_variable_fields()
        fixed = tpl.get_fixed_fields()
        assert len(variable) > 0
        assert len(fixed) > 0
        assert not set(variable) & set(fixed)
