---
name: meta-skill-guide
description: Comprehensive guide for creating Claude Code custom skills. Use when asked to create, design, or improve custom skills for Claude Code. Provides templates, best practices, and patterns for simple, moderate, and advanced skills.
---

# Meta-Skill Guide: Creating Claude Code Custom Skills

## Quick Reference

| Aspect | Constraint | Recommendation |
|--------|-----------|----------------|
| **SKILL.md size** | No hard limit | Keep under 500 lines for optimal performance |
| **Skill name** | Max 64 chars | Use lowercase, hyphens, gerund form (e.g., `processing-pdfs`) |
| **Description** | Max 1024 chars | Include WHAT it does AND WHEN to use it (third person) |
| **Reference depth** | One level deep | SKILL.md → File.md ✅ / SKILL.md → File1.md → File2.md ❌ |
| **File paths** | Forward slashes | Always `scripts/helper.py`, never `scripts\helper.py` |
| **Subagent context** | Completely isolated | NO conversation history, NO other subagent results, NO memory |

**Version Information:**
- Skills API: `skills-2025-10-02`
- Code Execution: `code-execution-2025-08-25`
- Files API: `files-api-2025-04-14`
- Last Updated: November 2025

---

## Architecture Fundamentals

### Three-Level Progressive Loading System

Skills use progressive disclosure to optimize token usage:

**Level 1: Metadata (Always Loaded - ~100 tokens/skill)**
```yaml
---
name: skill-name
description: Brief description with usage triggers
---
```
- Loaded at Claude Code startup
- Claude learns skill existence and when to trigger
- Critical for skill discovery

**Level 2: Instructions (Loaded When Triggered - <5,000 tokens)**
- Main SKILL.md body content
- Procedures, workflows, best practices
- Loaded only when user request matches description
- Optimal: Under 500 lines

**Level 3: Resources & Code (Loaded As Needed - Unlimited)**
- Additional markdown files (ADVANCED.md, REFERENCE.md)
- Scripts (.py, .js files)
- Templates and examples
- Scripts execute without loading code into context (only output consumes tokens)

**Key Insight**: Files remain on filesystem until accessed. Claude navigates using bash commands.

### File Structure Patterns

**Basic Structure:**
```
skill-name/
├── SKILL.md              # Main instructions (mandatory)
├── LICENSE.txt           # Optional licensing
├── README.md             # Optional user-facing docs
├── reference/            # Optional reference docs
│   ├── advanced.md
│   └── api_reference.md
├── scripts/              # Optional executable code
│   ├── helper.py
│   └── validator.js
└── templates/            # Optional templates
    └── template.ext
```

### YAML Frontmatter Specification

**Required Fields:**
```yaml
---
name: skill-name
description: What the skill does and when Claude should use it. Include specific triggers and key terms.
---
```

**Optional Fields (Claude Code):**
```yaml
---
name: skill-name
description: Description text
allowed-tools: ["Bash", "Read", "Write"]  # Restrict available tools
model: claude-sonnet-4-5-20250929          # Force specific model
---
```

**Field Constraints:**
- `name`: Max 64 chars, lowercase letters/numbers/hyphens only, no reserved words
- `description`: Max 1024 chars, must specify WHAT and WHEN
- Use gerund form: ✅ `processing-pdfs` / ❌ `process-pdf`
- Avoid vague names: ❌ `helper`, `utils`, `documents`

---

## Skill Level Templates

### Level 1: Simple Skills (100-300 lines)

**Characteristics:**
- Single focused task
- Minimal dependencies
- Instructions only (no scripts/resources)
- Self-contained workflow

**Template:**
```yaml
---
name: simple-skill-name
description: Performs specific task X. Use when user needs to accomplish Y or mentions terms Z.
---

# Skill Name

## Overview
[1-2 sentence description of skill purpose]

## When to Use
- Use case 1
- Use case 2
- Use case 3

## Core Workflow

1. **Step 1**: [Action description]
   - Detail A
   - Detail B

2. **Step 2**: [Action description]
   - Detail A
   - Detail B

3. **Step 3**: [Completion/validation]

## Principles
- Principle 1: [Why it matters]
- Principle 2: [Why it matters]
- Principle 3: [Why it matters]

## Required Features/Standards
- Requirement 1
- Requirement 2
- Requirement 3

## Example

**Input:**
```
[Example input]
```

**Output:**
```
[Example output]
```

[Optional: Additional context about the example]
```

**Real-World Example**: `algorithmic-art` skill (creative generative art with p5.js)

---

### Level 2: Moderate Skills (300-500 lines)

**Characteristics:**
- Multiple related operations
- 1-3 scripts for validation/processing
- Template files for structure
- Quality assurance workflows

