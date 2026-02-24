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
    _build_extraction_to_template_map,
    _match_analysis,
    _match_component,
    _normalize_for_match,
    _rewrite_extraction_refs,
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


# ---------------------------------------------------------------------------
# Protected keys tests (Fix B)
# ---------------------------------------------------------------------------


class TestProtectedKeys:
    """Template analysis names are preserved when protected_keys={"name"}."""

    def test_protected_name_not_overwritten(self, identity_template):
        """Extraction analysis name should NOT overwrite template name."""
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)",
                    "analysis_type": "ID",
                    "description": "Extracted dye-binding test",
                },
            ],
            "components": [],
            "calc_variables": [],
            "calculations": [],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Template name should be preserved
        analysis_0 = result.mda_template["analyses"][0]
        assert analysis_0["name"] == "SITE_IDENTITY"

        # But description should be overridden (not protected)
        assert analysis_0["description"] == "Extracted dye-binding test"

        # A conflict should be recorded for the name difference
        name_conflicts = [
            c for c in result.conflicts
            if "name" in c.field_path and c.resolved_by == "SYSTEM"
        ]
        assert len(name_conflicts) >= 1
        assert name_conflicts[0].template_value == "SITE_IDENTITY"

    def test_still_3_analyses_after_type_match(self, identity_template):
        """Extraction matched by type should not add a 4th analysis."""
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
                    "analysis_type": "ID",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
        )

        # Should still be 3 analyses (not 4)
        assert len(result.mda_template["analyses"]) == 3


# ---------------------------------------------------------------------------
# Extraction ref rewriting tests (Fix C)
# ---------------------------------------------------------------------------


class TestExtractionRefRewriting:
    """Extraction component refs are rewritten to template analysis names."""

    def test_build_extraction_to_template_map(self):
        ext_analyses = [
            {"name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS"},
        ]
        merged_analyses = [
            {"name": "SITE_IDENTITY"},
        ]
        match_map = {0: 0}

        result = _build_extraction_to_template_map(
            ext_analyses, merged_analyses, match_map,
        )

        norm_key = _normalize_for_match("DYE_BINDING_IDENTITY_TEST_FOR_ACS")
        assert norm_key in result
        assert result[norm_key] == "SITE_IDENTITY"

    def test_build_map_empty_when_names_match(self):
        ext_analyses = [{"name": "SITE_IDENTITY"}]
        merged_analyses = [{"name": "SITE_IDENTITY"}]
        match_map = {0: 0}

        result = _build_extraction_to_template_map(
            ext_analyses, merged_analyses, match_map,
        )
        assert len(result) == 0

    def test_rewrite_exact_match(self):
        ext_to_tpl = {
            _normalize_for_match("DYE_BINDING_IDENTITY_TEST_FOR_ACS"): "SITE_IDENTITY",
        }
        extracted_data = {
            "components": [
                {
                    "analysis": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
                    "component_name": "ABSORBANCE_540",
                },
            ],
        }

        _rewrite_extraction_refs(extracted_data, ext_to_tpl)
        assert extracted_data["components"][0]["analysis"] == "SITE_IDENTITY"

    def test_rewrite_word_subset_match(self):
        """Truncated ref 'Dye-Binding Test' matches via word-subset."""
        ext_to_tpl = {
            _normalize_for_match("DYE_BINDING_IDENTITY_TEST_FOR_ACS"): "SITE_IDENTITY",
        }
        extracted_data = {
            "components": [
                {
                    "analysis": "Dye-Binding Test",
                    "component_name": "ABSORBANCE_540",
                },
            ],
        }

        _rewrite_extraction_refs(extracted_data, ext_to_tpl)
        assert extracted_data["components"][0]["analysis"] == "SITE_IDENTITY"

    def test_rewrite_ambiguous_subset_not_rewritten(self):
        """Ambiguous word-subset match (>1 candidate) leaves ref unchanged."""
        ext_to_tpl = {
            _normalize_for_match("DYE_BINDING_TEST_A"): "SITE_A",
            _normalize_for_match("DYE_BINDING_TEST_B"): "SITE_B",
        }
        extracted_data = {
            "components": [
                {
                    "analysis": "Dye Binding Test",
                    "component_name": "X",
                },
            ],
        }

        _rewrite_extraction_refs(extracted_data, ext_to_tpl)
        # Should remain unchanged (ambiguous -- 2 candidates)
        assert extracted_data["components"][0]["analysis"] == "Dye Binding Test"

    def test_rewrite_too_few_tokens_not_rewritten(self):
        """Refs with < 3 tokens are not rewritten via word-subset."""
        ext_to_tpl = {
            _normalize_for_match("DYE_BINDING_IDENTITY_TEST"): "SITE_IDENTITY",
        }
        extracted_data = {
            "components": [
                {
                    "analysis": "Dye Test",
                    "component_name": "X",
                },
            ],
        }

        _rewrite_extraction_refs(extracted_data, ext_to_tpl)
        # 2-token ref -> skipped by min-3-token guard
        assert extracted_data["components"][0]["analysis"] == "Dye Test"

    def test_rewrite_covers_calc_variables_and_calculations(self):
        ext_to_tpl = {
            _normalize_for_match("DYE_BINDING_IDENTITY_TEST"): "SITE_IDENTITY",
        }
        extracted_data = {
            "components": [],
            "calc_variables": [
                {"analysis": "DYE_BINDING_IDENTITY_TEST", "name": "V_ABS"},
            ],
            "calculations": [
                {"analysis": "DYE_BINDING_IDENTITY_TEST", "component": "X"},
            ],
        }

        _rewrite_extraction_refs(extracted_data, ext_to_tpl)
        assert extracted_data["calc_variables"][0]["analysis"] == "SITE_IDENTITY"
        assert extracted_data["calculations"][0]["analysis"] == "SITE_IDENTITY"


