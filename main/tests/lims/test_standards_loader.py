"""Tests for L13 standards RAG loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from main.src.lims import rag_loader, standards_loader


class _FakeCollection:
    def __init__(self) -> None:
        self._documents: list[str] = []
        self._metadatas: list[dict[str, str]] = []
        self._ids: list[str] = []

    def add(self, documents: list[str], metadatas: list[dict[str, str]], ids: list[str]) -> None:
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        self._ids.extend(ids)

    def count(self) -> int:
        return len(self._documents)

    def query(self, query_texts: list[str], n_results: int) -> dict:
        _ = query_texts
        return {
            "documents": [self._documents[:n_results]],
            "metadatas": [self._metadatas[:n_results]],
        }


class _FakeClient:
    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


def _write_prepared_fixture(root: Path, *, with_calc_content: bool = True) -> None:
    (root / "per_document" / "doc-a").mkdir(parents=True)

    manifest = {
        "documents": [
            {
                "document_id": "SOP-00597",
                "slug": "doc-a",
            }
        ]
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    sections = [
        {
            "id": "sec_1",
            "number": "1.1",
            "title": "Scope",
            "page_start": 1,
            "page_end": 2,
            "content": "Standard naming rules and variable naming conventions",
        },
        {
            "id": "sec_2",
            "number": "3.2.13",
            "title": "Subroutines",
            "page_start": 3,
            "page_end": 3,
            "content": "GOSUB CALC_SR_PICKER\nIF X THEN RESULT = Y" if with_calc_content else "General notes",
        },
    ]
    (root / "per_document" / "doc-a" / "sections.json").write_text(
        json.dumps(sections),
        encoding="utf-8",
    )

    tables = [
        {
            "page": 4,
            "table_index": 1,
            "plain_text": "CALC_INST_PICKER and RESULT = VAR" if with_calc_content else "No formula text",
        }
    ]
    (root / "per_document" / "doc-a" / "tables_cleaned.json").write_text(
        json.dumps(tables),
        encoding="utf-8",
    )


def test_chunk_by_sections_splits_numbered_headers() -> None:
    text = "1 Introduction\nalpha\n2.1 Scope\nbeta\n# Heading\ngamma"
    chunks = standards_loader.chunk_by_sections(text, max_chunk_size=1000)

    assert len(chunks) == 3
    assert chunks[0]["title"] == "1 Introduction"
    assert "alpha" in chunks[0]["content"]
    assert chunks[1]["title"] == "2.1 Scope"
    assert chunks[2]["title"] == "Heading"


def test_seed_standards_collection_rejects_missing_manifest(tmp_path: Path) -> None:
    empty_dir = tmp_path / "prepared"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="Required artifact missing"):
        standards_loader.seed_standards_collection(prepared_root=str(empty_dir))


def test_seed_standards_collection_from_prepared_writes_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared"
    _write_prepared_fixture(prepared)

    fake_client = _FakeClient()
    monkeypatch.setattr(standards_loader.chromadb, "PersistentClient", lambda path: fake_client)

    added = standards_loader.seed_standards_collection(
        prepared_root=str(prepared),
        collection_name="lims_standards",
    )

    assert added >= 1
    collection = fake_client.get_or_create_collection("lims_standards")
    assert collection.count() == added
    assert collection._metadatas[0]["source_file"] == "doc-a/sections.json"

    trace_dir = prepared / "L13_rag"
    assert (trace_dir / "lims_standards_seed_trace.json").exists()
    assert (trace_dir / "lims_standards_chunks.jsonl").exists()


def test_seed_calculation_patterns_requires_calc_signals(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared"
    _write_prepared_fixture(prepared, with_calc_content=False)

    fake_client = _FakeClient()
    monkeypatch.setattr(standards_loader.chromadb, "PersistentClient", lambda path: fake_client)

    with pytest.raises(ValueError, match="No calculation blocks were detected"):
        standards_loader.seed_standards_collection(
            prepared_root=str(prepared),
            collection_name="calculation_patterns",
        )


def test_query_standards_returns_structured_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared"
    _write_prepared_fixture(prepared)

    fake_client = _FakeClient()
    monkeypatch.setattr(standards_loader.chromadb, "PersistentClient", lambda path: fake_client)

    standards_loader.seed_standards_collection(
        prepared_root=str(prepared),
        collection_name="lims_standards",
    )
    results = standards_loader.query_standards(
        query_text="variable naming",
        collection_name="lims_standards",
        top_k=2,
    )

    assert len(results) == 2
    assert set(results[0].keys()) == {"content", "title", "source_file"}


def test_rag_loader_supports_custom_collection_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    demo_dir = tmp_path / "demo"
    demo_dir.mkdir()
    (demo_dir / "AND_SAMPLE.xlsx").write_text("placeholder", encoding="utf-8")

    fake_client = _FakeClient()
    monkeypatch.setattr(rag_loader.chromadb, "PersistentClient", lambda path: fake_client)
    monkeypatch.setattr(
        rag_loader,
        "parse_xlsx_to_text",
        lambda xlsx_path: f"Parsed {Path(xlsx_path).name}",
    )

    added = rag_loader.seed_mda_templates(
        demo_data_dir=str(demo_dir),
        collection_name="custom_templates",
    )
    assert added == 1

    matches = rag_loader.query_similar_templates(
        extraction_text="sample",
        top_k=1,
        collection_name="custom_templates",
    )
    assert len(matches) == 1
    assert "Parsed AND_SAMPLE.xlsx" in matches[0]
