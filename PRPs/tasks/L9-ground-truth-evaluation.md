# Task L9 — Ground Truth Evaluation: Accuracy Scoring & Quality Dashboard

**Phase:** 7 (Optimization) | **Dependencies:** L7 (normalization), L8 (RAG optimization)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 1-1.5 days

---

## Objective

Build an automated evaluation pipeline that compares AI-generated MDA templates against human-created ground truth XLSX files. This enables measuring the impact of L7 (normalization) and L8 (RAG optimization) quantitatively, and provides a baseline accuracy score for the thesis.

---

## Problem

Currently there's no way to measure extraction/generation quality objectively. The team manually inspects output. With 16 PDF+XLSX ground truth pairs available in `demo_data/`, a systematic comparison is possible.

---

## Demo Data Pairs (Ground Truth)

16 matched pairs where `{name}.pdf` -> `{name}.xlsx`:

| Site | Pair | PDF | XLSX (Ground Truth) |
|------|------|-----|---------------------|
| AND | ACS_DYE | AND_ACS_DYE-LAB-2499.pdf | AND_ACS_DYE-LAB-2499.xlsx |
| AND | ACS_AQ126 | AND_ACS_AQ126-LAB-2349.pdf | AND_ACS_AQ126-AQ126.xlsx |
| AND | ASY_HSUCC | AND_ASY_HSUCC-LAB-2873.pdf | AND_ASY_HSUCC-LAB-2873.xlsx |
| AND | BCMA_CEX | AND_BCMA_CEX-LAB-38176.pdf | AND_BCMA_CEX-LAB-38176.xlsx |
| AND | BI_STRIP | AND_BI_STRIP-LAB-2387.pdf | AND_BI_STRIP-LAB-2387.xlsx |
| FRE | ABRO_B_AS_PU | FRE_ABRO_B_AS_PU-TM8832A.pdf | FRE_ABRO_B_AS_PU-TM8832A.xlsx |
| FRE | BOSU_R_ASSAY | FRE_BOSU_R_ASSAY-TM6687A.pdf | FRE_BOSU_R_ASSAY-TM6687A.xlsx |
| FRE | BOSU_R_RESO | FRE_BOSU_R_RESO-TM6692A.pdf | FRE_BOSU_R_RESO-TM6692A.xlsx |
| FRE | PALBO_ASY_IMPS | FRE_PALBO_ASY_IMPS-TM8439A.pdf | FRE_PALBO_ASY_IMPS-TM8439A.xlsx |
| FRE | QUI_R_ASPU_ALT | FRE_QUI_R_ASPU_ALT-TM0269A.pdf | FRE_QUI_R_ASPU_ALT-TM0269A.xlsx |
| FRE | TAF_CAP_AS_PU | FRE_TAF_CAP_AS_PU-TM9831.pdf | FRE_TAF_CAP_AS_PU-TM9831.xlsx |
| FRE | TAF20_C_APU | FRE_TAF20_C_APU-TM0019B.pdf | FRE_TAF20_C_APU-TM0019B.xlsx |
| TUA | TM0265A | TUA_TM0265A-MCD-006943.pdf | TUA_TM0265A.xlsx |
| TUA | TM1678A | TUA_TM1678A-MCD-055379.pdf | TUA_TM1678A.xlsx |
| TUA | TM2008A | TUA_TM2008A-MCD-056293.pdf | TUA_TM2008A.xlsx |
| TUA | TM7205A | TUA_TM7205A-MCD-057670.pdf | TUA_TM7205A.xlsx |

**Note**: Some XLSX filenames don't exactly match PDF filenames (e.g., `AND_ACS_AQ126-AQ126.xlsx` vs `AND_ACS_AQ126-LAB-2349.pdf`). The evaluator needs to handle this mapping.

Additional files without direct PDF pairs (calculations examples): `TUA_TM7948A`, `TUA_TM6735A_*`, `TUA_TM0717A_*`, `AND_FIX_A280_*`, `AND_FQ538_*`, `AND_USP_LOD_*`, `FRE_KF_*`, `FRE_TM0240B_*`, `FRE_TM9541A_*`

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/evaluator.py` | Parse ground truth XLSX, compare with AI-generated MDA, compute accuracy metrics |
| `scripts/run_evaluation.py` | CLI script: batch-process demo PDFs, compare against ground truth, output scores |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/lims_router.py` | Add `GET /lims/evaluate/{job_id}` endpoint for single-job evaluation (optional) |