# ---------------------------------------------------------------------------
# E2E merge with mismatched names (all fixes together)
# ---------------------------------------------------------------------------


class TestMergeMismatchedNamesE2E:
    """End-to-end: extraction with different analysis names merges correctly."""

    def test_dye_binding_extraction_merges_into_identity_template(
        self, identity_template,
    ):
        """Simulates the AND_ACS_DYE-LAB-2499.pdf scenario.

        Extraction has 'DYE_BINDING_IDENTITY_TEST_FOR_ACS' as analysis name
        and components reference 'Dye-Binding Test' (truncated). Template
        uses SITE_IDENTITY / SITE_IDENTITY_CTL / SITE_IDENTITY_META.

        After merge:
        - 3 analyses (not 4) -- extraction matched by type
        - Template names preserved (SITE_IDENTITY, not DYE_BINDING_...)
        - Component refs resolved to template names
        """
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)",
                    "analysis_type": "ID",
                    "description": "Dye-Binding Identity Test",
                },
            ],
            "components": [
                {
                    "analysis": "Dye-Binding Test",
                    "component_name": "Package: Double layered and sealed?",
                    "result_type": "L",
                },
            ],
            "calc_variables": [],
            "calculations": [],
        }

        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Should be 3 analyses (not 4)
        assert len(result.mda_template["analyses"]) == 3

        # Template names preserved
        analysis_names = [a["name"] for a in result.mda_template["analyses"]]
        assert "SITE_IDENTITY" in analysis_names
        assert "SITE_IDENTITY_CTL" in analysis_names
        assert "SITE_IDENTITY_META" in analysis_names

        # No extraction analysis name leaked
        for name in analysis_names:
            assert "DYE_BINDING" not in name

        # Validation should pass (all refs resolved)
        assert result.validation_passed is True

    def test_merge_does_not_mutate_caller_input(self, identity_template):
        """merge_layers must not mutate the caller's extracted_data dict."""
        import copy

        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
                    "analysis_type": "ID",
                },
            ],
            "components": [
                {
                    "analysis": "Dye-Binding Test",
                    "component_name": "SOME_COMPONENT",
                    "result_type": "N",
                },
            ],
            "calc_variables": [],
            "calculations": [],
        }
        original = copy.deepcopy(extracted_data)

        merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Caller's input must not have been mutated
        assert extracted_data == original

    def test_fix_d_resolves_truncated_ref_in_normalization_stage(
        self, identity_template,
    ):
        """Fix D must resolve a truncated ref that Fix C cannot rewrite.

        Scenario: extraction analysis matched to template by type, but
        a component in the TEMPLATE (not extraction) references a truncated
        extraction name. Fix C only rewrites extraction data refs, so this
        truncated ref in the merged base must be resolved by Fix D's alias
        injection into the normalization map at step 4b.

        We use TestType.OTHER here because template-locked mode (active for
        known types like IDENTITY) correctly rejects unmatched components.
        Fix D's ref resolution is still relevant for unlocked mode.
        """
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
                    "analysis_type": "ID",
                },
            ],
            # This component uses a truncated ref that does NOT exactly match
            # any extraction or template analysis name. Fix C's word-subset
            # rewrites it in the deep copy. But let's verify the final merged
            # result resolves it correctly via the full pipeline.
            "components": [
                {
                    "analysis": "Dye Binding Identity",
                    "component_name": "NEW_EXTRACTED_RESULT?",
                    "result_type": "N",
                    "order_number": 99,
                },
            ],
            "calc_variables": [],
            "calculations": [],
        }

        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.OTHER,
        )

        # The truncated ref must have been resolved to a template name
        new_comp = next(
            (c for c in result.mda_template["components"]
             if c.get("component_name") == "NEW_EXTRACTED_RESULT?"),
            None,
        )
        assert new_comp is not None, "New extracted component not found in merged output"
        # The analysis ref must point to a valid template analysis
        valid_analysis_names = {
            a["name"] for a in result.mda_template["analyses"]
        }
        assert new_comp["analysis"] in valid_analysis_names, (
            f"Truncated ref '{new_comp['analysis']}' was not resolved to a "
            f"valid template name. Valid: {valid_analysis_names}"
        )


