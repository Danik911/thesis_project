from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_SRC_ROOT = REPO_ROOT / "main"
if str(MAIN_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(MAIN_SRC_ROOT))

from src.lims.config import get_lims_config
from src.lims.langfuse_tracing import flush_lims_langfuse, get_lims_langfuse
from src.lims.pdf_extractor import extract_mda_from_pdf


MANIFEST_SCHEMA_VERSION = "1.0.0"


def _counts(mda: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(mda, dict):
        return {
            "analyses": 0,
            "components": 0,
            "calc_variables": 0,
            "calculations": 0,
        }
    return {
        "analyses": len(mda.get("analyses", []) or []),
        "components": len(mda.get("components", []) or []),
        "calc_variables": len(mda.get("calc_variables", []) or []),
        "calculations": len(mda.get("calculations", []) or []),
    }


def _flatten_paths(data: Any, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            child = f"{prefix}.{key}" if prefix else key
            paths.add(child)
            paths |= _flatten_paths(value, child)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            child = f"{prefix}[{index}]"
            paths.add(child)
            paths |= _flatten_paths(value, child)
    return paths


def _shape_similarity(a: dict[str, Any] | None, b: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {
            "jaccard": 0.0,
            "intersection": 0,
            "a_paths": 0,
            "b_paths": 0,
        }

    a_paths = _flatten_paths(a)
    b_paths = _flatten_paths(b)
    intersection = len(a_paths & b_paths)
    union = len(a_paths | b_paths)
    return {
        "jaccard": (intersection / union) if union else 0.0,
        "intersection": intersection,
        "a_paths": len(a_paths),
        "b_paths": len(b_paths),
    }


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().upper().split())


def _extract_method_family(stem: str) -> str | None:
    match = re.match(r"([A-Z]{3}_[A-Z0-9]+(?:_[A-Z0-9]+){1,3})", stem.upper())
    if match:
        return match.group(1)
    return None


def _canonical_analysis_name(name: Any, method_family: str | None, alias_mode: bool) -> str:
    normalized = _normalize_text(name)
    if not alias_mode or not method_family:
        return normalized

    if normalized == "SITE_IDENTITY":
        return method_family
    if normalized == "SITE_IDENTITY_CTL":
        return f"{method_family}_CTL"
    if normalized == "SITE_IDENTITY_META":
        return f"{method_family}_META"
    return normalized


def _sheet_key(
    sheet_name: str,
    record: dict[str, Any],
    *,
    alias_mode: bool,
    method_family: str | None,
) -> tuple[str, ...] | None:
    if not isinstance(record, dict):
        return None

    analysis = _canonical_analysis_name(record.get("analysis") or record.get("name"), method_family, alias_mode)

    if sheet_name == "analyses":
        return (analysis,)

    if sheet_name == "components":
        component_name = _normalize_text(record.get("component_name"))
        if not component_name:
            return None
        return (analysis, component_name)

    if sheet_name == "calc_variables":
        name = _normalize_text(record.get("name"))
        if not name:
            return None
        return (analysis, name)

    if sheet_name == "calculations":
        component = _normalize_text(record.get("component"))
        source_code = _normalize_text(record.get("source_code"))
        if not component and not source_code:
            return None
        return (analysis, component, source_code)

    return None


def _compare_sheet(
    ground_truth_items: list[dict[str, Any]],
    app_items: list[dict[str, Any]],
    *,
    sheet_name: str,
    alias_mode: bool,
    method_family: str | None,
) -> dict[str, Any]:
    gt_keys = {
        key
        for item in ground_truth_items
        if (key := _sheet_key(sheet_name, item, alias_mode=alias_mode, method_family=method_family))
        is not None
    }
    app_keys = {
        key
        for item in app_items
        if (key := _sheet_key(sheet_name, item, alias_mode=alias_mode, method_family=method_family))
        is not None
    }

    matched = gt_keys & app_keys
    precision = len(matched) / len(app_keys) if app_keys else 0.0
    recall = len(matched) / len(gt_keys) if gt_keys else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    missing = sorted(gt_keys - app_keys)
    extra = sorted(app_keys - gt_keys)

    return {
        "ground_truth_count": len(gt_keys),
        "app_count": len(app_keys),
        "matched_count": len(matched),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "missing_items": [list(item) for item in missing[:50]],
        "extra_items": [list(item) for item in extra[:50]],
    }


def _compare_ground_truth(
    ground_truth: dict[str, Any],
    app_mda: dict[str, Any] | None,
    *,
    method_family: str | None,
) -> dict[str, Any]:
    app_payload = app_mda if isinstance(app_mda, dict) else {}

    sheets = ("analyses", "components", "calc_variables", "calculations")
    strict: dict[str, Any] = {}
    alias_aware: dict[str, Any] = {}
    for sheet in sheets:
        gt_items = ground_truth.get(sheet, []) or []
        app_items = app_payload.get(sheet, []) or []
        strict[sheet] = _compare_sheet(
            gt_items,
            app_items,
            sheet_name=sheet,
            alias_mode=False,
            method_family=method_family,
        )
        alias_aware[sheet] = _compare_sheet(
            gt_items,
            app_items,
            sheet_name=sheet,
            alias_mode=True,
            method_family=method_family,
        )

    return {
        "method_family": method_family,
        "strict": strict,
        "alias_aware": alias_aware,
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_optional_json(path_arg: str) -> dict[str, Any] | None:
    if not path_arg:
        return None
    path = Path(path_arg)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON at {path} must be an object")
    return payload


def _build_mismatch_inventory(entity_compare: dict[str, Any]) -> dict[str, Any]:
    inventory: dict[str, Any] = {"strict": {}, "alias_aware": {}}
    for mode in ("strict", "alias_aware"):
        mode_payload = entity_compare.get(mode, {})
        mode_inventory: dict[str, Any] = {}
        for sheet in ("analyses", "components", "calc_variables", "calculations"):
            sheet_payload = mode_payload.get(sheet, {})
            mode_inventory[sheet] = {
                "missing_count": len(sheet_payload.get("missing_items", [])),
                "extra_count": len(sheet_payload.get("extra_items", [])),
                "missing_items": sheet_payload.get("missing_items", []),
                "extra_items": sheet_payload.get("extra_items", []),
            }
        inventory[mode] = mode_inventory
    return inventory


def _write_canonical_evidence_package(
    *,
    run_dir: Path,
    run_id: str,
    timestamp_utc: str,
    pdf_path: Path,
    direct_result: dict[str, Any],
    app_result: dict[str, Any],
    comparison: dict[str, Any],
    ground_truth_json_path: Path | None,
    reviewer_decisions: dict[str, Any] | None,
) -> dict[str, Any]:
    method_family = _extract_method_family(pdf_path.stem)
    input_hashes = {
        "pdf_sha256": _sha256_file(pdf_path),
    }
    if ground_truth_json_path is not None:
        input_hashes["ground_truth_json_sha256"] = _sha256_file(ground_truth_json_path)

    entity_compare = comparison.get("ground_truth_vs_app_entity_compare", {})
    mismatch_inventory = _build_mismatch_inventory(entity_compare) if entity_compare else {}

    trace_snapshot = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "trace": {
            "app_trace_id": app_result.get("trace_id"),
            "app_trace_url": app_result.get("trace_url"),
            "direct_extraction_trace": direct_result.get("extraction_trace"),
        },
    }

    evidence_manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "inputs": {
            "pdf_path": str(pdf_path),
            "ground_truth_json_path": str(ground_truth_json_path) if ground_truth_json_path else None,
            "method_family": method_family,
            "hashes": input_hashes,
        },
        "traceability": {
            "app_trace_id": app_result.get("trace_id"),
            "app_trace_url": app_result.get("trace_url"),
            "direct_extraction_trace": direct_result.get("extraction_trace"),
        },
        "metrics": {
            "direct_counts": comparison.get("direct_counts"),
            "app_counts": comparison.get("app_counts"),
            "shape": {
                "direct_vs_app": comparison.get("direct_vs_app_shape"),
                "ground_truth_vs_app": comparison.get("ground_truth_vs_app_shape"),
                "ground_truth_vs_direct": comparison.get("ground_truth_vs_direct_shape"),
            },
            "ground_truth_vs_app_entity_compare": entity_compare,
        },
        "mismatch_inventory": mismatch_inventory,
        "review": {
            "reviewer_decisions": reviewer_decisions if reviewer_decisions is not None else [],
        },
        "artifacts": {
            "direct_result_json": str(run_dir / "direct_result.json"),
            "app_result_json": str(run_dir / "app_result.json"),
            "comparison_json": str(run_dir / "comparison.json"),
            "trace_snapshot_json": str(run_dir / "trace_snapshot.json"),
        },
    }

    (run_dir / "trace_snapshot.json").write_text(
        json.dumps(trace_snapshot, indent=2, default=str),
        encoding="utf-8",
    )
    (run_dir / "evidence_manifest.json").write_text(
        json.dumps(evidence_manifest, indent=2, default=str),
        encoding="utf-8",
    )

    return evidence_manifest


def run_direct_extraction(pdf_path: Path) -> dict[str, Any]:
    pdf_content = pdf_path.read_bytes()
    cfg = get_lims_config()

    top_cfg = cfg.model_copy(
        update={
            "extraction_mode": "premium",
            "extraction_target": "per_doc",
            "extract_parse_model": "anthropic-sonnet-4.5",
            "extract_model": "openai-gpt-5",
            "extract_cite_sources": True,
            "extract_use_reasoning": True,
            "extract_confidence_scores": False,
            "extract_num_pages_context": 3,
            "extract_chunk_mode": "section",
            "extract_high_resolution_mode": True,
            "extract_invalidate_cache": False,
        }
    )

    return extract_mda_from_pdf(
        pdf_content=pdf_content,
        filename=pdf_path.name,
        config=top_cfg,
    )


def run_app_extraction(pdf_path: Path, base_url: str) -> dict[str, Any]:
    with pdf_path.open("rb") as file_obj:
        response = requests.post(
            f"{base_url.rstrip('/')}/lims/extract",
            files={"file": (pdf_path.name, file_obj, "application/pdf")},
            timeout=1800,
        )
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv(".env.local", override=True)

    parser = argparse.ArgumentParser(
        description="Compare direct top-model LlamaExtract vs app /lims/extract output with Langfuse trace logging."
    )
    parser.add_argument("--pdf", required=True, help="Path to PDF input")
    parser.add_argument("--base-url", default="http://localhost:8080", help="LIMS API base URL")
    parser.add_argument(
        "--out-dir",
        default="demo_data/e2e_outputs",
        help="Directory to write comparison artifacts",
    )
    parser.add_argument(
        "--llama-cloud-results-dir",
        default="demo_data/llama_cloud_results",
        help="Directory to persist direct LlamaCloud extraction outputs",
    )
    parser.add_argument(
        "--langfuse-traces-dir",
        default="demo_data/langfuse",
        help="Directory to persist Langfuse trace reference artifacts",
    )
    parser.add_argument(
        "--ground-truth-md-dir",
        default="demo_data/testing_data_ground_truth",
        help="Directory containing parsed ground-truth markdown files",
    )
    parser.add_argument(
        "--ground-truth-json",
        default="",
        help="Optional JSON file for ground-truth MDA output comparison",
    )
    parser.add_argument(
        "--reviewer-decisions-json",
        default="",
        help="Optional JSON file with reviewer decisions to include in evidence manifest",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    llama_cloud_results_dir = Path(args.llama_cloud_results_dir)
    llama_cloud_results_dir.mkdir(parents=True, exist_ok=True)
    langfuse_traces_dir = Path(args.langfuse_traces_dir)
    langfuse_traces_dir.mkdir(parents=True, exist_ok=True)

    langfuse = get_lims_langfuse()
    span = None
    if langfuse is not None:
        span = langfuse.start_span(
            name="lims-e2e-compare",
            input={
                "pdf": str(pdf_path),
                "base_url": args.base_url,
                "run_id": run_id,
            },
        )

    direct_result = run_direct_extraction(pdf_path)
    app_result = run_app_extraction(pdf_path, args.base_url)

    direct_mda = direct_result.get("mda_template") or direct_result.get("normalized_extraction")
    app_mda = app_result.get("mda_template")
    method_family = _extract_method_family(pdf_path.stem)

    comparison: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "pdf": str(pdf_path),
        "base_url": args.base_url,
        "direct_counts": _counts(direct_mda),
        "app_counts": _counts(app_mda),
        "direct_vs_app_shape": _shape_similarity(direct_mda, app_mda),
        "direct_trace": direct_result.get("extraction_trace"),
        "app_trace_id": app_result.get("trace_id"),
        "app_trace_url": app_result.get("trace_url"),
        "app_pipeline_type": app_result.get("pipeline_type"),
        "app_test_type": app_result.get("test_type"),
    }

    ground_truth_json_path: Path | None = None
    if args.ground_truth_json:
        gt_path = Path(args.ground_truth_json)
        if not gt_path.exists():
            raise FileNotFoundError(f"Ground truth JSON not found: {gt_path}")
        ground_truth_json_path = gt_path
        ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
        comparison["ground_truth_counts"] = _counts(ground_truth)
        comparison["ground_truth_vs_app_shape"] = _shape_similarity(ground_truth, app_mda)
        comparison["ground_truth_vs_direct_shape"] = _shape_similarity(ground_truth, direct_mda)
        comparison["ground_truth_vs_app_entity_compare"] = _compare_ground_truth(
            ground_truth,
            app_mda,
            method_family=method_family,
        )

    (run_dir / "direct_result.json").write_text(
        json.dumps(direct_result, indent=2, default=str),
        encoding="utf-8",
    )
    (run_dir / "app_result.json").write_text(
        json.dumps(app_result, indent=2, default=str),
        encoding="utf-8",
    )
    (run_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2, default=str),
        encoding="utf-8",
    )

    reviewer_decisions = _load_optional_json(args.reviewer_decisions_json)
    evidence_manifest = _write_canonical_evidence_package(
        run_dir=run_dir,
        run_id=run_id,
        timestamp_utc=comparison["timestamp_utc"],
        pdf_path=pdf_path,
        direct_result=direct_result,
        app_result=app_result,
        comparison=comparison,
        ground_truth_json_path=ground_truth_json_path,
        reviewer_decisions=reviewer_decisions,
    )

    (llama_cloud_results_dir / f"{run_id}_direct_result.json").write_text(
        json.dumps(direct_result, indent=2, default=str),
        encoding="utf-8",
    )

    trace_refs = {
        "run_id": run_id,
        "timestamp_utc": comparison["timestamp_utc"],
        "app_trace_id": app_result.get("trace_id"),
        "app_trace_url": app_result.get("trace_url"),
        "langfuse_output_artifact": str((run_dir / "comparison.json")),
    }
    (langfuse_traces_dir / f"{run_id}_trace_refs.json").write_text(
        json.dumps(trace_refs, indent=2, default=str),
        encoding="utf-8",
    )

    ground_truth_md_dir = Path(args.ground_truth_md_dir)
    stem = pdf_path.stem
    input_md = ground_truth_md_dir / f"{stem}_pdf.md"
    output_md = ground_truth_md_dir / f"{stem}_xlsx.md"
    comparison["ground_truth_md"] = {
        "directory": str(ground_truth_md_dir),
        "input_pdf_md": str(input_md),
        "input_pdf_md_exists": input_md.exists(),
        "output_xlsx_md": str(output_md),
        "output_xlsx_md_exists": output_md.exists(),
    }
    (run_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2, default=str),
        encoding="utf-8",
    )

    if span is not None:
        span.update(output={
            "comparison": comparison,
            "evidence_manifest": {
                "schema_version": evidence_manifest["schema_version"],
                "run_id": evidence_manifest["run_id"],
            },
        })
        span.score(
            name="direct_vs_app_shape_jaccard",
            value=float(comparison["direct_vs_app_shape"]["jaccard"]),
        )
        if "ground_truth_vs_app_shape" in comparison:
            span.score(
                name="ground_truth_vs_app_shape_jaccard",
                value=float(comparison["ground_truth_vs_app_shape"]["jaccard"]),
            )
        span.end()
        flush_lims_langfuse()

    print(json.dumps({
        "run_id": run_id,
        "run_dir": str(run_dir),
        "comparison": comparison,
        "evidence_manifest": {
            "schema_version": evidence_manifest["schema_version"],
            "path": str(run_dir / "evidence_manifest.json"),
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
