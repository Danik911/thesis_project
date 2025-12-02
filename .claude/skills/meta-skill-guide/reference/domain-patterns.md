# Domain-Specific Skill Patterns

## Creative & Design Skills

**Characteristics:**
- Conceptual depth over functionality
- Iterative refinement through subtlety
- Constraint as creative fuel
- Philosophy-first approach

**Pattern:**
```markdown
## Core Process

1. **Philosophy Creation**: Develop conceptual framework
2. **Conceptual Seeding**: Identify thematic references
3. **Implementation**: Express philosophy through code

## Principles
- Philosophy-first design dictates implementation
- Craftsmanship over feature addition
- Reductive mastery (refine, don't add)
- Template-based structure for consistency
```

**Example**: `algorithmic-art` (generative art with p5.js)

---

## Document Processing Skills

**Characteristics:**
- Format-specific expertise (Excel, PDF, PowerPoint, Word)
- Industry standard compliance
- Quality validation workflows
- Template-based generation

**Pattern:**
```markdown
## Mandatory Standards
[Industry requirements: ZERO errors, specific formatting]

## Workflow
1. Create document
2. Save file
3. Run validation script: `python scripts/validate.py file.ext`
4. Fix errors reported in output
5. Repeat until validation passes

## Tool Selection
- Tool A: Use case 1 (recommended)
- Tool B: Use case 2 (edge cases)

## Templates
See templates/ directory for structure examples
```

**Examples**: `xlsx` (Excel), `pdf` (documents), `pptx` (presentations)

---

## Development & Technical Skills

**Characteristics:**
- Multi-phase workflow orchestration
- Code quality standards
- Best practices enforcement
- Quality gates between phases

**Pattern:**
```markdown
## Phase-Based Workflow
Phase 1: Research -> Phase 2: Implementation -> Phase 3: Review -> Phase 4: Testing

## Each Phase
1. Prerequisites check
2. [Load relevant reference: reference/phase_N.md]
3. Execute phase tasks
4. Quality gate validation
5. Proceed to next phase

## Quality Gates
**Gate 1**: Requirements documented
**Gate 2**: Implementation complete, builds successful
**Gate 3**: Tests passing, code reviewed
**Gate 4**: Evaluation passed
```

**Examples**: `mcp-builder` (MCP servers), `webapp-testing` (Playwright automation)

---

## Enterprise & Communication Skills

**Characteristics:**
- Template-based routing
- Organizational standards encoding
- Multiple format support
- Clarification protocols

**Pattern:**
```markdown
## Communication Types
1. Type A -> [Load reference/type_a.md]
2. Type B -> [Load reference/type_b.md]
3. Type C -> [Load reference/type_c.md]

## Workflow
1. Classify request
2. Load appropriate template
3. Apply format standards
4. Generate output

## Fallback
If type unclear, ask user for clarification:
- "Which format do you need: A, B, or C?"
```

**Examples**: `internal-comms` (newsletters, FAQs), `brand-guidelines` (corporate styling)

---

## Workflow & Automation Skills

**Characteristics:**
- Protective abstraction layers
- Slash command interfaces
- Automated configuration
- Prevention of manual operations

**Pattern:**
```markdown
## Operations
- `/command_1 <params>`: Operation 1 - [When to use]
- `/command_2 <params>`: Operation 2 - [When to use]
- `/command_3 <params>`: Operation 3 - [When to use]

## Critical Constraints
Do NOT:
- Perform manual process X
- Run direct command Y
- Modify configuration Z manually

## Automation
All configuration handled automatically by scripts
```

**Examples**: `worktree-manager` (git worktree automation)