---

## Implementation Details

### 1. evaluator.py -- Accuracy Metrics

```python
"""MDA accuracy evaluator: compare AI output against ground truth.

Metrics computed per sheet and aggregated:
- Analysis accuracy: name matching, type correctness
- Component accuracy: name matching, result_type correctness, order matching
- CalcVariable accuracy: reference correctness
- Calculation accuracy: source_code similarity (fuzzy match, not exact)

Overall score: weighted average across sheets.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC -- evaluation errors propagate with full diagnostics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import openpyxl

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

SHEET_WEIGHTS = {
    "analyses": 0.10,        # 10% -- analysis-level metadata
    "components": 0.40,      # 40% -- most critical for LIMS config
    "calc_variables": 0.25,  # 25% -- calculation variable references
    "calculations": 0.25,    # 25% -- LIMS Basic source code
}

# Within components, result_type is weighted 2x
COMPONENT_FIELD_WEIGHTS = {
    "result_type": 2.0,      # Most consequential field
    "order_number": 1.0,
    "units": 1.0,
    "auto_calc": 1.0,
    "list_key": 1.0,
    "uses_instrument": 1.0,
    "instrument_group": 0.5,
    "reportable": 0.5,
}


# ---------------------------------------------------------------------------
# Ground truth column mapping (LabWare -> our schema)
# ---------------------------------------------------------------------------

GROUND_TRUTH_COLUMN_MAP = {
    # Analysis sheet
    "Analysis": "name",
    "NAME": "name",
    "Description": "description",
    "DESCRIPTION": "description",
    "Analysis Type": "analysis_type",
    "ANALYSIS_TYPE": "analysis_type",
    "Group Name": "group_name",
    "GROUP_NAME": "group_name",
    "Active": "active",
    "ACTIVE": "active",
    "QC Samples": "qc_samples",
    "QC_SAMPLES": "qc_samples",

    # Component sheet
    "COMPONENT": "component_name",
    "Component": "component_name",
    "Component Name": "component_name",
    "Result Type": "result_type",
    "RESULT_TYPE": "result_type",
    "Order Number": "order_number",
    "ORDER_NUMBER": "order_number",
    "Units": "units",
    "UNITS": "units",
    "Uses Instrument": "uses_instrument",
    "USES_INSTRUMENT": "uses_instrument",
    "Auto Calc": "auto_calc",
    "AUTO_CALC": "auto_calc",
    "List Key": "list_key",
    "LIST_KEY": "list_key",
    "S/R Pickers": "sr_picker",
    "Instrument Groups": "instrument_group",
    "INSTRUMENT_GROUPS": "instrument_group",
    "Reportable": "reportable",
    "REPORTABLE": "reportable",
    "Places": "places",
    "PLACES": "places",
    "Minimum": "minimum",
    "Maximum": "maximum",

    # CalcVariable sheet
    "Variable Name": "name",
    "Reference Type": "reference_type",
    "Reference Analysis": "reference_analysis",
    "Reference Component": "reference_component",

    # Calculation sheet
    "Calculation Type": "calculation_type",
    "Source Code": "source_code",
    "SOURCE_CODE": "source_code",
}

# Boolean mapping: LabWare uses T/F strings
BOOL_MAP = {
    "T": True, "F": False,
    "TRUE": True, "FALSE": False,
    "True": True, "False": False,
    "t": True, "f": False,
    "Y": True, "N": False,
    "1": True, "0": False,
}


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SheetScore:
    """Accuracy score for one MDA sheet."""

    sheet_name: str
    total_expected: int = 0          # Items in ground truth
    total_generated: int = 0         # Items AI produced
    matched: int = 0                 # Items correctly identified
    field_accuracy: float = 0.0      # Average field-level accuracy (0.0-1.0)
    missing: list[str] = field(default_factory=list)   # In ground truth but not AI
    extra: list[str] = field(default_factory=list)      # In AI but not ground truth
    field_errors: list[dict] = field(default_factory=list)  # Specific mismatches


@dataclass
class EvaluationResult:
    """Complete evaluation result for one PDF."""

    pdf_name: str
    ground_truth_xlsx: str
    sheets: dict[str, SheetScore] = field(default_factory=dict)
    overall_score: float = 0.0       # Weighted average (0.0-1.0)
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Ground truth parsing
# ---------------------------------------------------------------------------


def parse_ground_truth_xlsx(xlsx_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Parse a human-created XLSX into the same dict format as MDATemplate.

    Handles LabWare column naming conventions and maps them to our
    Pydantic field names. Converts T/F booleans and string numbers.

    Args:
        xlsx_path: Path to ground truth XLSX file.

    Returns:
        Dict with keys: analyses, components, calc_variables, calculations.
        Each value is a list of item dicts.

    Raises:
        FileNotFoundError: If xlsx_path does not exist.
    """
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Ground truth XLSX not found: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    result: dict[str, list[dict[str, Any]]] = {
        "analyses": [],
        "components": [],
        "calc_variables": [],
        "calculations": [],
    }

    # Map sheet names to our keys
    sheet_key_map = {
        "analysis": "analyses",
        "component": "components",
        "calc variable": "calc_variables",
        "calculation variables": "calc_variables",
        "calc_variables": "calc_variables",
        "calculation": "calculations",
    }

    for sheet_name in wb.sheetnames:
        normalized_name = sheet_name.lower().strip()
        target_key = sheet_key_map.get(normalized_name)
        if target_key is None:
            continue

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue

        headers = [str(h).strip() if h else "" for h in rows[0]]
        mapped_headers = [
            GROUND_TRUTH_COLUMN_MAP.get(h, h.lower().replace(" ", "_"))
            for h in headers
        ]

        for row in rows[1:]:
            if all(c is None for c in row):
                continue

            item: dict[str, Any] = {}
            for col_idx, value in enumerate(row):
                if col_idx >= len(mapped_headers):
                    break
                field_name = mapped_headers[col_idx]
                item[field_name] = _convert_value(value, field_name)

            # Add analysis reference for components/calc_vars/calcs
            if target_key != "analyses" and "analysis" not in item:
                # Some XLSX files have Analysis as first column across all sheets
                for h_idx, h in enumerate(mapped_headers):
                    if h in ("analysis", "name") and h_idx < len(row):
                        item["analysis"] = str(row[h_idx] or "")
                        break

            result[target_key].append(item)

    wb.close()

    logger.info(
        "Parsed ground truth '%s': %d analyses, %d components, %d calc_vars, %d calcs",
        xlsx_path.name,
        len(result["analyses"]),
        len(result["components"]),
        len(result["calc_variables"]),
        len(result["calculations"]),
    )

    return result


def _convert_value(value: Any, field_name: str) -> Any:
    """Convert a LabWare cell value to the appropriate Python type.

    Args:
        value: Raw cell value.
        field_name: Target field name for type inference.

    Returns:
        Converted value.
    """
    if value is None:
        return None

    str_val = str(value).strip()

    # Boolean fields
    if field_name in (
        "auto_calc", "uses_instrument", "reportable", "active",
        "optional", "allow_out_of_range",
    ):
        if str_val in BOOL_MAP:
            return BOOL_MAP[str_val]

    # Numeric fields
    if field_name in ("order_number", "places", "version"):
        try:
            return int(float(str_val)) if str_val else None
        except (ValueError, TypeError):
            return str_val

    if field_name in ("minimum", "maximum"):
        try:
            return float(str_val) if str_val else None
        except (ValueError, TypeError):
            return str_val

    return str_val if str_val else None


# ---------------------------------------------------------------------------
# Comparison functions
# ---------------------------------------------------------------------------


def compare_analyses(
    generated: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> SheetScore:
    """Compare generated analyses against ground truth.

    Match by name (case-insensitive), check: analysis_type, group_name, active.

    Args:
        generated: AI-generated analysis dicts.
        ground_truth: Human-created analysis dicts.

    Returns:
        SheetScore with accuracy metrics.
    """
    score = SheetScore(
        sheet_name="analyses",
        total_expected=len(ground_truth),
        total_generated=len(generated),
    )

    gt_by_name = {
        str(a.get("name", "")).upper(): a for a in ground_truth
    }
    gen_by_name = {
        str(a.get("name", "")).upper(): a for a in generated
    }

    for name, gt_item in gt_by_name.items():
        if name in gen_by_name:
            score.matched += 1
            # Check field accuracy
            gen_item = gen_by_name[name]
            errors = _compare_fields(
                gen_item, gt_item,
                fields=["analysis_type", "group_name", "active", "description"],
            )
            score.field_errors.extend(errors)
        else:
            # Try fuzzy match
            best_match = _fuzzy_find(name, gen_by_name.keys())
            if best_match:
                score.matched += 1
                score.field_errors.append({
                    "item": name,
                    "field": "name",
                    "expected": name,
                    "got": best_match,
                    "note": "fuzzy match",
                })
            else:
                score.missing.append(name)

    for name in gen_by_name:
        if name not in gt_by_name:
            score.extra.append(name)

    # Calculate field accuracy
    total_checks = max(score.matched * 4, 1)  # 4 fields per analysis
    errors_count = len(score.field_errors)
    score.field_accuracy = max(0.0, 1.0 - errors_count / total_checks)

    return score


def compare_components(
    generated: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> SheetScore:
    """Compare components -- the most complex and important sheet.

    Match by (analysis, component_name) with fuzzy matching.
    Check: result_type (critical, 2x weight), order_number, units,
    auto_calc, list_key, uses_instrument, instrument_group.

    Args:
        generated: AI-generated component dicts.
        ground_truth: Human-created component dicts.

    Returns:
        SheetScore with weighted accuracy metrics.
    """
    score = SheetScore(
        sheet_name="components",
        total_expected=len(ground_truth),
        total_generated=len(generated),
    )

    def _comp_key(c: dict) -> str:
        analysis = str(c.get("analysis", "")).upper()
        name = str(c.get("component_name", "")).upper()
        return f"{analysis}::{name}"

    gt_by_key = {_comp_key(c): c for c in ground_truth}
    gen_by_key = {_comp_key(c): c for c in generated}

    weighted_correct = 0.0
    weighted_total = 0.0

    for key, gt_item in gt_by_key.items():
        if key in gen_by_key:
            score.matched += 1
            gen_item = gen_by_key[key]

            # Check weighted fields
            for field_name, weight in COMPONENT_FIELD_WEIGHTS.items():
                weighted_total += weight
                gt_val = gt_item.get(field_name)
                gen_val = gen_item.get(field_name)
                if _values_match(gt_val, gen_val):
                    weighted_correct += weight
                else:
                    score.field_errors.append({
                        "item": key,
                        "field": field_name,
                        "expected": gt_val,
                        "got": gen_val,
                        "weight": weight,
                    })
        else:
            score.missing.append(key)

    for key in gen_by_key:
        if key not in gt_by_key:
            score.extra.append(key)

    # Weighted field accuracy
    score.field_accuracy = (
        weighted_correct / weighted_total if weighted_total > 0 else 0.0
    )

    return score


def compare_calc_variables(
    generated: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> SheetScore:
    """Compare calculation variables.

    Match by (analysis, component, name). Check reference fields.

    Args:
        generated: AI-generated calc variable dicts.
        ground_truth: Human-created calc variable dicts.

    Returns:
        SheetScore with accuracy metrics.
    """
    score = SheetScore(
        sheet_name="calc_variables",
        total_expected=len(ground_truth),
        total_generated=len(generated),
    )

    def _cv_key(cv: dict) -> str:
        analysis = str(cv.get("analysis", "")).upper()
        comp = str(cv.get("component", "")).upper()
        name = str(cv.get("name", "")).upper()
        return f"{analysis}::{comp}::{name}"

    gt_by_key = {_cv_key(cv): cv for cv in ground_truth}
    gen_by_key = {_cv_key(cv): cv for cv in generated}

    for key, gt_item in gt_by_key.items():
        if key in gen_by_key:
            score.matched += 1
            errors = _compare_fields(
                gen_by_key[key], gt_item,
                fields=["reference_type", "reference_analysis", "reference_component"],
            )
            score.field_errors.extend(errors)
        else:
            score.missing.append(key)

    for key in gen_by_key:
        if key not in gt_by_key:
            score.extra.append(key)

    total_checks = max(score.matched * 3, 1)
    score.field_accuracy = max(0.0, 1.0 - len(score.field_errors) / total_checks)

    return score


def compare_calculations(
    generated: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> SheetScore:
    """Compare calculations with fuzzy source_code matching.

    Exact code match is unlikely; use normalized comparison
    (strip whitespace, lowercase, compare logic structure).

    Args:
        generated: AI-generated calculation dicts.
        ground_truth: Human-created calculation dicts.

    Returns:
        SheetScore with accuracy metrics.
    """
    score = SheetScore(
        sheet_name="calculations",
        total_expected=len(ground_truth),
        total_generated=len(generated),
    )

    def _calc_key(c: dict) -> str:
        analysis = str(c.get("analysis", "")).upper()
        comp = str(c.get("component", "")).upper()
        return f"{analysis}::{comp}"

    gt_by_key = {_calc_key(c): c for c in ground_truth}
    gen_by_key = {_calc_key(c): c for c in generated}

    code_similarity_sum = 0.0

    for key, gt_item in gt_by_key.items():
        if key in gen_by_key:
            score.matched += 1
            gen_item = gen_by_key[key]

            # Fuzzy compare source_code
            gt_code = _normalize_code(str(gt_item.get("source_code", "")))
            gen_code = _normalize_code(str(gen_item.get("source_code", "")))

            similarity = SequenceMatcher(None, gt_code, gen_code).ratio()
            code_similarity_sum += similarity

            if similarity < 0.8:
                score.field_errors.append({
                    "item": key,
                    "field": "source_code",
                    "similarity": round(similarity, 3),
                    "expected_length": len(gt_code),
                    "got_length": len(gen_code),
                })

            # Check calculation_type
            if not _values_match(
                gt_item.get("calculation_type"),
                gen_item.get("calculation_type"),
            ):
                score.field_errors.append({
                    "item": key,
                    "field": "calculation_type",
                    "expected": gt_item.get("calculation_type"),
                    "got": gen_item.get("calculation_type"),
                })
        else:
            score.missing.append(key)

    for key in gen_by_key:
        if key not in gt_by_key:
            score.extra.append(key)

    # Field accuracy based on code similarity + type accuracy
    if score.matched > 0:
        avg_code_sim = code_similarity_sum / score.matched
        type_errors = sum(
            1 for e in score.field_errors if e.get("field") == "calculation_type"
        )
        type_accuracy = 1.0 - type_errors / max(score.matched, 1)
        score.field_accuracy = (avg_code_sim * 0.7 + type_accuracy * 0.3)
    else:
        score.field_accuracy = 0.0

    return score


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------


def evaluate_mda(
    generated_mda: dict[str, Any],
    ground_truth_xlsx_path: Path,
    pdf_name: str = "",
) -> EvaluationResult:
    """Full evaluation: parse ground truth, compare all 4 sheets, aggregate.

    Args:
        generated_mda: AI-generated MDA template dict (from MDATemplate.model_dump()).
        ground_truth_xlsx_path: Path to human-created ground truth XLSX.
        pdf_name: Name of the source PDF (for reporting).

    Returns:
        EvaluationResult with per-sheet scores and weighted overall score.
    """
    ground_truth = parse_ground_truth_xlsx(ground_truth_xlsx_path)

    result = EvaluationResult(
        pdf_name=pdf_name or "unknown",
        ground_truth_xlsx=ground_truth_xlsx_path.name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Compare each sheet
    result.sheets["analyses"] = compare_analyses(
        generated_mda.get("analyses", []),
        ground_truth.get("analyses", []),
    )
    result.sheets["components"] = compare_components(
        generated_mda.get("components", []),
        ground_truth.get("components", []),
    )
    result.sheets["calc_variables"] = compare_calc_variables(
        generated_mda.get("calc_variables", []),
        ground_truth.get("calc_variables", []),
    )
    result.sheets["calculations"] = compare_calculations(
        generated_mda.get("calculations", []),
        ground_truth.get("calculations", []),
    )

    # Weighted overall score
    # Combines: item recall (matched/expected) and field accuracy
    weighted_score = 0.0
    for sheet_name, weight in SHEET_WEIGHTS.items():
        sheet_score = result.sheets.get(sheet_name)
        if sheet_score and sheet_score.total_expected > 0:
            recall = sheet_score.matched / sheet_score.total_expected
            combined = (recall * 0.5 + sheet_score.field_accuracy * 0.5)
            weighted_score += weight * combined
        # If no ground truth for this sheet, don't penalize

    result.overall_score = round(weighted_score, 4)

    logger.info(
        "Evaluation '%s': overall=%.2f, analyses=%.2f, components=%.2f, "
        "calc_vars=%.2f, calcs=%.2f",
        pdf_name,
        result.overall_score,
        result.sheets["analyses"].field_accuracy,
        result.sheets["components"].field_accuracy,
        result.sheets["calc_variables"].field_accuracy,
        result.sheets["calculations"].field_accuracy,
    )

    return result


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _compare_fields(
    generated: dict[str, Any],
    ground_truth: dict[str, Any],
    fields: list[str],
) -> list[dict[str, Any]]:
    """Compare specific fields between generated and ground truth items.

    Returns list of error dicts for mismatched fields.
    """
    errors = []
    for f in fields:
        gt_val = ground_truth.get(f)
        gen_val = generated.get(f)
        if not _values_match(gt_val, gen_val):
            errors.append({
                "field": f,
                "expected": gt_val,
                "got": gen_val,
            })
    return errors


def _values_match(expected: Any, actual: Any) -> bool:
    """Compare two values with type-flexible matching.

    Handles: None vs empty string, case-insensitive strings,
    numeric string vs int/float, T/F vs bool.
    """
    if expected is None and actual is None:
        return True
    if expected is None and actual in ("", None, "None"):
        return True
    if actual is None and expected in ("", None, "None"):
        return True

    # String comparison (case-insensitive)
    str_exp = str(expected).strip().upper() if expected is not None else ""
    str_act = str(actual).strip().upper() if actual is not None else ""

    if str_exp == str_act:
        return True

    # Boolean comparison
    if str_exp in ("TRUE", "T", "1") and str_act in ("TRUE", "T", "1"):
        return True
    if str_exp in ("FALSE", "F", "0") and str_act in ("FALSE", "F", "0"):
        return True

    return False


def _fuzzy_find(
    name: str,
    candidates: Any,
    threshold: float = 0.8,
) -> str | None:
    """Find the best fuzzy match for a name in candidates.

    Args:
        name: Name to search for.
        candidates: Iterable of candidate names.
        threshold: Minimum similarity ratio (0.0-1.0).

    Returns:
        Best matching candidate name, or None if below threshold.
    """
    best_match = None
    best_ratio = 0.0

    for candidate in candidates:
        ratio = SequenceMatcher(None, name, str(candidate)).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = str(candidate)

    return best_match if best_ratio >= threshold else None


def _normalize_code(code: str) -> str:
    """Normalize LIMS Basic code for fuzzy comparison.

    Strips whitespace, lowercases, removes comments, normalizes
    variable names to allow structural comparison.
    """
    import re

    code = code.lower()
    # Remove single-line comments (LIMS Basic uses ')
    code = re.sub(r"'[^\n]*", "", code)
    # Normalize whitespace
    code = re.sub(r"\s+", " ", code).strip()
    return code
```

