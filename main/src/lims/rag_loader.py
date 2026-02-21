"""RAG loader for MDA templates -- parse XLSX files into ChromaDB.

Parses demo LabWare XLSX files into text representations and stores them
in the ChromaDB ``mda_templates`` collection for RAG-based retrieval
during MDA generation.

ChromaDB storage is kept separate from the thesis project:
  - Thesis:   ``./chroma_db/``
  - AI4LIMS:  ``./chroma_db_lims/``

NO FALLBACK LOGIC: all errors raise with full diagnostics.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import chromadb
import openpyxl
from langfuse import observe

from main.src.lims.chunking import parse_xlsx_to_chunks

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("LIMS_CHROMADB_PATH", "./chroma_db_lims")
COLLECTION_NAME = "mda_templates"


# ---------------------------------------------------------------------------
# 1. XLSX parsing
# ---------------------------------------------------------------------------


def parse_xlsx_to_text(xlsx_path: Path) -> str:
    """Parse a LabWare XLSX workbook into a single text string for embedding.

    Reads every sheet in the workbook, extracts header rows and data rows,
    and returns a human-readable text representation suitable for ChromaDB
    embedding and similarity search.

    Args:
        xlsx_path: Absolute or relative path to an ``.xlsx`` file.

    Returns:
        A multi-line string containing sheet names, headers, and row data.

    Raises:
        FileNotFoundError: If *xlsx_path* does not exist.
        openpyxl.utils.exceptions.InvalidFileException: If the file is not
            a valid XLSX workbook.
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        msg = f"XLSX file does not exist: {xlsx_path.resolve()}"
        raise FileNotFoundError(msg)

    logger.info("Parsing XLSX: %s", xlsx_path.name)
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)

    parts: list[str] = [f"File: {xlsx_path.name}"]

    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))

            if not rows:
                parts.append(f"\nSheet: {sheet_name}\n(empty)")
                continue

            # First row is treated as the header
            headers = [str(cell) if cell is not None else "" for cell in rows[0]]
            parts.append(f"\nSheet: {sheet_name}")
            parts.append(f"Headers: {' | '.join(headers)}")

            # Data rows
            for row_idx, row in enumerate(rows[1:], start=1):
                values = [
                    str(cell) if cell is not None else "" for cell in row
                ]
                parts.append(f"Row {row_idx}: {' | '.join(values)}")
    finally:
        wb.close()

    text = "\n".join(parts)
    logger.info(
        "Parsed %s: %d characters across %d sheets",
        xlsx_path.name,
        len(text),
        len(wb.sheetnames),
    )
    return text


# ---------------------------------------------------------------------------
# 2. Seed ChromaDB from demo XLSX files
# ---------------------------------------------------------------------------


def seed_mda_templates(
    demo_data_dir: str = "./demo_data",
    collection_name: str = COLLECTION_NAME,
    chroma_path: str = CHROMA_PATH,
) -> int:
    """Seed a ChromaDB collection from demo XLSX files using sheet-level chunks.

    Iterates over all ``*.xlsx`` files in *demo_data_dir*, chunks each into
    per-sheet markdown tables via :func:`parse_xlsx_to_chunks`, and upserts
    the resulting chunks into the target collection.

    Args:
        demo_data_dir: Directory containing demo ``*.xlsx`` files.
        collection_name: ChromaDB collection name (defaults to ``mda_templates``).
        chroma_path: Path to the ChromaDB persistent storage directory.

    Returns:
        Number of chunks added to the collection.

    Raises:
        FileNotFoundError: If *demo_data_dir* does not exist or contains
            no ``.xlsx`` files.
    """
    demo_dir = Path(demo_data_dir)
    if not demo_dir.exists():
        msg = f"Demo data directory does not exist: {demo_dir.resolve()}"
        raise FileNotFoundError(msg)

    xlsx_files = sorted(demo_dir.glob("*.xlsx"))
    if not xlsx_files:
        msg = (
            f"No .xlsx files found in {demo_dir.resolve()}. "
            f"Expected LabWare demo XLSX files with AND_*, FRE_*, TUA_* prefixes."
        )
        raise FileNotFoundError(msg)

    logger.info(
        "Found %d XLSX files in %s", len(xlsx_files), demo_dir.resolve()
    )

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)

    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    for xlsx_path in xlsx_files:
        chunks = parse_xlsx_to_chunks(xlsx_path)
        for chunk in chunks:
            documents.append(chunk["text"])
            # ChromaDB metadata values must be str, int, float, or bool
            meta = {
                "source_file": chunk["metadata"]["source_file"],
                "sheet_name": chunk["metadata"]["sheet_name"],
                "is_priority": chunk["metadata"]["is_priority"],
                "is_summary": chunk["metadata"]["is_summary"],
                "row_count": chunk["metadata"]["row_count"],
                "prefix": chunk["metadata"]["prefix"],
            }
            metadatas.append(meta)
            ids.append(chunk["id"])

    # Bulk upsert to ChromaDB (idempotent -- safe to re-run)
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

    final_count = collection.count()
    logger.info(
        "Seeded %d chunks from %d XLSX files into '%s' (total: %d)",
        len(documents),
        len(xlsx_files),
        collection_name,
        final_count,
    )

    return len(documents)


