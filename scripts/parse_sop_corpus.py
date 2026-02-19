#!/usr/bin/env python3
"""Batch-parse SOP PDFs and generate organized metadata artifacts.

This utility runs the PP-Structure extractor for each PDF in a source directory,
then builds:
- Per-document metadata JSON and description markdown
- Corpus-level manifest for downstream L10-L16 tasks

NO FALLBACK LOGIC: failures are raised with full context.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_slug(name: str) -> str:
    value = name.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Failed to create slug from empty filename stem.")
    return value


def _extract_doc_code(filename_stem: str) -> str:
    match = re.search(r"([A-Z]{2,}-\d{3,})", filename_stem, flags=re.IGNORECASE)
    if match is None:
        return "UNKNOWN"
    return match.group(1).upper()


def _extractor_script_path() -> Path:
    script_path = Path(__file__).resolve().parent / "extract_pdf_ppstructure.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Extractor script not found: {script_path}")
    return script_path


@dataclass
class ParseConfig:
    source_dir: Path
    output_root: Path
    dpi: int
    lang: str


def _run_extractor(
    extractor_script: Path,
    pdf_path: Path,
    output_dir: Path,
    dpi: int,
    lang: str,
) -> None:
    cmd = [
        sys.executable,
        str(extractor_script),
        "--pdf",
        str(pdf_path),
        "--output-dir",
        str(output_dir),
        "--dpi",
        str(dpi),
        "--lang",
        lang,
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "PP-Structure extraction failed for "
            f"{pdf_path}. Return code: {completed.returncode}. "
            f"STDOUT: {completed.stdout}\nSTDERR: {completed.stderr}"
        )


def _read_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        raise FileNotFoundError(f"Expected summary.json not found: {summary_path}")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _build_doc_metadata(
    *,
    pdf_path: Path,
    source_dir: Path,
    output_dir: Path,
    summary: dict[str, Any],
    dpi: int,
    lang: str,
) -> dict[str, Any]:
    doc_code = _extract_doc_code(pdf_path.stem)
    rel_pdf = pdf_path.relative_to(source_dir.parent).as_posix()
    rel_output = output_dir.relative_to(output_dir.parent.parent).as_posix()

    return {
        "document_id": doc_code,
        "document_name": pdf_path.stem,
        "source": {
            "filename": pdf_path.name,
            "relative_path": rel_pdf,
            "size_bytes": pdf_path.stat().st_size,
        },
        "pipeline": {
            "name": "paddleocr_ppstructure",
            "script": "scripts/extract_pdf_ppstructure.py",
            "executed_at_utc": _utc_now_iso(),
            "parameters": {"dpi": dpi, "lang": lang},
        },
        "artifacts": {
            "output_dir": rel_output,
            "summary_json": f"{rel_output}/summary.json",
            "text_extracted": f"{rel_output}/text_extracted.txt",
            "tables_extracted": f"{rel_output}/tables_extracted.json",
            "pages_dir": f"{rel_output}/pages",
        },
        "metrics": {
            "total_pages": summary.get("total_pages"),
            "text_line_count": summary.get("text_line_count"),
            "table_count": summary.get("table_count"),
        },
        "l10_l16_context": {
            "intended_usage": "Two-layer pipeline development and validation",
            "tags": ["SOP", "MDA", "two-layer-pipeline", "L10-L16"],
        },
    }


def _write_description(metadata: dict[str, Any], output_dir: Path) -> None:
    lines = [
        f"# {metadata['document_name']}",
        "",
        "## Metadata",
        f"- document_id: {metadata['document_id']}",
        f"- source_file: {metadata['source']['filename']}",
        f"- pages: {metadata['metrics']['total_pages']}",
        f"- text_lines: {metadata['metrics']['text_line_count']}",
        f"- tables: {metadata['metrics']['table_count']}",
        f"- parser: {metadata['pipeline']['name']}",
        f"- executed_at_utc: {metadata['pipeline']['executed_at_utc']}",
        "",
        "## Artifacts",
        f"- {metadata['artifacts']['summary_json']}",
        f"- {metadata['artifacts']['text_extracted']}",
        f"- {metadata['artifacts']['tables_extracted']}",
        f"- {metadata['artifacts']['pages_dir']}",
        "",
        "## L10-L16 Usage",
        "- Build classification evidence and test-type heuristics from extracted text.",
        "- Track template vs extracted fields during augmentation and merge.",
        "- Support provenance-ready validation and conflict analysis workflows.",
    ]
    (output_dir / "description.md").write_text("\n".join(lines), encoding="utf-8")


def parse_all(config: ParseConfig) -> None:
    if not config.source_dir.exists() or not config.source_dir.is_dir():
        raise NotADirectoryError(f"Invalid source directory: {config.source_dir}")

    config.output_root.mkdir(parents=True, exist_ok=True)
    documents_dir = config.output_root / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(config.source_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in source directory: {config.source_dir}")

    extractor_script = _extractor_script_path()

    parsed_docs: list[dict[str, Any]] = []
    for pdf_path in pdf_files:
        doc_slug = _safe_slug(pdf_path.stem)
        doc_output_dir = documents_dir / doc_slug
        doc_output_dir.mkdir(parents=True, exist_ok=True)

        _run_extractor(
            extractor_script=extractor_script,
            pdf_path=pdf_path,
            output_dir=doc_output_dir,
            dpi=config.dpi,
            lang=config.lang,
        )

        summary = _read_summary(doc_output_dir / "summary.json")
        metadata = _build_doc_metadata(
            pdf_path=pdf_path,
            source_dir=config.source_dir,
            output_dir=doc_output_dir,
            summary=summary,
            dpi=config.dpi,
            lang=config.lang,
        )

        (doc_output_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _write_description(metadata, doc_output_dir)
        parsed_docs.append(metadata)

    corpus_manifest = {
        "generated_at_utc": _utc_now_iso(),
        "source_dir": config.source_dir.as_posix(),
        "output_root": config.output_root.as_posix(),
        "pipeline": {
            "name": "paddleocr_ppstructure",
            "dpi": config.dpi,
            "lang": config.lang,
        },
        "documents_count": len(parsed_docs),
        "totals": {
            "pages": sum(int(doc["metrics"]["total_pages"] or 0) for doc in parsed_docs),
            "text_lines": sum(int(doc["metrics"]["text_line_count"] or 0) for doc in parsed_docs),
            "tables": sum(int(doc["metrics"]["table_count"] or 0) for doc in parsed_docs),
        },
        "documents": parsed_docs,
    }

    (config.output_root / "manifest.json").write_text(
        json.dumps(corpus_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(corpus_manifest["totals"], ensure_ascii=False, indent=2))


def parse_args() -> ParseConfig:
    parser = argparse.ArgumentParser(
        description="Batch parse SOP PDFs and build metadata manifest for L10-L16"
    )
    parser.add_argument(
        "--source-dir",
        default="demo_data/SOP",
        help="Directory containing SOP PDF files",
    )
    parser.add_argument(
        "--output-root",
        default="output/sop_parsed",
        help="Root directory for parsed SOP outputs",
    )
    parser.add_argument("--dpi", type=int, default=220, help="PDF rasterization DPI")
    parser.add_argument("--lang", default="en", help="OCR language")
    args = parser.parse_args()

    if args.dpi < 100 or args.dpi > 600:
        raise ValueError("DPI must be between 100 and 600.")

    return ParseConfig(
        source_dir=Path(args.source_dir).expanduser().resolve(),
        output_root=Path(args.output_root).expanduser().resolve(),
        dpi=args.dpi,
        lang=args.lang,
    )


def main() -> None:
    config = parse_args()
    parse_all(config)


if __name__ == "__main__":
    main()
