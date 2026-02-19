# Task L13 — Standards RAG: Ingest CD-026972, SOP-00597 & Augmentation Prompt

**Phase:** 8d (Two-Layer Pipeline — Standards RAG) | **Dependencies:** L10 (Foundation Models)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2 days
**Status:** NOT STARTED (READY AFTER L10 — handoff updated 2026-02-19)

## Handoff Update (2026-02-19)

- **Implementation readiness:** Source standards/test-method PDFs are parsed and organized.
- **Canonical source artifacts:** `output/sop_parsed/manifest.json` and `output/prepared_l10l15/per_document/*/sections.json`.
- **Current output state:** `output/prepared_l10l15/L13_rag/` exists but is empty (chunks not built yet).
- **Collection mapping agreed in prep notes:**
    - `lims_standards`: SOP/governance standards docs
    - `calculation_patterns`: training material + calculation-heavy docs
- **Known data caveat:** Training slides document uses `document_id: UNKNOWN`; rely on slug/path metadata rather than ID-only matching.
- **Next agent action:** Implement loader/chunking, generate chunk artifacts into `output/prepared_l10l15/L13_rag/`, then seed ChromaDB collections.

---

## Objective

Create a standards document loader that ingests pharmaceutical standards PDFs (CD-026972, SOP-00597, gLIMS training materials) into new ChromaDB collections. Build an augmentation prompt that fills template gaps using standards knowledge via RAG. These standards provide the ~46% of MDA knowledge not found in individual test method PDFs.

---

## Context

The two-layer pipeline has an "AUGMENT" stage where AI fills template gaps using standards documents. Currently, `rag_loader.py` only handles `mda_templates` collection from XLSX files. We need:
- `lims_standards` collection: CD-026972, SOP-00597, gLIMS Training PDFs (section-based chunking)
- `calculation_patterns` collection: 200+ calc examples from training material (per-block chunking)

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/standards_loader.py` | ChromaDB loader for standards PDFs. Section-based chunking by headers. Supports `lims_standards` and `calculation_patterns` collections |
| `main/src/lims/prompts/augmentation_prompt.py` | System prompt for gap-filling from standards RAG context. Instructs LLM to cite source sections |

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `main/src/lims/rag_loader.py` | Extend to support configurable collection names (not just hardcoded `mda_templates`) | LOW |

---

## Implementation Details

### 1. standards_loader.py — Standards Document Loader

```python
"""ChromaDB loader for pharmaceutical standards documents.

Ingests standards PDFs (CD-026972, SOP-00597, gLIMS training) into
ChromaDB collections with section-based chunking for targeted retrieval.

Collections:
- lims_standards: General LIMS standards and SOPs
- calculation_patterns: Calculation code examples from training material

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = "./chroma_db_lims"


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
    ...


def seed_standards_collection(
    pdf_dir: str,
    collection_name: str = "lims_standards",
    chroma_path: str = DEFAULT_CHROMA_PATH,
) -> int:
    """Seed a ChromaDB collection from PDF files in the given directory.

    Args:
        pdf_dir: Directory containing PDF files.
        collection_name: ChromaDB collection name.
        chroma_path: Path to ChromaDB storage.

    Returns:
        Number of chunks added.

    Raises:
        FileNotFoundError: If pdf_dir doesn't exist or has no PDFs.
    """
    ...


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
    ...
```

### 2. augmentation_prompt.py

```python
"""Augmentation prompt for gap-filling from standards RAG.

Used in the AUGMENT stage of the two-layer pipeline.
The LLM receives: template gaps + standards context + test type info
and returns: suggested values with citations.
"""

AUGMENTATION_SYSTEM_PROMPT = """You are a pharmaceutical LIMS specialist filling gaps in MDA (Method Definition and Analysis) templates.

You are given:
1. A partially-filled MDA template with gaps marked as SME_REQUIRED
2. Standards document excerpts from CD-026972, SOP-00597, and gLIMS training materials
3. The test type classification (HPLC, LOD, Titration, Identity)

Your task:
- For each SME_REQUIRED gap, determine if the standards documents provide enough information to fill it
- If yes: provide the value and cite the source (document name, section number)
- If no: leave as SME_REQUIRED and explain what information is missing
- NEVER guess or hallucinate values not supported by the provided standards

Output format for each gap:
{
    "field_path": "components[3].units",
    "suggested_value": "mg/mL",
    "source": "CD-026972 Section 4.2.1",
    "confidence": 0.85,
    "reasoning": "Standard specifies concentration units for HPLC methods"
}

If you cannot fill a gap from the standards, return:
{
    "field_path": "components[3].units",
    "suggested_value": null,
    "source": "SME_REQUIRED",
    "confidence": 0.0,
    "reasoning": "No applicable standard found for this field"
}
"""
```

### 3. rag_loader.py modification

Add a `collection_name` parameter to `query_similar_templates()` and `seed_mda_templates()` so they support multiple collections instead of hardcoding `mda_templates`.

---

## Testing Strategy

```bash
# Standards loader tests
uv run pytest main/tests/lims/test_standards_loader.py -v

# Verify existing RAG tests still pass
uv run pytest main/tests/lims/ -v
```

---

## Gate Criteria

- [ ] `chunk_by_sections()` correctly splits standards text at headers
- [ ] `seed_standards_collection()` ingests PDFs and creates ChromaDB collection
- [ ] `query_standards()` returns relevant sections for LIMS queries
- [ ] Augmentation prompt produces structured gap-fill suggestions
- [ ] `rag_loader.py` supports configurable collection names
- [ ] All existing LIMS tests pass
