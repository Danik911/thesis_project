"""Tests for main.src.lims.chunking -- sheet-level XLSX chunking."""

from __future__ import annotations

import tempfile
from pathlib import Path

import openpyxl
import pytest

from main.src.lims.chunking import (
    parse_xlsx_to_chunks,
    sheet_to_markdown_table,
    generate_workbook_summary,
)


def _create_test_xlsx(path: Path, sheets: dict[str, list[list]]) -> None:
    """Helper: create an XLSX file with given sheets and data."""
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(sheet_name)
        for row in rows:
            ws.append(row)
    wb.save(str(path))
    wb.close()


class TestSheetToMarkdownTable:
    def test_basic_table(self):
        md = sheet_to_markdown_table(
            "Analysis",
            ["Name", "Type", "Code"],
            [["Dye", "Quant", "DY01"], ["pH", "Limit", "PH01"]],
        )
        assert "## Sheet: Analysis" in md
        assert "| Name | Type | Code |" in md
        assert "| --- | --- | --- |" in md
        assert "| Dye | Quant | DY01 |" in md
        assert "| pH | Limit | PH01 |" in md

    def test_empty_headers(self):
        md = sheet_to_markdown_table("Empty", [], [])
        assert "(empty)" in md

    def test_pipe_escaping(self):
        md = sheet_to_markdown_table(
            "Test",
            ["Name"],
            [["value|with|pipes"]],
        )
        assert "value\\|with\\|pipes" in md


class TestGenerateWorkbookSummary:
    def test_summary_structure(self):
        summaries = [
            {"sheet_name": "Analysis", "row_count": 5, "headers": ["Name"], "sample_values": {"Name": ["Dye"]}},
            {"sheet_name": "Component", "row_count": 10, "headers": ["Code"], "sample_values": {}},
        ]
        text = generate_workbook_summary("AND_ACS_DYE-LAB-2499.xlsx", summaries)
        assert "AND_ACS_DYE-LAB-2499.xlsx" in text
        assert "Site prefix: AND" in text
        assert "Sheets: 2" in text
        assert "### Analysis (5 rows)" in text
        assert "Dye" in text


class TestParseXlsxToChunks:
    def test_returns_multiple_chunks(self, tmp_path):
        xlsx_path = tmp_path / "AND_TEST_SAMPLE.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name", "Type"], ["Dye", "Quant"]],
            "Component": [["Code", "Desc"], ["C01", "Component 1"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        # 2 sheets + 1 summary = 3 chunks
        assert len(chunks) == 3

    def test_chunk_has_markdown_format(self, tmp_path):
        xlsx_path = tmp_path / "FRE_TEST.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name", "Type"], ["pH", "Limit"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        sheet_chunk = [c for c in chunks if not c["metadata"]["is_summary"]][0]
        assert "## Sheet:" in sheet_chunk["text"]
        assert "| Name | Type |" in sheet_chunk["text"]
        assert "| --- | --- |" in sheet_chunk["text"]

    def test_summary_chunk_included(self, tmp_path):
        xlsx_path = tmp_path / "TUA_TEST.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name"], ["Test"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        summary_chunks = [c for c in chunks if c["metadata"]["is_summary"]]
        assert len(summary_chunks) == 1
        assert "SUMMARY" in summary_chunks[0]["id"]

    def test_priority_flags(self, tmp_path):
        xlsx_path = tmp_path / "AND_PRI.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name"], ["A"]],
            "Component": [["Code"], ["C"]],
            "Calc Variable": [["Var"], ["V"]],
            "Calculation": [["Expr"], ["E"]],
            "Other Sheet": [["Data"], ["D"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        non_summary = [c for c in chunks if not c["metadata"]["is_summary"]]
        priority = [c for c in non_summary if c["metadata"]["is_priority"]]
        non_priority = [c for c in non_summary if not c["metadata"]["is_priority"]]
        assert len(priority) == 4
        assert len(non_priority) == 1

    def test_unique_ids(self, tmp_path):
        xlsx_path = tmp_path / "AND_UNIQUE.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name"], ["A"]],
            "Component": [["Code"], ["C"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"

    def test_empty_sheets_skipped(self, tmp_path):
        xlsx_path = tmp_path / "AND_EMPTY.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name"], ["A"]],
            "Empty": [],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        sheet_names = [c["metadata"]["sheet_name"] for c in chunks]
        assert "Empty" not in sheet_names

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_xlsx_to_chunks(Path("/nonexistent/file.xlsx"))

    def test_metadata_fields(self, tmp_path):
        xlsx_path = tmp_path / "AND_META.xlsx"
        _create_test_xlsx(xlsx_path, {
            "Analysis": [["Name"], ["A"]],
        })
        chunks = parse_xlsx_to_chunks(xlsx_path)
        meta = chunks[0]["metadata"]
        assert "source_file" in meta
        assert "sheet_name" in meta
        assert "is_priority" in meta
        assert "is_summary" in meta
        assert "row_count" in meta
        assert "prefix" in meta
        assert meta["source_file"] == "AND_META.xlsx"
        assert meta["prefix"] == "AND"
