# LIMS-007 — L12 Hybrid Test Type Classifier

**Date:** 2026-02-19
**Task:** L12 — Hybrid Test Type Classifier
**Phase:** 8c (Two-Layer Pipeline — Classification)
**Branch:** `prjoject_p_protatype`

## Summary

Built a deterministic hybrid classifier that classifies uploaded PDFs into test types (HPLC, LOD, TITRATION, IDENTITY, OTHER) using a 4-step pipeline. Achieved **100% accuracy on all 25 demo PDFs** (target was >90%).

## Classification Pipeline

1. **Filename rules** (confidence 0.95) — matches pharmaceutical lab naming conventions (ASY, CEX, LOD, KF, ACS, etc.)
2. **Keyword matching** (confidence 0.55-0.92, step function) — regex patterns against PDF text content
3. **Exclusion-based OTHER** (confidence 0.85) — when no keyword matches are strong enough
4. **LLM fallback** — raises `NotImplementedError` (not yet integrated, no fallback logic)

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/classifier.py` | `TestTypeClassifier` class with 4-step hybrid classification |
| `main/src/lims/prompts/classification_prompt.py` | LLM system prompt for future LLM classification step |
| `main/tests/lims/test_classifier.py` | 78 tests with ground truth for all 25 demo PDFs |
| `output/prepared_l10l15/L12_classifier/evaluation_results.json` | Per-PDF classification results |
| `output/prepared_l10l15/L12_classifier/accuracy_report.md` | Summary accuracy report |
| `output/prepared_l10l15/L12_classifier/keyword_patterns.json` | Agent-extracted keyword patterns from SOPs |
| `output/prepared_l10l15/L12_classifier/training_examples.json` | Agent-extracted training examples from SOPs |

## Files Modified

None (classifier is a new module; uses existing L10 foundation models).

## Key Design Decisions

1. **Underscore-delimited filename boundaries** — used `(?:^|_)` and `(?:_|$)` instead of `\b` word boundaries because `_` is a word character in regex, making `\b` ineffective for underscore-separated filename segments.
2. **Step-function confidence** for keyword matching (not linear) — prevents 1-keyword matches from exceeding the 0.8 threshold.
3. **Negative patterns** suppress HPLC classification for ion chromatography (`ion.?chromatograph`), residue on ignition, light diffraction, and biological indicator texts.
4. **Exclusion step** classifies as OTHER when text exists but no keyword type scores more than 1 match.

## Test Results

```
78 passed, 0 failed (test_classifier.py)
247 passed, 4 skipped, 0 failed (all LIMS tests)
Accuracy: 25/25 = 100%
```

## Issues Encountered

- **ISSUE: `\b` word boundary failure** — Initial implementation used `\b` in filename patterns (e.g., `\basy\b`). This failed because `_` is a word character, so `\b` doesn't fire between `_` and letter characters. Fixed by using `(?:^|_)` / `(?:_|$)` boundaries on normalized (lowercased, hyphens→underscores, extension-stripped) filenames.

## Useful Commands

```bash
# Run classifier tests
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run pytest main/tests/lims/test_classifier.py -v"

# Run all LIMS tests
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run pytest main/tests/lims/ -v"
```

## Next Steps

- L13: Standards RAG loader (ChromaDB ingestion of SOP documents for augmentation step)
- L14: Pipeline orchestrator (wire classifier → template loader → extraction → augmentation → merge)
- Future: Integrate LLM classification in `_classify_by_llm()` when rule confidence is insufficient
