# Archived Compliance System

**STATUS: ARCHIVED - NOT PART OF ACTIVE SYSTEM**

This directory contains legacy compliance validation code from an earlier iteration of the thesis project.

## What's Here

- `compliance_system/compliance_validation/` — ALCOA scorer, CFR Part 11 verifier, GAMP-5 assessor, gap analyzer, evidence collector, remediation planner
- `compliance_system/planner/` — Agent coordination, GAMP strategies, strategy generator

## Why It's Archived

This implementation was superseded by the current architecture:
- Compliance logic: `main/src/compliance/`
- Validation patterns: `main/src/validation/`

The current system provides a cleaner, more modular approach to pharmaceutical compliance validation.

## Use Cases

- **Reference**: Study compliance patterns from this earlier approach
- **Archaeology**: Understanding design decisions in compliance architecture

## Warning

**Do not import from this code.** Dependencies are likely missing, and patterns may not align with current standards. Use the active compliance modules instead.
