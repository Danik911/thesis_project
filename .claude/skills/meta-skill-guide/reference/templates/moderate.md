# Moderate Skill Template (300-500 lines)

**Characteristics:**
- Multiple related operations
- 1-3 scripts for validation/processing
- Template files for structure
- Quality assurance workflows

---

## Template

```yaml
---
name: moderate-skill-name
description: Creates/processes X with Y validation. Use when working with Z formats or needing W outputs.
---

# Skill Name

## Overview
[Brief description of capabilities]

## Critical Requirements

### Zero Errors Mandate
[Define quality standards - e.g., "MUST deliver with ZERO validation errors"]

### Mandatory Workflow
1. Create/modify artifact
2. Save file to disk
3. Run `python scripts/validator.py artifact.ext`
4. Verify output for errors
5. Fix errors and re-run until success

## Tool Selection

Choose the right tool for your task:
- **Tool A**: Use for scenario 1 (most common)
- **Tool B**: Use for scenario 2 (edge case handling)
- **Tool C**: Use for scenario 3 (specialized)

## Best Practices
- Practice 1: [Specific guidance]
- Practice 2: [Specific guidance]
- Practice 3: [Specific guidance]

## Common Operations

### Operation 1: [Name]
```
[Step-by-step instructions]
```

### Operation 2: [Name]
```
[Step-by-step instructions]
```

## Quality Checklist
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3
- [ ] Validation passed

## Advanced Features
For advanced usage, see reference/advanced.md
For templates, see templates/
```

---

## File Structure

```
moderate-skill/
├── SKILL.md              # Main instructions
├── scripts/
│   └── validator.py      # Validation script
└── templates/
    └── template.ext      # Base templates
```

---

## Real-World Example

**Skill**: `xlsx` (Excel with formula validation)

**Key Features:**
- Multiple operations (create, modify, validate)
- `recalc.py` script for formula validation
- Template files for common structures
- Zero-error mandate for formula correctness