**Scoring weights**: Analysis (10%), Component (40%), CalcVariable (25%), Calculation (25%).
Component `result_type` is weighted 2x within the Component sheet score because it's the most consequential field for LIMS configuration.

### 2. PDF-to-XLSX Pair Mapping

The evaluator needs a hardcoded mapping for pairs where filenames don't match:

```python
# In run_evaluation.py or evaluator.py

PAIR_MAPPING: dict[str, str] = {
    # PDF stem -> XLSX stem
    "AND_ACS_DYE-LAB-2499": "AND_ACS_DYE-LAB-2499",
    "AND_ACS_AQ126-LAB-2349": "AND_ACS_AQ126-AQ126",
    "AND_ASY_HSUCC-LAB-2873": "AND_ASY_HSUCC-LAB-2873",
    "AND_BCMA_CEX-LAB-38176": "AND_BCMA_CEX-LAB-38176",
    "AND_BI_STRIP-LAB-2387": "AND_BI_STRIP-LAB-2387",
    "FRE_ABRO_B_AS_PU-TM8832A": "FRE_ABRO_B_AS_PU-TM8832A",
    "FRE_BOSU_R_ASSAY-TM6687A": "FRE_BOSU_R_ASSAY-TM6687A",
    "FRE_BOSU_R_RESO-TM6692A": "FRE_BOSU_R_RESO-TM6692A",
    "FRE_PALBO_ASY_IMPS-TM8439A": "FRE_PALBO_ASY_IMPS-TM8439A",
    "FRE_QUI_R_ASPU_ALT-TM0269A": "FRE_QUI_R_ASPU_ALT-TM0269A",
    "FRE_TAF_CAP_AS_PU-TM9831": "FRE_TAF_CAP_AS_PU-TM9831",
    "FRE_TAF20_C_APU-TM0019B": "FRE_TAF20_C_APU-TM0019B",
    "TUA_TM0265A-MCD-006943": "TUA_TM0265A",
    "TUA_TM1678A-MCD-055379": "TUA_TM1678A",
    "TUA_TM2008A-MCD-056293": "TUA_TM2008A",
    "TUA_TM7205A-MCD-057670": "TUA_TM7205A",
}
```

