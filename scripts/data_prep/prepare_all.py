#!/usr/bin/env python3
"""CLI orchestrator: discover all parsed docs, run full cleaning pipeline, write outputs.

Usage:
    python scripts/data_prep/prepare_all.py \\
        --input-dirs output/ppstructure_cd025658 output/sop_parsed/documents \\
        --output-dir output/prepared

Discovers page JSON files under each input directory, runs:
1. Spatial reordering (bbox-based reading order)
2. OCR cleaning (character-level corrections)
3. Table cleaning (empty row removal, plain-text extraction)
4. Section building (numbered headers or slide-mode)
5. Document assembly (markdown + JSON artifacts)

Writes per-document artifacts and a manifest.json.

NO FALLBACK LOGIC. Uses only Python stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _discover_documents(input_dirs: list[Path]) -> list[tuple[str, Path]]:
    """Discover all parsed documents from input directories.

    Supports two directory layouts:
    1. Direct: input_dir/pages/page_XXXX.json (single document)
    2. Nested: input_dir/documents/{slug}/pages/page_XXXX.json (multiple documents)
    3. Nested: input_dir/{slug}/pages/page_XXXX.json (multiple documents, no 'documents' subdir)

    Returns:
        List of (doc_name, pages_dir) tuples.
    """
    documents: list[tuple[str, Path]] = []

    for input_dir in input_dirs:
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Check if this directory directly contains pages/
        direct_pages = input_dir / "pages"
        if direct_pages.is_dir() and any(direct_pages.glob("page_*.json")):
            # Single document at this level
            documents.append((input_dir.name, direct_pages))
            continue

        # Check for nested documents/ subdirectory
        documents_subdir = input_dir / "documents"
        search_dir = documents_subdir if documents_subdir.is_dir() else input_dir

        for subdir in sorted(search_dir.iterdir()):
            if not subdir.is_dir():
                continue
            pages_dir = subdir / "pages"
            if pages_dir.is_dir() and any(pages_dir.glob("page_*.json")):
                documents.append((subdir.name, pages_dir))

    if not documents:
        raise FileNotFoundError(
            f"No parsed documents found in: {[str(d) for d in input_dirs]}. "
            "Expected page_XXXX.json files under a 'pages/' subdirectory."
        )

    return documents


def _load_pages(pages_dir: Path) -> list[dict[str, Any]]:
    """Load all page JSON files from a directory, sorted by page number."""
    page_files = sorted(pages_dir.glob("page_*.json"))
    if not page_files:
        raise FileNotFoundError(f"No page JSON files in: {pages_dir}")

    pages: list[dict[str, Any]] = []
    for pf in page_files:
        data = json.loads(pf.read_text(encoding="utf-8"))
        pages.append(data)

    return pages


def _process_single_document(
    doc_name: str,
    pages_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run the full pipeline on a single document.

    Returns:
        Summary dict for this document.
    """
    # Import pipeline modules (deferred to avoid import issues when running as script)
    from scripts.data_prep.document_assembler import assemble_document, write_artifacts
    from scripts.data_prep.ocr_cleaner import clean_document
    from scripts.data_prep.section_builder import build_sections
    from scripts.data_prep.spatial_reorderer import reorder_document
    from scripts.data_prep.table_cleaner import clean_document_tables

    print(f"  Loading pages from {pages_dir}...")
    pages = _load_pages(pages_dir)
    total_pages = len(pages)

    print(f"  [{doc_name}] {total_pages} pages loaded. Reordering spatially...")
    reordered_pages = reorder_document(pages)

    print(f"  [{doc_name}] Cleaning OCR text...")
    cleaning_result = clean_document(reordered_pages)

    print(f"  [{doc_name}] Cleaning tables...")
    tables = clean_document_tables(reordered_pages)

    print(f"  [{doc_name}] Building sections...")
    sections = build_sections(reordered_pages)

    print(f"  [{doc_name}] Assembling artifacts...")
    artifacts = assemble_document(
        doc_name=doc_name,
        cleaning_result=cleaning_result,
        sections=sections,
        tables=tables,
        total_pages=total_pages,
    )

    doc_dir = write_artifacts(artifacts, output_dir)

    summary = {
        "document_id": artifacts.doc_id,
        "slug": artifacts.slug,
        "output_dir": str(doc_dir),
        "pages": total_pages,
        "sections": len(sections),
        "tables_cleaned": len(tables),
        "ocr_corrections": cleaning_result.total_corrections,
        "low_confidence_lines": cleaning_result.low_confidence_count,
    }

    print(
        f"  [{doc_name}] Done: {total_pages} pages, "
        f"{len(sections)} sections, {len(tables)} tables, "
        f"{cleaning_result.total_corrections} OCR corrections"
    )
    return summary


