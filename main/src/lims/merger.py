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

_NON_COMPONENT_NAME_HINTS = {
    "ORBITAL SHAKER",
    "CALIBRATED TIMER",
    "FILTER UNIT",
    "GLACIAL ACETIC ACID",
    "PURIFIED WATER",
    "DIRECT RED 80",
    "ABSORBABLE COLLAGEN SPONGE",
    "TYPE I COLLAGEN",
    "PETRI DISH",
    "WEIGH BOAT",
}


def _looks_like_non_component_row(component_name: str) -> bool:
    """Heuristic classifier for extracted rows that are not true LIMS components.

    These rows are typically equipment/material/procedure entities and should
    not be auto-admitted as result-entry components.
    """
    normalized = _normalize_for_match(component_name)
    if not normalized:
        return True

    for hint in _NON_COMPONENT_NAME_HINTS:
        if hint.lower() in normalized:
            return True

    # Most true result-entry prompts are question-style or explicitly outcome-like.
    if "?" not in component_name and "result" not in normalized:
        # Keep conservative: if no explicit result semantics, require manual review.
        return True

    return False


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
) -> dict[str, Any] | None:
    """Ensure a new extracted component has all required fields.

    Called when an extracted component does not match any template component.
    Rejects rows that cannot be deterministically classified as true components.

    Args:
        item: Raw extracted component dict.
        existing_components: Current merged component list (for order numbering).

    Returns:
        Sanitized component dict with required fields present,
        or None if the row is rejected.
    """
    component_name = str(item.get("component_name") or "").strip()
    if not component_name:
        logger.info("Rejecting new component row with empty component_name")
        return None

    if _looks_like_non_component_row(component_name):
        logger.info(
            "Rejecting non-component extracted row '%s' (routed to manual review)",
            component_name,
        )
        return None

    valid_result_types = {"N", "K", "L", "T", "D"}
    raw_rt = str(item.get("result_type", "")).upper().strip()
    if not raw_rt:
        logger.info(
            "Rejecting new component '%s': missing result_type (no default fallback)",
            component_name,
        )
        return None
    if raw_rt not in valid_result_types:
        logger.info(
            "Rejecting new component '%s': invalid result_type '%s'",
            component_name,
            raw_rt,
        )
        return None

    item["result_type"] = raw_rt

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
    protected_keys: set[str] | None = None,
    match_map_out: dict[int, int] | None = None,
    template_locked: bool = False,
) -> tuple[list[dict[str, Any]], int]:
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
        protected_keys: Set of field names where template values are preserved
            during overlay. Conflicts are recorded for SME review.
        match_map_out: If provided, populated with ext_idx -> tpl_idx mapping
            for matched items.
        template_locked: When True, unmatched extracted items are rejected
            (logged at WARNING level) instead of being sanitized and appended.
            Use for known test types where the template defines exact structure.

    Returns:
        Tuple of (merged item list, count of rejected unmatched items).
    """
    merged = copy.deepcopy(template_items)
    matched_indices: set[int] = set()
    rejected_count = 0

    for ext_idx, ext_item in enumerate(extracted_items):
        match_idx = match_fn(ext_item, merged)

        if match_idx is not None:
            matched_indices.add(match_idx)
            if match_map_out is not None:
                match_map_out[ext_idx] = match_idx
            tpl_item = merged[match_idx]

            for key, ext_value in ext_item.items():
                if ext_value is None or ext_value == "":
                    continue

                tpl_value = tpl_item.get(key)
                path = f"{prefix}[{match_idx}].{key}"

                # Protected keys: preserve template value, record conflict
                if (
                    protected_keys
                    and key in protected_keys
                    and tpl_value is not None
                    and tpl_value != ""
                ):
                    if tpl_value != ext_value:
                        conflicts.append(
                            MergeConflict(
                                field_path=path,
                                template_value=tpl_value,
                                extracted_value=ext_value,
                                resolution="Template value preserved (protected key)",
                                resolved_by="SYSTEM",
                            )
                        )
                        logger.info(
                            "Protected key '%s' preserved: template='%s', extraction='%s'",
                            key,
                            tpl_value,
                            ext_value,
                        )
                    continue

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
            # Unmatched extracted item — not in template
            if template_locked:
                item_id = (
                    ext_item.get("name")
                    or ext_item.get("component_name")
                    or ext_item.get("component")
                    or f"index-{ext_idx}"
                )
                logger.warning(
                    "Template-locked: rejecting unmatched %s item '%s' "
                    "(not in template, would have been appended in unlocked mode)",
                    prefix,
                    item_id,
                )
                rejected_count += 1
                continue

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

    return merged, rejected_count


def _build_extraction_to_template_map(
    ext_analyses: list[dict[str, Any]],
    merged_analyses: list[dict[str, Any]],
    match_map: dict[int, int],
) -> dict[str, str]:
    """Build mapping from extraction analysis names to template analysis names.

    When protected_keys prevents name overwrite, the merged analyses still have
    template names. This map lets us rewrite extraction refs to use those names.

    Args:
        ext_analyses: Original extracted analyses list.
        merged_analyses: Analyses list after overlay (template names preserved).
        match_map: ext_idx -> tpl_idx mapping from overlay.

    Returns:
        Mapping of normalized extraction name -> template name.
    """
    name_map: dict[str, str] = {}
    for ext_idx, tpl_idx in match_map.items():
        ext_name = str(ext_analyses[ext_idx].get("name", ""))
        tpl_name = str(merged_analyses[tpl_idx].get("name", ""))
        if ext_name and tpl_name and ext_name != tpl_name:
            norm_ext = _normalize_for_match(ext_name)
            name_map[norm_ext] = tpl_name
            logger.info(
                "Extraction->template analysis map: '%s' -> '%s'",
                ext_name,
                tpl_name,
            )
    return name_map


def _rewrite_extraction_refs(
    extracted_data: dict[str, Any],
    ext_to_tpl_map: dict[str, str],
) -> None:
    """Rewrite analysis refs in extraction data to use template names.

    Uses exact match on normalized name, then unambiguous word-subset match.
    Word-subset is safe because extraction names are unique descriptive names
    (not template-pattern names sharing prefixes like SITE_IDENTITY_*).

    Mutates extracted_data in place.

    Args:
        extracted_data: The extraction result dict with components, etc.
        ext_to_tpl_map: Mapping of normalized extraction name -> template name.
    """
    for sheet_key in ("components", "calc_variables", "calculations"):
        items = extracted_data.get(sheet_key) or []
        for item in items:
            if not isinstance(item, dict):
                continue
            for field in ("analysis", "reference_analysis"):
                raw_ref = item.get(field)
                if not raw_ref:
                    continue
                norm_ref = _normalize_for_match(str(raw_ref))

                # Exact match
                if norm_ref in ext_to_tpl_map:
                    old_ref = item[field]
                    item[field] = ext_to_tpl_map[norm_ref]
                    logger.info(
                        "Rewrote extraction ref: '%s' -> '%s' (exact)",
                        old_ref,
                        item[field],
                    )
                    continue

                # Word-subset match: all words in ref appear in an
                # extraction name. Guarded by:
                #   1. Minimum 3 tokens (blocks generic refs like "Test")
                #   2. Exactly 1 unambiguous match
                ref_words = set(norm_ref.split())
                if len(ref_words) < 3:
                    # Too few tokens — not specific enough for subset match
                    continue
                subset_matches = [
                    tpl_name
                    for ext_norm, tpl_name in ext_to_tpl_map.items()
                    if ref_words.issubset(set(ext_norm.split()))
                ]
                if len(subset_matches) == 1:
                    old_ref = item[field]
                    item[field] = subset_matches[0]
                    logger.info(
                        "Rewrote extraction ref: '%s' -> '%s' (word-subset, %d ref tokens)",
                        old_ref,
                        item[field],
                        len(ref_words),
                    )


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

    # Deep-copy extracted_data to avoid mutating the caller's input
    # (_rewrite_extraction_refs modifies refs in place for the overlay step)
    extracted_data = copy.deepcopy(extracted_data)

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

    # Determine template-locked mode based on test_type.
    # Known test types with registered templates define exact structure;
    # unmatched extraction items should be rejected (not appended).
    template_locked = test_type is not None and test_type != TestType.OTHER
    if template_locked:
        logger.info(
            "Template-locked mode ENABLED for test_type=%s — "
            "unmatched extracted items will be rejected",
            test_type.value,
        )

    # Rejection counters for template-locked mode
    rejected_analyses = 0
    rejected_components = 0
    rejected_calc_vars = 0
    rejected_calculations = 0

    # 2. Overlay extracted data
    # Use `or []` instead of `.get(key, [])` because the key may exist with
    # value None (e.g. when Pydantic validation fails on raw extraction).
    ext_analyses = extracted_data.get("analyses") or []
    ext_components = extracted_data.get("components") or []
    ext_calc_vars = extracted_data.get("calc_variables") or []
    ext_calculations = extracted_data.get("calculations") or []

    # Track original template analysis names before overlay (for rename detection)
    original_analysis_names = [
        str(a.get("name", "")) for a in base.get("analyses", [])
    ]

    # Track extraction->template analysis name mapping for ref rewriting
    ext_to_tpl_name_map: dict[str, str] = {}

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

        analysis_match_map: dict[int, int] = {}
        base["analyses"], rejected_analyses = _overlay_extracted_items(
            base.get("analyses", []),
            ext_analyses,
            _exclusive_match_analysis,
            provenance,
            "analyses",
            conflicts,
            conflict_fields={"analysis_type"},
            sanitize_fn=_sanitize_new_analysis,
            protected_keys={"name"},
            match_map_out=analysis_match_map,
            template_locked=template_locked,
        )

        # Build extraction->template name map for ref rewriting
        ext_to_tpl_name_map = _build_extraction_to_template_map(
            ext_analyses, base.get("analyses", []), analysis_match_map,
        )

    # Build analysis rename map: detect where extraction changed analysis names
    # (with protected_keys={"name"}, renames should not occur, but kept as safety)
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

    # Rewrite extraction refs to use template analysis names before overlay
    if ext_to_tpl_name_map:
        _rewrite_extraction_refs(extracted_data, ext_to_tpl_name_map)

    if ext_components:
        base["components"], rejected_components = _overlay_extracted_items(
            base.get("components", []),
            ext_components,
            _match_component,
            provenance,
            "components",
            conflicts,
            conflict_fields={"result_type", "units", "list_key"},
            sanitize_fn=_sanitize_new_component,
            template_locked=template_locked,
        )

    if ext_calc_vars:
        base["calc_variables"], rejected_calc_vars = _overlay_extracted_items(
            base.get("calc_variables", []),
            ext_calc_vars,
            lambda ext, tpl: _match_calc_var(ext, tpl),
            provenance,
            "calc_variables",
            conflicts,
            sanitize_fn=_sanitize_new_calc_variable,
            template_locked=template_locked,
        )

    if ext_calculations:
        base["calculations"], rejected_calculations = _overlay_extracted_items(
            base.get("calculations", []),
            ext_calculations,
            lambda ext, tpl: _match_calculation(ext, tpl),
            provenance,
            "calculations",
            conflicts,
            sanitize_fn=_sanitize_new_calculation,
            template_locked=template_locked,
        )

    total_rejected = (
        rejected_analyses + rejected_components
        + rejected_calc_vars + rejected_calculations
    )
    if total_rejected > 0:
        logger.warning(
            "Template-locked merge rejected %d unmatched items: "
            "%d analyses, %d components, %d calc_variables, %d calculations",
            total_rejected,
            rejected_analyses,
            rejected_components,
            rejected_calc_vars,
            rejected_calculations,
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
        _normalize_lookup_key,
        sanitize_component_numeric_bounds,
    )

    known_analyses = [
        str(a["name"]) for a in base.get("analyses", [])
        if isinstance(a, dict) and a.get("name")
    ]
    analysis_name_map_norm = _build_analysis_name_map(base.get("analyses", []))

    # Fix D: Inject extraction->template aliases into normalization map
    # Covers full extraction names AND truncated refs from components/etc.
    # that may not have been rewritten by Fix C (belt-and-suspenders).
    if ext_to_tpl_name_map:
        # Inject full extraction analysis names
        for ext_analysis in ext_analyses:
            ext_name = str(ext_analysis.get("name", ""))
            ext_norm = _normalize_for_match(ext_name)
            if ext_norm in ext_to_tpl_name_map:
                tpl_name = ext_to_tpl_name_map[ext_norm]
                lookup_key = _normalize_lookup_key(ext_name)
                if lookup_key not in analysis_name_map_norm:
                    analysis_name_map_norm[lookup_key] = tpl_name
                    logger.info(
                        "Injected extraction alias into normalization map: '%s' -> '%s'",
                        lookup_key,
                        tpl_name,
                    )

        # Also scan for truncated refs in dependent sheets and inject those
        for sheet_key in ("components", "calc_variables", "calculations"):
            for item in (base.get(sheet_key) or []):
                if not isinstance(item, dict):
                    continue
                for field in ("analysis", "reference_analysis"):
                    ref = item.get(field)
                    if not ref or not isinstance(ref, str):
                        continue
                    ref_lookup = _normalize_lookup_key(ref)
                    if ref_lookup in analysis_name_map_norm:
                        continue  # already resolvable
                    # Check if this ref matches a known extraction name
                    # via exact match or word-subset (same guards as Fix C)
                    ref_norm = _normalize_for_match(ref)
                    ref_words = set(ref_norm.split())
                    matched_tpl_name: str | None = None

                    # Exact match
                    if ref_norm in ext_to_tpl_name_map:
                        matched_tpl_name = ext_to_tpl_name_map[ref_norm]
                    # Word-subset match (min 3 tokens, unambiguous)
                    elif len(ref_words) >= 3:
                        subset_hits = [
                            tpl_name
                            for ext_norm, tpl_name in ext_to_tpl_name_map.items()
                            if ref_words.issubset(set(ext_norm.split()))
                        ]
                        if len(subset_hits) == 1:
                            matched_tpl_name = subset_hits[0]

                    if matched_tpl_name:
                        analysis_name_map_norm[ref_lookup] = matched_tpl_name
                        logger.info(
                            "Injected truncated alias into normalization map: '%s' -> '%s'",
                            ref_lookup,
                            matched_tpl_name,
                        )
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
    if template_locked and total_rejected > 0:
        stats["TEMPLATE_LOCKED_REJECTED"] = total_rejected

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
