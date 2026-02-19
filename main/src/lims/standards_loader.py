"""ChromaDB loader for pharmaceutical standards documents.

Ingests prepared standards artifacts from ``output/prepared_l10l15`` into
ChromaDB collections with section-based chunking for targeted retrieval.

Collections:
- lims_standards: General LIMS standards and SOPs
- calculation_patterns: Calculation code examples from training material

Traceability and monitoring:
- Writes ingestion trace summary JSON
- Writes chunk-level JSONL artifact for debugging

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import chromadb

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = "./chroma_db_lims"
CALCULATION_COLLECTION = "calculation_patterns"
DEFAULT_PREPARED_ROOT = "./output/prepared_l10l15"
DEFAULT_TRACE_DIRNAME = "L13_rag"


def _looks_like_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    if re.match(r"^#{1,6}\s+\S+", stripped):
        return True

    if re.match(r"^\d+(?:\.\d+){0,4}\.?\s+\S+", stripped):
        return True

    if re.match(r"^[A-Z][A-Z0-9\s\-/()]{6,}$", stripped):
        return True

    return False


def _split_large_content(title: str, content: str, max_chunk_size: int) -> list[dict[str, str]]:
    if len(content) <= max_chunk_size:
        return [{"title": title, "content": content.strip()}]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    if not paragraphs:
        paragraphs = [content.strip()]

    chunks: list[dict[str, str]] = []
    buffer = ""

    for paragraph in paragraphs:
        proposed = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(proposed) <= max_chunk_size:
            buffer = proposed
            continue

        if buffer:
            chunks.append({"title": title, "content": buffer})
            buffer = ""

        if len(paragraph) <= max_chunk_size:
            buffer = paragraph
            continue

        start = 0
        while start < len(paragraph):
            part = paragraph[start : start + max_chunk_size].strip()
            if part:
                chunks.append({"title": title, "content": part})
            start += max_chunk_size

    if buffer:
        chunks.append({"title": title, "content": buffer})

    return chunks


def chunk_by_sections(text: str, max_chunk_size: int = 2000) -> list[dict[str, str]]:
    """Split text into chunks at section headers.

    Detects markdown-style headers (#, ##) and numbered sections (1., 1.1).
    Each chunk includes the section header and content up to the next header.

    Args:
        text: Full document text.
        max_chunk_size: Maximum characters per chunk.

    Returns:
        List of dicts with 'title' and 'content' keys.
    """
    if max_chunk_size <= 0:
        raise ValueError(f"max_chunk_size must be > 0, got {max_chunk_size}")

    if not text.strip():
        return []

    lines = text.splitlines()
    chunks: list[dict[str, str]] = []
    current_title = "Introduction"
    current_content: list[str] = []

    def flush_chunk() -> None:
        if not current_content:
            return
        content = "\n".join(current_content).strip()
        if not content:
            return
        chunks.extend(_split_large_content(current_title, content, max_chunk_size))

    for raw_line in lines:
        line = raw_line.rstrip()
        if _looks_like_header(line):
            flush_chunk()
            current_title = line.strip().lstrip("#").strip()
            current_content = []
            continue
        current_content.append(line)

    flush_chunk()
    return chunks


def _load_json_file(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path.resolve()}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in artifact {path.resolve()}: {exc}") from exc


def _build_section_chunks(
    sections: list[dict[str, object]],
    slug: str,
    document_id: str,
) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    for section in sections:
        section_id = str(section.get("id", "UNKNOWN"))
        section_number = str(section.get("number", "")).strip()
        section_title = str(section.get("title", "Untitled")).strip()
        section_content = str(section.get("content", "")).strip()
        page_start = section.get("page_start")
        page_end = section.get("page_end")

        if not section_content:
            continue

        canonical_title = (
            f"{section_number} {section_title}".strip()
            if section_number
            else section_title
        )

        split_chunks = _split_large_content(canonical_title, section_content, max_chunk_size=2000)
        for chunk_index, chunk in enumerate(split_chunks, start=1):
            chunks.append({
                "id": f"{slug}-{section_id}-sec-{chunk_index}",
                "title": chunk["title"],
                "content": chunk["content"],
                "source_file": f"{slug}/sections.json",
                "source_slug": slug,
                "document_id": document_id,
                "section_id": section_id,
                "page_start": str(page_start) if page_start is not None else "",
                "page_end": str(page_end) if page_end is not None else "",
                "chunk_type": "section",
            })
    return chunks


def _build_calculation_chunks(
    sections: list[dict[str, object]],
    tables: list[dict[str, object]],
    slug: str,
    document_id: str,
) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []

    calc_sections = _chunk_calculation_blocks(
        "\n\n".join(str(section.get("content", "")) for section in sections if section.get("content")),
        max_chunk_size=1500,
    )
    for index, chunk in enumerate(calc_sections, start=1):
        chunks.append({
            "id": f"{slug}-calc-section-{index}",
            "title": chunk["title"],
            "content": chunk["content"],
            "source_file": f"{slug}/sections.json",
            "source_slug": slug,
            "document_id": document_id,
            "section_id": "",
            "page_start": "",
            "page_end": "",
            "chunk_type": "calc_section",
        })

    calc_signal = re.compile(
        r"(\bGOSUB\b|\bIF\b.*\bTHEN\b|\bRESULT\s*=|\bSELECT\b|\bUPDATE\b|\bINSERT\b|\bFOR\b.*\bTO\b|\bCALC_[A-Z0-9_]+\b)",
        re.IGNORECASE,
    )
    table_hits = 0
    for table in tables:
        plain_text = str(table.get("plain_text", "")).strip()
        if not plain_text:
            continue
        if not calc_signal.search(plain_text):
            continue

        table_hits += 1
        table_page = table.get("page")
        table_index = table.get("table_index")
        split_chunks = _split_large_content(
            title=f"Table Calc Pattern p{table_page} t{table_index}",
            content=plain_text,
            max_chunk_size=1500,
        )
        for chunk_idx, chunk in enumerate(split_chunks, start=1):
            chunks.append({
                "id": f"{slug}-table-{table_page}-{table_index}-calc-{chunk_idx}",
                "title": chunk["title"],
                "content": chunk["content"],
                "source_file": f"{slug}/tables_cleaned.json",
                "source_slug": slug,
                "document_id": document_id,
                "section_id": "",
                "page_start": str(table_page) if table_page is not None else "",
                "page_end": str(table_page) if table_page is not None else "",
                "chunk_type": "calc_table",
            })

    if not chunks:
        raise ValueError(
            f"No calculation chunks detected for prepared artifact slug '{slug}'. "
            "Expected calculation-heavy content in sections or tables."
        )

    logger.info(
        "Calculation chunking: slug=%s section_chunks=%d table_hits=%d total_chunks=%d",
        slug,
        len(calc_sections),
        table_hits,
        len(chunks),
    )

    return chunks


def _write_trace_artifacts(
    trace_dir: Path,
    collection_name: str,
    ingestion_run_id: str,
    chunks: list[dict[str, str]],
    docs_seen: set[str],
    prepared_root: Path,
) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC).isoformat()
    trace_summary = {
        "ingestion_run_id": ingestion_run_id,
        "generated_at_utc": now,
        "collection_name": collection_name,
        "prepared_root": str(prepared_root.resolve()),
        "documents_count": len(docs_seen),
        "chunks_count": len(chunks),
        "documents": sorted(docs_seen),
    }
    trace_summary_path = trace_dir / f"{collection_name}_seed_trace.json"
    trace_summary_path.write_text(json.dumps(trace_summary, indent=2), encoding="utf-8")

    chunks_path = trace_dir / f"{collection_name}_chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    logger.info(
        "Trace artifacts written: summary=%s chunks=%s",
        trace_summary_path.resolve(),
        chunks_path.resolve(),
    )


def _chunk_calculation_blocks(text: str, max_chunk_size: int = 1500) -> list[dict[str, str]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    calc_signal = re.compile(
        r"(\bGOSUB\b|\bIF\b.*\bTHEN\b|\bRESULT\s*=|\bSELECT\b|\bUPDATE\b|\bINSERT\b|\bFOR\b.*\bTO\b)",
        re.IGNORECASE,
    )

    chunks: list[dict[str, str]] = []
    for index, block in enumerate(blocks, start=1):
        if not calc_signal.search(block):
            continue
        chunks.extend(_split_large_content(f"Calculation Block {index}", block, max_chunk_size))

    if not chunks:
        raise ValueError(
            "No calculation blocks were detected. "
            "Expected code-heavy standards/training content with formulas or LIMS Basic patterns."
        )

    return chunks


def seed_standards_collection(
    prepared_root: str = DEFAULT_PREPARED_ROOT,
    collection_name: str = "lims_standards",
    chroma_path: str = DEFAULT_CHROMA_PATH,
    trace_output_dir: str | None = None,
) -> int:
    """Seed a ChromaDB collection from prepared standards artifacts.

    Args:
        prepared_root: Prepared artifacts root containing ``manifest.json`` and
            ``per_document/*`` directories.
        collection_name: ChromaDB collection name.
        chroma_path: Path to ChromaDB storage.
        trace_output_dir: Optional path to write traceability/monitoring artifacts.
            Defaults to ``{prepared_root}/L13_rag``.

    Returns:
        Number of chunks added.

    Raises:
        FileNotFoundError: If prepared artifacts are missing.
    """
    prepared_path = Path(prepared_root)
    if not prepared_path.exists():
        raise FileNotFoundError(f"Prepared root does not exist: {prepared_path.resolve()}")

    manifest_path = prepared_path / "manifest.json"
    manifest_raw = _load_json_file(manifest_path)
    if not isinstance(manifest_raw, dict):
        raise ValueError(f"Manifest must be a JSON object: {manifest_path.resolve()}")

    manifest_documents = manifest_raw.get("documents")
    if not isinstance(manifest_documents, list) or not manifest_documents:
        raise ValueError(
            f"Manifest has no documents for standards ingestion: {manifest_path.resolve()}"
        )

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)

    ingestion_run_id = str(uuid4())
    logger.info(
        "Starting standards ingestion run=%s collection=%s prepared_root=%s",
        ingestion_run_id,
        collection_name,
        prepared_path.resolve(),
    )

    collection_documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    ids: list[str] = []
    trace_chunks: list[dict[str, str]] = []
    docs_seen: set[str] = set()

    for manifest_doc in manifest_documents:
        if not isinstance(manifest_doc, dict):
            raise ValueError(f"Invalid document entry in manifest: {manifest_doc!r}")

        slug = str(manifest_doc.get("slug", "")).strip()
        document_id = str(manifest_doc.get("document_id", "UNKNOWN")).strip() or "UNKNOWN"
        if not slug:
            raise ValueError(f"Manifest document is missing slug: {manifest_doc}")

        doc_dir = prepared_path / "per_document" / slug
        sections_path = doc_dir / "sections.json"
        tables_path = doc_dir / "tables_cleaned.json"

        sections_raw = _load_json_file(sections_path)
        tables_raw = _load_json_file(tables_path)
        if not isinstance(sections_raw, list):
            raise ValueError(f"sections.json must be a list: {sections_path.resolve()}")
        if not isinstance(tables_raw, list):
            raise ValueError(f"tables_cleaned.json must be a list: {tables_path.resolve()}")

        section_chunks = (
            _build_calculation_chunks(sections_raw, tables_raw, slug, document_id)
            if collection_name == CALCULATION_COLLECTION
            else _build_section_chunks(sections_raw, slug, document_id)
        )

        if not section_chunks:
            raise ValueError(
                f"No chunks generated for slug '{slug}' in collection '{collection_name}'"
            )

        for chunk in section_chunks:
            chunk_id = chunk["id"]
            chunk_content = chunk["content"].strip()
            chunk_title = chunk["title"].strip()
            if not chunk_content:
                raise ValueError(f"Empty chunk generated for chunk id '{chunk_id}'")

            collection_documents.append(chunk_content)
            metadatas.append({
                "title": chunk_title,
                "source_file": chunk["source_file"],
                "source_slug": chunk["source_slug"],
                "document_id": chunk["document_id"],
                "section_id": chunk["section_id"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "collection": collection_name,
                "chunk_type": chunk["chunk_type"],
                "ingestion_run_id": ingestion_run_id,
            })
            ids.append(chunk_id)
            trace_chunks.append(chunk)

        docs_seen.add(slug)
        logger.info(
            "Prepared doc ingested: slug=%s doc_id=%s chunks=%d collection=%s",
            slug,
            document_id,
            len(section_chunks),
            collection_name,
        )

    if not collection_documents:
        raise ValueError(
            f"No chunks available to seed collection '{collection_name}' from {prepared_path.resolve()}"
        )

    collection.add(documents=collection_documents, metadatas=metadatas, ids=ids)

    trace_dir = (
        Path(trace_output_dir)
        if trace_output_dir is not None
        else prepared_path / DEFAULT_TRACE_DIRNAME
    )
    _write_trace_artifacts(
        trace_dir=trace_dir,
        collection_name=collection_name,
        ingestion_run_id=ingestion_run_id,
        chunks=trace_chunks,
        docs_seen=docs_seen,
        prepared_root=prepared_path,
    )

    logger.info(
        "Seeded %d chunks into standards collection '%s' from %d prepared documents",
        len(collection_documents),
        collection_name,
        len(docs_seen),
    )
    return len(collection_documents)


def query_standards(
    query_text: str,
    collection_name: str = "lims_standards",
    top_k: int = 5,
    chroma_path: str = DEFAULT_CHROMA_PATH,
) -> list[dict[str, str]]:
    """Query standards collection for relevant sections.

    Returns:
        List of dicts with 'content', 'title', 'source_file' keys.
    """
    if not query_text.strip():
        raise ValueError("query_text must not be empty")
    if top_k <= 0:
        raise ValueError(f"top_k must be > 0, got {top_k}")

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)

    doc_count = collection.count()
    if doc_count == 0:
        raise RuntimeError(
            f"ChromaDB collection '{collection_name}' is empty. "
            f"Run seed_standards_collection(prepared_root=..., collection_name='{collection_name}') first."
        )

    effective_k = min(top_k, doc_count)
    logger.info(
        "Query standards: collection=%s top_k=%d effective_k=%d docs_available=%d",
        collection_name,
        top_k,
        effective_k,
        doc_count,
    )
    results = collection.query(query_texts=[query_text], n_results=effective_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    output: list[dict[str, str]] = []
    for content, metadata in zip(documents, metadatas, strict=False):
        safe_metadata = metadata or {}
        output.append({
            "content": str(content),
            "title": str(safe_metadata.get("title", "Untitled Section")),
            "source_file": str(safe_metadata.get("source_file", "UNKNOWN")),
        })

    logger.info(
        "Query standards complete: collection=%s returned=%d",
        collection_name,
        len(output),
    )

    return output
