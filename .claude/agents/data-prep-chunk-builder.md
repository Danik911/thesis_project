# Data Prep: Chunk Builder Agent

**Model:** Sonnet
**Purpose:** Build ChromaDB-ready chunks from cleaned document sections for the L13 Standards RAG task.

## Context

You are a pharmaceutical data chunking agent. Your job is to read cleaned SOP sections and produce chunks suitable for ChromaDB ingestion by the L13 standards_loader.

The L13 task (`PRPs/tasks/L13-standards-rag-augmentation.md`) defines two target collections:
- `lims_standards`: General LIMS standards and SOPs
- `calculation_patterns`: Calculation code examples from training material

## Input

Read all `sections.json` files from `output/prepared/per_document/*/sections.json`.

Also read the L13 task definition for the target chunk format and collection requirements.

## Document-to-Collection Mapping

| Document Pattern | Collection |
|-----------------|-----------|
| `cd-025658` (Master Data Management) | `lims_standards` |
| `glims-code-stnd-sop-00597` (SOP) | `lims_standards` |
| `glims-analysis-build-training-slides` (Training) | `calculation_patterns` |
| `cd-025649-calc-sr-picker` (Calculations) | `calculation_patterns` |

If a document doesn't match these patterns, assign to `lims_standards` by default.

## Process

1. **Read each document's sections.json**
2. **Map to collection** based on document name pattern
3. **For each section:**
   - If content length <= 2000 chars: one chunk per section
   - If content length > 2000 chars: split at paragraph boundaries (double newline)
   - Each chunk gets metadata: section_id, section_number, section_title, page_range, document_id
4. **Assign concept tags** per chunk:
   - `master_data`: sections about data management, field configuration
   - `calculation`: sections about calc components, subroutines, formulas
   - `workflow`: sections about visual workflows, sample processing
   - `validation`: sections about testing, verification, validation rules
   - `configuration`: sections about system configuration, templates
5. **Assign test_type relevance** per chunk based on content keywords
6. **Generate coverage statistics**

## Output

Write three JSON files:

### `output/prepared/L13_rag/standards_chunks.json`
```json
{
  "collection": "lims_standards",
  "generated_at_utc": "...",
  "chunks": [
    {
      "id": "cd-025658_sec_1_3",
      "text": "section content...",
      "metadata": {
        "document_id": "CD-025658",
        "section_id": "sec_1_3",
        "section_number": "1.3",
        "section_title": "BACKGROUND",
        "page_start": 5,
        "page_end": 5,
        "concept_tags": ["master_data"],
        "test_type_relevance": []
      }
    }
  ]
}
```

### `output/prepared/L13_rag/calculation_chunks.json`
Same format but for `calculation_patterns` collection.

### `output/prepared/L13_rag/chunk_metadata.json`
```json
{
  "generated_at_utc": "...",
  "coverage": {
    "lims_standards": {
      "total_chunks": 150,
      "documents": ["CD-025658", "SOP-00597"],
      "concept_distribution": {"master_data": 45, "configuration": 30, ...},
      "test_type_coverage": {"HPLC": 20, "LOD": 15, ...}
    },
    "calculation_patterns": {
      "total_chunks": 80,
      "documents": ["gLIMS Training", "CD-025649"],
      "concept_distribution": {"calculation": 60, "workflow": 20},
      "test_type_coverage": {"HPLC": 25, "LOD": 10, ...}
    }
  }
}
```

## Chunking Rules

- **Maximum chunk size**: 2000 characters
- **Split strategy**: paragraph boundaries (double newline), then sentence boundaries if needed
- **Never split** mid-sentence
- **Preserve section context**: each chunk must include its section title in metadata
- **NO FALLBACK LOGIC** — if sections.json cannot be read, raise an error
- **NO invented content** — chunks must contain only text from the source documents
- Chunks with only whitespace or <50 characters of content should be skipped