**Template:**
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

**Real-World Example**: `xlsx` skill (Excel with formula validation via recalc.py script)

---

### Level 3: Advanced Skills (500+ lines distributed)

**Characteristics:**
- Complex multi-phase workflows
- Extensive reference documentation (5-10+ files)
- Multiple scripts and utilities
- Domain-specific knowledge bases
- Progressive disclosure across files

**Template:**
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

**Supporting Files Structure:**
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

**Real-World Example**: `mcp-builder` skill (multi-phase MCP server development with Python/TypeScript support)

---

## Best Practices Checklist

### Content & Structure ✅ DO

1. **Keep SKILL.md under 500 lines**
   - Context window shared across system prompts, conversation, and skills
   - Use progressive disclosure for additional content

2. **Write descriptions in third person with triggers**
   - ✅ "Extracts text from PDFs. Use when working with PDF files or document extraction."
   - ❌ "I can help you process Excel files" (wrong perspective)
   - ❌ "Helps with documents" (too vague)

3. **Use consistent terminology throughout**
   - Pick one term and stick to it (e.g., always "API endpoint" not URL/route/path)
   - Mixing terms creates confusion

4. **Provide concrete examples with input/output pairs**
   - Demonstrates desired style and detail level
   - Especially critical for code/content generation

5. **Implement validation loops for quality**
   - Pattern: Create → Validate → Fix → Repeat
   - Dramatically improves output quality
   - Example: Generate JSON → Validate schema → Execute

6. **Structure long reference files with table of contents**
   - Files over 100 lines need navigation
   - Ensures visibility of available information

7. **Use checklists for complex multi-step tasks**
   ```markdown
   Task Progress:
   - [ ] Step 1: [Action with command]
   - [ ] Step 2: [Validation step]
   - [ ] Step 3: [Next action]
   ```

8. **Appropriate degrees of freedom**
   - **High freedom (text instructions)**: Multiple valid approaches
   - **Medium freedom (pseudocode)**: Preferred patterns with variations
   - **Low freedom (scripts)**: Exact sequences for fragile operations

### Code & Scripts ✅ DO

1. **Solve problems, don't punt to Claude**
   - Handle error conditions explicitly
   - Provide alternatives for common issues
   - Scripts should be production-ready

2. **Justify all constants and magic numbers**
   - ❌ `TIMEOUT = 47` (why 47?)
   - ✅ `TIMEOUT = 47  # Most failures resolve by second retry`

3. **List required packages explicitly**
   ```markdown
   ## Required Packages
   ```bash
   pip install pypdf pydantic
   ```
   ```

4. **Create verifiable intermediate outputs**
   - Pattern: Create plan file → Validate → Execute
   - Catches errors before destructive changes

5. **Provide default approach with escape hatches**
   - ✅ "Use pdfplumber for text extraction. For scanned PDFs, use pdf2image with pytesseract."
   - ❌ Listing multiple equal options without guidance

### Subagent Delegation ✅ DO

1. **Provide complete, self-contained context**
   - Include all background information in delegation prompt
   - Specify requirements and constraints explicitly
   - Define success criteria and output format
   - Never assume knowledge from conversation history

2. **Use file artifacts for state transfer**
   - Save subagent outputs to files (e.g., `research-notes.md`)
   - Pass file paths to next subagent in chain
   - Maintain master status document for complex workflows
   - Include metadata (timestamps, versions, status)

3. **Specify exact output format**
   - Prevent context overload from verbose responses
   - Use structured formats (JSON, YAML, markdown sections)
   - Example: "Return: 1. Top 3 patterns (2-3 sentences each), 2. Code example, 3. Anti-patterns (bullets)"

