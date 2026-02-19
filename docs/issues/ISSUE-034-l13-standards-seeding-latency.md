# ISSUE-034: L13 Standards RAG Seeding Latency on First Ingestion

**Date:** 2026-02-19  
**Status:** Open  
**Category:** Database  
**Priority:** Medium

---

## Symptom

First-time seeding of L13 standards collections can take a long time:

- `lims_standards`
- `calculation_patterns`

Observed during real L13 run after prepared-artifact ingestion was enabled.

---

## Impact

- Slower feedback loop during development/debug when reseeding repeatedly.
- Perception of runtime hang, especially when both collections are seeded back-to-back.

---

## Affected Scope

- `main/src/lims/standards_loader.py`
- ChromaDB local vector store at `./chroma_db_lims`
- Prepared input artifacts in `output/prepared_l10l15/per_document/*`

---

## Root Cause

Seeding performs embedding + indexing for hundreds of chunks, which is computationally expensive. This is expected behavior for first ingestion and full reseed operations.

---

## Current Workaround

1. Seed once, query many times.
2. Avoid reseeding both collections during every test/debug cycle.
3. Use generated trace artifacts under `output/prepared_l10l15/L13_rag/` to debug chunk quality without re-ingesting.

---

## Suggested Improvements

1. Add incremental seeding mode (skip unchanged chunks by hash/id).
2. Add per-document selective seeding for targeted debugging.
3. Add optional max-chunk limit for quick local smoke runs.
