"""Base classes for test-type-specific MDA template skeletons.

Templates provide the ~46% of MDA components that come from LIMS
conventions and standards, not from the PDF.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from main.src.lims.mda_schema import MDATemplate
from main.src.lims.provenance import ComponentSource
from main.src.lims.test_type import TestType


@dataclass
class TemplateComponent:
    """A single pre-defined component in a template skeleton."""

    sheet: str
    field_path: str
    value: Any
    source: ComponentSource = ComponentSource.TEMPLATE
    is_variable: bool = False


class TestTypeTemplate:
    """Base class for test-type-specific MDA templates.

    Subclasses (HPLCTemplate, LODTemplate, etc.) define the skeleton
    components. Variable fields (is_variable=True) are placeholders
    to be filled by PDF extraction.
    """

    test_type: TestType = TestType.OTHER

    def get_components(self) -> list[TemplateComponent]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_components()"
        )

    def get_variable_fields(self) -> list[str]:
        """Return field paths that need PDF extraction."""
        return [component.field_path for component in self.get_components() if component.is_variable]

    def get_fixed_fields(self) -> list[str]:
        """Return field paths from the template skeleton."""
        return [component.field_path for component in self.get_components() if not component.is_variable]

    def to_mda_template(self) -> MDATemplate:
        """Build an MDATemplate from just the template skeleton.
        Variable fields will have placeholder/default values."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_mda_template()"
        )
