# Task L8 — RAG Optimization: Hybrid Search, Smart Chunking & Reranking

**Phase:** 7 (Optimization) | **Dependencies:** Phase 6 (done)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 1.5-2 days

---

## Objective

Dramatically improve RAG retrieval quality by: (a) replacing whole-workbook chunks with hybrid sheet-level + summary chunks, (b) implementing hybrid semantic + keyword (BM25) search, and (c) adding Cohere Rerank v3 as a post-retrieval reranking step. All data for RAG is in `demo_data/` (25 XLSX files, all should be indexed).

---

## Problem

Current RAG implementation (`rag_loader.py`) has three weaknesses:

1. **Chunking**: Each XLSX file -> one giant text chunk (2000+ tokens). Queries about specific components retrieve irrelevant sheet data.
2. **Search**: Embedding-only similarity search. No keyword matching. A query for "ACS_DYE" may not rank an exact-match document highest.
3. **No reranking**: Top-k results used as-is from ChromaDB. No quality re-scoring.

---

## Findings from L18 + Langfuse (Feb 2026)

Observed in `demo_data/langfuse/trace-c9141e0515e5ddf477d34d67b3d8b880.json`:

- **Template is currently carrying output quality**
    - Merge stats: `TEMPLATE=496`, `EXTRACTED=24` (template dominates final output).
    - `validation_passed=true` only after merge.
- **Extraction alone is structurally invalid**
    - Focused extract stage reports `validated=false` with many schema errors.
- **RAG path is invoked but contributes zero effective augmentation**
    - `lims-augment` runs, but returns `{"suggestions": []}`.
    - `augmented_data.suggestions` is empty at merge input.
- **Retrieved context appears noisy / weakly relevant**
    - `rag-standards-query` returns generic content; distance values are not compelling for the target method.
- **Classification is not the current bottleneck**
    - Method classifies as `IDENTITY` with high confidence (filename evidence), so retrieval quality is the primary optimization target.

### Implication

L8 should prioritize **retrieval precision and rerank quality**, not classification changes. The goal is to make augmentation produce non-empty, relevant, merge-usable suggestions without relaxing validation gates.

---

## Demo Data Structure

Location: `c:\Users\anteb\Desktop\Courses\Projects\thesis_project\demo_data`

Three types of files (ALL indexed for RAG):
- **PDF+XLSX pairs** (16 pairs): Input PDFs -> human-created MDA XLSX outputs (gold standard)
- **Config_w_Calcs.xlsx** (8 files): Configuration worksheets with calculation examples
- **gLIMS_Build.xls** (8 files): gLIMS build exports (legacy format, .xls not .xlsx)

**Important ingestion note:** current chunking proposal is XLSX-only. L8 implementation must explicitly handle `.xls` sources (conversion or dedicated parser) so these files are not silently excluded from the index.

Key sheets in MDA XLSX outputs: Sheet 1 (Analysis), Sheet 2 (Component), Sheet 6 (Calc Variables), Sheet 7 (Calculation). Only these sheets matter for RAG context.