def prepare_all(input_dirs: list[Path], output_dir: Path) -> None:
    """Run the full preparation pipeline on all discovered documents."""
    print("Discovering documents...")
    documents = _discover_documents(input_dirs)
    print(f"Found {len(documents)} document(s):")
    for name, pages_dir in documents:
        page_count = len(list(pages_dir.glob("page_*.json")))
        print(f"  - {name}: {page_count} pages at {pages_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create stub directories for L12 and L13 outputs (populated by subagents)
    (output_dir / "L12_classifier").mkdir(parents=True, exist_ok=True)
    (output_dir / "L13_rag").mkdir(parents=True, exist_ok=True)

    doc_summaries: list[dict[str, Any]] = []
    for doc_name, pages_dir in documents:
        print(f"\nProcessing: {doc_name}")
        summary = _process_single_document(doc_name, pages_dir, output_dir)
        doc_summaries.append(summary)

    # Build manifest
    manifest = {
        "generated_at_utc": _utc_now_iso(),
        "pipeline": "scripts/data_prep/prepare_all.py",
        "input_dirs": [str(d) for d in input_dirs],
        "output_dir": str(output_dir),
        "documents_count": len(doc_summaries),
        "documents": doc_summaries,
        "quality_summary": {
            "total_pages": sum(d["pages"] for d in doc_summaries),
            "total_sections": sum(d["sections"] for d in doc_summaries),
            "total_tables": sum(d["tables_cleaned"] for d in doc_summaries),
            "total_ocr_corrections": sum(d["ocr_corrections"] for d in doc_summaries),
            "total_low_confidence": sum(d["low_confidence_lines"] for d in doc_summaries),
        },
        "downstream_ready": {
            "L12_classifier": str(output_dir / "L12_classifier"),
            "L13_rag": str(output_dir / "L13_rag"),
        },
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'='*60}")
    print("Preparation complete!")
    print(json.dumps(manifest["quality_summary"], ensure_ascii=False, indent=2))
    print(f"\nManifest: {manifest_path}")
    print(f"Per-document artifacts: {output_dir / 'per_document'}")
    print(f"\nNext steps:")
    print(f"  1. Invoke data-prep-keyword-extractor subagent -> {output_dir / 'L12_classifier'}")
    print(f"  2. Invoke data-prep-chunk-builder subagent -> {output_dir / 'L13_rag'}")


def parse_args() -> tuple[list[Path], Path]:
    parser = argparse.ArgumentParser(
        description="Run full data preparation pipeline for L10-L16 tasks"
    )
    parser.add_argument(
        "--input-dirs",
        nargs="+",
        required=True,
        help="Directories containing parsed document pages",
    )
    parser.add_argument(
        "--output-dir",
        default="output/prepared",
        help="Output directory for prepared artifacts (default: output/prepared)",
    )
    args = parser.parse_args()

    input_dirs = [Path(d).expanduser().resolve() for d in args.input_dirs]
    output_dir = Path(args.output_dir).expanduser().resolve()

    return input_dirs, output_dir


def main() -> None:
    input_dirs, output_dir = parse_args()
    prepare_all(input_dirs, output_dir)


if __name__ == "__main__":
    main()
