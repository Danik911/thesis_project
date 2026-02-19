"""Detect section headers and build hierarchical section tree.

Uses title blocks from spatially-reordered pages to detect numbered
sections (e.g. "1.3 BACKGROUND") and build a parent-child hierarchy.

Handles two modes:
- SOP mode: numbered sections (r'^(\\d+(?:\\.\\d+)*)\\s+(.*)')
- Slide mode: page-boundary sections for training materials (no numbered headers)

TOC pages (>5 title blocks, <2 text blocks) are detected and skipped.

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Section number pattern: "1.", "1.3", "1.3.2", "3.2.13.54" etc.
SECTION_HEADER_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)")

# Minimum title blocks to consider a page as TOC
TOC_TITLE_THRESHOLD = 5
# Maximum text blocks allowed on a TOC page
TOC_TEXT_MAX = 2


@dataclass
class Section:
    """A document section with hierarchical structure."""

    id: str
    number: str  # e.g. "1.3" or "slide_p5"
    title: str
    level: int  # 1 for top-level, 2 for subsection, etc.
    page_start: int
    page_end: int = 0
    content_lines: list[str] = field(default_factory=list)
    table_indices: list[tuple[int, int]] = field(default_factory=list)  # (page, table_idx)
    children: list[str] = field(default_factory=list)  # child section IDs
    parent: str | None = None


def _compute_level(number: str) -> int:
    """Compute section level from number. '1' -> 1, '1.3' -> 2, '1.3.2' -> 3."""
    return number.count(".") + 1


def _is_toc_page(page_data: dict[str, Any]) -> bool:
    """Detect if a page is a Table of Contents page.

    TOC pages typically have many title blocks and very few text blocks.
    """
    raw_structure = page_data.get("raw_structure", [])
    title_count = sum(1 for b in raw_structure if b.get("type") == "title")
    text_count = sum(1 for b in raw_structure if b.get("type") == "text")
    return title_count >= TOC_TITLE_THRESHOLD and text_count <= TOC_TEXT_MAX


def _extract_title_text(block: dict[str, Any]) -> str:
    """Extract combined text from a title block's res array."""
    res = block.get("res", [])
    parts = []
    for item in res:
        if isinstance(item, dict):
            text = item.get("text", "").strip()
            if text:
                parts.append(text)
    return " ".join(parts)


def detect_document_type(pages: list[dict[str, Any]]) -> str:
    """Detect whether document uses SOP-style numbered sections or slide-style.

    Returns:
        'sop' for numbered sections, 'slide' for training material.
    """
    numbered_title_count = 0
    total_title_count = 0

    for page_data in pages[:20]:  # Sample first 20 pages
        if _is_toc_page(page_data):
            continue
        for block in page_data.get("raw_structure", []):
            if block.get("type") == "title":
                total_title_count += 1
                title_text = _extract_title_text(block)
                if SECTION_HEADER_RE.match(title_text):
                    numbered_title_count += 1

    if total_title_count == 0:
        return "slide"

    ratio = numbered_title_count / total_title_count
    return "sop" if ratio > 0.3 else "slide"