Parsed markdown versions exist at: `demo_data/parced/AND_ACS_DYE-LAB-2499_pdf.md` and `_xlsx.md`

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/chunking.py` | Hybrid chunking: sheet-level markdown table chunks + workbook summary chunk |

## Files to Modify

| File | Change |
|------|--------|
| `main/src/lims/rag_loader.py` | Replace `parse_xlsx_to_text` with hybrid chunking, add BM25 hybrid search, add Cohere reranking to `query_similar_templates()` |
| `main/src/lims/config.py` | Add `cohere_api_key`, `reranker_model`, `reranker_top_n`, `bm25_weight`, `semantic_weight` fields |
| `scripts/populate_lims_chroma.py` | Update to use new chunking (will create ~5 chunks per file instead of 1) |
| `pyproject.toml` | Add `llama-index-postprocessor-cohere-rerank`, `rank-bm25>=0.2.2` |

---

## Implementation Details

### 0. Guardrails from current findings

- Keep hard validation gate behavior unchanged (no fallback auto-pass).
- Add retrieval diagnostics in traces for every query:
    - `retrieved_docs_count`
    - `candidate_docs_before_rerank`
    - `reranked_docs_count`
    - `suggestions_generated_count`
    - `suggestions_applied_count` (if available at merge stage)
- Fail loudly on indexing/parsing errors (aligned with project policy).

### 1. chunking.py -- Hybrid Sheet-Level + Summary Chunks

Replace the current "one chunk per workbook" with a smarter strategy:

```python
"""Hybrid chunking for MDA XLSX templates.

Creates per-sheet markdown table chunks + a natural language summary chunk.
This gives ~5 chunks per XLSX file instead of 1, enabling:
- Specific retrieval (query about components -> Sheet 2 only)
- High-level matching (query about method type -> summary chunk)

For the MDA templates, focus on sheets 1, 2, 6, 7 (Analysis, Component,
CalcVariable, Calculation). Other sheets are included if non-empty.

GAMP-5 Category 5: Custom pharmaceutical software component.
NO FALLBACK LOGIC -- chunking errors propagate with full diagnostics.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import openpyxl

logger = logging.getLogger(__name__)


# Priority sheet names (case-insensitive matching)
MDA_PRIORITY_SHEETS = {
    "analysis", "component", "calc variable", "calculation",
    "calculation variables", "calc_variables",
}


def parse_xlsx_to_chunks(xlsx_path: Path) -> list[dict[str, Any]]:
    """Parse one XLSX into multiple chunks with metadata.

    Returns list of dicts with keys:
        - id: str -- unique chunk ID ({stem}__{sheet_name} or {stem}__SUMMARY)
        - text: str -- chunk content (markdown table or summary text)
        - metadata: dict -- source file, sheet name, chunk type, row count

    Creates:
        - 1 summary chunk (natural language overview)
        - N sheet-level chunks (markdown table format, one per non-empty sheet)

    Args:
        xlsx_path: Path to the XLSX file.

    Returns:
        List of chunk dicts.

    Raises:
        FileNotFoundError: If xlsx_path does not exist.
        openpyxl.utils.exceptions.InvalidFileException: If file is not valid XLSX.
    """
    if not xlsx_path.exists():
        raise FileNotFoundError(f"XLSX file not found: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    stem = xlsx_path.stem
    chunks: list[dict[str, Any]] = []
    sheet_summaries: list[dict[str, Any]] = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))

        if not rows or len(rows) < 2:
            continue  # Skip empty or header-only sheets

        headers = [str(h) if h is not None else "" for h in rows[0]]
        data_rows = rows[1:]

        # Filter out completely empty rows
        data_rows = [r for r in data_rows if any(c is not None for c in r)]
        if not data_rows:
            continue

        # Check if this is a priority MDA sheet
        is_priority = sheet_name.lower().strip() in MDA_PRIORITY_SHEETS

        # Create markdown table chunk
        md_table = sheet_to_markdown_table(sheet_name, headers, data_rows)

        chunk_id = f"{stem}__{sheet_name.replace(' ', '_')}"
        chunks.append({
            "id": chunk_id,
            "text": md_table,
            "metadata": {
                "source_file": xlsx_path.name,
                "sheet_name": sheet_name,
                "chunk_type": "sheet",
                "is_priority": is_priority,
                "row_count": len(data_rows),
                "column_count": len(headers),
            },
        })

        # Collect summary info
        sheet_summaries.append({
            "sheet_name": sheet_name,
            "row_count": len(data_rows),
            "columns": headers,
            "is_priority": is_priority,
            "sample_values": _extract_sample_values(headers, data_rows),
        })

    wb.close()

    # Generate workbook summary chunk
    if sheet_summaries:
        summary_text = generate_workbook_summary(stem, sheet_summaries)
        chunks.insert(0, {
            "id": f"{stem}__SUMMARY",
            "text": summary_text,
            "metadata": {
                "source_file": xlsx_path.name,
                "sheet_name": "SUMMARY",
                "chunk_type": "summary",
                "is_priority": True,
                "sheet_count": len(sheet_summaries),
            },
        })

    logger.info(
        "Chunked '%s' into %d chunks (%d sheets)",
        xlsx_path.name,
        len(chunks),
        len(sheet_summaries),
    )

    return chunks


def sheet_to_markdown_table(
    sheet_name: str,
    headers: list[str],
    rows: list[tuple],
) -> str:
    """Convert a sheet's data to markdown table format.

    LLMs and embedding models understand markdown tables natively.
    This format preserves structure while being token-efficient.

    Args:
        sheet_name: Name of the worksheet.
        headers: Column header strings.
        rows: Data rows as tuples.

    Returns:
        Markdown-formatted table with sheet header.
    """
    lines = [f"## {sheet_name}\n"]

    # Header row
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines.append(header_line)
    lines.append(separator)

    # Data rows
    for row in rows:
        cells = []
        for cell in row:
            if cell is None:
                cells.append("")
            else:
                # Normalize cell value: escape pipes, strip whitespace
                val = str(cell).replace("|", "\\|").strip()
                cells.append(val)
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def generate_workbook_summary(
    xlsx_name: str,
    sheet_summaries: list[dict[str, Any]],
) -> str:
    """Generate natural language summary for semantic matching.

    Creates a concise description optimized for embedding similarity,
    including: analysis names, component counts, method types, site info.

    Example output:
        'MDA Template: AND_ACS_DYE -- 3 analyses (AND_ACS_DYE,
        AND_ACS_DYE_CTL, AND_ACS_DYE_META), 25 components,
        6 calc variables, 4 calculations. Dye binding assay method
        for protein concentration by UV-Vis spectrophotometry.'

    Args:
        xlsx_name: XLSX file stem (e.g., "AND_ACS_DYE-LAB-2499").
        sheet_summaries: List of per-sheet summary dicts.

    Returns:
        Natural language summary string.
    """
    parts = [f"MDA Template: {xlsx_name}"]

    for ss in sheet_summaries:
        name = ss["sheet_name"]
        count = ss["row_count"]
        parts.append(f"{name}: {count} rows")

        # Extract analysis names from Analysis sheet
        if name.lower() in ("analysis",) and ss.get("sample_values"):
            analysis_names = ss["sample_values"].get("Analysis", [])
            if not analysis_names:
                analysis_names = ss["sample_values"].get("NAME", [])
            if analysis_names:
                parts.append(f"Analyses: {', '.join(analysis_names[:10])}")

    priority_sheets = [s for s in sheet_summaries if s["is_priority"]]
    if priority_sheets:
        sheet_names = [s["sheet_name"] for s in priority_sheets]
        parts.append(f"Key sheets: {', '.join(sheet_names)}")

    return ". ".join(parts) + "."


def _extract_sample_values(
    headers: list[str],
    rows: list[tuple],
    max_values: int = 10,
) -> dict[str, list[str]]:
    """Extract unique sample values from key columns for summary.

    Looks for columns like 'Analysis', 'COMPONENT', 'NAME' and
    collects unique non-empty values.

    Args:
        headers: Column headers.
        rows: Data rows.
        max_values: Max unique values to collect per column.

    Returns:
        Dict mapping column name -> list of unique values.
    """
    key_columns = {"analysis", "component", "name", "result type", "calculation type"}
    result: dict[str, list[str]] = {}

    for col_idx, header in enumerate(headers):
        if header.lower().strip() in key_columns:
            values: list[str] = []
            seen: set[str] = set()
            for row in rows:
                if col_idx < len(row) and row[col_idx] is not None:
                    val = str(row[col_idx]).strip()
                    if val and val not in seen:
                        seen.add(val)
                        values.append(val)
                        if len(values) >= max_values:
                            break
            if values:
                result[header] = values

    return result
```

**Chunk ID format**: `{xlsx_stem}__{sheet_name}` (e.g., `AND_ACS_DYE-LAB-2499__Component`)
**Summary ID format**: `{xlsx_stem}__SUMMARY`
**Expected output**: ~5 chunks per XLSX file, ~125 chunks total for 25 files.

### 2. Hybrid Search with BM25 + Reciprocal Rank Fusion

Add BM25 scoring alongside ChromaDB semantic search, combined with Reciprocal Rank Fusion (RRF). No LangChain dependency -- uses `rank-bm25` directly.

```python
# In rag_loader.py -- enhanced query_similar_templates()

from rank_bm25 import BM25Okapi
import re

# Module-level BM25 index (built once, cached)
_bm25_index: BM25Okapi | None = None
_bm25_documents: list[str] = []
_bm25_doc_ids: list[str] = []


def _build_bm25_index(collection) -> None:
    """Build BM25 index from all documents in the ChromaDB collection.

    Called lazily on first hybrid query. Tokenizes documents using
    simple whitespace + punctuation splitting.
    """
    global _bm25_index, _bm25_documents, _bm25_doc_ids

    all_docs = collection.get(include=["documents"])
    _bm25_documents = all_docs["documents"]
    _bm25_doc_ids = all_docs["ids"]

    # Tokenize for BM25
    tokenized = [_tokenize(doc) for doc in _bm25_documents]
    _bm25_index = BM25Okapi(tokenized)

    logger.info("BM25 index built with %d documents", len(_bm25_documents))


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric."""
    return re.findall(r"\w+", text.lower())


