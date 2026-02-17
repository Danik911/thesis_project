# Archive: Legacy Test Files

This directory contains approximately 83 **ARCHIVED** test files from the thesis project's development history. These tests are **NOT ACTIVE** and **NOT part of the current test suite**.

## Warning

Running these tests will **LIKELY FAIL** due to:
- Outdated imports and removed APIs
- Deprecated module structures
- Superseded implementations
- Missing or changed dependencies

**Do not run these tests in CI/CD or as part of active validation.**

## Purpose

These files are retained for:
- Historical reference of development patterns
- Documentation of trial-and-error approaches during thesis development
- Examples of test patterns used at different project stages
- Git history and audit trail

## Current Active Tests

Please use the active test suites instead:
- `main/tests/unit/` - Unit tests
- `main/tests/integration/` - Integration tests
- `main/tests/lims/` - AI4LIMS PoC tests
- `main/tests/rag/` - RAG workflow tests
- `main/tests/compliance/` - Compliance framework tests

## Running Current Tests

```bash
uv run pytest main/tests/ -v
```
