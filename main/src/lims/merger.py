"""Merge template skeleton with extracted variables and augmented values.

Produces a complete MDATemplate with full provenance tracking.
Detects conflicts where extracted values disagree with template values.

Priority: Extracted > Template > Augmented > SME_REQUIRED
Conflicts are recorded, not auto-resolved.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Optional

from langfuse import observe
from pydantic import BaseModel, Field

from main.src.lims.mda_schema import MDATemplate
from main.src.lims.provenance import ComponentSource, FieldProvenance, ProvenanceMap
from main.src.lims.test_type import TestType

logger = logging.getLogger(__name__)


class MergeConflict(BaseModel):
    """A conflict between template and extracted values."""

    field_path: str
    template_value: Any
    extracted_value: Any
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None


class MergeResult(BaseModel):
    """Result of merging template + extraction + augmentation."""

    mda_template: dict[str, Any]
    provenance: dict[str, Any]
    conflicts: list[MergeConflict] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
    validation_passed: bool = False
    validation_error: Optional[str] = None


def _normalize_for_match(name: str) -> str:
    """Normalize a name for fuzzy matching.

    Lowercases, strips whitespace, replaces underscores/hyphens with spaces,
    and collapses multiple spaces.
    """
    return " ".join(name.lower().replace("_", " ").replace("-", " ").split())


def _match_analysis(
    extracted_analysis: dict[str, Any],
    template_analyses: list[dict[str, Any]],
    exclude_indices: set[int] | None = None,
) -> int | None:
    """Find the matching template analysis index for an extracted analysis.

    Matches by normalized name or analysis_type. Indices in
    ``exclude_indices`` are skipped so that a second extracted analysis
    with the same type matches the next available template entry (e.g.
    two QC_SAMPLES analyses match distinct template QC rows).

    Returns:
        Index into template_analyses, or None if no match.
    """
    ext_name = _normalize_for_match(str(extracted_analysis.get("name", "")))
    ext_type = str(extracted_analysis.get("analysis_type", "")).upper()
    _exclude = exclude_indices or set()

    for i, tpl_analysis in enumerate(template_analyses):
        if i in _exclude:
            continue
        tpl_name = _normalize_for_match(str(tpl_analysis.get("name", "")))
        tpl_type = str(tpl_analysis.get("analysis_type", "")).upper()

        if ext_name and tpl_name and ext_name == tpl_name:
            return i
        if ext_type and tpl_type and ext_type == tpl_type:
            return i

    return None


def _match_component(
    extracted_component: dict[str, Any],
    template_components: list[dict[str, Any]],
) -> int | None:
    """Find the matching template component index for an extracted component.

    Matches by (analysis, component_name) tuple using normalized names.

    Returns:
        Index into template_components, or None if no match.
    """
    ext_analysis = _normalize_for_match(str(extracted_component.get("analysis", "")))
    ext_name = _normalize_for_match(str(extracted_component.get("component_name", "")))

    for i, tpl_comp in enumerate(template_components):
        tpl_analysis = _normalize_for_match(str(tpl_comp.get("analysis", "")))
        tpl_name = _normalize_for_match(str(tpl_comp.get("component_name", "")))

        if ext_analysis == tpl_analysis and ext_name == tpl_name:
            return i

    return None


def _set_provenance_for_list(
    provenance: ProvenanceMap,
    prefix: str,
    items: list[dict[str, Any]],
    source: ComponentSource,
    confidence: float,
    detail: str = "",
) -> None:
    """Set provenance for all fields in a list of dicts."""
    for i, item in enumerate(items):
        item_prefix = f"{prefix}[{i}]"
        for key, value in item.items():
            if value is not None and value != "" and value != []:
                provenance.set_provenance(
                    f"{item_prefix}.{key}",
                    source=source,
                    confidence=confidence,
                    detail=detail,
                )



# Mapping for coercing unknown analysis_type values to valid AnalysisType enums
_ANALYSIS_TYPE_COERCION: dict[str, str] = {
    "IDENTITY": "ID",
    "ASSAY": "ASY",
    "IMPURITY": "IMP",
    "IMPURITIES": "IMP",
    "PHYSICAL": "PHYS",
    "DISSOLUTION": "PHYS",
    "KARL FISCHER": "KF",
    "MOISTURE": "KF",
    "LOD": "PHYS",
    "TITRATION": "KF",
    "TEST METHOD": "PHYS",
    "QC": "QC_SAMPLES",
    "RAW MATERIAL": "RM",
    "RAW_MATERIAL": "RM",
}

# Valid analysis_type values (from AnalysisType enum)
_VALID_ANALYSIS_TYPES = {"ID", "ASY", "IMP", "PHYS", "QC_SAMPLES", "HPLC", "RM", "KF"}


def _sanitize_new_analysis(
    item: dict[str, Any],
) -> dict[str, Any] | None:
    """Ensure a new extracted analysis has all required fields.

    Called when an extracted analysis does not match any template analysis.
    Fills missing required fields with sensible defaults derived from
    available data. Returns None for phantom rows (revision history,
    page headers) that should be rejected.

    Args:
        item: Raw extracted analysis dict.

    Returns:
        Sanitized analysis dict with all required fields present,
        or None if the item is a phantom row that should be rejected.
    """
    raw_name = item.get("name")
    # Reject phantom rows: None, empty, "None", "unknown" names
    if raw_name is None or str(raw_name).strip().lower() in ("", "none", "unknown"):
        logger.info(
            "Rejecting phantom analysis row with name=%r (likely revision history or page header)",
            raw_name,
        )
        return None

    name = str(item.get("name", "UNKNOWN"))

    if "reported_name" not in item or not item["reported_name"]:
        item["reported_name"] = name

    if "common_name" not in item or not item["common_name"]:
        item["common_name"] = name

    # Coerce analysis_type to valid enum value
    raw_type = str(item.get("analysis_type", "")).upper().strip()
    if raw_type not in _VALID_ANALYSIS_TYPES:
        coerced = _ANALYSIS_TYPE_COERCION.get(raw_type, "PHYS")
        logger.info(
            "Coercing analysis_type '%s' -> '%s' for extracted analysis '%s'",
            raw_type,
            coerced,
            name,
        )
        item["analysis_type"] = coerced

    # Ensure name has site prefix (required by Analysis validator)
    if "_" not in name:
        item["name"] = f"EXT_{name}"
        logger.info(
            "Added site prefix to analysis name: '%s' -> '%s'",
            name,
            item["name"],
        )

    return item


def _sanitize_new_component(
    item: dict[str, Any],
    existing_components: list[dict[str, Any]],
) -> dict[str, Any]:
    """Ensure a new extracted component has all required fields.

    Called when an extracted component does not match any template component.
    Assigns sequential order_number and defaults result_type to 'T' (text).

    Args:
        item: Raw extracted component dict.
        existing_components: Current merged component list (for order numbering).

    Returns:
        Sanitized component dict with all required fields present.
    """
    if "order_number" not in item or item["order_number"] is None:
        max_order = max(
            (c.get("order_number", 0) for c in existing_components if c.get("order_number") is not None),
            default=0,
        )
        item["order_number"] = max_order + 10
        logger.info(
            "Auto-assigned order_number=%d for new component '%s'",
            item["order_number"],
            item.get("component_name", "UNKNOWN"),
        )

    if "result_type" not in item or not item["result_type"]:
        item["result_type"] = "T"
        logger.info(
            "Defaulted result_type='T' for new component '%s'",
            item.get("component_name", "UNKNOWN"),
        )

    # Validate result_type is valid
    valid_result_types = {"N", "K", "L", "T", "D"}
    raw_rt = str(item.get("result_type", "")).upper().strip()
    if raw_rt not in valid_result_types:
        logger.info(
            "Coercing result_type '%s' -> 'T' for component '%s'",
            raw_rt,
            item.get("component_name", "UNKNOWN"),
        )
        item["result_type"] = "T"

    return item


def _sanitize_new_calc_variable(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Ensure a new extracted calc_variable has all required fields.

    Args:
        item: Raw extracted calc_variable dict.

    Returns:
        Sanitized calc_variable dict with required fields present.
    """
    if "reference_type" not in item or not item["reference_type"]:
        item["reference_type"] = "C"
        logger.info(
            "Defaulted reference_type='C' for new calc_variable '%s'",
            item.get("name", "UNKNOWN"),
        )

    # Validate reference_type is valid
    valid_ref_types = {"C", "A"}
    raw_rt = str(item.get("reference_type", "")).upper().strip()
    if raw_rt not in valid_ref_types:
        logger.info(
            "Coercing reference_type '%s' -> 'C' for calc_variable '%s'",
            raw_rt,
            item.get("name", "UNKNOWN"),
        )
        item["reference_type"] = "C"

    return item