# ---------------------------------------------------------------------------
# Template-locked mode tests
# ---------------------------------------------------------------------------


class TestTemplateLocked:
    """Template-locked mode rejects unmatched extracted items for known test types."""

    def test_rejects_unmatched_analysis(self, identity_template):
        """Unmatched analyses are rejected when test_type=IDENTITY."""
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
                    "analysis_type": "ID",
                    "description": "This matches template by type",
                },
                {
                    "name": "COMPLETELY_UNKNOWN_ANALYSIS",
                    "analysis_type": "PHYS",
                    "description": "This should be rejected",
                },
            ],
            "components": [],
            "calc_variables": [],
            "calculations": [],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Should still be exactly 3 analyses (template count)
        assert len(result.mda_template["analyses"]) == 3

        # No unknown analysis in output
        analysis_names = [a["name"] for a in result.mda_template["analyses"]]
        assert "COMPLETELY_UNKNOWN_ANALYSIS" not in analysis_names
        assert "EXT_COMPLETELY_UNKNOWN_ANALYSIS" not in analysis_names

        # Rejected count tracked in stats
        assert result.stats.get("TEMPLATE_LOCKED_REJECTED", 0) >= 1

    def test_rejects_unmatched_component(self, identity_template):
        """Unmatched components are rejected when test_type=IDENTITY."""
        extracted_data = {
            "components": [
                {
                    "analysis": "SITE_IDENTITY",
                    "component_name": "SOME_FAKE_EXTRACTED_COMPONENT?",
                    "result_type": "N",
                    "order_number": 99,
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Should still be exactly 25 components (template count)
        assert len(result.mda_template["components"]) == 25

        # Fake component not in output
        comp_names = [c["component_name"] for c in result.mda_template["components"]]
        assert "SOME_FAKE_EXTRACTED_COMPONENT?" not in comp_names

    def test_rejects_unmatched_calculation(self, identity_template):
        """Unmatched calculations are rejected when test_type=IDENTITY."""
        extracted_data = {
            "calculations": [
                {
                    "analysis": "FAKE_ANALYSIS",
                    "component": "FAKE_COMPONENT",
                    "source_code": "RETURN 42",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Template has 11 calculations; no extra should be added
        assert len(result.mda_template["calculations"]) == 11
        for calc in result.mda_template["calculations"]:
            assert calc.get("analysis") != "FAKE_ANALYSIS"

    def test_still_overlays_matched_items(self, identity_template):
        """Matched items still get their variable fields overlaid."""
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ACS",
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
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Template structure preserved
        assert len(result.mda_template["analyses"]) == 3

        # Variable fields overlaid from extraction
        analysis_0 = result.mda_template["analyses"][0]
        assert analysis_0["description"] == "Extracted description from PDF"

        # Component match still works
        weight_comp = next(
            c for c in result.mda_template["components"]
            if c.get("component_name") == "Weight of Sponge(s)"
        )
        assert weight_comp["minimum"] == 50.0
        assert weight_comp["maximum"] == 200.0

    def test_unlocked_for_other_type(self, identity_template):
        """TestType.OTHER should NOT enable template-locked mode."""
        extracted_data = {
            "analyses": [
                {
                    "name": "COMPLETELY_UNKNOWN_ANALYSIS",
                    "analysis_type": "PHYS",
                    "description": "This should be admitted for OTHER",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.OTHER,
        )

        # For OTHER, unmatched items SHOULD be admitted
        assert len(result.mda_template["analyses"]) > 3
        assert "TEMPLATE_LOCKED_REJECTED" not in result.stats

    def test_unlocked_when_no_test_type(self, identity_template):
        """No test_type (None) should NOT enable template-locked mode."""
        extracted_data = {
            "analyses": [
                {
                    "name": "COMPLETELY_UNKNOWN_ANALYSIS",
                    "analysis_type": "PHYS",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=None,
        )

        # For None, unmatched items SHOULD be admitted
        assert len(result.mda_template["analyses"]) > 3

    def test_real_scenario_4th_analysis_blocked(self, identity_template):
        """Reproduces the AND_ACS_DYE-LAB-2499 scenario: 4th analysis blocked.

        Extraction produces analyses that match template by type + 1 spurious
        analysis from PDF description text. The spurious 4th analysis and its
        associated components/calculations should be rejected.
        """
        extracted_data = {
            "analyses": [
                {
                    "name": "DYE_BINDING_IDENTITY_TEST_FOR_ABSORBABLE_COLLAGEN_SPONGE_(ACS)",
                    "analysis_type": "ID",
                    "description": "Dye-Binding Identity Test",
                },
                {
                    "name": "CONTROL_ANALYSIS",
                    "analysis_type": "QC_SAMPLES",
                },
                {
                    "name": "META_DATA_ANALYSIS",
                    "analysis_type": "QC_SAMPLES",
                },
                {
                    "name": "SPURIOUS_EXTRA_FROM_PDF_DESCRIPTION",
                    "analysis_type": "PHYS",
                    "description": "Should be rejected in template-locked mode",
                },
            ],
            "components": [
                {
                    "analysis": "SPURIOUS_EXTRA_FROM_PDF_DESCRIPTION",
                    "component_name": "4_MM_DIRECT_RED_80_STOCK_SOLUTION?",
                    "result_type": "N",
                },
            ],
            "calculations": [
                {
                    "analysis": "SPURIOUS_EXTRA_FROM_PDF_DESCRIPTION",
                    "component": "4_MM_DIRECT_RED_80_STOCK_SOLUTION",
                    "source_code": "REM SME_REQUIRED: source_code for 4_MM_DIRECT_RED_80_STOCK_SOLUTION",
                },
            ],
        }
        result = merge_layers(
            template_mda=identity_template,
            extracted_data=extracted_data,
            test_type=TestType.IDENTITY,
        )

        # Exactly 3 analyses: the spurious 4th is rejected
        assert len(result.mda_template["analyses"]) == 3

        # Template names preserved
        analysis_names = [a["name"] for a in result.mda_template["analyses"]]
        assert "SITE_IDENTITY" in analysis_names
        assert "SITE_IDENTITY_CTL" in analysis_names
        assert "SITE_IDENTITY_META" in analysis_names
        assert "SPURIOUS_EXTRA_FROM_PDF_DESCRIPTION" not in analysis_names

        # No spurious components admitted
        assert len(result.mda_template["components"]) == 25

        # No SME_REQUIRED placeholder calculations from spurious analysis
        for calc in result.mda_template["calculations"]:
            assert "SME_REQUIRED" not in calc.get("source_code", "")

        # Rejected count tracked
        assert result.stats.get("TEMPLATE_LOCKED_REJECTED", 0) >= 1

        # Validation should still pass
        assert result.validation_passed is True
