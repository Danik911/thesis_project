"""Assemble cleaned text, sections, and tables into final per-document artifacts.

Combines outputs from ocr_cleaner, spatial_reorderer, section_builder,
and table_cleaner into the target artifact structure:
- cleaned_text.md: OCR-corrected, section-structured markdown
- sections.json: hierarchical section tree
- tables_cleaned.json: cleaned tables with section context
- quality_report.json: OCR stats, corrections log

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.data_prep.ocr_cleaner import CleanedLine, OCRCleaningResult, apply_substitutions
from scripts.data_prep.section_builder import Section, sections_to_json
from scripts.data_prep.table_cleaner import CleanedTable, tables_to_json


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_slug(name: str) -> str:
    """Create a filesystem-safe slug from a name."""
    value = name.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError(f"Failed to create slug from: {name!r}")
    return value


def _extract_doc_code(filename_stem: str) -> str:
    """Extract document code (e.g. CD-025658) from filename or directory name."""
    # Try standard pattern first: CD-025658, SOP-00597
    match = re.search(r"([A-Z]{2,}-\d{3,})", filename_stem, flags=re.IGNORECASE)
    if match is not None:
        return match.group(1).upper()
    # Try extracting from slug-style names: ppstructure_cd025658 -> CD-025658
    match = re.search(r"([a-zA-Z]{2,})[\-_]?(\d{5,})", filename_stem)
    if match is not None:
        prefix = match.group(1).upper()
        number = match.group(2)
        return f"{prefix}-{number}"
    return "UNKNOWN"


@dataclass
class DocumentArtifacts:
    """All assembled artifacts for a single document."""

    doc_id: str
    slug: str
    cleaned_text_md: str
    sections_json: list[dict[str, Any]]
    tables_json: list[dict[str, Any]]
    quality_report: dict[str, Any]


def _clean_section_content(sections: list[Section]) -> None:
    """Apply OCR corrections to section content lines in-place."""
    for section in sections:
        cleaned_lines: list[str] = []
        for line in section.content_lines:
            cleaned, _ = apply_substitutions(line)
            cleaned_lines.append(cleaned.strip())
        section.content_lines = cleaned_lines
        # Also clean title
        cleaned_title, _ = apply_substitutions(section.title)
        section.title = cleaned_title.strip()


def build_cleaned_markdown(
    sections: list[Section],
    cleaning_result: OCRCleaningResult,
    tables: list[CleanedTable],
) -> str:
    """Build a section-structured markdown document from cleaned data.

    If sections exist, organizes content under section headers.
    Otherwise, produces flat content from cleaned lines.
    """
    lines: list[str] = []

    if sections:
        # Apply OCR corrections to section content
        _clean_section_content(sections)

        for section in sections:
            # Markdown header level
            header_prefix = "#" * min(section.level, 6)
            lines.append(f"{header_prefix} {section.number} {section.title}")
            lines.append("")

            if section.content_lines:
                for content_line in section.content_lines:
                    lines.append(content_line)
                lines.append("")

            # Include tables in this section
            for page_num, table_idx in section.table_indices:
                matching = [
                    t for t in tables
                    if t.page == page_num and t.table_index == table_idx
                ]
                for table in matching:
                    lines.append(f"**Table (page {table.page})**")
                    lines.append("")
                    lines.append(table.plain_text)
                    lines.append("")
    else:
        # No sections detected — output flat cleaned lines
        current_page = -1
        for cleaned_line in cleaning_result.lines:
            if cleaned_line.page != current_page:
                if current_page != -1:
                    lines.append("")
                lines.append(f"--- Page {cleaned_line.page} ---")
                lines.append("")
                current_page = cleaned_line.page
            lines.append(cleaned_line.text)

    return "\n".join(lines)


def build_quality_report(
    doc_id: str,
    cleaning_result: OCRCleaningResult,
    sections: list[Section],
    tables: list[CleanedTable],
    total_pages: int,
) -> dict[str, Any]:
    """Build quality report with OCR stats and corrections log."""
    # Confidence statistics
    confidences = [line.confidence for line in cleaning_result.lines if line.confidence > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    min_confidence = min(confidences) if confidences else 0.0

    # Table cleaning stats
    total_empty_rows_removed = sum(t.empty_rows_removed for t in tables)

    return {
        "document_id": doc_id,
        "generated_at_utc": _utc_now_iso(),
        "pages_processed": total_pages,
        "ocr_statistics": {
            "total_text_lines": len(cleaning_result.lines),
            "total_corrections_applied": cleaning_result.total_corrections,
            "low_confidence_lines": cleaning_result.low_confidence_count,
            "average_confidence": round(avg_confidence, 4),
            "min_confidence": round(min_confidence, 4),
        },
        "section_statistics": {
            "total_sections": len(sections),
            "max_depth": max((s.level for s in sections), default=0),
            "sections_with_content": sum(
                1 for s in sections if s.content_lines
            ),
        },
        "table_statistics": {
            "total_tables_cleaned": len(tables),
            "empty_rows_removed": total_empty_rows_removed,
        },
        "corrections_log": cleaning_result.corrections_log,
    }


def assemble_document(
    *,
    doc_name: str,
    cleaning_result: OCRCleaningResult,
    sections: list[Section],
    tables: list[CleanedTable],
    total_pages: int,
) -> DocumentArtifacts:
    """Assemble all artifacts for a single document.

    Args:
        doc_name: Original document directory/filename stem.
        cleaning_result: OCR cleaning output.
        sections: Detected sections with hierarchy.
        tables: Cleaned tables.
        total_pages: Total pages in document.

    Returns:
        DocumentArtifacts with all assembled outputs.
    """
    doc_id = _extract_doc_code(doc_name)
    slug = _safe_slug(doc_name)

    cleaned_md = build_cleaned_markdown(sections, cleaning_result, tables)
    sections_json = sections_to_json(sections)
    tables_json_data = tables_to_json(tables)
    quality = build_quality_report(
        doc_id, cleaning_result, sections, tables, total_pages
    )

    return DocumentArtifacts(
        doc_id=doc_id,
        slug=slug,
        cleaned_text_md=cleaned_md,
        sections_json=sections_json,
        tables_json=tables_json_data,
        quality_report=quality,
    )


def write_artifacts(artifacts: DocumentArtifacts, output_dir: Path) -> Path:
    """Write assembled artifacts to the output directory.

    Creates:
        output_dir/per_document/{slug}/cleaned_text.md
        output_dir/per_document/{slug}/sections.json
        output_dir/per_document/{slug}/tables_cleaned.json
        output_dir/per_document/{slug}/quality_report.json

    Returns:
        Path to the document's output directory.
    """
    doc_dir = output_dir / "per_document" / artifacts.slug
    doc_dir.mkdir(parents=True, exist_ok=True)

    (doc_dir / "cleaned_text.md").write_text(
        artifacts.cleaned_text_md, encoding="utf-8"
    )
    (doc_dir / "sections.json").write_text(
        json.dumps(artifacts.sections_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (doc_dir / "tables_cleaned.json").write_text(
        json.dumps(artifacts.tables_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (doc_dir / "quality_report.json").write_text(
        json.dumps(artifacts.quality_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return doc_dir