def _sanitize_new_calculation(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Ensure a new extracted calculation has all required fields.

    Args:
        item: Raw extracted calculation dict.

    Returns:
        Sanitized calculation dict with required fields present.
    """
    if "source_code" not in item or not item.get("source_code", "").strip():
        component = item.get("component", "UNKNOWN")
        item["source_code"] = f"REM SME_REQUIRED: source_code for {component}"
        logger.info(
            "Defaulted source_code placeholder for new calculation on '%s'",
            component,
        )

    return item


def _propagate_analysis_renames(
    base: dict[str, Any],
    rename_map: dict[str, str],
) -> None:
    """Propagate analysis renames to dependent sheets.

    When extraction overrides an analysis name (e.g. SITE_IDENTITY ->
    AND_ACS_DYE), components, calc_variables, and calculations still
    reference the old template name. This function updates those
    references to preserve cross-sheet integrity.

    Mutates ``base`` in place.

    Args:
        base: The merged MDA dict.
        rename_map: Mapping of old_name -> new_name for renamed analyses.
    """
    if not rename_map:
        return

    for sheet_key in ("components", "calc_variables", "calculations"):
        items = base.get(sheet_key, [])
        for item in items:
            if not isinstance(item, dict):
                continue
            for field in ("analysis", "reference_analysis"):
                old_ref = item.get(field)
                if old_ref and str(old_ref) in rename_map:
                    new_ref = rename_map[str(old_ref)]
                    logger.info(
                        "Propagating analysis rename in %s: %s.%s '%s' -> '%s'",
                        sheet_key,
                        item.get("component_name") or item.get("name") or item.get("component", "?"),
                        field,
                        old_ref,
                        new_ref,
                    )
                    item[field] = new_ref


def _overlay_extracted_items(
    template_items: list[dict[str, Any]],
    extracted_items: list[dict[str, Any]],
    match_fn,
    provenance: ProvenanceMap,
    prefix: str,
    conflicts: list[MergeConflict],
    conflict_fields: set[str] | None = None,
    sanitize_fn=None,
) -> list[dict[str, Any]]:
    """Overlay extracted items onto template items.

    Args:
        template_items: List of template item dicts (base).
        extracted_items: List of extracted item dicts (overlay).
        match_fn: Function(extracted_item, template_items) -> index | None.
        provenance: ProvenanceMap to update.
        prefix: Path prefix for provenance (e.g., "analyses", "components").
        conflicts: List to append MergeConflict objects to.
        conflict_fields: Set of field names that trigger conflict detection
            when template and extraction disagree. If None, all fields checked.
        sanitize_fn: Optional function to sanitize new (unmatched) items
            before appending. Called as sanitize_fn(item) for analyses or
            sanitize_fn(item, merged) for components.

    Returns:
        Merged list of item dicts.
    """
    merged = copy.deepcopy(template_items)
    matched_indices: set[int] = set()

    for ext_item in extracted_items:
        match_idx = match_fn(ext_item, merged)

        if match_idx is not None:
            matched_indices.add(match_idx)
            tpl_item = merged[match_idx]

            for key, ext_value in ext_item.items():
                if ext_value is None or ext_value == "":
                    continue

                tpl_value = tpl_item.get(key)
                path = f"{prefix}[{match_idx}].{key}"

                if (
                    tpl_value is not None
                    and tpl_value != ""
                    and tpl_value != ext_value
                ):
                    if conflict_fields is None or key in conflict_fields:
                        conflicts.append(
                            MergeConflict(
                                field_path=path,
                                template_value=tpl_value,
                                extracted_value=ext_value,
                            )
                        )

                # Coerce analysis_type to valid enum if needed
                if prefix == "analyses" and key == "analysis_type":
                    raw_at = str(ext_value).upper().strip()
                    if raw_at not in _VALID_ANALYSIS_TYPES:
                        ext_value = _ANALYSIS_TYPE_COERCION.get(raw_at, "PHYS")
                        logger.info(
                            "Coerced matched analysis_type '%s' -> '%s'",
                            raw_at,
                            ext_value,
                        )

                tpl_item[key] = ext_value
                provenance.set_provenance(
                    path,
                    source=ComponentSource.EXTRACTED,
                    confidence=0.8,
                    detail="Overridden by PDF extraction",
                )
        else:
            new_item = copy.deepcopy(ext_item)
            # Sanitize new items to ensure required fields are present
            if sanitize_fn is not None:
                try:
                    new_item = sanitize_fn(new_item, merged)
                except TypeError:
                    new_item = sanitize_fn(new_item)
            # Sanitize returned None -> reject this item (phantom row)
            if new_item is None:
                continue
            new_idx = len(merged)
            merged.append(new_item)
            item_prefix = f"{prefix}[{new_idx}]"
            for key, value in new_item.items():
                if value is not None and value != "":
                    provenance.set_provenance(
                        f"{item_prefix}.{key}",
                        source=ComponentSource.EXTRACTED,
                        confidence=0.7,
                        detail="New item from PDF extraction (not in template)",
                    )

    return merged


@observe(name="lims-merge")
def merge_layers(
    template_mda: MDATemplate,
    extracted_data: dict[str, Any],
    augmented_data: dict[str, Any] | None = None,
    test_type: TestType | None = None,
) -> MergeResult:
    """Merge template + extracted + augmented layers into final MDA.

    Priority: Extracted > Template > Augmented > SME_REQUIRED
    Conflicts are recorded, not auto-resolved.

    Args:
        template_mda: The template skeleton MDATemplate.
        extracted_data: Raw extraction result dict (may have analyses,
            components, calc_variables, calculations keys).
        augmented_data: Optional augmentation suggestions. Expected format:
            ``{"suggestions": [{"field_path": ..., "suggested_value": ...,
              "confidence": ..., "source": ...}]}``.
        test_type: The classified test type (for logging).

    Returns:
        MergeResult with merged MDA, provenance, conflicts, and stats.
    """
    provenance = ProvenanceMap()
    conflicts: list[MergeConflict] = []

    # 1. Initialize base from template
    base = template_mda.model_dump()

    # Set template provenance for all fields
    _set_provenance_for_list(
        provenance, "analyses", base.get("analyses", []),
        ComponentSource.TEMPLATE, 1.0, "Template skeleton",
    )
    _set_provenance_for_list(
        provenance, "components", base.get("components", []),
        ComponentSource.TEMPLATE, 1.0, "Template skeleton",
    )
    _set_provenance_for_list(
        provenance, "calc_variables", base.get("calc_variables", []),
        ComponentSource.TEMPLATE, 1.0, "Template skeleton",
    )
    _set_provenance_for_list(
        provenance, "calculations", base.get("calculations", []),
        ComponentSource.TEMPLATE, 1.0, "Template skeleton",
    )

    logger.info(
        "Merge base initialized from template: %d analyses, %d components, "
        "%d calc_variables, %d calculations",
        len(base.get("analyses", [])),
        len(base.get("components", [])),
        len(base.get("calc_variables", [])),
        len(base.get("calculations", [])),
    )

    # 2. Overlay extracted data
    ext_analyses = extracted_data.get("analyses", [])
    ext_components = extracted_data.get("components", [])
    ext_calc_vars = extracted_data.get("calc_variables", [])
    ext_calculations = extracted_data.get("calculations", [])

    # Track original template analysis names before overlay (for rename detection)
    original_analysis_names = [
        str(a.get("name", "")) for a in base.get("analyses", [])
    ]

    if ext_analyses:
        # Wrap _match_analysis with exclusive index tracking so that
        # duplicate analysis_types (e.g. two QC_SAMPLES) match distinct
        # template entries instead of both matching the first one.
        _matched_analysis_indices: set[int] = set()

        def _exclusive_match_analysis(
            ext_item: dict[str, Any],
            tpl_items: list[dict[str, Any]],
        ) -> int | None:
            idx = _match_analysis(ext_item, tpl_items, exclude_indices=_matched_analysis_indices)
            if idx is not None:
                _matched_analysis_indices.add(idx)
            return idx

        base["analyses"] = _overlay_extracted_items(
            base.get("analyses", []),
            ext_analyses,
            _exclusive_match_analysis,
            provenance,
            "analyses",
            conflicts,
            conflict_fields={"analysis_type", "name"},
            sanitize_fn=_sanitize_new_analysis,
        )

    # Build analysis rename map: detect where extraction changed analysis names
    analysis_rename_map: dict[str, str] = {}
    for i, orig_name in enumerate(original_analysis_names):
        if i < len(base.get("analyses", [])):
            new_name = str(base["analyses"][i].get("name", ""))
            if orig_name and new_name and orig_name != new_name:
                analysis_rename_map[orig_name] = new_name
                logger.info(
                    "Analysis rename detected: '%s' -> '%s'",
                    orig_name,
                    new_name,
                )

    # Propagate renames to dependent sheets before component overlay
    _propagate_analysis_renames(base, analysis_rename_map)

    if ext_components:
        base["components"] = _overlay_extracted_items(
            base.get("components", []),
            ext_components,
            _match_component,
            provenance,
            "components",
            conflicts,
            conflict_fields={"result_type", "units", "list_key"},
            sanitize_fn=_sanitize_new_component,
        )

    if ext_calc_vars:
        base["calc_variables"] = _overlay_extracted_items(
            base.get("calc_variables", []),
            ext_calc_vars,
            lambda ext, tpl: _match_calc_var(ext, tpl),
            provenance,
            "calc_variables",
            conflicts,
            sanitize_fn=_sanitize_new_calc_variable,
        )

    if ext_calculations:
        base["calculations"] = _overlay_extracted_items(
            base.get("calculations", []),
            ext_calculations,
            lambda ext, tpl: _match_calculation(ext, tpl),
            provenance,
            "calculations",
            conflicts,
            sanitize_fn=_sanitize_new_calculation,
        )

    logger.info(
        "Extraction overlay complete: %d conflicts detected",
        len(conflicts),
    )

    # 3. Apply augmented data
    if augmented_data and "suggestions" in augmented_data:
        suggestions = augmented_data["suggestions"]
        for suggestion in suggestions:
            field_path = suggestion.get("field_path", "")
            suggested_value = suggestion.get("suggested_value")
            confidence = float(suggestion.get("confidence", 0.0))
            source_detail = str(suggestion.get("source", "standards RAG"))

            if suggested_value is None:
                continue

            existing_prov = provenance.get_provenance(field_path)
            if existing_prov and existing_prov.source == ComponentSource.EXTRACTED:
                continue

            _apply_suggestion_to_dict(base, field_path, suggested_value)
            provenance.set_provenance(
                field_path,
                source=ComponentSource.INFERRED,
                confidence=confidence,
                detail=source_detail,
            )

        logger.info(
            "Augmentation applied: %d suggestions processed",
            len(suggestions),
        )

    # 4. Mark remaining gaps as SME_REQUIRED
    _mark_sme_required_gaps(base, provenance)

    # 4b. Normalize analysis refs and forward-fill BEFORE validation
    # This ensures the reviewer sees the final normalized form (not deferred
    # to export time, which would violate the HITL contract).
    from main.src.lims.data_normalizer import (
        _build_analysis_name_map,
        _forward_fill_field,
        _normalize_analysis_refs,
        sanitize_component_numeric_bounds,
    )

    known_analyses = [
        str(a["name"]) for a in base.get("analyses", [])
        if isinstance(a, dict) and a.get("name")
    ]
    analysis_name_map_norm = _build_analysis_name_map(base.get("analyses", []))
    for sheet_key in ("components", "calc_variables", "calculations"):
        if sheet_key in base and isinstance(base[sheet_key], list):
            _normalize_analysis_refs(base[sheet_key], analysis_name_map_norm)
            _forward_fill_field(
                base[sheet_key], "analysis",
                available_values=known_analyses,
            )
            if sheet_key in ("calc_variables", "calculations"):
                _forward_fill_field(base[sheet_key], "component")

    if "components" in base and isinstance(base["components"], list):
        sanitize_component_numeric_bounds(base["components"])

    logger.info("Pre-review normalization applied (analysis refs + forward-fill)")

    # 5. Validate cross-sheet integrity
    validation_passed = False
    validation_error: str | None = None
    try:
        MDATemplate.model_validate(base)
        validation_passed = True
        logger.info("Cross-sheet integrity validation passed after merge")
    except Exception as e:
        validation_error = str(e)
        logger.warning(
            "Cross-sheet integrity validation failed after merge: %s", e
        )

    # 6. Build stats
    stats = provenance.summary()

    logger.info(
        "Merge complete: test_type=%s stats=%s conflicts=%d validation=%s",
        test_type.value if test_type else "N/A",
        stats,
        len(conflicts),
        "PASSED" if validation_passed else "FAILED",
    )

    return MergeResult(
        mda_template=base,
        provenance=provenance.model_dump(),
        conflicts=conflicts,
        stats=stats,
        validation_passed=validation_passed,
        validation_error=validation_error,
    )


def _match_calc_var(
    extracted: dict[str, Any],
    template_items: list[dict[str, Any]],
) -> int | None:
    """Match calc_variable by (analysis, component, name) tuple."""
    ext_analysis = _normalize_for_match(str(extracted.get("analysis", "")))
    ext_component = _normalize_for_match(str(extracted.get("component", "")))
    ext_name = _normalize_for_match(str(extracted.get("name", "")))

    for i, tpl in enumerate(template_items):
        tpl_analysis = _normalize_for_match(str(tpl.get("analysis", "")))
        tpl_component = _normalize_for_match(str(tpl.get("component", "")))
        tpl_name = _normalize_for_match(str(tpl.get("name", "")))

        if (
            ext_analysis == tpl_analysis
            and ext_component == tpl_component
            and ext_name == tpl_name
        ):
            return i

    return None


def _match_calculation(
    extracted: dict[str, Any],
    template_items: list[dict[str, Any]],
) -> int | None:
    """Match calculation by (analysis, component) tuple."""
    ext_analysis = _normalize_for_match(str(extracted.get("analysis", "")))
    ext_component = _normalize_for_match(str(extracted.get("component", "")))

    for i, tpl in enumerate(template_items):
        tpl_analysis = _normalize_for_match(str(tpl.get("analysis", "")))
        tpl_component = _normalize_for_match(str(tpl.get("component", "")))

        if ext_analysis == tpl_analysis and ext_component == tpl_component:
            return i

    return None


def _apply_suggestion_to_dict(
    base: dict[str, Any], field_path: str, value: Any
) -> None:
    """Apply a suggestion value to a nested dict using dot-notation path.

    Supports paths like "components[3].units" or "analyses[0].description".

    Raises:
        ValueError: If path cannot be resolved — data integrity error.
    """
    import re

    parts = re.split(r"\.", field_path)
    current: Any = base

    for i, part in enumerate(parts[:-1]):
        match = re.match(r"^(\w+)\[(\d+)\]$", part)
        if match:
            key, idx = match.group(1), int(match.group(2))
            if isinstance(current, dict) and key in current:
                lst = current[key]
                if isinstance(lst, list) and idx < len(lst):
                    current = lst[idx]
                else:
                    raise ValueError(
                        f"Cannot resolve augmentation path '{field_path}': "
                        f"index {idx} out of range for '{key}'"
                    )
            else:
                raise ValueError(
                    f"Cannot resolve augmentation path '{field_path}': "
                    f"key '{key}' not found"
                )
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ValueError(
                f"Cannot resolve augmentation path '{field_path}': "
                f"segment '{part}' not found"
            )

    last_part = parts[-1]
    last_match = re.match(r"^(\w+)\[(\d+)\]$", last_part)
    if last_match:
        key, idx = last_match.group(1), int(last_match.group(2))
        if isinstance(current, dict) and key in current:
            lst = current[key]
            if isinstance(lst, list) and idx < len(lst):
                lst[idx] = value
    elif isinstance(current, dict):
        current[last_part] = value


def _mark_sme_required_gaps(
    base: dict[str, Any], provenance: ProvenanceMap
) -> None:
    """Mark fields that are still null/empty as SME_REQUIRED.

    Skips fields that are legitimately Optional in the Pydantic schema —
    these are None by design (e.g., list_key is only needed for L-type
    components, instrument_group only for N-type with instruments).
    """
    # Fields that are Optional in the schema and legitimately None
    optional_fields: dict[str, set[str]] = {
        "analyses": {"worklist_link", "description"},
        "components": {
            "units", "minimum", "maximum",
            "instrument_group", "list_key", "sr_picker",
            "round_type", "places",
        },
        "calc_variables": {
            "reference_analysis", "reference_component", "attribute_1",
        },
        "calculations": {"description"},
    }

    for sheet_key in ("analyses", "components", "calc_variables", "calculations"):
        items = base.get(sheet_key, [])
        skip_fields = optional_fields.get(sheet_key, set())
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if key in skip_fields:
                    continue
                path = f"{sheet_key}[{i}].{key}"
                existing = provenance.get_provenance(path)
                if existing is not None:
                    continue
                if value is None or value == "":
                    provenance.set_provenance(
                        path,
                        source=ComponentSource.SME_REQUIRED,
                        confidence=0.0,
                        detail="No value from template, extraction, or augmentation",
                    )
