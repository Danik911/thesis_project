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
from pathlib import Path

import chromadb
import openpyxl

logger = logging.getLogger(__name__)

CHROMA_PATH = "./chroma_db_lims"
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
    chroma_path: str = CHROMA_PATH,
) -> int:
    """Seed the ``mda_templates`` ChromaDB collection from demo XLSX files.

    Iterates over all ``*.xlsx`` files in *demo_data_dir*, parses each with
    :func:`parse_xlsx_to_text`, and upserts the resulting text documents into
    the ``mda_templates`` collection.

    Args:
        demo_data_dir: Directory containing demo ``*.xlsx`` files.
        chroma_path: Path to the ChromaDB persistent storage directory.

    Returns:
        Number of documents added to the collection.

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
    collection = client.get_or_create_collection(COLLECTION_NAME)

    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    ids: list[str] = []

    for xlsx_path in xlsx_files:
        text = parse_xlsx_to_text(xlsx_path)
        doc_id = xlsx_path.stem  # e.g. "AND_ACS_AQ126-AQ126"

        # Derive site prefix from filename (AND, FRE, TUA, etc.)
        prefix = xlsx_path.stem.split("_")[0] if "_" in xlsx_path.stem else "UNKNOWN"

        documents.append(text)
        metadatas.append({
            "filename": xlsx_path.name,
            "prefix": prefix,
            "source_dir": str(demo_dir.resolve()),
        })
        ids.append(doc_id)

        logger.info("Prepared document: %s (prefix=%s)", doc_id, prefix)

    # Bulk add to ChromaDB
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    final_count = collection.count()
    logger.info(
        "Seeded %d documents into '%s' collection (total in collection: %d)",
        len(documents),
        COLLECTION_NAME,
        final_count,
    )

    return len(documents)


# ---------------------------------------------------------------------------
# 3. Query similar templates
# ---------------------------------------------------------------------------


def query_similar_templates(
    extraction_text: str,
    top_k: int = 3,
    chroma_path: str = CHROMA_PATH,
) -> list[str]:
    """Query ChromaDB for MDA templates similar to the given extraction text.

    Args:
        extraction_text: Text from a PDF extraction or user query to find
            similar templates for.
        top_k: Maximum number of similar documents to return.
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
    collection = client.get_or_create_collection(COLLECTION_NAME)

    doc_count = collection.count()
    if doc_count == 0:
        msg = (
            f"ChromaDB collection '{COLLECTION_NAME}' is empty. "
            f"Run seed_mda_templates() first to populate the collection "
            f"from demo_data/*.xlsx files."
        )
        raise RuntimeError(msg)

    # Clamp top_k to available document count
    effective_k = min(top_k, doc_count)

    logger.info(
        "Querying '%s' collection (top_k=%d, docs_available=%d)",
        COLLECTION_NAME,
        effective_k,
        doc_count,
    )

    results = collection.query(
        query_texts=[extraction_text],
        n_results=effective_k,
    )

    # results["documents"] is a list of lists -- one per query text
    matched_docs: list[str] = results["documents"][0]  # type: ignore[index]

    logger.info(
        "Query returned %d similar templates", len(matched_docs)
    )

    return matched_docs
