# Archive: Legacy Root Scripts

This directory contains approximately 88 **ARCHIVED** scripts that were originally located at the project root during early development. These files were moved here during cleanup and are **NOT ACTIVE**.

## Warning

Running these scripts will **LIKELY FAIL** due to:
- Changed module paths and imports
- Removed APIs and deprecated functions
- Outdated environment configurations
- Superseded implementations

**Do not execute these scripts in production or as part of active workflows.**

## Purpose

These files are retained for:
- Historical reference of early development approaches
- Documentation of trial-and-error experimentation
- Examples of workflow patterns used during development
- Git history and audit trail (GAMP-5 compliance)

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