def build_sections_sop(pages: list[dict[str, Any]]) -> list[Section]:
    """Build section tree from SOP-style numbered sections.

    Scans title blocks for section numbers, assigns content between
    consecutive headers to the preceding section.
    """
    sections: list[Section] = []
    current_section: Section | None = None

    for page_data in pages:
        page_num = page_data.get("page", 0)

        if _is_toc_page(page_data):
            continue

        raw_structure = page_data.get("raw_structure", [])

        for block in raw_structure:
            block_type = block.get("type", "")

            if block_type == "title":
                title_text = _extract_title_text(block)
                match = SECTION_HEADER_RE.match(title_text)

                if match:
                    # Close previous section
                    if current_section is not None:
                        current_section.page_end = page_num

                    number = match.group(1)
                    title = match.group(2).strip()
                    level = _compute_level(number)
                    section_id = f"sec_{number.replace('.', '_')}"

                    current_section = Section(
                        id=section_id,
                        number=number,
                        title=title,
                        level=level,
                        page_start=page_num,
                    )
                    sections.append(current_section)
                elif current_section is not None:
                    # Non-numbered title becomes content of current section
                    current_section.content_lines.append(title_text)

            elif block_type in {"text", "list", "figure_caption"}:
                if current_section is not None:
                    # Add text content to current section
                    for item in block.get("res", []):
                        if isinstance(item, dict):
                            text = item.get("text", "").strip()
                            if text:
                                current_section.content_lines.append(text)

            elif block_type == "table":
                if current_section is not None:
                    # Track which tables belong to this section
                    tables = page_data.get("tables", [])
                    # Find this table's index
                    table_blocks = [
                        b for b in raw_structure if b.get("type") == "table"
                    ]
                    try:
                        table_idx = table_blocks.index(block) + 1
                    except ValueError:
                        table_idx = len(current_section.table_indices) + 1
                    current_section.table_indices.append((page_num, table_idx))

    # Close last section
    if current_section is not None and pages:
        current_section.page_end = pages[-1].get("page", 0)

    # Build parent-child relationships
    _assign_hierarchy(sections)

    return sections


def build_sections_slide(pages: list[dict[str, Any]]) -> list[Section]:
    """Build sections from training slides using page boundaries.

    Each page becomes its own section, titled from the first title block
    or "Slide {n}" if no title found.
    """
    sections: list[Section] = []

    for page_data in pages:
        page_num = page_data.get("page", 0)
        raw_structure = page_data.get("raw_structure", [])

        # Find first title block for section title
        title = f"Slide {page_num}"
        for block in raw_structure:
            if block.get("type") == "title":
                extracted = _extract_title_text(block)
                if extracted:
                    title = extracted
                    break

        section = Section(
            id=f"slide_p{page_num}",
            number=f"p{page_num}",
            title=title,
            level=1,
            page_start=page_num,
            page_end=page_num,
        )

        # Collect all text content
        for block in raw_structure:
            block_type = block.get("type", "")
            if block_type in {"text", "list", "title", "figure_caption"}:
                for item in block.get("res", []):
                    if isinstance(item, dict):
                        text = item.get("text", "").strip()
                        if text:
                            section.content_lines.append(text)
            elif block_type == "table":
                tables = page_data.get("tables", [])
                table_blocks = [b for b in raw_structure if b.get("type") == "table"]
                try:
                    table_idx = table_blocks.index(block) + 1
                except ValueError:
                    table_idx = 1
                section.table_indices.append((page_num, table_idx))

        sections.append(section)

    return sections


def _assign_hierarchy(sections: list[Section]) -> None:
    """Assign parent/children relationships based on section numbering.

    Section "1.3" is a child of "1". Section "1.3.2" is a child of "1.3".
    """
    section_map = {s.number: s for s in sections}

    for section in sections:
        parts = section.number.split(".")
        if len(parts) > 1:
            parent_number = ".".join(parts[:-1])
            parent = section_map.get(parent_number)
            if parent is not None:
                section.parent = parent.id
                parent.children.append(section.id)


def build_sections(pages: list[dict[str, Any]]) -> list[Section]:
    """Auto-detect document type and build section tree.

    Returns:
        List of Section objects with hierarchy.
    """
    doc_type = detect_document_type(pages)
    if doc_type == "sop":
        return build_sections_sop(pages)
    return build_sections_slide(pages)


def sections_to_json(sections: list[Section]) -> list[dict[str, Any]]:
    """Serialize sections to JSON-compatible format."""
    return [
        {
            "id": s.id,
            "number": s.number,
            "title": s.title,
            "level": s.level,
            "page_start": s.page_start,
            "page_end": s.page_end,
            "content": "\n".join(s.content_lines),
            "tables": [{"page": p, "table_index": t} for p, t in s.table_indices],
            "parent": s.parent,
            "children": s.children,
        }
        for s in sections
    ]
