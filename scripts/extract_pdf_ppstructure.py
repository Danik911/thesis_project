#!/usr/bin/env python3
"""Extract text and tables from a PDF using PaddleOCR PP-Structure.

This script is designed for protected/non-selectable SOP-style PDFs where OCR is required.
It runs locally and writes page-level and consolidated outputs.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_dependencies() -> tuple[Any, Any, Any]:
    missing: list[str] = []
    try:
        import cv2  # type: ignore
    except ImportError:
        missing.append("opencv-python")
        cv2 = None

    try:
        import fitz  # type: ignore
    except ImportError:
        missing.append("PyMuPDF")
        fitz = None

    paddle_import_error: Exception | None = None
    try:
        from paddleocr import PPStructure  # type: ignore
    except ImportError as exc:
        paddle_import_error = exc
        missing.append("paddleocr (with PPStructure API)")
        PPStructure = None

    if missing:
        extra_hint = ""
        if paddle_import_error is not None:
            extra_hint = (
                " Detected PaddleOCR without legacy PPStructure symbol. "
                "Install a PPStructure-compatible version, for example: "
                "uv pip install 'paddleocr<3' paddlepaddle PyMuPDF opencv-python"
            )
        raise RuntimeError(
            "Missing required packages: "
            f"{', '.join(missing)}. "
            "Install with: uv pip install paddleocr paddlepaddle PyMuPDF opencv-python"
            f"{extra_hint}"
        )

    return cv2, fitz, PPStructure


@dataclass
class ExtractionConfig:
    pdf_path: Path
    output_dir: Path
    language: str
    dpi: int
    use_gpu: bool


def _pdf_page_to_bgr_image(fitz_mod: Any, page: Any, dpi: int, cv2_mod: Any) -> Any:
    zoom = dpi / 72.0
    matrix = fitz_mod.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    import numpy as np  # type: ignore

    if pix.n not in {1, 3}:
        raise RuntimeError(
            f"Unsupported channel count in pixmap: {pix.n}. Expected 1 or 3 channels."
        )

    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 1:
        return cv2_mod.cvtColor(image, cv2_mod.COLOR_GRAY2BGR)
    return cv2_mod.cvtColor(image, cv2_mod.COLOR_RGB2BGR)


def _extract_text_blocks(structure_result: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for block in structure_result:
        block_type = block.get("type", "")
        if block_type in {"text", "title", "list", "figure_caption", "header", "footer"}:
            block_res = block.get("res", [])
            if isinstance(block_res, list):
                for item in block_res:
                    text = item.get("text") if isinstance(item, dict) else None
                    if text and text.strip():
                        lines.append(text.strip())
    return lines


def _extract_table_items(structure_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for block in structure_result:
        if block.get("type") != "table":
            continue
        res = block.get("res")
        if isinstance(res, dict):
            table_payload = {
                "html": res.get("html"),
                "cell_bbox": res.get("cell_bbox"),
            }
            tables.append(table_payload)
        else:
            tables.append({"raw": res})
    return tables


def run_extraction(config: ExtractionConfig) -> None:
    cv2_mod, fitz_mod, PPStructure = _load_dependencies()

    if not config.pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {config.pdf_path}")

    config.output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = config.output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    engine = PPStructure(show_log=False, ocr=True, lang=config.language, use_gpu=config.use_gpu)

    all_text_lines: list[str] = []
    all_tables: list[dict[str, Any]] = []

    with fitz_mod.open(config.pdf_path) as doc:
        if len(doc) == 0:
            raise RuntimeError("PDF has zero pages; cannot extract content.")

        for page_index, page in enumerate(doc, start=1):
            image = _pdf_page_to_bgr_image(fitz_mod, page, config.dpi, cv2_mod)
            page_result = engine(image)

            if not isinstance(page_result, list):
                raise RuntimeError(
                    f"Unexpected PP-Structure output on page {page_index}: {type(page_result)}"
                )

            sanitized_page_result: list[dict[str, Any]] = []
            for block in page_result:
                if not isinstance(block, dict):
                    raise RuntimeError(
                        f"Unexpected block type on page {page_index}: {type(block)}"
                    )
                block_copy = {k: v for k, v in block.items() if k != "img"}
                sanitized_page_result.append(block_copy)

            page_text_lines = _extract_text_blocks(sanitized_page_result)
            page_tables = _extract_table_items(sanitized_page_result)

            all_text_lines.extend(page_text_lines)
            for table_idx, table_data in enumerate(page_tables, start=1):
                table_data_with_meta = {
                    "page": page_index,
                    "table_index_on_page": table_idx,
                    **table_data,
                }
                all_tables.append(table_data_with_meta)

            page_json = {
                "page": page_index,
                "text_lines": page_text_lines,
                "tables": page_tables,
                "raw_structure": sanitized_page_result,
            }

            page_json_path = pages_dir / f"page_{page_index:04d}.json"
            page_json_path.write_text(
                json.dumps(page_json, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    (config.output_dir / "text_extracted.txt").write_text(
        "\n".join(all_text_lines),
        encoding="utf-8",
    )
    (config.output_dir / "tables_extracted.json").write_text(
        json.dumps(all_tables, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "input_pdf": str(config.pdf_path),
        "total_pages": len(list((config.output_dir / "pages").glob("page_*.json"))),
        "text_line_count": len(all_text_lines),
        "table_count": len(all_tables),
        "output_dir": str(config.output_dir),
    }
    (config.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> ExtractionConfig:
    parser = argparse.ArgumentParser(
        description="Extract text and tables from PDF using PaddleOCR PP-Structure"
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF file")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for extraction output files",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="PaddleOCR language code (default: en)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Rasterization DPI for PDF pages (default: 200)",
    )
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="Enable GPU for PaddleOCR if available",
    )
    args = parser.parse_args()

    if args.dpi < 100 or args.dpi > 600:
        raise ValueError("DPI must be between 100 and 600.")

    return ExtractionConfig(
        pdf_path=Path(args.pdf).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        language=args.lang,
        dpi=args.dpi,
        use_gpu=bool(args.use_gpu),
    )


def main() -> None:
    config = parse_args()
    run_extraction(config)


if __name__ == "__main__":
    main()