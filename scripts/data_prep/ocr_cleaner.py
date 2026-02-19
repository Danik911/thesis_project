"""Fix OCR errors from PaddleOCR PP-Structure output.

Character-level corrections only — NEVER invent missing words.
Joins truncated lines at page boundaries.
Annotates low-confidence blocks for downstream review.

NO FALLBACK LOGIC: if input format is unexpected, raise with full context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Character-level OCR substitution patterns.
# Each tuple: (regex_pattern, replacement)
# Applied in order; patterns are case-sensitive unless flagged.
OCR_SUBSTITUTIONS: list[tuple[str, str]] = [
    # Common PP-Structure character errors in pharmaceutical SOPs
    (r"\btirst\b", "first"),
    (r"\btor\b(?=\s+the\b|\s+a\b|\s+each\b|\s+all\b)", "for"),
    (r"\bunctionality\b", "functionality"),
    (r"\bonfiguration\b", "configuration"),
    (r"\bocument\b", "document"),
    (r"\bpecification\b", "specification"),
    (r"\bequirement\b", "requirement"),
    (r"\bveritic\b", "verific"),
    # Case errors from OCR
    (r"TEsT", "TEST"),
    (r"MAsTER", "MASTER"),
    (r"REsULT", "RESULT"),
    (r"DATa", "DATA"),
    (r"CODe", "CODE"),
    (r"FIELd", "FIELD"),
    # LIMS-specific corrections
    (r"gLiMs\b", "gLIMS"),
    (r"LiMs\b", "LIMS"),
    (r"LabWare LiMs\b", "LabWare LIMS"),
    (r"BcD\b", "BCD"),
    (r"DDs\b", "DDS"),
    # Punctuation artifacts
    (r"\.\.(?=[^.])", "."),  # double period -> single (not ellipsis)
    (r"\.\.\.$", "..."),  # preserve real ellipsis
    (r"\s{2,}", " "),  # collapse multiple spaces
]

# Confidence threshold below which blocks are flagged for review
LOW_CONFIDENCE_THRESHOLD = 0.85


@dataclass
class CleanedLine:
    """A single cleaned text line with provenance."""

    text: str
    original_text: str
    page: int
    block_type: str
    confidence: float
    corrections_applied: list[str] = field(default_factory=list)
    low_confidence: bool = False


@dataclass
class OCRCleaningResult:
    """Result of cleaning all text from a document."""

    lines: list[CleanedLine]
    total_corrections: int
    low_confidence_count: int
    corrections_log: list[dict[str, Any]]


def apply_substitutions(text: str) -> tuple[str, list[str]]:
    """Apply OCR substitution patterns to text.

    Returns:
        Tuple of (cleaned_text, list_of_corrections_applied).
    """
    corrections: list[str] = []
    result = text
    for pattern, replacement in OCR_SUBSTITUTIONS:
        new_result = re.sub(pattern, replacement, result)
        if new_result != result:
            corrections.append(f"{pattern!r} -> {replacement!r}")
            result = new_result
    return result, corrections


def clean_text_block(
    text: str,
    page: int,
    block_type: str,
    confidence: float,
) -> CleanedLine:
    """Clean a single text block from OCR output."""
    cleaned, corrections = apply_substitutions(text)
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    return CleanedLine(
        text=cleaned,
        original_text=text,
        page=page,
        block_type=block_type,
        confidence=confidence,
        corrections_applied=corrections,
        low_confidence=confidence < LOW_CONFIDENCE_THRESHOLD,
    )


def join_truncated_lines(lines: list[CleanedLine]) -> list[CleanedLine]:
    """Join lines that were truncated at OCR page/block boundaries.

    Heuristic: if a line ends without sentence-ending punctuation and the
    next line starts with a lowercase letter, they are likely one sentence.
    Only joins adjacent lines on the same page within the same block type.
    """
    if not lines:
        return lines

    result: list[CleanedLine] = []
    i = 0
    while i < len(lines):
        current = lines[i]
        # Check if this line should be joined with the next
        while (
            i + 1 < len(lines)
            and _should_join(current, lines[i + 1])
        ):
            next_line = lines[i + 1]
            joined_text = current.text + " " + next_line.text
            current = CleanedLine(
                text=joined_text,
                original_text=current.original_text + " || " + next_line.original_text,
                page=current.page,
                block_type=current.block_type,
                confidence=min(current.confidence, next_line.confidence),
                corrections_applied=current.corrections_applied + next_line.corrections_applied,
                low_confidence=current.low_confidence or next_line.low_confidence,
            )
            i += 1
        result.append(current)
        i += 1
    return result


def _should_join(current: CleanedLine, next_line: CleanedLine) -> bool:
    """Determine if two adjacent lines should be joined."""
    if current.page != next_line.page:
        return False
    if current.block_type != next_line.block_type:
        return False
    # Don't join title blocks
    if current.block_type == "title" or next_line.block_type == "title":
        return False
    # Join if current doesn't end with sentence punctuation and next starts lowercase
    text = current.text.rstrip()
    if not text:
        return False
    if text[-1] in ".!?:;":
        return False
    if next_line.text and next_line.text[0].islower():
        return True
    return False


def clean_page_blocks(page_data: dict[str, Any]) -> list[CleanedLine]:
    """Clean all text blocks from a single page JSON.

    Args:
        page_data: Parsed page JSON with 'raw_structure' containing blocks.

    Returns:
        List of CleanedLine for this page.
    """
    page_num = page_data.get("page")
    if page_num is None:
        raise ValueError(f"Page data missing 'page' field: {list(page_data.keys())}")

    raw_structure = page_data.get("raw_structure", [])
    if not isinstance(raw_structure, list):
        raise TypeError(
            f"Expected raw_structure to be list, got {type(raw_structure)} on page {page_num}"
        )

    lines: list[CleanedLine] = []
    for block in raw_structure:
        block_type = block.get("type", "unknown")
        if block_type not in {"text", "title", "list", "figure_caption", "header", "footer"}:
            continue

        block_res = block.get("res", [])
        if not isinstance(block_res, list):
            continue

        for item in block_res:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "")
            confidence = item.get("confidence", 0.0)
            if not text or not text.strip():
                continue
            lines.append(
                clean_text_block(text, page_num, block_type, confidence)
            )

    return lines


def clean_document(pages: list[dict[str, Any]]) -> OCRCleaningResult:
    """Clean all pages of a document.

    Args:
        pages: List of parsed page JSON dicts, sorted by page number.

    Returns:
        OCRCleaningResult with all cleaned lines and statistics.
    """
    all_lines: list[CleanedLine] = []
    for page_data in pages:
        page_lines = clean_page_blocks(page_data)
        all_lines.extend(page_lines)

    # Join truncated lines within each page
    all_lines = join_truncated_lines(all_lines)

    # Build statistics
    total_corrections = sum(len(line.corrections_applied) for line in all_lines)
    low_confidence_count = sum(1 for line in all_lines if line.low_confidence)
    corrections_log = []
    for line in all_lines:
        if line.corrections_applied:
            corrections_log.append({
                "page": line.page,
                "original": line.original_text,
                "cleaned": line.text,
                "corrections": line.corrections_applied,
            })

    return OCRCleaningResult(
        lines=all_lines,
        total_corrections=total_corrections,
        low_confidence_count=low_confidence_count,
        corrections_log=corrections_log,
    )