# ---------------------------------------------------------------------------
# 3. Query similar templates
# ---------------------------------------------------------------------------


@observe(name="rag-mda-templates-query")
def query_similar_templates(
    extraction_text: str,
    top_k: int = 3,
    collection_name: str = COLLECTION_NAME,
    chroma_path: str = CHROMA_PATH,
) -> list[str]:
    """Query ChromaDB for MDA templates similar to the given extraction text.

    Args:
        extraction_text: Text from a PDF extraction or user query to find
            similar templates for.
        top_k: Maximum number of similar documents to return.
        collection_name: ChromaDB collection name (defaults to ``mda_templates``).
        chroma_path: Path to the ChromaDB persistent storage directory.

    Returns:
        List of document strings from the most similar templates.

    Raises:
        ValueError: If *extraction_text* is empty.
        RuntimeError: If the collection is empty (seed first).
    """
    if not extraction_text.strip():
        msg = (
            "extraction_text must not be empty. "
            "Provide text from a PDF extraction or a search query."
        )
        raise ValueError(msg)

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)

    doc_count = collection.count()
    if doc_count == 0:
        msg = (
            f"ChromaDB collection '{collection_name}' is empty. "
            f"Run seed_mda_templates() first to populate the collection "
            f"from demo_data/*.xlsx files."
        )
        raise RuntimeError(msg)

    # Clamp top_k to available document count
    effective_k = min(top_k, doc_count)

    logger.info(
        "Querying '%s' collection (top_k=%d, docs_available=%d)",
        collection_name,
        effective_k,
        doc_count,
    )

    results = collection.query(
        query_texts=[extraction_text],
        n_results=effective_k,
        include=["documents", "metadatas", "distances"],
    )

    # results["documents"] is a list of lists -- one per query text
    matched_docs: list[str] = results["documents"][0]  # type: ignore[index]
    distances: list[float] = results.get("distances", [[]])[0]  # type: ignore[union-attr]

    logger.info(
        "Query returned %d similar templates (distances: %s)",
        len(matched_docs),
        [round(d, 4) for d in distances[:5]],
    )

    return matched_docs


@observe(name="rag-mda-templates-query-scored")
def query_similar_templates_with_scores(
    extraction_text: str,
    top_k: int = 3,
    collection_name: str = COLLECTION_NAME,
    chroma_path: str = CHROMA_PATH,
) -> list[dict[str, Any]]:
    """Query ChromaDB and return documents with distance scores and metadata.

    Same as :func:`query_similar_templates` but returns full result dicts
    needed by the RAG evaluator.

    Args:
        extraction_text: Text from a PDF extraction or user query.
        top_k: Maximum number of similar documents to return.
        collection_name: ChromaDB collection name.
        chroma_path: Path to the ChromaDB persistent storage directory.

    Returns:
        List of dicts with keys: ``content``, ``distance``, ``metadata``.

    Raises:
        ValueError: If *extraction_text* is empty.
        RuntimeError: If the collection is empty.
    """
    if not extraction_text.strip():
        raise ValueError("extraction_text must not be empty.")

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)

    doc_count = collection.count()
    if doc_count == 0:
        raise RuntimeError(
            f"ChromaDB collection '{collection_name}' is empty. "
            f"Run seed_mda_templates() first."
        )

    effective_k = min(top_k, doc_count)

    results = collection.query(
        query_texts=[extraction_text],
        n_results=effective_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output: list[dict[str, Any]] = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=False):
        output.append({
            "content": str(doc),
            "distance": float(dist),
            "metadata": dict(meta) if meta else {},
        })

    logger.info(
        "Scored query returned %d results (top distance: %.4f)",
        len(output),
        output[0]["distance"] if output else float("inf"),
    )

    return output