4. **Orchestrate from main agent/skill**
   - Main agent coordinates all subagent delegation
   - No nested delegation (subagents can't invoke others)
   - Manually aggregate results from parallel executions
   - Manage dependencies in sequential workflows

5. **Use parallel execution for independent tasks**
   - Single message with multiple Task tool calls
   - 3x-5x speedup for parallelizable work
   - Each subagent gets full 200k context
   - Example: Launch product-manager, ux-designer, engineer simultaneously

### Progressive Disclosure Patterns

**Pattern 1: High-Level Guide with References**
```markdown
# Main Skill

## Quick Start
[Basic instructions]

## Common Operations
[Frequent use cases]

For advanced features, see reference/advanced.md
For API reference, see reference/api.md
```

**Pattern 2: Conditional Details**
```markdown
## Basic Usage
[Standard approach]

<details>
<summary>Advanced: Handling Edge Cases</summary>

[Special case handling - collapsed by default]
</details>
```

**Critical Constraint**: Keep references **one level deep** from SKILL.md. Claude may partially read deeply nested files.

### Anti-Patterns ❌ DON'T

1. **Reference time-sensitive information**
   - ❌ "As of January 2025..."
   - ✅ Use "current method" vs. "legacy" sections

2. **Use Windows-style paths**
   - ❌ `scripts\helper.py`
   - ✅ `scripts/helper.py`

3. **Assume tools are pre-installed**
   - Always show explicit installation steps

4. **Use vague MCP tool references**
   - ❌ `tool_name`
   - ✅ `ServerName:tool_name` (e.g., `BigQuery:bigquery_schema`)

5. **Provide too many equal options**
   - Causes decision paralysis
   - Provide default + alternatives for specific scenarios

6. **Create deeply nested references**
   - SKILL.md → File1.md ✅
   - SKILL.md → File1.md → File2.md ❌

7. **Inspect DOM before network stabilization (web testing)**
   - Wait for `networkidle` state before inspection
   - Critical for dynamic web apps

### Subagent Integration ❌ DON'T

1. **Context Amnesia**
   - ❌ "Now fix the issues you found" (subagent has no memory of previous invocation)
   - ✅ "Fix issues in auth-review.md: [paste specific issues]"

2. **Nested Delegation**
   - ❌ Subagent tries to invoke another subagent (not supported)
   - ✅ Main agent orchestrates all delegation

3. **Implicit Context**
   - ❌ "Review the API changes" (which changes? what to look for?)
   - ✅ "Review src/api/auth.ts for: JWT validation security, error handling, rate limiting"

4. **Output Format Ambiguity**
   - ❌ "Research best practices" (returns 15 pages → context overload)
   - ✅ "Return: Top 3 patterns (2-3 sentences), 1 code example, anti-patterns (bullets)"

5. **Over-Scoped Agents**
   - ❌ Creating "do-everything" agents (defeats specialization)
   - ✅ Focused specialists with clear, narrow domains

See "Skill → Subagent Integration Patterns" section for detailed anti-patterns and correct approaches.

---

## Domain-Specific Patterns

### Creative & Design Skills

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

### Document Processing Skills

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

### Development & Technical Skills

**Characteristics:**
- Multi-phase workflow orchestration
- Code quality standards
- Best practices enforcement
- Quality gates between phases

**Pattern:**
```markdown
## Phase-Based Workflow
Phase 1: Research → Phase 2: Implementation → Phase 3: Review → Phase 4: Testing

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

### Enterprise & Communication Skills

**Characteristics:**
- Template-based routing
- Organizational standards encoding
- Multiple format support
- Clarification protocols

**Pattern:**
```markdown
## Communication Types
1. Type A → [Load reference/type_a.md]
2. Type B → [Load reference/type_b.md]
3. Type C → [Load reference/type_c.md]

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

### Workflow & Automation Skills

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

---

## Skill → Subagent Integration Patterns

### When to Delegate vs. Direct Implementation

**Skills provide the "WHEN" and "WHAT"**
**Subagents provide the "HOW"**

**Decision Matrix:**

| Task Characteristics | Recommendation |
|---------------------|----------------|
| Simple, <10 min tasks | Direct implementation in skill |
| Research-heavy tasks | Delegate to `context-collector` subagent |
| Multi-stage workflows | Orchestrate multiple specialized subagents |
| Language-specific code generation | Delegate to specialist subagents (python-expert, typescript-pro) |
| Quality assurance | Delegate to `code-reviewer`, `test-automator` |
| Security analysis | Delegate to `security-auditor` |

**Performance Benefits:**
- **90.2% improvement** for parallel tasks over single-agent approaches
- Each subagent operates in independent 200k token context
- No context window pressure when running multiple specialists
- 3x-5x speedup for parallelizable workflows

### Subagent Capabilities Matrix

#### ✅ What Subagents CAN Do

**Dedicated Execution Environment:**
- Operate in independent 200k token context window per subagent
- Execute parallel tasks without context interference
- Access explicitly granted tools (Read, Write, Edit, Bash, Grep, Glob, MCP)
- Maintain specialized domain knowledge in system prompt
- Return condensed summaries (1,000-2,000 tokens) to parent agent

**Task Specialization:**
- Code review with domain-specific patterns
- Security audits with compliance frameworks
- Test generation and execution
- Documentation creation
- Research and context gathering
- Architecture design and validation

#### ❌ What Subagents CANNOT Do

**Context Limitations:**
- **NO access to main conversation history** - subagents don't see prior messages
- **NO access to user preferences** from current session
- **NO access to other subagent results** unless explicitly provided
- **NO memory of previous invocations** - each invocation is fresh start
- **NO automatic state sharing** between subagents

**Execution Constraints:**
- **CANNOT invoke other subagents** - no nested delegation
- **CANNOT modify their own configuration** during execution
- **CANNOT persist state** across invocations without explicit file writes
- **CANNOT access parent agent's tool history** or reasoning
- **CANNOT infer context** from previous work unless explicitly passed

#### ⚠️ What Requires Special Handling

**Multi-Step Workflows:**
- Sequential tasks need explicit output → input chaining
- State must be persisted to files/documents between steps
- Parent agent must orchestrate information flow manually

**Error Recovery:**
- Subagents don't inherit error context from previous attempts
- Failed operations require full context re-provision on retry
- No automatic rollback or recovery mechanisms

**Complex Coordination:**
- Parallel execution requires independent task decomposition
- Dependency management must be explicit in orchestration
- Results must be aggregated manually by parent agent

### Context Isolation Mechanics

**How Isolation Works:**

Each subagent receives a completely isolated execution environment:
- Fresh 200k token context window
- Independent execution loop
- Separate tool permission set
- Custom system prompt (no inheritance from main agent)

**Information Flow:**
```
MAIN AGENT → [Explicit Context + Task] → SUBAGENT
           ←  [Condensed Summary]    ←
```

**What Gets Passed:**
1. Initial prompt with task description + all necessary context (manually embedded)
2. Tool permissions explicitly granted
3. System prompt with role definition

**What Gets Returned:**
1. Condensed output (1,000-2,000 token summary, not full transcript)
2. Artifacts (files, documents, code created)
3. Status (success/failure indicators)

**Critical Implications for Prompt Design:**

**MUST Include:**
- Complete task description
- All relevant background information
- Specific success criteria
- Output format requirements
- Any dependencies or constraints

**CANNOT Assume:**
- Previous conversation context
- User preferences mentioned earlier
- Decisions made in main thread
- Results from other subagents

**File Artifacts as State Transfer:**
- Subagent A writes results to `results-a.md`
- Main agent passes `results-a.md` path to Subagent B
- Subagent B reads file and builds on results
- Chain continues through explicit file references

### Special Instruction Keywords

#### Proactive Delegation Triggers (in `description` field)

**High-Priority Keywords:**
- **"Use PROACTIVELY"** - Encourages automatic delegation without explicit request
- **"MUST BE USED"** - Strongest trigger for automatic invocation
- **"ALWAYS USE when"** - Conditional automatic delegation
- **"Use automatically for"** - Explicit automation instruction

**Example:**
```yaml
description: "Use PROACTIVELY after code changes to review security, performance, and best practices. MUST BE USED before commits."
```

#### System Prompt Emphasis Keywords

**Priority Hierarchy (Increasing Strength):**
1. Normal text - Standard instructions
2. **"IMPORTANT:"** - Flags critical instructions
3. **"CRITICAL:"** - Highest priority operational rules
4. **"YOU MUST"** - Mandatory requirements
5. **"NEVER"** - Absolute prohibitions
6. **"ALWAYS"** - Invariant behaviors

**Extended Thinking Triggers:**
- **"think"** - Basic reasoning
- **"think hard"** - Moderate computation
- **"think harder"** - Significant analysis
- **"ultrathink"** - Maximum computation allocation

**Best Practices for Emphasis:**

✅ **DO:**
- Use emphasis sparingly for genuinely critical instructions
- Place emphasized rules at beginning of sections
- Combine with XML tags for clarity: `<critical>NEVER implement fallback logic</critical>`
- Use consistent emphasis patterns across related subagents

❌ **DON'T:**
- Overuse capitalization - dilutes effectiveness
- Mix emphasis styles inconsistently
- Rely solely on emphasis without clear instructions
- Use emphasis as substitute for specificity

### Prompt Engineering for Subagents

#### Subagent File Template

```yaml
---
name: agent-identifier
description: Brief capability overview. Use PROACTIVELY when [trigger condition]. MUST BE USED for [specific scenarios].
tools: Read, Grep, Glob, Edit, Write, Bash
model: inherit
---

# [Agent Role Title]

## Core Expertise
[Clear definition of specialized domain and capabilities]

## Activation Scenarios
- [Specific trigger condition 1]
- [Specific trigger condition 2]
- [Specific trigger condition 3]

## Tools & Capabilities
[Description of how granted tools will be used]

## Output Format
[Structured format specification with examples]

## Critical Rules
- **IMPORTANT:** [High-priority rule]
- **NEVER:** [Absolute prohibition]
- **ALWAYS:** [Invariant behavior]

## Examples
<example>
Context: [Situation description]
Task: [What needs to be done]
Approach: [How agent should handle it]
Output: [Expected result format]
</example>
```

#### Effective Delegation Prompt Template

```markdown
Use the [subagent-name] agent to [specific task].

Context:
- [Relevant background information]
- [Project constraints or requirements]
- [Dependencies or prerequisites]

Specific Requirements:
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

Success Criteria:
- [Measurable outcome 1]
- [Measurable outcome 2]

Output Format:
[Expected structure - JSON, markdown, code, etc.]
```

### Multi-Subagent Orchestration Patterns

#### Pattern 1: Parallel Execution (Independent Tasks)

**Use Case:** Multiple unrelated tasks that don't depend on each other

**Implementation:**
```markdown
Launch 3 subagents in parallel using single message with multiple Task tool calls:
- Task(product-manager, "Define user stories and business value")
- Task(ux-designer, "Propose UX covering all states")
- Task(senior-engineer, "Outline technical approach and risks")

Each agent works independently with full 200k context for their domain.
```

**Benefits:**
- 3x-5x speed improvement
- No context window pressure
- Each specialist uses full context for their specialty

**Limitations:**
- Cannot share insights between parallel agents during execution
- Requires independent task decomposition
- Manual result aggregation by parent agent

#### Pattern 2: Sequential Chain (Dependent Tasks)

**Use Case:** Multi-stage workflow where each step depends on previous output

**Implementation:**
```markdown
Step 1: Use context-collector agent
  → Output: research-notes.md

Step 2: Use architect agent (provide research-notes.md)
  → Output: design-spec.md

Step 3: Use implementer agent (provide design-spec.md)
  → Output: code + tests

Step 4: Use reviewer agent (provide code location)
  → Output: review-report.md
```

**Key Technique:** Use file artifacts as explicit state transfer mechanism

**Orchestration by Main Agent:**
- Pass previous output file path to next subagent
- Embed critical context from previous steps in next prompt
- Maintain master status document tracking progress

#### Pattern 3: Hub-and-Spoke (Verification/Validation)

**Use Case:** Single implementation with multiple specialist reviews

**Implementation:**
```markdown
Step 1: implementer agent → feature-code.py

Step 2: Parallel validation (single message, multiple Task calls):
  ├─ security-auditor reviews feature-code.py → security-report.md
  ├─ performance-engineer reviews feature-code.py → perf-report.md
  └─ qa-specialist tests feature-code.py → qa-report.md

Step 3: Main agent aggregates reports → final decision
```

**Benefits:**
- Comprehensive multi-perspective analysis
- Parallel execution of reviews
- Each reviewer focuses on specific domain

#### Pattern 4: Iterative Refinement

**Use Case:** Complex problem requiring multiple improvement cycles

**Implementation:**
```markdown
Iteration 1:
  architect → draft-design-v1.md
  reviewer (with draft-v1) → feedback-v1.md

Iteration 2:
  architect (with feedback-v1) → draft-design-v2.md
  reviewer (with draft-v2) → feedback-v2.md

Iteration N:
  architect (with feedback-v(N-1)) → final-design.md
```

**Challenge:** Each invocation requires full context re-provision
**Solution:** Maintain cumulative context document that grows with each iteration

### Subagent Anti-Patterns

#### ❌ Anti-Pattern 1: Context Amnesia

**Mistake:** Assuming subagent remembers previous invocations
```markdown
# WRONG
First: "Review the authentication module"
Later: "Now fix the issues you found" ← Subagent has no memory
```

**Correct Approach:**
```markdown
# RIGHT
First: "Review auth module and save findings to auth-review.md"
Later: "Fix issues listed in auth-review.md: [paste specific issues]"
```

#### ❌ Anti-Pattern 2: Nested Delegation

**Mistake:** Expecting subagents to invoke other subagents
```markdown
# WRONG - Subagents CANNOT invoke other subagents
orchestrator-agent tries to invoke worker-agent → FAILS
```

**Correct Approach:**
```markdown
# RIGHT - Main agent orchestrates all delegation
main → agent-1 → result-1
main (reads result-1) → agent-2 with result-1 context → result-2
```

#### ❌ Anti-Pattern 3: Implicit Context Transfer

**Mistake:** Expecting subagent to infer context from project state
```markdown
# WRONG
"Use code-reviewer to check the API changes"
(Subagent doesn't know what changes, when, or what to look for)
```

**Correct Approach:**
```markdown
# RIGHT
"Use code-reviewer to review src/api/auth-endpoint.ts for:
- Security vulnerabilities in JWT validation
- Proper error handling
- Rate limiting implementation
Context: This is a new OAuth2 authentication endpoint for user login."
```

#### ❌ Anti-Pattern 4: Output Format Ambiguity

**Mistake:** Not specifying expected output structure
```markdown
# WRONG
"Research best practices for error handling"
(Subagent returns 15 pages → context overload)
```

**Correct Approach:**
```markdown
# RIGHT
"Research error handling best practices and return:
1. Top 3 recommended patterns (2-3 sentences each)
2. One code example for our Node.js context
3. Key anti-patterns to avoid (bullet list)
Format: Markdown with clear sections"
```

### Integration Strategy for Skills

#### When Creating a Skill with Subagent Integration

**1. Task Complexity Analysis**
- Simple tasks (< 10 min): Direct implementation in skill
- Research-heavy: Delegate to `context-collector`
- Multi-stage workflows: Orchestrate specialized subagents

**2. Specialization Mapping**
- Code generation → Language-specific subagents
- Quality assurance → `code-reviewer`, `test-automator`
- Documentation → `documentation-expert`
- Security → `security-auditor`

**3. State Management Strategy**
```markdown
Skill (Main Orchestrator)
├─ Maintains project context
├─ Manages state across invocations
├─ Delegates specialized tasks
└─ Aggregates results

Subagents (Specialized Workers)
├─ Receive explicit context per task
├─ Execute specialized operations
├─ Return condensed summaries
└─ No cross-invocation memory
```

#### Skill Template with Subagent Integration

```markdown
## Orchestration Flow

1. **Initial Assessment** (Main Agent/Skill)
   - Analyze user request
   - Decompose into subtasks
   - Determine which subagents needed

2. **Parallel Research** (If Needed)
   - Delegate to context-collector for background
   - Delegate to domain specialist for technical analysis
   - Wait for parallel completion

3. **Sequential Implementation**
   - Design: Use architect with research results
   - Implementation: Use specialist with design
   - Validation: Use qa-specialist with implementation

4. **Integration & Finalization** (Main Agent/Skill)
   - Aggregate all subagent outputs
   - Resolve conflicts or gaps
   - Create final deliverable
   - Update persistent documentation

## Subagent Integration Points

### Research Phase
Use context-collector when:
- Domain knowledge required
- Technical research needed
- Compliance validation

### Implementation Phase
Use [language]-specialist when:
- Complex code generation
- Performance optimization
- Domain-specific patterns

### Validation Phase
Use code-reviewer when:
- Implementation complete
- Security review required
- Best practices validation

## State Management

**Persistent State (Across Invocations):**
- Maintain in skill's working directory
- Use structured files (JSON, YAML, markdown)
- Include metadata (timestamps, versions, status)

**Subagent Context Provision:**
- Extract relevant state for each delegation
- Embed in subagent prompt explicitly
- Reference file artifacts for detailed data

## Error Recovery

**Subagent Failure Handling:**
1. Capture error output
2. Analyze failure reason
3. Provide additional context if context-related
4. Retry with refined prompt
5. Escalate to user if persistent failure
```

---

## Quality & Evaluation

### Build Evaluations First

**Process:**
1. **Identify gaps**: Run Claude WITHOUT skill on real tasks
2. **Create test scenarios**: Minimum 3 representative cases
3. **Establish baseline**: Document current performance
4. **Write minimal instructions**: Pass evaluations with least documentation
5. **Iterate**: Refine based on results

**Rationale**: Ensures solving real problems, not imagined ones.

### Iterative Development with Claude

**Two-Claude Method:**
- **Claude A**: Skill author/developer
- **Claude B**: Skill user/tester

**Cycle:**
1. Complete task with Claude A, noting repeated context
2. Ask Claude A to create skill from pattern
3. Test with Claude B on real tasks
4. Observe where Claude B struggles
5. Return to Claude A for refinements
6. Repeat based on observations

**Key**: Iterate based on real behavior, not assumptions.

### Testing Checklist

**Core Quality:**
- [ ] Description is specific with key terms and triggers
- [ ] SKILL.md body under 500 lines
- [ ] Additional details in separate files (one level deep)
- [ ] No time-sensitive information
- [ ] Consistent terminology throughout
- [ ] Examples are concrete with input/output
- [ ] Progressive disclosure used appropriately

**Code & Scripts:**
- [ ] Scripts solve problems, not punt to Claude
- [ ] Error handling is explicit
- [ ] All constants justified with comments
- [ ] Required packages listed and verified
- [ ] Scripts have clear documentation
- [ ] No Windows paths (always forward slashes)
- [ ] Validation steps for critical operations
- [ ] Feedback loops for quality tasks

**Cross-Model Testing:**
- [ ] Tested with Haiku (cost optimization)
- [ ] Tested with Sonnet (standard model)
- [ ] Tested with Opus (complex tasks)
- [ ] Tested with real usage scenarios
- [ ] Team feedback incorporated

---

## Complete Skill Template

```yaml
---
name: skill-name
description: What this skill does and when Claude should use it. Include specific triggers, use cases, and key terms that indicate when this skill is relevant.
allowed-tools: ["Bash", "Read", "Write", "Edit"]  # Optional: Claude Code only
model: claude-sonnet-4-5-20250929                   # Optional: Claude Code only
---

# Skill Name

## Overview
[1-3 sentence description of skill purpose and capabilities]

## When to Use
- Use case 1: [Specific scenario]
- Use case 2: [Specific scenario]
- Use case 3: [Specific scenario]

## Core Workflow

### Phase 1: [Phase Name]
1. **Step 1**: [Action description]
   - Detail A
   - Detail B

2. **Step 2**: [Action with validation]
   - Run: `command example`
   - Verify: [Expected outcome]

3. **Step 3**: [Next action]
   - [Optional: Load reference] See reference/advanced.md

**Quality Gate**: [Criteria to proceed to next phase]

### Phase 2: [Phase Name]
1. **Step 1**: [Action description]
2. **Step 2**: [Validation checkpoint]
3. **Step 3**: Continue or fix issues

**Quality Gate**: [Criteria to proceed]

## Best Practices
- **Practice 1**: [Specific guidance with rationale]
- **Practice 2**: [Specific guidance with rationale]
- **Practice 3**: [Specific guidance with rationale]

## Common Pitfalls
❌ **Don't**: [Anti-pattern]
✅ **Do**: [Correct approach]

❌ **Don't**: [Anti-pattern]
✅ **Do**: [Correct approach]

## Quality Checklist
- [ ] Requirement 1: [Specific check]
- [ ] Requirement 2: [Specific check]
- [ ] Requirement 3: [Specific check]
- [ ] All validations passed

## Examples

### Example 1: [Use Case Name]
**Input:**
```
[Input example]
```

**Process:**
1. [Step description]
2. [Step description]

**Output:**
```
[Output example]
```

**Notes**: [Additional context about the example]

### Example 2: [Use Case Name]
[Second example with different scenario]

## Advanced Usage
For advanced features and edge cases, see reference/advanced.md
For API reference, see reference/api_reference.md
For templates, see templates/

## Subagent Integration (If Applicable)

### When to Delegate
- Research tasks requiring domain expertise
- Complex multi-step workflows
- Specialized code generation
- Quality assurance and validation

### Research Phase
```
Use context-collector when:
- Domain knowledge required
- Technical research needed
- Compliance/standards validation
```

### Implementation Phase
```
Use [specialist] when:
- Language-specific code generation
- Performance optimization required
- Domain-specific patterns needed
```

### Validation Phase
```
Use code-reviewer/qa-specialist when:
- Implementation complete
- Security review required
- Best practices validation
```

### Integration Example
```markdown
1. **Assess** (Main Agent): Analyze requirements, decompose tasks
2. **Research** (Parallel): context-collector + domain-specialist
3. **Implement** (Sequential): architect → implementer → reviewer
4. **Finalize** (Main Agent): Aggregate results, resolve gaps
```

### State Management
**Files for State Transfer:**
- Save subagent outputs: `phase-results.md`
- Pass to next: "Read phase-results.md for context"
- Master status: `workflow-status.json`

**Context Provision:**
- Embed complete background in each delegation
- Specify exact output format expected
- Never assume conversation history

## Troubleshooting

### Issue 1: [Problem Description]
**Cause**: [Why it happens]
**Solution**: [How to fix]
```bash
# Command to resolve
command example
```

### Issue 2: [Problem Description]
**Cause**: [Why it happens]
**Solution**: [How to fix]

## Additional Resources
- [Official Documentation](https://example.com/docs)
- [GitHub Repository](https://github.com/example/repo)
- reference/domain_knowledge.md
```

---

## Reference Links & Versioning

### Official Documentation
- **Skills Overview**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Claude Code Skills**: https://docs.claude.com/en/docs/claude-code/skills
- **Release Notes**: https://docs.claude.com/en/release-notes/overview

### GitHub Repositories
- **Anthropic Skills**: https://github.com/anthropics/skills
- **Claude Cookbooks**: https://github.com/anthropics/claude-cookbooks/tree/main/skills
- **Custom Skills Examples**: https://github.com/anthropics/claude-cookbooks/tree/main/skills/custom_skills

### Skill Examples by Complexity

**Simple Skills:**
- **Algorithmic Art**: https://github.com/anthropics/skills/tree/main/algorithmic-art

**Moderate Skills:**
- **XLSX**: https://github.com/anthropics/skills/tree/main/document-skills/xlsx
- **PDF**: https://github.com/anthropics/skills/tree/main/document-skills/pdf

**Advanced Skills:**
- **MCP Builder**: https://github.com/anthropics/skills/tree/main/mcp-builder
- **Webapp Testing**: https://github.com/anthropics/skills/tree/main/webapp-testing

**Enterprise Skills:**
- **Brand Guidelines**: https://github.com/anthropics/skills/tree/main/brand-guidelines
- **Internal Comms**: https://github.com/anthropics/skills/tree/main/internal-comms

**Workflow Skills:**
- **Worktree Manager**: https://github.com/disler/claude-code-hooks-multi-agent-observability/tree/main/.claude/skills

### Subagent Resources
- **Official Guide**: https://docs.claude.com/en/docs/claude-code/sub-agents
- **Community Collection**: https://github.com/VoltAgent/awesome-claude-code-subagents
- **Practical Integration**: https://jewelhuq.medium.com/practical-guide-to-mastering-claude-codes-main-agent-and-sub-agents-fd52952dcf00
- **Parallelization Guide**: https://zachwills.net/how-to-use-claude-code-subagents-to-parallelize-development/
- **Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices

### API Version Headers

```python
# For programmatic skill creation via API
headers = {
    "anthropic-beta": "skills-2025-10-02",
    "anthropic-beta": "code-execution-2025-08-25",
    "anthropic-beta": "files-api-2025-04-14"
}
```

### Versioning & Updates

**This Guide Version**: 1.1.0 (November 2025)
- **v1.1.0 (November 2025)**: Added comprehensive subagent integration patterns, capabilities matrix, orchestration strategies, and anti-patterns
- **v1.0.0 (January 2025)**: Initial release with skill levels, best practices, and templates

**Update Policy:**
- When official documentation changes skill specifications
- When new skill patterns emerge from Anthropic
- When API versions update (check headers above)
- Review quarterly against official docs

**How to Update This Guide:**
1. Check official documentation for changes
2. Review new skill examples from Anthropic repository
3. Test new patterns with Claude Code
4. Update relevant sections
5. Increment version number
6. Document changes in comments

---

## Summary: Key Takeaways

### Architecture
1. **Three-level progressive loading**: metadata → instructions → resources
2. **Filesystem-based**: bash navigation, scripts execute without loading code
3. **One level deep**: References should be direct from SKILL.md

### Structure
1. **SKILL.md under 500 lines** (optimal for context)
2. **YAML frontmatter**: name (max 64 chars) + description (max 1024 chars, third person with triggers)
3. **Forward slashes always**: `scripts/helper.py` not `scripts\helper.py`
4. **Gerund naming**: `processing-pdfs` not `process-pdf`

### Skill Levels
1. **Simple**: Single task, instructions only, 100-300 lines
2. **Moderate**: Multiple operations, 1-3 scripts/templates, 300-500 lines
3. **Advanced**: Multi-phase workflows, 5-10+ files, extensive references

### Best Practices
1. **Evaluations first**: Build tests, iterate based on real behavior
2. **Validation loops**: Create → Validate → Fix → Repeat
3. **Solve in scripts**: Don't punt complex logic to Claude
4. **Consistent terms**: Pick one, stick with it
5. **Concrete examples**: Input/output pairs demonstrate style
6. **Test cross-model**: Haiku, Sonnet, Opus compatibility

### Anti-Patterns
1. **No time-sensitive info**, **no Windows paths**, **no deep nesting**
2. **Don't assume installed tools**, **don't list equal options**, **don't expose internal errors**
3. **Avoid vague descriptions**, **missing validation**, **decision paralysis**

### Distribution
1. **Skills don't sync** across surfaces (claude.ai, API, Code)
2. **Claude Code**: Filesystem-based (personal: `~/.claude/skills/` or project: `.claude/skills/`)
3. **Share via git** for team project skills
4. **Semantic versioning** for stability

### Security
1. **Only trusted sources**: You created or Anthropic official
2. **Input validation**: Pydantic/Zod for structured validation
3. **Educational errors**: Helpful, actionable messages
4. **Tool hints**: `readOnlyHint`, `destructiveHint`, `idempotentHint`

### Subagent Integration
1. **Context isolation**: Each invocation is fresh, NO conversation history, NO memory
2. **Explicit orchestration**: Main agent manually manages workflow, NO nested delegation
3. **File artifacts**: State transfer mechanism between subagents
4. **Parallel power**: 3x-5x speedup for independent tasks, each gets full 200k context
5. **Specialization wins**: Focused experts outperform generalists (90.2% improvement)
6. **Keywords matter**: Use PROACTIVELY, MUST BE USED, CRITICAL, NEVER, ALWAYS strategically
7. **Output format**: Always specify exact structure to prevent context overload