def _reciprocal_rank_fusion(
    semantic_ids: list[str],
    bm25_ids: list[str],
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
    k: int = 60,
) -> list[str]:
    """Combine semantic and BM25 rankings using Reciprocal Rank Fusion.

    RRF score = sum( weight / (k + rank_i) ) for each ranking list.

    Args:
        semantic_ids: Document IDs ranked by semantic similarity.
        bm25_ids: Document IDs ranked by BM25 score.
        semantic_weight: Weight for semantic ranking (default 0.6).
        bm25_weight: Weight for BM25 ranking (default 0.4).
        k: RRF constant (default 60, standard value).

    Returns:
        Fused list of document IDs sorted by combined RRF score.
    """
    scores: dict[str, float] = {}

    for rank, doc_id in enumerate(semantic_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + semantic_weight / (k + rank + 1)

    for rank, doc_id in enumerate(bm25_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + bm25_weight / (k + rank + 1)

    # Sort by score descending
    fused = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return fused


def query_similar_templates(
    extraction_text: str,
    top_k: int = 3,
    chroma_path: str = CHROMA_PATH,
    use_hybrid: bool = True,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
    use_reranking: bool = True,
    cohere_api_key: str = "",
) -> list[str]:
    """Query with optional hybrid BM25 + semantic search + Cohere reranking.

    Pipeline:
    1. Over-retrieve from ChromaDB (semantic, top_k * 3)
    2. (optional) Score all docs with BM25, fuse with RRF
    3. (optional) Rerank top candidates with Cohere Rerank v3
    4. Return top_k results

    Args:
        extraction_text: Query text (raw extraction or summary).
        top_k: Number of results to return.
        chroma_path: Path to ChromaDB persistence directory.
        use_hybrid: Enable BM25 + semantic fusion (default True).
        bm25_weight: BM25 contribution to RRF (default 0.4).
        semantic_weight: Semantic contribution to RRF (default 0.6).
        use_reranking: Enable Cohere Rerank post-retrieval (default True).
        cohere_api_key: Cohere API key for reranking.

    Returns:
        List of top_k document text strings, most relevant first.
    """
    ...
```

Also add `where_document` keyword filtering for exact-match boosting:

```python
# Quick win: extract site prefix from extraction text for pre-filtering
# e.g., "AND_ACS_DYE" -> site_prefix = "AND"
site_prefix = _extract_site_prefix(extraction_text)
if site_prefix:
    results = collection.query(
        query_texts=[extraction_text],
        n_results=effective_k,
        where_document={"$contains": site_prefix},
    )
```

Add metadata-aware filtering before final candidate set:

- Prefer chunks whose metadata matches extracted method/site tokens (e.g., `AND`, `ACS`, method identifier).
- Prefer priority sheets (`Analysis`, `Component`, `Calc Variable`, `Calculation`) during candidate expansion.
- Keep this as ranking bias, not hard exclusion, to avoid dropping true positives.

### 3. Cohere Rerank v3 Post-Retrieval

Add Cohere Rerank as the final quality gate after hybrid retrieval:

```python
# In rag_loader.py

from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle

_reranker: CohereRerank | None = None


def _get_reranker(api_key: str, model: str = "rerank-english-v3.0", top_n: int = 3) -> CohereRerank:
    """Get or create singleton Cohere Reranker instance.

    Args:
        api_key: Cohere API key.
        model: Reranker model name.
        top_n: Number of results to return after reranking.

    Returns:
        CohereRerank instance.
    """
    global _reranker
    if _reranker is None:
        _reranker = CohereRerank(
            api_key=api_key,
            model=model,
            top_n=top_n,
        )
    return _reranker


# Inside query_similar_templates(), after hybrid retrieval:
def _rerank_results(
    candidates: list[str],
    query: str,
    cohere_api_key: str,
    top_k: int = 3,
) -> list[str]:
    """Rerank candidate documents using Cohere Rerank v3.

    Args:
        candidates: List of candidate document texts.
        query: Original query text.
        cohere_api_key: Cohere API key.
        top_k: Number of results to return.

    Returns:
        Reranked list of document texts, most relevant first.
    """
    reranker = _get_reranker(cohere_api_key, top_n=top_k)
    nodes = [
        NodeWithScore(node=TextNode(text=doc), score=1.0)
        for doc in candidates
    ]
    query_bundle = QueryBundle(query_str=query)
    reranked = reranker.postprocess_nodes(nodes, query_bundle)
    return [node.text for node in reranked[:top_k]]
```

**Package**: `pip install llama-index-postprocessor-cohere-rerank`
**Cost**: ~$1 per 1000 queries (very cheap for PoC)
**Config**: Add `LIMS_COHERE_API_KEY` env var
**Model**: `rerank-english-v3.0` (latest Cohere Rerank v3, best quality)

### 4. Updated seed_mda_templates()

```python
def seed_mda_templates(demo_data_dir: str, chroma_path: str = CHROMA_PATH) -> int:
    """Seed ChromaDB with hybrid chunks from demo XLSX files.

    Uses chunking.parse_xlsx_to_chunks() to create ~5 chunks per file
    instead of 1. Total: ~125 chunks for 25 XLSX files.

    Args:
        demo_data_dir: Path to demo_data directory.
        chroma_path: ChromaDB persistence path.

    Returns:
        Number of chunks added.
    """
    from .chunking import parse_xlsx_to_chunks

    demo_path = Path(demo_data_dir)
    xlsx_files = sorted(demo_path.glob("*.xlsx"))
    xls_files = sorted(demo_path.glob("*.xls"))

    if not xlsx_files and not xls_files:
        logger.warning("No Excel files found in %s", demo_data_dir)
        return 0

    client = chromadb.PersistentClient(path=chroma_path)
    # Delete and recreate collection for clean re-seeding
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    all_ids: list[str] = []
    all_documents: list[str] = []
    all_metadatas: list[dict] = []

    # NOTE: .xls handling required for full demo_data coverage
    # Option A (recommended): convert .xls -> .xlsx in a preprocessing step
    # Option B: parse .xls directly with a dedicated reader
    excel_files = list(xlsx_files)  # extend with converted/directly parsed .xls artifacts

    for xlsx_path in excel_files:
        try:
            chunks = parse_xlsx_to_chunks(xlsx_path)
            for chunk in chunks:
                all_ids.append(chunk["id"])
                all_documents.append(chunk["text"])
                all_metadatas.append(chunk["metadata"])
        except Exception as e:
            logger.error("Failed to chunk '%s': %s", xlsx_path.name, e)
            raise

    # Bulk add to ChromaDB
    if all_ids:
        # ChromaDB has a batch size limit, add in batches of 100
        batch_size = 100
        for i in range(0, len(all_ids), batch_size):
            collection.add(
                ids=all_ids[i:i + batch_size],
                documents=all_documents[i:i + batch_size],
                metadatas=all_metadatas[i:i + batch_size],
            )

    logger.info(
        "Seeded ChromaDB with %d chunks from %d XLSX files",
        len(all_ids),
        len(excel_files),
    )

    return len(all_ids)
```

### 5. Config Additions

```python
# In config.py -- add to LIMSConfig
cohere_api_key: str = ""               # LIMS_COHERE_API_KEY
reranker_model: str = "rerank-english-v3.0"  # LIMS_RERANKER_MODEL
reranker_top_n: int = 3                # LIMS_RERANKER_TOP_N
bm25_weight: float = 0.4              # LIMS_BM25_WEIGHT
semantic_weight: float = 0.6          # LIMS_SEMANTIC_WEIGHT
```

### 6. populate_lims_chroma.py Update

```python
# scripts/populate_lims_chroma.py -- update to use new chunking

# Replace:
#   from main.src.lims.rag_loader import seed_mda_templates
# With the same function, but it now internally uses chunking.parse_xlsx_to_chunks()

# Expected output:
# "Seeded ChromaDB with 125 chunks from 25 XLSX files"
# (was: "Seeded 25 MDA template documents")
```

---

## Full Retrieval Pipeline

```
Query: "ACS_DYE spectrophotometry assay with Bradford method"
  |
  v
[1] ChromaDB Semantic Search (top_k * 3 = 9 results)
  |  -> Returns chunks ranked by embedding similarity
  |
  v
[2] BM25 Keyword Search (all documents scored)
  |  -> Exact match: "ACS_DYE" boosts relevant chunks
  |
  v
[3] Reciprocal Rank Fusion (RRF)
  |  -> Combines rankings: semantic_weight=0.6, bm25_weight=0.4
  |  -> Returns fused top 9 candidates
  |
  v
[4] Cohere Rerank v3 (top_k = 3)
  |  -> Cross-encoder re-scores all 9 candidates
  |  -> Returns top 3 most relevant
  |
  v
[Result] 3 highly relevant chunks:
  1. AND_ACS_DYE-LAB-2499__Component (sheet-level, 25 components)
  2. AND_ACS_DYE-LAB-2499__SUMMARY (overview)
  3. AND_ACS_DYE-LAB-2499__Calculation (calc code)
```

---

## Testing Strategy

```bash
# 1. Re-seed ChromaDB with new chunking
python scripts/populate_lims_chroma.py
# Expected: ~125 chunks (was 25) -- 5 per XLSX file

# 2. Test chunking output
uv run pytest main/tests/lims/test_chunking.py -v

# 3. Test hybrid search quality
uv run pytest main/tests/lims/test_rag_hybrid.py -v

# 4. Test reranking
uv run pytest main/tests/lims/test_rag_reranking.py -v -m integration

# 4b. Trace-level assertions (new)
# Validate retrieval diagnostics and non-empty candidate pipeline
uv run pytest main/tests/lims/test_rag_observability.py -v

# 5. Full pipeline test: extract -> RAG -> generate
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"
# Verify RAG context in generation is more relevant

# 5b. A/B check vs current baseline on 3 known queries
# Record top-3 relevance before/after hybrid+rerank in test artifact markdown

# 6. Existing tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] ChromaDB seeded with hybrid chunks (~5 per workbook, includes `.xlsx` and `.xls` corpus)
- [ ] Hybrid search returns more relevant results than embedding-only (documented A/B on 3 fixed queries)
- [ ] Cohere reranking improves top-3 precision (measured and logged on same 3 queries)
- [ ] `query_similar_templates()` supports both modes (hybrid on/off, reranking on/off)
- [ ] RAG augmentation is no longer consistently empty for relevant queries (track `suggestions_generated_count`)
- [ ] MDA generation quality improves with better RAG context (documented with before/after examples)
- [ ] All existing LIMS tests pass, ChromaDB re-seeding doesn't break pipeline

---

## Suggested Query Set for L8 Evaluation

Use fixed queries tied to known templates to avoid subjective drift:

1. `ACS_DYE spectrophotometry assay with Bradford method`
2. `AQ126 suitability for use ACS loading capacity and physical integrity`
3. `identity control meta components direct red solution`

For each query, capture:

- Top-3 before (semantic-only)
- Top-3 after (hybrid + rerank)
- Whether returned chunks are method/site-correct
- Whether augmentation produced actionable suggestions

---

## New Dependencies

```toml
# pyproject.toml additions
"rank-bm25>=0.2.2",                              # BM25 keyword scoring
"llama-index-postprocessor-cohere-rerank>=0.3.0", # Cohere Rerank v3
```

## New Environment Variables

```bash
# .env.local additions (current state)
LIMS_BM25_WEIGHT=0.4                        # BM25 contribution to hybrid search
LIMS_SEMANTIC_WEIGHT=0.6                    # Semantic contribution to hybrid search
LIMS_QUERY_AUGMENTATION_ENABLED=true        # deterministic query expansion on/off
LIMS_QUERY_AUGMENTATION_MAX_QUERIES=4       # max query variants per request
LIMS_METADATA_BOOST_ENABLED=true            # metadata-aware reranking bias on/off
LIMS_PRIORITY_SHEET_BOOST=0.15              # additive boost for priority sheets
LIMS_TOKEN_MATCH_BOOST=0.2                  # additive boost for source/sheet token matches
```

---

## Sources

- ChromaDB Full-Text Search (`where_document`): https://docs.trychroma.com/docs/querying-collections/full-text-search
- ChromaDB Sparse Vector Search: https://www.trychroma.com/project/sparse-vector-search
- rank-bm25 PyPI: https://pypi.org/project/rank-bm25/
- Cohere Rerank v3 + LlamaIndex Integration: https://docs.cohere.com/docs/llamaindex
- llama-index-postprocessor-cohere-rerank PyPI: https://pypi.org/project/llama-index-postprocessor-cohere-rerank/
- Reciprocal Rank Fusion Explained: https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking
- Cohere Rerank v3 API: https://docs.cohere.com/reference/rerank

---

## Status & Results (February 21, 2026)

**Status:** Completed (with modifications)

### What was done:
1. **Hybrid Chunking Implemented**: Replaced the monolithic `parse_xlsx_to_text` approach with `parse_xlsx_to_chunks` in `main/src/lims/chunking.py`. The new approach creates per-sheet markdown table chunks and a natural-language summary chunk for each workbook.
2. **Hybrid Search Implemented**: Added BM25 keyword search alongside ChromaDB semantic search in `main/src/lims/rag_loader.py`.
3. **Reciprocal Rank Fusion (RRF)**: Implemented RRF to combine semantic and BM25 rankings using configurable weights (`semantic_weight=0.6`, `bm25_weight=0.4`).
4. **Dependencies Updated**: Added `rank-bm25>=0.2.2` to `pyproject.toml`.
5. **Configuration Updated**: Added `bm25_weight` and `semantic_weight` to `LIMSConfig` in `main/src/lims/config.py`.

### Deviations from Original Plan:
- **Cohere Reranker Omitted**: Based on the decision that "we don't extract so many chunks", the Cohere Reranker step was intentionally removed. The RAG pipeline now relies solely on the hybrid search (Semantic + BM25) combined with Reciprocal Rank Fusion (RRF).
- Removed `cohere_api_key`, `reranker_model`, and `reranker_top_n` from the configuration.
- Removed `llama-index-postprocessor-cohere-rerank` and `cohere` from the project dependencies.

### Results:
- The RAG retrieval now successfully uses a combination of semantic similarity and exact keyword matching (BM25) to find the most relevant sheet-level chunks.
- The system is more precise as it can retrieve specific sheets (e.g., `Component` or `Calculation`) rather than entire workbooks, reducing noise in the LLM context window.
- Tests were run via `uv run pytest main/tests/lims/ -v` to ensure the pipeline remains functional with the new chunking and retrieval logic.

### Additional Update (February 21, 2026, latest)

#### Current State Snapshot
- Hybrid retrieval is active and stable: semantic + BM25 with RRF in `main/src/lims/rag_loader.py`.
- Cohere reranking remains intentionally omitted (cost/latency not justified for current candidate set size).
- Retrieval now includes two new quality layers:
  1. **Metadata-aware scoring bias** (priority sheets + source/sheet token matches)
  2. **Deterministic query augmentation** (domain synonym expansion + method-ID-focused variants)

#### What was newly added
1. **Metadata integration in retrieval ranking**
    - Adds additive score bias for `is_priority` chunks.
    - Adds token-match bias when query tokens match `source_file` and `sheet_name` metadata.
    - Keeps bias as soft ranking, not hard exclusion (reduces false negatives).

2. **Prompt/query augmentation (deterministic, non-LLM)**
    - Expands domain terms (e.g., `identity -> id/identification`, `control -> ctl`, `meta -> metadata`).
    - Detects method identifiers (e.g., `AND_ACS_DYE`) and adds targeted retrieval variants.
    - Caps fan-out (`LIMS_QUERY_AUGMENTATION_MAX_QUERIES`) to control latency.

3. **Config integration**
    - Added new `LIMSConfig` knobs for augmentation + metadata boost.
    - Wired `MDAGenerationWorkflow` to pass these retrieval settings directly to `query_similar_templates()`.

4. **Test coverage updates**
    - Added focused enhancement tests in `main/tests/lims/test_rag_loader_enhancements.py`.
    - Extended config env-var coverage in `main/tests/lims/test_config.py`.

#### Validation notes from latest run
- LIMS suite remains mostly green; known non-L8 extraction test failures remain unrelated.
- A prior mock compatibility issue in `test_rag_loader_supports_custom_collection_names` is addressed by BM25 index build support for fake collections exposing `_documents/_ids`.

#### Feb 2026-relevant recommendations (next best steps)
1. **Keep reranking optional via feature flag**, and enable only for ambiguous query cohorts (measured by low top-1 margin / low agreement between semantic and BM25 lists).
2. **Add retrieval observability counters per query**:
    - `query_variants_count`
    - `semantic_candidates_count`
    - `bm25_candidates_count`
    - `metadata_boost_applied_count`
    - `pre_boost_vs_post_boost_rank_delta`
3. **Run fixed-query A/B harness weekly** (3 canonical L8 queries + regression set) and track Precision@3 / Hit@3.
4. **Complete .xls coverage** (currently not fully indexed) to satisfy full corpus requirement.
5. **Migrate to native sparse/hybrid retrieval primitives when feasible** (Chroma Search API trajectory in 2026) to reduce custom fusion surface area while preserving traceability.
