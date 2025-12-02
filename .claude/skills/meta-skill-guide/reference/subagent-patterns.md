# Subagent Integration Patterns

## When to Delegate vs Direct Implementation

**Skills provide the "WHEN" and "WHAT"**
**Subagents provide the "HOW"**

| Task Characteristics | Recommendation |
|---------------------|----------------|
| Simple, <10 min tasks | Direct implementation in skill |
| Research-heavy tasks | Delegate to `context-collector` |
| Multi-stage workflows | Orchestrate multiple specialized subagents |
| Language-specific code | Delegate to specialists (python-expert, typescript-pro) |
| Quality assurance | Delegate to `code-reviewer`, `test-automator` |
| Security analysis | Delegate to `security-auditor` |

**Performance**: 90.2% improvement for parallel tasks, 3x-5x speedup for parallelizable workflows.

---

## Subagent Capabilities Matrix

### What Subagents CAN Do
- Operate in independent 200k token context window
- Execute parallel tasks without context interference
- Access explicitly granted tools (Read, Write, Edit, Bash, Grep, Glob, MCP)
- Maintain specialized domain knowledge in system prompt
- Return condensed summaries (1,000-2,000 tokens)

### What Subagents CANNOT Do
- **NO access to main conversation history**
- **NO access to user preferences** from current session
- **NO access to other subagent results** unless explicitly provided
- **NO memory of previous invocations**
- **CANNOT invoke other subagents** (no nested delegation)
- **CANNOT persist state** without explicit file writes

### What Requires Special Handling
- **Multi-step workflows**: Explicit output → input chaining
- **Error recovery**: Full context re-provision on retry
- **Complex coordination**: Dependency management must be explicit

---

## Context Isolation Mechanics

Each subagent receives completely isolated environment:
- Fresh 200k token context window
- Independent execution loop
- Separate tool permission set
- Custom system prompt (no inheritance)

**Information Flow:**
```
MAIN AGENT → [Explicit Context + Task] → SUBAGENT
           ←  [Condensed Summary]    ←
```

**What Gets Passed:**
1. Initial prompt with task description + all necessary context
2. Tool permissions explicitly granted
3. System prompt with role definition

**What Gets Returned:**
1. Condensed output (1,000-2,000 token summary)
2. Artifacts (files, documents, code)
3. Status (success/failure)

---

## Special Instruction Keywords

### Proactive Delegation Triggers (in `description`)
- **"Use PROACTIVELY"** - Automatic delegation without explicit request
- **"MUST BE USED"** - Strongest automatic invocation trigger
- **"ALWAYS USE when"** - Conditional automatic delegation

### System Prompt Emphasis (Increasing Strength)
1. Normal text - Standard instructions
2. **"IMPORTANT:"** - Critical instructions
3. **"CRITICAL:"** - Highest priority
4. **"YOU MUST"** - Mandatory requirements
5. **"NEVER"** - Absolute prohibitions
6. **"ALWAYS"** - Invariant behaviors

### Extended Thinking Triggers
- **"think"** - Basic reasoning
- **"think hard"** - Moderate computation
- **"think harder"** - Significant analysis
- **"ultrathink"** - Maximum computation

---

## Subagent File Template

```yaml
---
name: agent-identifier
description: Brief capability overview. Use PROACTIVELY when [trigger]. MUST BE USED for [scenarios].
tools: Read, Grep, Glob, Edit, Write, Bash
model: inherit
---

# [Agent Role Title]

## Core Expertise
[Clear definition of specialized domain]

## Activation Scenarios
- [Trigger condition 1]
- [Trigger condition 2]

## Output Format
[Structured format specification]

## Critical Rules
- **IMPORTANT:** [High-priority rule]
- **NEVER:** [Prohibition]
- **ALWAYS:** [Invariant behavior]
```

---

## Delegation Prompt Template

```markdown
Use the [subagent-name] agent to [specific task].

Context:
- [Relevant background information]
- [Project constraints]
- [Dependencies]

Specific Requirements:
1. [Requirement 1]
2. [Requirement 2]

Success Criteria:
- [Measurable outcome 1]
- [Measurable outcome 2]

Output Format:
[Expected structure - JSON, markdown, code, etc.]
```

---

## Orchestration Patterns

### Pattern 1: Parallel Execution (Independent Tasks)

```markdown
Launch 3 subagents in parallel (single message, multiple Task calls):
- Task(product-manager, "Define user stories")
- Task(ux-designer, "Propose UX covering all states")
- Task(senior-engineer, "Outline technical approach")

Each agent works independently with full 200k context.
```

**Benefits**: 3x-5x speed, no context pressure
**Limitations**: Cannot share insights during execution

### Pattern 2: Sequential Chain (Dependent Tasks)

```markdown
Step 1: context-collector → research-notes.md
Step 2: architect (with research-notes.md) → design-spec.md
Step 3: implementer (with design-spec.md) → code + tests
Step 4: reviewer (with code) → review-report.md
```

**Key**: Use file artifacts as state transfer mechanism

### Pattern 3: Hub-and-Spoke (Verification)

```markdown
Step 1: implementer → feature-code.py

Step 2: Parallel validation:
  ├─ security-auditor → security-report.md
  ├─ performance-engineer → perf-report.md
  └─ qa-specialist → qa-report.md

Step 3: Main agent aggregates reports → decision
```

### Pattern 4: Iterative Refinement

```markdown
Iteration 1:
  architect → draft-v1.md
  reviewer → feedback-v1.md

Iteration 2:
  architect (with feedback-v1) → draft-v2.md
  reviewer → feedback-v2.md

Iteration N: → final-design.md
```

**Challenge**: Each invocation requires full context re-provision
**Solution**: Cumulative context document that grows each iteration

---

## Anti-Patterns

### Context Amnesia
```markdown
# WRONG
First: "Review the authentication module"
Later: "Now fix the issues you found" ← NO MEMORY

# RIGHT
First: "Review auth module and save to auth-review.md"
Later: "Fix issues in auth-review.md: [paste issues]"
```

### Nested Delegation
```markdown
# WRONG - Subagents CANNOT invoke other subagents
orchestrator-agent tries to invoke worker-agent → FAILS

# RIGHT - Main agent orchestrates all
main → agent-1 → result-1
main (reads result-1) → agent-2 → result-2
```

### Implicit Context Transfer
```markdown
# WRONG
"Review the API changes" (which changes? what to look for?)

# RIGHT
"Review src/api/auth.ts for:
- Security vulnerabilities in JWT validation
- Proper error handling
- Rate limiting implementation
Context: New OAuth2 endpoint for user login."
```

### Output Format Ambiguity
```markdown
# WRONG
"Research best practices for error handling"
(returns 15 pages → context overload)

# RIGHT
"Research error handling and return:
1. Top 3 patterns (2-3 sentences each)
2. One code example for Node.js
3. Key anti-patterns (bullet list)
Format: Markdown with clear sections"
```

---

## Skill Integration Strategy

### Task Complexity Analysis
- Simple tasks (< 10 min): Direct implementation
- Research-heavy: Delegate to `context-collector`
- Multi-stage: Orchestrate specialized subagents

### Specialization Mapping
- Code generation → Language-specific subagents
- Quality assurance → `code-reviewer`, `test-automator`
- Documentation → `documentation-expert`
- Security → `security-auditor`

### State Management
```
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

### Error Recovery
1. Capture error output
2. Analyze failure reason
3. Provide additional context if needed
4. Retry with refined prompt
5. Escalate to user if persistent
