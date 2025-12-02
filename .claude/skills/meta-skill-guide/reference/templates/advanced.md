# Advanced Skill Template (500+ lines distributed)

**Characteristics:**
- Complex multi-phase workflows
- Extensive reference documentation (5-10+ files)
- Multiple scripts and utilities
- Domain-specific knowledge bases
- Progressive disclosure across files

---

## Template

```yaml
---
name: advanced-skill-name
description: Builds/orchestrates X through Y phases with Z validation. Use when creating complex W or needing enterprise-grade V.
---

# Skill Name

## Overview
[High-level description of multi-phase workflow]

## Workflow Overview

**Phase 1: Research** → **Phase 2: Implementation** → **Phase 3: Review** → **Phase 4: Validation**

---

## Phase 1: Research & Planning

### 1.1 Gather Requirements
[Instructions for requirement gathering]

### 1.2 Technical Research
[Read reference/domain_knowledge.md]
[Read reference/technology_options.md]

### 1.3 Decision Points
- Decision A: Option 1 vs Option 2
- Decision B: Approach X vs Approach Y

**Quality Gate**: All requirements documented, technology selected

---

## Phase 2: Implementation

### 2.1 Setup
[Read reference/language_specific_setup.md]
[Instructions for initialization]

### 2.2 Core Development
[Step-by-step implementation guidance]

### 2.3 Integration
[Integration instructions]

### 2.4 Language-Specific Checklist

**Python Checklist:**
- [ ] Type hints on all functions
- [ ] Pydantic validation models
- [ ] Error handling with specific exceptions
- [ ] Async context managers

**TypeScript Checklist:**
- [ ] Zod schemas for validation
- [ ] Proper type annotations
- [ ] Promise error boundaries
- [ ] ESLint compliance

**Quality Gate**: All checklist items complete, builds successfully

---

## Phase 3: Review & Testing

### 3.1 Code Quality Review
- [ ] DRY principles
- [ ] Type safety
- [ ] Error handling
- [ ] Documentation

### 3.2 Testing
[Read reference/testing_standards.md]
[Testing instructions]

**Quality Gate**: All tests passing, no linting errors

---

## Phase 4: Evaluation & Documentation

### 4.1 Evaluation
[Read reference/evaluation.md]
Run evaluation suite

### 4.2 Documentation
Generate final documentation

**Quality Gate**: Evaluation passed, documentation complete

---

## Key Principles
- Principle 1: [Detailed explanation]
- Principle 2: [Detailed explanation]
- Principle 3: [Detailed explanation]

## Troubleshooting
Common issues and solutions available in reference/troubleshooting.md
```

---

## File Structure

```
advanced-skill/
├── SKILL.md (workflow orchestration)
├── reference/
│   ├── domain_knowledge.md (conceptual guidance)
│   ├── language_specific_setup.md (tech-specific)
│   ├── testing_standards.md (quality requirements)
│   ├── evaluation.md (quality gates)
│   └── troubleshooting.md (common issues)
└── scripts/
    ├── validator.py
    └── evaluator.py
```

---

## Real-World Example

**Skill**: `mcp-builder` (multi-phase MCP server development)

**Key Features:**
- 4-phase workflow (Research → Implementation → Review → Testing)
- Python and TypeScript support
- Extensive reference documentation
- Quality gates between phases
- Language-specific checklists
