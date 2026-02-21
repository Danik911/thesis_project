# LIMS-016: Extraction Optimization and LlamaCloud v2 Alignment

**Date:** 2026-02-21  
**Scope:** Improve AI4LIMS PDF extraction quality and traceability by wiring LlamaExtract configuration knobs and strengthening schema guidance.

## Summary
This update addresses a major runtime gap: extraction tuning settings were defined in config but not applied to LlamaExtract `ExtractConfig`. The extraction path now applies mode/target/model/context/metadata options directly.

## Root Findings
1. The LlamaCloud UI showing two processes is expected:
   - Parse stage (document parsing/layout/OCR)
   - Extract stage (schema-constrained field extraction)
2. Runtime bug found:
   - `pdf_extractor.py` used `ExtractConfig()` with defaults only.
   - `LIMS_EXTRACTION_MODE` and quality controls were effectively ignored.
3. Quality gaps in sample output vs LabWare ground truth were consistent with under-configured extraction and weak schema descriptions.

## Files Modified
| File | Change |
|------|--------|
| `main/src/lims/config.py` | Added extraction tuning fields + validation + env parsing |
| `main/src/lims/pdf_extractor.py` | Build `ExtractConfig` from `LIMSConfig` and include active config in extraction trace |
| `main/src/lims/extraction_schema.py` | Added field-level descriptions to improve extraction grounding |

## New Environment Variables
- `LIMS_EXTRACTION_MODE` (`fast|balanced|multimodal|premium`, default `multimodal`)
- `LIMS_EXTRACTION_TARGET` (`per_doc|per_page|per_table_row`, default `per_doc`)
- `LIMS_EXTRACT_PARSE_MODEL` (optional)
- `LIMS_EXTRACT_MODEL` (optional)
- `LIMS_EXTRACT_CITE_SOURCES` (default `true`)
- `LIMS_EXTRACT_USE_REASONING` (default `true`)
- `LIMS_EXTRACT_CONFIDENCE_SCORES` (default `true`)
- `LIMS_EXTRACT_NUM_PAGES_CONTEXT` (default `2`)
- `LIMS_EXTRACT_CHUNK_MODE` (`page|section`, default `page`)
- `LIMS_EXTRACT_PAGE_RANGE` (optional, 1-based ranges)
- `LIMS_EXTRACT_HIGH_RESOLUTION_MODE` (default `true`)
- `LIMS_EXTRACT_INVALIDATE_CACHE` (default `false`)

## Recommended Quality Profile (for complex pharma methods)
```env
LIMS_EXTRACTION_MODE=premium
LIMS_EXTRACTION_TARGET=per_doc
LIMS_EXTRACT_PARSE_MODEL=anthropic-sonnet-4.5
LIMS_EXTRACT_MODEL=openai-gpt-5
LIMS_EXTRACT_CITE_SOURCES=true
LIMS_EXTRACT_USE_REASONING=true
LIMS_EXTRACT_CONFIDENCE_SCORES=false
LIMS_EXTRACT_NUM_PAGES_CONTEXT=3
LIMS_EXTRACT_CHUNK_MODE=section
LIMS_EXTRACT_HIGH_RESOLUTION_MODE=true
LIMS_EXTRACT_INVALIDATE_CACHE=false
```

## Ground Truth Gap Notes (AQ126 sample)
Observed extraction (`llama-extract-...lims_extract_efc96qx0.json`) diverges from expected LabWare structure (`AND_ACS_DYE-LAB-2499_xlsx.md`) in key ways:
- Single analysis extracted instead of expected multi-analysis pattern for this family of methods.
- `result_type` emitted as semantic labels (`qualitative`, `percent`) instead of strict LabWare codes (`L/N/K/T/D`).
- Missing `calc_variables.reference_type/scope/function` in many records.

These issues should improve with stronger mode/model settings, richer schema descriptions, and (for larger docs) section chunking + context pages.

## Validation
- VS Code diagnostics on modified files: no errors.
- Ruff run: no blocking regressions introduced for this feature work.

## Next Steps
1. Run A/B extraction on same PDF with:
   - Baseline: `balanced` (current old behavior)
   - Optimized: `premium + sonnet-4.5 + gpt-5`
2. Compare field-level precision/recall against parsed ground truth markdown.
3. If needed, split extraction into two passes:
   - Pass A: analysis/component skeleton (`PER_DOC`)
   - Pass B: calc variables/calculations (`PER_DOC` with focused schema)
