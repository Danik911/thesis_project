"""Tests for the MDA template merger (two-layer pipeline).

Validates merge algorithm: template base -> extraction overlay -> augmentation
-> SME_REQUIRED gap marking -> cross-sheet validation.

GAMP-5 Category 5: Custom pharmaceutical software component.
"""

import pytest

from main.src.lims.merger import (
    MergeConflict,
    MergeResult,
    _apply_suggestion_to_dict,
    _match_analysis,
    _match_component,
    _normalize_for_match,
    merge_layers,
)
from main.src.lims.provenance import ComponentSource
from main.src.lims.test_type import TestType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def identity_template():
    """Build an IdentityTemplate MDATemplate."""
    from main.src.lims.templates.identity import IdentityTemplate

    template = IdentityTemplate()
    return template.to_mda_template()


@pytest.fixture
def identity_template_extracted_data():
    """Mock extraction data that matches identity template structure."""
    return {
        "analyses": [
            {
                "name": "SITE_IDENTITY",
                "analysis_type": "ID",
                "description": "Extracted description from PDF",
            },
        ],
        "components": [
            {
                "analysis": "SITE_IDENTITY",
                "component_name": "Weight of Sponge(s)",
                "minimum": 50.0,
                "maximum": 200.0,
            },
        ],
        "calc_variables": [],
        "calculations": [],
    }


@pytest.fixture
def sample_augmentation():
    """Mock augmentation suggestions."""
    return {
        "suggestions": [
            {
                "field_path": "analyses[2].description",
                "suggested_value": "Meta data analysis from standards",
                "confidence": 0.7,
                "source": "ICH Q6A standards",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------


class TestNormalization:
    def test_normalize_basic(self):
        assert _normalize_for_match("Hello_World") == "hello world"

    def test_normalize_hyphens(self):
        assert _normalize_for_match("Dye-Binding") == "dye binding"

    def test_normalize_extra_spaces(self):
        assert _normalize_for_match("  multiple   spaces  ") == "multiple spaces"

    def test_normalize_mixed(self):
        assert _normalize_for_match("ACS_Dye-Binding  Test") == "acs dye binding test"


# ---------------------------------------------------------------------------
# Matching tests
# ---------------------------------------------------------------------------


class TestMatching:
    def test_match_analysis_by_name(self):
        extracted = {"name": "SITE_IDENTITY", "analysis_type": "ID"}
        template = [
            {"name": "SITE_IDENTITY", "analysis_type": "ID"},
            {"name": "SITE_IDENTITY_CTL", "analysis_type": "QC_SAMPLES"},
        ]
        assert _match_analysis(extracted, template) == 0

    def test_match_analysis_by_type(self):
        extracted = {"name": "UNKNOWN_NAME", "analysis_type": "QC_SAMPLES"}
        template = [
            {"name": "SITE_IDENTITY", "analysis_type": "ID"},
            {"name": "SITE_IDENTITY_CTL", "analysis_type": "QC_SAMPLES"},
        ]
        assert _match_analysis(extracted, template) == 1

    def test_match_analysis_no_match(self):
        extracted = {"name": "TOTALLY_DIFFERENT", "analysis_type": "UNKNOWN"}
        template = [
            {"name": "SITE_IDENTITY", "analysis_type": "ID"},
        ]
        assert _match_analysis(extracted, template) is None

    def test_match_component_by_tuple(self):
        extracted = {
            "analysis": "SITE_IDENTITY",
            "component_name": "Weight of Sponge(s)",
        }
        template = [
            {
                "analysis": "SITE_IDENTITY",
                "component_name": "Package: Double layered and sealed?",
            },
            {
                "analysis": "SITE_IDENTITY",
                "component_name": "Weight of Sponge(s)",
            },
        ]
        assert _match_component(extracted, template) == 1

    def test_match_component_no_match(self):
        extracted = {
            "analysis": "SITE_IDENTITY",
            "component_name": "NONEXISTENT_COMPONENT",
        }
        template = [
            {
                "analysis": "SITE_IDENTITY",
                "component_name": "Weight of Sponge(s)",
            },
        ]
        assert _match_component(extracted, template) is None


# ---------------------------------------------------------------------------
# Merge tests
# ---------------------------------------------------------------------------


class TestMergeTemplateOnly:
    """Template MDA with no extraction -> all TEMPLATE provenance."""

    def test_merge_template_only(self, identity_template):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
            augmented_data=None,
            test_type=TestType.IDENTITY,
        )

        assert isinstance(result, MergeResult)
        assert result.mda_template is not None
        assert len(result.conflicts) == 0
        assert "TEMPLATE" in result.stats
        assert result.stats["TEMPLATE"] > 0

    def test_template_provenance_only(self, identity_template):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
        )

        provenance = result.provenance
        assert "fields" in provenance
        # Every populated field from template should have TEMPLATE provenance
        for path, field_prov in provenance["fields"].items():
            assert field_prov["source"] in ("TEMPLATE", "SME_REQUIRED")


class TestMergeExtractedOverrides:
    """Extracted values replace variable fields, tagged EXTRACTED."""

    def test_extracted_overrides_variable_fields(
        self, identity_template, identity_template_extracted_data
    ):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=identity_template_extracted_data,
            test_type=TestType.IDENTITY,
        )

        # The description should be overwritten by extraction
        analysis_0 = result.mda_template["analyses"][0]
        assert analysis_0["description"] == "Extracted description from PDF"

        # Check provenance for the overridden field
        prov_fields = result.provenance["fields"]
        assert prov_fields["analyses[0].description"]["source"] == "EXTRACTED"

    def test_extracted_stats_present(
        self, identity_template, identity_template_extracted_data
    ):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=identity_template_extracted_data,
        )
        assert "EXTRACTED" in result.stats
        assert result.stats["EXTRACTED"] > 0


