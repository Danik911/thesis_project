from __future__ import annotations

import argparse
import json
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
        default="output/lims/e2e_compare",
        help="Directory to write comparison artifacts",
    )
    parser.add_argument(
        "--ground-truth-json",
        default="",
        help="Optional JSON file for ground-truth MDA output comparison",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

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

    if args.ground_truth_json:
        gt_path = Path(args.ground_truth_json)
        if not gt_path.exists():
            raise FileNotFoundError(f"Ground truth JSON not found: {gt_path}")
        ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
        comparison["ground_truth_counts"] = _counts(ground_truth)
        comparison["ground_truth_vs_app_shape"] = _shape_similarity(ground_truth, app_mda)
        comparison["ground_truth_vs_direct_shape"] = _shape_similarity(ground_truth, direct_mda)

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

    if span is not None:
        span.update(output=comparison)
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

    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "comparison": comparison}, indent=2, default=str))


if __name__ == "__main__":
    main()
