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

    def upsert(self, documents: list[str], metadatas: list[dict[str, str]], ids: list[str]) -> None:
        for i, doc_id in enumerate(ids):
            if doc_id in self._ids:
                idx = self._ids.index(doc_id)
                self._documents[idx] = documents[i]
                self._metadatas[idx] = metadatas[i]
            else:
                self._ids.append(doc_id)
                self._documents.append(documents[i])
                self._metadatas.append(metadatas[i])

    def count(self) -> int:
        return len(self._documents)

    def query(self, query_texts: list[str], n_results: int, **kwargs) -> dict:
        _ = query_texts
        docs = self._documents[:n_results]
        metas = self._metadatas[:n_results]
        distances = [0.1 * (i + 1) for i in range(len(docs))]
        return {
            "documents": [docs],
            "metadatas": [metas],
            "distances": [distances],
        }


class _FakeClient:
    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]

    def delete_collection(self, name: str) -> None:
        if name in self.collections:
            del self.collections[name]


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
    assert {"content", "title", "source_file", "distance"}.issubset(results[0].keys())


def test_query_standards_with_metrics_returns_gate_inputs(
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
    payload = standards_loader.query_standards_with_metrics(
        query_text="AND_ACS_DYE identity variable naming",
        collection_name="lims_standards",
        top_k=2,
        method_family="AND_ACS_DYE",
    )

    assert "results" in payload
    assert "metrics" in payload
    assert isinstance(payload["results"], list)
    assert payload["metrics"]["returned_count"] >= 0
    assert "avg_distance" in payload["metrics"]
    assert "method_match_ratio" in payload["metrics"]


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
        "parse_xlsx_to_chunks",
        lambda xlsx_path: [{
            "id": "AND_SAMPLE__analysis",
            "text": f"Parsed {Path(xlsx_path).name}",
            "metadata": {
                "source_file": Path(xlsx_path).name,
                "sheet_name": "Analysis",
                "is_priority": True,
                "is_summary": False,
                "row_count": 1,
                "prefix": "AND",
            },
        }],
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