class TestMergeConflicts:
    """Template result_type=L, extraction=N -> MergeConflict created."""

    def test_conflict_on_fixed_field(self, identity_template):
        """Extraction disagrees with template on result_type."""
        extracted_data = {
            "components": [
                {
                    "analysis": "SITE_IDENTITY",
                    "component_name": "Package: Double layered and sealed?",
                    "result_type": "N",  # Template says "L"
                    "units": "GRAMS",  # Template says "NONE"
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        assert len(result.conflicts) > 0
        conflict_paths = [c.field_path for c in result.conflicts]
        # result_type and units are in conflict_fields for components
        assert any("result_type" in p for p in conflict_paths)

    def test_conflict_records_both_values(self, identity_template):
        extracted_data = {
            "components": [
                {
                    "analysis": "SITE_IDENTITY",
                    "component_name": "Package: Double layered and sealed?",
                    "result_type": "N",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
        )

        conflict = next(
            c for c in result.conflicts if "result_type" in c.field_path
        )
        assert conflict.template_value == "L"
        assert conflict.extracted_value == "N"


class TestMergeAugmentation:
    """Augmented data fills null fields -> tagged INFERRED."""

    def test_augmented_fills_gaps(
        self, identity_template, sample_augmentation
    ):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
            augmented_data=sample_augmentation,
            test_type=TestType.IDENTITY,
        )

        # Check that augmentation was applied
        analysis_2 = result.mda_template["analyses"][2]
        assert analysis_2["description"] == "Meta data analysis from standards"

        # Provenance should be INFERRED
        prov_fields = result.provenance["fields"]
        assert prov_fields["analyses[2].description"]["source"] == "INFERRED"

    def test_augmented_does_not_override_extracted(self, identity_template):
        """Extracted values take priority over augmented."""
        extracted_data = {
            "analyses": [
                {
                    "name": "SITE_IDENTITY_META",
                    "description": "Extracted meta description",
                },
            ],
        }
        augmented_data = {
            "suggestions": [
                {
                    "field_path": "analyses[2].description",
                    "suggested_value": "Should NOT appear",
                    "confidence": 0.9,
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            augmented_data=augmented_data,
        )

        # Extraction wins over augmentation
        analysis_2 = result.mda_template["analyses"][2]
        assert analysis_2["description"] == "Extracted meta description"


class TestSMERequired:
    """Remaining nulls -> SME_REQUIRED provenance."""

    def test_sme_required_for_unfilled(self, identity_template):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
        )

        prov_fields = result.provenance["fields"]
        sme_required_paths = [
            path
            for path, prov in prov_fields.items()
            if prov["source"] == "SME_REQUIRED"
        ]
        # A complete template skeleton has no true SME_REQUIRED gaps —
        # Optional[...] fields (list_key, units, etc.) that are None by
        # design are correctly excluded from SME_REQUIRED marking.
        assert len(sme_required_paths) == 0

    def test_every_field_has_provenance(self, identity_template):
        """After merge, every non-null field in analyses/components has provenance."""
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
        )

        prov_fields = result.provenance["fields"]

        for sheet_key in ("analyses", "components", "calc_variables", "calculations"):
            items = result.mda_template.get(sheet_key, [])
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                for key, value in item.items():
                    if value is not None and value != "" and value != []:
                        path = f"{sheet_key}[{i}].{key}"
                        assert path in prov_fields, (
                            f"Non-null field {path}={value!r} has no provenance entry"
                        )


class TestMergeStats:
    """Stats dict matches actual provenance counts."""

    def test_merge_stats_correct(self, identity_template):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data={},
        )

        # Recount from provenance
        actual_counts: dict[str, int] = {}
        for prov in result.provenance["fields"].values():
            source = prov["source"]
            actual_counts[source] = actual_counts.get(source, 0) + 1

        assert result.stats == actual_counts


class TestMergeIdentityE2E:
    """IdentityTemplate + mock extraction -> valid MergeResult."""

    def test_identity_template_e2e(
        self, identity_template, identity_template_extracted_data
    ):
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=identity_template_extracted_data,
            augmented_data=None,
            test_type=TestType.IDENTITY,
        )

        assert result.mda_template is not None
        assert "analyses" in result.mda_template
        assert "components" in result.mda_template
        assert "calc_variables" in result.mda_template
        assert "calculations" in result.mda_template

        # Should have 3 analyses (template has 3)
        assert len(result.mda_template["analyses"]) == 3
        # Should have at least 25 components (template has 25)
        assert len(result.mda_template["components"]) >= 25

        # Provenance should be populated
        assert len(result.provenance["fields"]) > 0

        # Stats should have at least TEMPLATE entries
        assert result.stats.get("TEMPLATE", 0) > 0


class TestApplySuggestionErrors:
    """_apply_suggestion_to_dict raises ValueError on unresolvable paths."""

    def test_bad_key_raises(self):
        base = {"analyses": [{"name": "A"}]}
        with pytest.raises(ValueError, match="key 'nonexistent' not found"):
            _apply_suggestion_to_dict(base, "nonexistent[0].name", "value")

    def test_index_out_of_range_raises(self):
        base = {"analyses": [{"name": "A"}]}
        with pytest.raises(ValueError, match="index 99 out of range"):
            _apply_suggestion_to_dict(base, "analyses[99].name", "value")

    def test_missing_segment_raises(self):
        base = {"analyses": [{"name": "A", "nested": {"x": 1}}]}
        with pytest.raises(ValueError, match="segment 'missing' not found"):
            _apply_suggestion_to_dict(base, "analyses[0].missing.field", "value")
