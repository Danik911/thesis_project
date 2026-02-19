# Task L12 — Hybrid Test Type Classifier

**Phase:** 8c (Two-Layer Pipeline — Classification) | **Dependencies:** L10 (Foundation Models)
**Branch:** `prjoject_p_protatype`
**Estimated effort:** 2 days
**Status:** DONE (IMPLEMENTED & VERIFIED 2026-02-19)

## Completion Summary (2026-02-19)

- **Accuracy:** 25/25 = **100%** on all demo PDFs (gate threshold was >90%)
- **Tests:** 78 passed, 0 failed (`test_classifier.py`); 247 passed, 4 skipped across all LIMS tests
- **Classification pipeline:** 4-step (filename → keywords → exclusion → LLM stub)
- **Evaluation artifacts:** `output/prepared_l10l15/L12_classifier/` — `evaluation_results.json`, `accuracy_report.md`, `keyword_patterns.json`, `training_examples.json`
- **Documentation:** `docs/project_p/LIMS-007-l12-hybrid-classifier.md`

### Classification breakdown (25 PDFs)

| Method | Count | Confidence | PDFs |
|--------|-------|------------|------|
| Filename | 13 | 0.95 | 11 HPLC, 1 LOD, 1 TITRATION, 2 IDENTITY (lab naming conventions) |
| Keywords | 5 | 0.85–0.92 | 3 HPLC, 1 TITRATION, 1 IDENTITY (content-based) |
| Exclusion | 7 | 0.85 | 7 OTHER (no strong keyword matches) |
| LLM | 0 | N/A | `NotImplementedError` — no fallback logic |

### Key implementation decision
Used `(?:^|_)` and `(?:_|$)` segment boundaries instead of `\b` word boundaries in filename patterns. Regex `\b` treats `_` as a word character, so `\basy\b` fails to match `AND_ASY_HSUCC`. The segment-boundary approach correctly handles underscore-delimited pharmaceutical filenames after normalization (lowercase, hyphens→underscores, extension stripped).

---

## Objective

Build a hybrid classifier that detects test type (HPLC, LOD, Titration, Identity) from uploaded PDFs. Primary classification via deterministic rules (keyword matching, structure analysis); LLM fallback when rule confidence < threshold. Must achieve >90% accuracy on 18+ demo PDFs.

---

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/classifier.py` | `TestTypeClassifier` — 4-step hybrid pipeline (filename → keywords → exclusion → LLM stub) |
| `main/src/lims/prompts/classification_prompt.py` | LLM system prompt for future LLM classification integration |
| `main/tests/lims/test_classifier.py` | 78 tests: parametrized filename, keyword, negative pattern, exclusion, accuracy gate (25 PDFs) |
| `output/prepared_l10l15/L12_classifier/evaluation_results.json` | Per-PDF classification results with method, confidence, evidence |
| `output/prepared_l10l15/L12_classifier/accuracy_report.md` | Summary accuracy table |
| `output/prepared_l10l15/L12_classifier/keyword_patterns.json` | Agent-extracted keyword patterns from 4 SOP documents |
| `output/prepared_l10l15/L12_classifier/training_examples.json` | Agent-extracted training examples from SOPs |
| `docs/project_p/LIMS-007-l12-hybrid-classifier.md` | LIMS documentation |

## Files Modified

None (classifier is a new module; uses existing L10 foundation models).

---

## Implementation Details

### 4-Step Classification Pipeline (`classifier.py`)

1. **`_classify_by_filename(filename)`** → confidence 0.95
   - Normalizes filename: lowercase, hyphens→underscores, strips extension
   - Uses `(?:^|_)pattern(?:_|$)` segment boundaries (not `\b` — underscores are word chars)
   - Patterns: `asy`, `assay`, `as_pu`, `aspu`, `apu`, `cex`, `reso`, `lod`, `kf`, `acs`, `dye`, etc.

2. **`_classify_by_keywords(pdf_text)`** → step-function confidence (0.55–0.92)
   - 16 HPLC, 8 LOD, 10 TITRATION, 8 IDENTITY keyword regex patterns
   - Step-function: 5+ matches→0.92, 4→0.88, 3→0.85, 2→0.75, 1→0.55
   - Negative patterns suppress HPLC for: ion chromatography, residue on ignition, light diffraction, biological indicator, nitrate

3. **`_classify_by_exclusion(pdf_text, keyword_scores)`** → confidence 0.85
   - If text is non-empty AND best keyword score ≤1 match → OTHER

4. **`_classify_by_llm(pdf_text, filename)`** → raises `NotImplementedError`
   - No fallback logic per project policy; prompt ready in `classification_prompt.py`

### Prompt module (`classification_prompt.py`)

- `CLASSIFICATION_SYSTEM_PROMPT` — JSON-output system prompt for future LLM integration
- `build_classification_prompt(pdf_text, filename)` — formats user message with content

---

## Testing Strategy

```bash
# Run classifier tests (78 tests)
uv run pytest main/tests/lims/test_classifier.py -v

# Run all LIMS tests (verify no regressions)
uv run pytest main/tests/lims/ -v
```

### Test categories (78 tests)
- **Step-function confidence** — 6 tests for `_keyword_confidence()`
- **Filename classification** — 13 parametrized match tests + 12 no-match tests + 2 edge cases
- **Keyword classification** — 4 test-type tests + 2 empty/whitespace tests
- **Negative patterns** — 2 tests (IC not HPLC, ROI not HPLC)
- **Exclusion** — 2 tests (no-keywords→OTHER, empty text)
- **Full pipeline** — 4 integration tests (priority, keyword fallback, exclusion, LLM stub)
- **Accuracy gate** — 25 individual parametrized tests + aggregate >90% check + completeness check
- **Edge cases** — 4 tests (empty inputs, strict threshold, filename in result)

---

## Gate Criteria

- [x] Rule-based classification correctly identifies test types from demo PDF filenames
- [x] Keyword classification matches test types from PDF content
- [x] LLM fallback path verified as fail-loud (`NotImplementedError`) until integration
- [x] >90% accuracy across 18+ demo PDF filenames (verified at 25/25 = 100%)
- [x] Confidence scores are meaningful (rules > keywords > exclusion/LLM path)
- [x] `TestType.OTHER` returned for unrecognized test methods
- [x] All existing LIMS tests pass

### Audit Evidence (2026-02-19)

- `uv run pytest main/tests/lims/test_classifier.py -q` → `78 passed, 0 failed`
- `uv run pytest main/tests/lims/ -q` → `247 passed, 4 skipped, 0 failed`
- Accuracy artifact: `output/prepared_l10l15/L12_classifier/evaluation_results.json` reports `25/25` correct
