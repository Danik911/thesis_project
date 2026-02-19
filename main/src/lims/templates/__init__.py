"""Template library registry for test-type templates."""

from __future__ import annotations

from main.src.lims.templates.base import TestTypeTemplate
from main.src.lims.test_type import TestType


class TemplateLibrary:
    """Registry for test-type-specific MDA templates."""

    _registry: dict[TestType, type[TestTypeTemplate]] = {}

    @classmethod
    def register(cls, test_type: TestType):
        def decorator(template_cls: type[TestTypeTemplate]):
            cls._registry[test_type] = template_cls
            return template_cls

        return decorator

    @classmethod
    def get_template_for_type(cls, test_type: TestType) -> TestTypeTemplate:
        if test_type not in cls._registry:
            raise ValueError(
                f"No template registered for test type '{test_type.value}'. "
                f"Available: {sorted(t.value for t in cls._registry)}"
            )
        return cls._registry[test_type]()

    @classmethod
    def available_types(cls) -> list[TestType]:
        return sorted(cls._registry.keys(), key=lambda test_type: test_type.value)
