# Data Preparation Pipeline Status

## What Was Built
A Python data prep pipeline at `scripts/data_prep/` that transforms raw PaddleOCR PP-Structure JSON output into clean, structured artifacts for L10-L16 pharmaceutical test generation tasks.

## Pipeline Modules (all stdlib-only, no new dependencies)
| Module | Purpose |
|--------|---------|
| `ocr_cleaner.py` | Character-level OCR corrections (20+ regex patterns), confidence tracking |
| `spatial_reorderer.py` | Bbox-based reading order restoration, split title merging |
| `table_cleaner.py` | HTML table parsing, empty row removal, plain-text extraction |
| `section_builder.py` | SOP mode (numbered headers) + slide mode (page boundaries), hierarchy builder |
| `document_assembler.py` | Markdown assembly, OCR-cleaned sections, quality reports |
| `prepare_all.py` | CLI orchestrator, document discovery, manifest generation |

## Subagent Definitions
- `.claude/agents/data-prep-keyword-extractor.md` — produces L12 classifier keyword patterns
- `.claude/agents/data-prep-chunk-builder.md` — produces L13 RAG chunks for ChromaDB

## Current State (as of 2026-02-19)
### Source PDFs (4 total in `demo_data/SOP/`)
1. `CD-025658 (CALC_COMPONENTS_OPTIONAL).pdf` — 248 pages
2. `CD-025649(CALC_SR_PICKER).pdf` — 311 pages  
3. `gLIMS_Analysis_Build_Training_Slides.pdf` — NOT YET PARSED
4. `gLIMS_Code_STND_SOP-00597.pdf` — NOT YET PARSED

### Parsed Locations
- `output/ppstructure_cd025658/pages/` — CD-025658 full (248 pages, parsed first/separately)
- `output/sop_parsed/documents/cd-025649-calc-sr-picker/pages/` — CD-025649 (311 pages)
- `output/sop_parsed/documents/cd-025658-calc-components-optional/pages/` — CD-025658 subset (20 pages)

### Prepared Outputs (3 of ~5 documents done)
Location: `output/prepared/`
```
output/prepared/
├── per_document/
│   ├── ppstructure-cd025658/      (248 pg, 20 sec, 178 tbl, 29 OCR fixes)
│   ├── cd-025649-calc-sr-picker/  (311 pg, 25 sec, 142 tbl, 6 OCR fixes)
│   └── cd-025658-calc-components-optional/ (20 pg, 17 sec, 11 tbl, 21 OCR fixes)
├── L12_classifier/                (EMPTY — awaiting subagent)
├── L13_rag/                       (EMPTY — awaiting subagent)
└── manifest.json                  (3 docs, 579 pages, 62 sections, 331 tables)
```

## Run Command
```bash
python -m scripts.data_prep.prepare_all \
  --input-dirs output/ppstructure_cd025658 output/sop_parsed/documents \
  --output-dir output/prepared
```

## Remaining Work (see TaskList for dependencies)
1. Parse remaining 2 gLIMS PDFs (run `parse_sop_corpus.py` — ~40 min per PDF)
2. Re-run `prepare_all.py` on all input dirs
3. Invoke keyword-extractor subagent → populates `L12_classifier/`
4. Invoke chunk-builder subagent → populates `L13_rag/`
5. Verify final manifest

## Document-to-Collection Mapping (for L13)
- `lims_standards`: CD-025658 + SOP-00597
- `calculation_patterns`: gLIMS Training + CD-025649

## Key Design Decisions
- Stdlib only (no new pip dependencies)
- OCR corrections are character-level only — never invents missing words
- Spatial reordering uses bbox y_min with 20px tolerance for y-bands
- Section builder auto-detects SOP vs slide mode
- TOC pages skipped (>5 titles, <2 text blocks)
- Trailing dots in section numbers handled: "1." matches as section "1"