### 3. run_evaluation.py -- Batch Evaluation Script

```python
#!/usr/bin/env python3
"""Batch evaluate AI extraction quality against ground truth.

Usage:
    python scripts/run_evaluation.py                         # All pairs
    python scripts/run_evaluation.py AND_ACS_DYE             # Single pair (prefix match)
    python scripts/run_evaluation.py --output results.json   # Save results to file
    python scripts/run_evaluation.py --no-extract             # Skip extraction, use cached jobs

For each PDF+XLSX pair:
1. Run extraction: POST /lims/extract with PDF
2. Wait for job to reach PENDING_REVIEW or GENERATING state
3. Get MDA template from job status
4. Parse ground truth XLSX
5. Compare with evaluator.evaluate_mda()
6. Print score table and save detailed results

GAMP-5 Category 5: Custom pharmaceutical software component.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx


DEMO_DATA_DIR = Path("demo_data")
API_BASE = "http://localhost:8080/lims"
PAIR_MAPPING = { ... }  # As above


def extract_and_evaluate(
    pdf_path: Path,
    ground_truth_xlsx: Path,
    api_base: str = API_BASE,
) -> dict:
    """Extract from PDF via API, then evaluate against ground truth.

    Args:
        pdf_path: Path to input PDF.
        ground_truth_xlsx: Path to human-created XLSX.
        api_base: Base URL for LIMS API.

    Returns:
        Dict with job_id, scores, and detailed results.
    """
    # 1. Upload PDF
    with open(pdf_path, "rb") as f:
        response = httpx.post(
            f"{api_base}/extract",
            files={"file": (pdf_path.name, f, "application/pdf")},
            timeout=300.0,  # 5 min timeout for extraction
        )
    response.raise_for_status()
    job_data = response.json()
    job_id = job_data["job_id"]

    # 2. Get MDA template from job
    status_response = httpx.get(f"{api_base}/status/{job_id}")
    status_response.raise_for_status()
    mda_template = status_response.json().get("mda_template", {})

    if not mda_template:
        return {
            "pdf": pdf_path.name,
            "error": f"No MDA template generated (status: {job_data.get('status')})",
        }

    # 3. Evaluate
    from main.src.lims.evaluator import evaluate_mda
    result = evaluate_mda(
        generated_mda=mda_template,
        ground_truth_xlsx_path=ground_truth_xlsx,
        pdf_name=pdf_path.name,
    )

    return {
        "pdf": pdf_path.name,
        "xlsx": ground_truth_xlsx.name,
        "job_id": job_id,
        "overall": result.overall_score,
        "analyses": result.sheets["analyses"].field_accuracy,
        "components": result.sheets["components"].field_accuracy,
        "calc_variables": result.sheets["calc_variables"].field_accuracy,
        "calculations": result.sheets["calculations"].field_accuracy,
        "details": {
            sheet_name: {
                "expected": s.total_expected,
                "generated": s.total_generated,
                "matched": s.matched,
                "missing": s.missing,
                "extra": s.extra,
                "errors": s.field_errors,
            }
            for sheet_name, s in result.sheets.items()
        },
    }


def print_results_table(results: list[dict]) -> None:
    """Print formatted results table to stdout."""
    header = (
        f"{'PDF':<40} {'Overall':>8} {'Analysis':>9} "
        f"{'Component':>10} {'CalcVar':>8} {'Calc':>6}"
    )
    print("\n=== AI4LIMS Evaluation Results ===\n")
    print(header)
    print("-" * len(header))

    for r in results:
        if "error" in r:
            print(f"{r['pdf']:<40} ERROR: {r['error']}")
        else:
            print(
                f"{r['pdf']:<40} {r['overall']:>8.2f} {r['analyses']:>9.2f} "
                f"{r['components']:>10.2f} {r['calc_variables']:>8.2f} "
                f"{r['calculations']:>6.2f}"
            )

    # Average row
    valid = [r for r in results if "error" not in r]
    if valid:
        avg_overall = sum(r["overall"] for r in valid) / len(valid)
        avg_analyses = sum(r["analyses"] for r in valid) / len(valid)
        avg_components = sum(r["components"] for r in valid) / len(valid)
        avg_cv = sum(r["calc_variables"] for r in valid) / len(valid)
        avg_calc = sum(r["calculations"] for r in valid) / len(valid)
        print("-" * len(header))
        print(
            f"{'AVERAGE':<40} {avg_overall:>8.2f} {avg_analyses:>9.2f} "
            f"{avg_components:>10.2f} {avg_cv:>8.2f} {avg_calc:>6.2f}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate AI4LIMS MDA quality")
    parser.add_argument("filter", nargs="?", help="Filter by PDF name prefix")
    parser.add_argument("--output", "-o", help="Save results to JSON file")
    parser.add_argument("--api", default=API_BASE, help="API base URL")
    args = parser.parse_args()

    results = []
    for pdf_stem, xlsx_stem in PAIR_MAPPING.items():
        if args.filter and args.filter.upper() not in pdf_stem.upper():
            continue

        pdf_path = DEMO_DATA_DIR / f"{pdf_stem}.pdf"
        xlsx_path = DEMO_DATA_DIR / f"{xlsx_stem}.xlsx"

        if not pdf_path.exists():
            print(f"SKIP: {pdf_path} not found")
            continue
        if not xlsx_path.exists():
            print(f"SKIP: {xlsx_path} (ground truth) not found")
            continue

        print(f"Evaluating: {pdf_path.name} ...", end=" ", flush=True)
        try:
            result = extract_and_evaluate(pdf_path, xlsx_path, args.api)
            results.append(result)
            score = result.get("overall", "ERR")
            print(f"score={score}")
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({"pdf": pdf_path.name, "error": str(e)})

    print_results_table(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
```

