"""Path helpers for LIMS integration/E2E test artifacts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

GROUND_TRUTH_DIR = REPO_ROOT / "demo_data" / "testing_data_ground_truth"
LEGACY_PARSED_DIR = REPO_ROOT / "demo_data" / "parced"
DEMO_DATA_DIR = REPO_ROOT / "demo_data" / "data"


def resolve_demo_pdf(filename: str) -> Path | None:
    """Resolve a demo PDF path across current and legacy locations."""
    candidates = [
        GROUND_TRUTH_DIR / filename,
        DEMO_DATA_DIR / filename,
        REPO_ROOT / "demo_data" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_ground_truth_md(stem: str, kind: str) -> Path | None:
    """Resolve parsed markdown ground truth path.

    Args:
        stem: Base filename stem (e.g., AND_ACS_DYE-LAB-2499)
        kind: Either "pdf" or "xlsx"
    """
    filename = f"{stem}_{kind}.md"
    candidates = [
        GROUND_TRUTH_DIR / filename,
        LEGACY_PARSED_DIR / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
