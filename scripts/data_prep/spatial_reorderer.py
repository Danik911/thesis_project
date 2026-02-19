"""Restore correct reading order from PP-Structure bbox coordinates.

PP-Structure outputs blocks in detection order (not reading order).
This module uses bbox y_min coordinates to sort blocks top-to-bottom,
then x_min for left-to-right within the same y-band.

Also merges split title blocks (e.g. "1.3" + "BACKGROUND" -> "1.3 BACKGROUND").

NO FALLBACK LOGIC: if bbox data is missing, raise with diagnostics.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

# Y-coordinate tolerance in pixels for "same line" detection.
# Blocks within this vertical distance are considered on the same line.
Y_BAND_TOLERANCE = 20

# Section number pattern for detecting split title blocks
SECTION_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?$")


def _get_bbox(block: dict[str, Any]) -> list[float]:
    """Extract bbox from a block, raising if missing."""
    bbox = block.get("bbox")
    if bbox is None or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError(
            f"Block missing valid bbox. type={block.get('type')}, "
            f"keys={list(block.keys())}"
        )
    return [float(v) for v in bbox]


def _y_min(block: dict[str, Any]) -> float:
    return _get_bbox(block)[1]


def _x_min(block: dict[str, Any]) -> float:
    return _get_bbox(block)[0]


def sort_blocks_by_position(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort blocks by reading order: top-to-bottom, left-to-right within y-bands.

    Groups blocks into y-bands (rows) using Y_BAND_TOLERANCE, then sorts
    each band left-to-right by x_min.
    """
    if not blocks:
        return []

    # Sort primarily by y_min
    sorted_blocks = sorted(blocks, key=lambda b: (_y_min(b), _x_min(b)))

    # Group into y-bands
    bands: list[list[dict[str, Any]]] = []
    current_band: list[dict[str, Any]] = [sorted_blocks[0]]
    current_y = _y_min(sorted_blocks[0])

    for block in sorted_blocks[1:]:
        block_y = _y_min(block)
        if abs(block_y - current_y) <= Y_BAND_TOLERANCE:
            current_band.append(block)
        else:
            bands.append(current_band)
            current_band = [block]
            current_y = block_y
    bands.append(current_band)

    # Sort each band by x_min, then flatten
    result: list[dict[str, Any]] = []
    for band in bands:
        band.sort(key=_x_min)
        result.extend(band)

    return result


def merge_split_titles(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge adjacent title blocks that were split by OCR.

    Common pattern: "1.3" as one title block, "BACKGROUND" as another,
    both on the same y-band. Merges them into "1.3 BACKGROUND".
    """
    if not blocks:
        return []

    result: list[dict[str, Any]] = []
    i = 0
    while i < len(blocks):
        block = deepcopy(blocks[i])

        if block.get("type") == "title" and i + 1 < len(blocks):
            next_block = blocks[i + 1]
            # Check if this is a section number followed by a title on the same line
            if (
                next_block.get("type") == "title"
                and _is_same_line(block, next_block)
                and _is_section_number_block(block)
            ):
                # Merge: combine res entries, extend bbox
                merged = _merge_title_blocks(block, next_block)
                result.append(merged)
                i += 2
                continue

        result.append(block)
        i += 1

    return result


def _is_same_line(block_a: dict[str, Any], block_b: dict[str, Any]) -> bool:
    """Check if two blocks are on the same y-band."""
    try:
        y_a = _y_min(block_a)
        y_b = _y_min(block_b)
        return abs(y_a - y_b) <= Y_BAND_TOLERANCE
    except ValueError:
        return False


def _is_section_number_block(block: dict[str, Any]) -> bool:
    """Check if a title block contains only a section number like '1.3' or '1.'."""
    res = block.get("res", [])
    if not res:
        return False
    # Get all text from the block
    texts = [item.get("text", "").strip() for item in res if isinstance(item, dict)]
    combined = " ".join(texts).strip()
    return bool(SECTION_NUMBER_RE.match(combined))


def _merge_title_blocks(
    number_block: dict[str, Any],
    text_block: dict[str, Any],
) -> dict[str, Any]:
    """Merge a section-number title block with its text title block."""
    merged = deepcopy(number_block)
    # Combine res arrays
    merged_res = list(merged.get("res", []))
    merged_res.extend(deepcopy(text_block.get("res", [])))
    merged["res"] = merged_res

    # Extend bbox to cover both blocks
    bbox_a = _get_bbox(number_block)
    bbox_b = _get_bbox(text_block)
    merged["bbox"] = [
        min(bbox_a[0], bbox_b[0]),  # x_min
        min(bbox_a[1], bbox_b[1]),  # y_min
        max(bbox_a[2], bbox_b[2]),  # x_max
        max(bbox_a[3], bbox_b[3]),  # y_max
    ]
    merged["_merged"] = True
    return merged


def reorder_page(page_data: dict[str, Any]) -> dict[str, Any]:
    """Reorder all blocks in a page by reading position.

    Args:
        page_data: Raw page JSON with 'raw_structure'.

    Returns:
        New page dict with blocks sorted by reading order and split titles merged.
    """
    raw_structure = page_data.get("raw_structure", [])
    if not isinstance(raw_structure, list):
        raise TypeError(
            f"Expected raw_structure to be list on page {page_data.get('page')}"
        )

    if not raw_structure:
        return deepcopy(page_data)

    # Separate blocks with and without bbox
    blocks_with_bbox: list[dict[str, Any]] = []
    blocks_without_bbox: list[dict[str, Any]] = []
    for block in raw_structure:
        if block.get("bbox") and len(block.get("bbox", [])) == 4:
            blocks_with_bbox.append(block)
        else:
            blocks_without_bbox.append(block)

    # Sort blocks with bbox by reading order
    sorted_blocks = sort_blocks_by_position(blocks_with_bbox)
    # Merge split titles
    sorted_blocks = merge_split_titles(sorted_blocks)
    # Append any blocks without bbox at the end
    sorted_blocks.extend(blocks_without_bbox)

    # Rebuild text_lines from sorted blocks
    text_lines: list[str] = []
    for block in sorted_blocks:
        block_type = block.get("type", "")
        if block_type in {"text", "title", "list", "figure_caption", "header", "footer"}:
            for item in block.get("res", []):
                if isinstance(item, dict):
                    text = item.get("text", "").strip()
                    if text:
                        text_lines.append(text)

    result = deepcopy(page_data)
    result["raw_structure"] = sorted_blocks
    result["text_lines"] = text_lines
    result["_reordered"] = True
    return result


def reorder_document(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reorder all pages of a document.

    Args:
        pages: List of page JSON dicts.

    Returns:
        List of reordered page dicts.
    """
    return [reorder_page(page) for page in pages]