**Expected output**:

```
=== AI4LIMS Evaluation Results ===

PDF                                      Overall  Analysis  Component  CalcVar   Calc
--------------------------------------------------------------------------------
AND_ACS_DYE-LAB-2499.pdf                    0.72      1.00       0.65     0.68   0.55
FRE_BOSU_R_ASSAY-TM6687A.pdf                0.68      0.90       0.60     0.72   0.50
...                                           ...       ...        ...      ...    ...
--------------------------------------------------------------------------------
AVERAGE                                      0.70      0.95       0.63     0.70   0.53
```

---

## Testing Strategy

```bash
# 1. Unit test ground truth parsing
uv run pytest main/tests/lims/test_evaluator.py -v

# 2. Test evaluation on one known pair (no API needed -- direct function call)
python -c "
from pathlib import Path
from main.src.lims.evaluator import parse_ground_truth_xlsx
gt = parse_ground_truth_xlsx(Path('demo_data/AND_ACS_DYE-LAB-2499.xlsx'))
print(f'Analyses: {len(gt[\"analyses\"])}')
print(f'Components: {len(gt[\"components\"])}')
print(f'CalcVars: {len(gt[\"calc_variables\"])}')
print(f'Calcs: {len(gt[\"calculations\"])}')
"

# 3. Full batch evaluation (requires API keys + running server)
python scripts/run_evaluation.py --output evaluation_baseline.json

# 4. Single pair evaluation
python scripts/run_evaluation.py AND_ACS_DYE

# 5. Compare before/after optimizations
python scripts/run_evaluation.py --output evaluation_optimized.json
# diff evaluation_baseline.json evaluation_optimized.json

# 6. All existing tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] Ground truth XLSX parser correctly reads LabWare column format for all 16 pairs
- [ ] Evaluation produces scores for all 4 sheets with clear field-level error reporting
- [ ] Batch evaluation completes for at least 5 PDF+XLSX pairs
- [ ] Baseline accuracy score documented (pre-optimization)
- [ ] Post-optimization scores measurably improve after L7+L8
- [ ] All existing LIMS tests pass

---

## Task Dependency Graph

```
Phase 6: Full HITL UI -- DONE (L6.1-L6.4)
  |
  =================== GATE 6: FUNCTIONAL ===================
  |
Phase 7: Optimization
  L7 (extraction normalization + SDK)  ----------------+
  L8 (RAG: chunking + hybrid + reranking) -------------+
                                                        |
                                              L9 (ground truth evaluation) <-- L7, L8
                                                        |
  =================== GATE 7: QUALITY MEASURED ===================
```

L7 and L8 can be done in parallel. L9 depends on both (needs pipeline improvements to measure improvement vs baseline).

---

## Verification After All Phase 7 Tasks

1. Run `python scripts/run_evaluation.py` -- baseline scores
2. Apply L7 normalization -- re-run evaluation -- compare
3. Apply L8 RAG improvements -- re-run evaluation -- compare
4. Full E2E: upload PDF -> better extraction -> better RAG context -> better MDA -> export XLSX
5. `uv run pytest main/tests/lims/ -v` -- all tests pass
6. Thesis pipeline unaffected: `uv run pytest main/tests/ -v`
