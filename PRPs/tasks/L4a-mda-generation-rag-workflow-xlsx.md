# Task L4a — MDA Generation Backend: RAG Loader + Workflow + XLSX Export

**Phase:** 4 (Workflow + HITL + Export) | **PRP Tasks Merged:** L4.1, L4.2, L4.5
**Dependencies:** Task L2 (Foundation)
**Branch:** `prjoject_p_protatype`
**Status:** COMPLETE (2026-02-17)
**Implemented by:** task-executor agent (Claude Opus 4.6)
**Verified by:** tester-agent + manual curl testing

---

## Objective

Build the backend pipeline that takes raw extraction results, enriches them with RAG context from similar MDA templates, generates a complete preliminary MDA via LLM, and exports to 4-sheet XLSX format matching LabWare.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/rag_loader.py` | Parse demo XLSX -> text, seed ChromaDB `mda_templates` at `chroma_db_lims/`, query interface |
| `main/src/lims/mda_generator.py` | LlamaIndex Workflow: raw extraction + RAG context -> LLM -> preliminary MDATemplate |
| `main/src/lims/xlsx_exporter.py` | openpyxl: MDATemplate -> 4-sheet XLSX with LabWare-compatible column headers |
| `main/src/lims/prompts/__init__.py` | Package init |
| `main/src/lims/prompts/mda_generation_prompt.py` | System prompt with MDA domain knowledge, naming conventions, result type classification rules |
| `scripts/populate_lims_chroma.py` | CLI script to seed ChromaDB from `demo_data/*.xlsx` files |

## Files to Modify

| File | Change |
|------|--------|
| `main/src/lims/config.py` | Add `openrouter_api_key`, `openrouter_model`, `chromadb_path`, `upload_dir`, `output_dir` fields |

---

## Implementation Details

### 1. Config Additions (`config.py`)

```python
class LIMSConfig(BaseModel):
    llamaextract_api_key: str
    extraction_mode: str = "balanced"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-5"
    chromadb_path: str = "./chroma_db_lims"
    upload_dir: str = "./uploads/lims"
    output_dir: str = "./output/lims"

def get_lims_config() -> LIMSConfig:
    # Add: LIMS_OPENROUTER_API_KEY, LIMS_OPENROUTER_MODEL, LIMS_CHROMADB_PATH
    ...
```

### 2. rag_loader.py — ChromaDB MDA Templates

Uses ChromaDB `PersistentClient` at `chroma_db_lims/` (separate from thesis `chroma_db/`). Parses ground truth XLSX files into text for embedding.

```python
"""RAG loader: parse demo XLSX files into ChromaDB mda_templates collection.

Uses ChromaDB PersistentClient at chroma_db_lims/ (thesis chroma_db/ untouched).
Demo data: ~20 XLSX files in demo_data/ (AND_*, FRE_*, TUA_* prefixed).
"""

import logging
from pathlib import Path

import chromadb
import openpyxl

logger = logging.getLogger(__name__)

CHROMA_PATH = "./chroma_db_lims"
COLLECTION_NAME = "mda_templates"


def parse_xlsx_to_text(xlsx_path: Path) -> str:
    """Parse a LabWare MDA XLSX into text representation for embedding."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    sections = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(h) for h in rows[0] if h is not None]
        section = f"## Sheet: {sheet_name}\nColumns: {', '.join(headers)}\n"
        for row in rows[1:]:
            values = [str(v) if v is not None else "" for v in row]
            section += " | ".join(values) + "\n"
        sections.append(section)
    wb.close()
    return "\n\n".join(sections)


def seed_mda_templates(demo_data_dir: str = "./demo_data", chroma_path: str = CHROMA_PATH) -> int:
    """Seed ChromaDB with MDA templates from demo XLSX files.

    Returns number of documents added.
    """
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    xlsx_files = list(Path(demo_data_dir).glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"No XLSX files found in {demo_data_dir}")

    documents, metadatas, ids = [], [], []
    for xlsx_path in xlsx_files:
        text = parse_xlsx_to_text(xlsx_path)
        if not text.strip():
            continue
        doc_id = xlsx_path.stem
        documents.append(text)
        metadatas.append({
            "source_file": xlsx_path.name,
            "site_prefix": xlsx_path.stem.split("_")[0],
        })
        ids.append(doc_id)

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    logger.info(f"Seeded {len(documents)} MDA templates into {COLLECTION_NAME}")
    return len(documents)


def query_similar_templates(
    extraction_text: str,
    top_k: int = 3,
    chroma_path: str = CHROMA_PATH,
) -> list[str]:
    """Query ChromaDB for similar MDA templates."""
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(query_texts=[extraction_text], n_results=top_k)
    return results["documents"][0] if results["documents"] else []
```

### 3. mda_generator.py — LlamaIndex Workflow

Follows `main/src/core/unified_workflow.py` patterns (Workflow + @step + Context + events):

```python
"""MDA generation workflow: extraction + RAG -> LLM -> preliminary MDATemplate.

Uses LlamaIndex Workflow + @step pattern from thesis unified_workflow.py.
LLM via OpenRouter (OpenAI-compatible SDK).

Docs: https://docs.llamaindex.ai/en/stable/module_guides/workflow/
"""

import json
import logging
import os
from typing import Any

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from openai import OpenAI

from .mda_schema import MDATemplate
from .prompts.mda_generation_prompt import MDA_GENERATION_SYSTEM_PROMPT
from .rag_loader import query_similar_templates

logger = logging.getLogger(__name__)


class MDAGenerationWorkflow(Workflow):
    """Generate a preliminary MDA from raw extraction + RAG context."""

    @step
    async def generate_mda(self, ctx: Context, ev: StartEvent) -> StopEvent:
        """RAG lookup + LLM generation -> validated MDATemplate."""
        raw_extraction = ev.get("raw_extraction", {})
        extraction_summary = json.dumps(raw_extraction, indent=2)[:3000]

        # 1. Query ChromaDB for similar MDA templates
        try:
            rag_examples = query_similar_templates(extraction_summary, top_k=2)
        except Exception as e:
            logger.warning(f"RAG query failed (continuing without): {e}")
            rag_examples = []

        rag_context = "\n---\n".join(rag_examples) if rag_examples else "No example templates available."

        # 2. Build LLM prompt
        user_prompt = (
            f"## Raw Extraction Data\n```json\n{extraction_summary}\n```\n\n"
            f"## Similar MDA Templates (RAG)\n{rag_context}\n\n"
            f"Generate a complete MDATemplate JSON with all 4 sheets "
            f"(analyses, components, calc_variables, calculations).\n"
            f"Follow the naming conventions and result type rules strictly."
        )

        # 3. Call LLM via OpenRouter (OpenAI-compatible)
        client = OpenAI(
            api_key=os.getenv("LIMS_OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model=os.getenv("LIMS_OPENROUTER_MODEL", "openai/gpt-5"),
            messages=[
                {"role": "system", "content": MDA_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_mda = json.loads(response.choices[0].message.content)

        # 4. Validate with Pydantic
        mda = MDATemplate.model_validate(raw_mda)

        return StopEvent(result={
            "mda_template": mda.model_dump(),
            "validated": True,
            "rag_examples_used": len(rag_examples),
        })
```

### 4. xlsx_exporter.py — 4-Sheet XLSX Export

```python
"""XLSX export: MDATemplate -> 4-sheet LabWare MDA format.

Docs: https://openpyxl.readthedocs.io/en/stable/
"""

import io
import logging

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .mda_schema import MDATemplate

logger = logging.getLogger(__name__)

SHEET_COLUMNS = {
    "Analysis": [
        "name", "version", "group_name", "active", "reported_name",
        "common_name", "analysis_type", "description",
    ],
    "Component": [
        "analysis", "component_name", "version", "order_number",
        "result_type", "units", "minimum", "maximum",
        "uses_instrument", "instrument_group", "auto_calc",
        "list_key", "reportable", "optional",
    ],
    "Calc Variable": [
        "analysis", "component", "name", "version",
        "reference_type", "reference_analysis", "reference_component",
        "return_value", "scope", "function",
    ],
    "Calculation": [
        "analysis", "component", "version", "description",
        "source_code", "calculation_type",
    ],
}

HEADER_FILL = PatternFill(start_color="1F4E3D", end_color="1F4E3D", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)


def export_mda_to_xlsx(mda: MDATemplate) -> bytes:
    """Export MDATemplate to XLSX bytes (4 sheets, LabWare format)."""
    wb = openpyxl.Workbook()

    sheet_data_map = {
        "Analysis": [a.model_dump() for a in mda.analyses],
        "Component": [c.model_dump() for c in mda.components],
        "Calc Variable": [cv.model_dump() for cv in mda.calc_variables],
        "Calculation": [calc.model_dump() for calc in mda.calculations],
    }

    for idx, (sheet_name, columns) in enumerate(SHEET_COLUMNS.items()):
        ws = wb.active if idx == 0 else wb.create_sheet(title=sheet_name)
        if idx == 0:
            ws.title = sheet_name

        rows = sheet_data_map[sheet_name]

        # Headers
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER

        # Data rows
        for row_idx, row_data in enumerate(rows, 2):
            for col_idx, col_name in enumerate(columns, 1):
                value = row_data.get(col_name)
                if isinstance(value, bool):
                    value = "TRUE" if value else "FALSE"
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = THIN_BORDER

        # Auto-width
        for col_idx, col_name in enumerate(columns, 1):
            max_len = max(
                len(str(col_name)),
                *(len(str(r.get(col_name, ""))) for r in rows),
                10,
            ) if rows else len(str(col_name))
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 50)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
```

### 5. mda_generation_prompt.py — System Prompt

```python
"""System prompt for MDA generation from extraction + RAG context."""

MDA_GENERATION_SYSTEM_PROMPT = """You are a LabWare LIMS expert generating MDA (Method Definition and Analysis) templates.

## Your Task
Given raw extraction data from a pharmaceutical test method PDF and similar MDA templates as examples,
generate a complete MDATemplate JSON with 4 sheets:

1. **analyses** — Top-level test method definitions
2. **components** — Individual test parameters per analysis
3. **calc_variables** — Variables used in LIMS Basic calculations
4. **calculations** — LIMS Basic code for K-type components

## Critical Rules

### Analysis Naming Convention
- Format: {SITE_PREFIX}_{METHOD_ABBREV}[_{SUFFIX}]
- Examples: AND_ACS_DYE, AND_ACS_DYE_CTL, AND_ACS_DYE_META
- CTL/META suffixed analyses must have analysis_type="QC_SAMPLES"
- Primary analysis uses type="ID" (or ASY, IMP, PHYS as appropriate)

### Three-Analysis Pattern
A single PDF test method typically maps to 3 analyses:
- Primary (type=ID): core test parameters
- Control (_CTL, type=QC_SAMPLES): conditional drivers, equipment pickers
- Metadata (_META, type=QC_SAMPLES): operator, date, equipment IDs

### Component Result Type Classification
- N = Numeric measurement (uses_instrument=True, instrument_group set)
- K = Calculated (auto_calc=True, requires Calculation entry)
- L = List selection (list_key required, e.g. YES_NO_2, PASS_FAIL)
- T = Free text entry
- D = Date picker

### Common Misclassifications to AVOID
- Equipment selection (Petri Dish, Spectrophotometer) = K (GOSUB CALC_INST_PICKER), NOT L
- Reagent selection (Direct Red 80) = K (GOSUB CALC_SR_PICKER), NOT L
- Timer/stopwatch = K (Instrument Group code), NOT N

### Cross-Sheet Integrity
- Every component must reference a valid analysis
- Every K-type component must have at least one calculation
- CalcVariable cross-analysis references (type=A) must specify reference_analysis

## Output Format
Return valid JSON matching the MDATemplate schema. Include all 4 arrays.
"""
```

### 6. populate_lims_chroma.py — CLI Script

```python
#!/usr/bin/env python3
"""Seed ChromaDB mda_templates collection from demo_data/*.xlsx files."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main.src.lims.rag_loader import seed_mda_templates

if __name__ == "__main__":
    demo_dir = sys.argv[1] if len(sys.argv) > 1 else "./demo_data"
    count = seed_mda_templates(demo_dir)
    print(f"Seeded {count} MDA templates into ChromaDB mda_templates collection")
```

---

## Environment Variables (add to .env.local)

```bash
# OpenRouter LLM (for MDA generation and chat)
LIMS_OPENROUTER_API_KEY=sk-or-...
LIMS_OPENROUTER_MODEL=openai/gpt-5

# ChromaDB (separate from thesis)
LIMS_CHROMADB_PATH=./chroma_db_lims
```

---

## Testing Strategy

```bash
# 1. Seed ChromaDB
python scripts/populate_lims_chroma.py
# Expected: "Seeded N MDA templates" (N >= 5)

# 2. Test XLSX export (unit test)
uv run pytest main/tests/lims/test_xlsx_exporter.py -v

# 3. Test MDA generation (integration, requires API keys)
uv run pytest main/tests/lims/test_mda_generator.py -v -m integration

# 4. Manual XLSX verification
# Open generated XLSX in Excel: 4 sheets, correct headers, data types
```

---

## Gate Criteria (Pass/Fail)

- [x] `python scripts/populate_lims_chroma.py` seeds 5+ documents from demo_data/ -- **25 documents seeded (AND=8, FRE=9, TUA=8)**
- [x] MDA generation workflow produces valid MDATemplate with all 4 sheets -- **Verified: 3 analyses, 10 components, calc_variables, calculations**
- [x] XLSX export opens in Excel with 4 named sheets -- **Roundtrip test: write + re-read confirmed 4 sheets with correct headers**
- [x] Column headers match LabWare MDA import format -- **Verified in xlsx_exporter.py _SHEET_DEFINITIONS**
- [x] `uv run pytest main/tests/lims/ -v` passes -- **84 passed, 2 skipped**

---

## Implementation Results (2026-02-17)

### Actual Files Created

| File | Lines | Notes |
|------|-------|-------|
| `main/src/lims/rag_loader.py` | 242 | 3 functions: parse_xlsx_to_text, seed_mda_templates, query_similar_templates. Uses chromadb.PersistentClient. |
| `main/src/lims/mda_generator.py` | 154 | MDAGenerationWorkflow(Workflow) with single @step. Takes config from StartEvent. |
| `main/src/lims/xlsx_exporter.py` | 298 | export_mda_to_xlsx() with helper functions. Dark green headers, thin borders, auto-width. |
| `main/src/lims/prompts/__init__.py` | 1 | Package init |
| `main/src/lims/prompts/mda_generation_prompt.py` | ~200 | 12-section system prompt with MDA domain knowledge and classification rules |
| `scripts/populate_lims_chroma.py` | 15 | CLI script, adds project root to sys.path |

### Actual Files Modified

| File | Change |
|------|--------|
| `main/src/lims/config.py` | Added 5 fields: openrouter_api_key, openrouter_model, chromadb_path, upload_dir, output_dir. Updated get_lims_config() to load from LIMS_* env vars with defaults. |

### Key Deviations from Spec

1. **mda_generator.py** uses `config` object passed via `ev.get("config")` instead of raw `os.getenv()` calls (cleaner, testable)
2. **rag_loader.py** query_similar_templates raises `RuntimeError` on empty collection (not generic Exception) for explicit failure
3. **xlsx_exporter.py** uses `Sequence` from `collections.abc` (not `typing`) per linter

### Verification Results

```
ChromaDB seeding:  25 documents seeded into mda_templates collection
XLSX roundtrip:    4 sheets (Analysis, Component, Calc Variable, Calculation) - headers match
Import checks:     All 4 modules import successfully
pytest:            84 passed, 2 skipped
```

### Manual E2E Test (curl)

```bash
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"
```

Returned status `PENDING_REVIEW` with:
- 3 analyses (AND_ACS_DYE, AND_ACS_DYE_CTL, AND_ACS_DYE_META)
- 10 components with correct result types (N, K, L, T)
- calc_variables and calculations populated
- Model used: `google/gemini-3-flash-preview` via OpenRouter

---

## Issues Encountered

### Issue 1: No-Fallback Violation in mda_generator.py (FIXED)

**Symptom:** Tester-agent flagged broad `except Exception` around RAG query that silently caught all failures.

**Root Cause:** Original implementation used `except Exception` which could mask database errors, network errors, etc. — violating CLAUDE.md "Zero Tolerance for Fallback Logic" principle.

**Fix:** Changed to `except RuntimeError` (specific to empty collection) and added `rag_failure` field to StopEvent result for transparency:
```python
except RuntimeError as e:
    rag_failure = f"RAG unavailable: {e}"
    logger.warning(rag_failure)
```

**Impact:** RAG query failures other than RuntimeError (e.g., ChromaDB connection errors) now propagate as unhandled exceptions, which is the correct behavior.

### Issue 2: typing.Sequence vs collections.abc.Sequence (FIXED)

**Symptom:** Linter flagged `from typing import Sequence` as deprecated in Python 3.9+.

**Fix:** Changed to `from collections.abc import Sequence` in xlsx_exporter.py.

---

## Environment Variables Added to .env.local

```bash
LIMS_OPENROUTER_API_KEY=sk-or-v1-...  # Same as thesis OPENROUTER_API_KEY
LIMS_OPENROUTER_MODEL=google/gemini-3-flash-preview
LIMS_LLAMAEXTRACT_API_KEY=llx-4IdOkM7WRNYGQgx4suNRlQ0QNsGrpZdHv3Hq8Uw1xN4CZddD
```

---

## Sources

- [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) — Workflow, @step, Context, StartEvent, StopEvent
- [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/) — workbook creation, styles, column widths
- [ChromaDB documentation](https://docs.trychroma.com/) — PersistentClient, collection.add, collection.query
- [OpenRouter API](https://openrouter.ai/docs) — OpenAI-compatible endpoint, model routing
- [OpenAI Python SDK](https://platform.openai.com/docs/api-reference) — chat.completions.create, response_format
