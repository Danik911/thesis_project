"""Unit tests for L10 template base classes and registry."""

import pytest

from main.src.lims.provenance import ComponentSource
from main.src.lims.templates import TemplateLibrary
from main.src.lims.templates.base import TemplateComponent, TestTypeTemplate
from main.src.lims.test_type import TestType as LimsTestType


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