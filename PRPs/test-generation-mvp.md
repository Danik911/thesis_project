name: "LLM Test Generation MVP - Multi-Agent System for CSV"
description: |

## Purpose

MVP implementation of a multi-agent LLM system for generating Operational Qualification (OQ) test scripts from User Requirements Specifications (URS) in pharmaceutical CSV context. This PRP focuses on establishing the core workflow with security and compliance considerations.

## Core Principles

1. **Security First**: OWASP LLM Top 10 compliance from the start
2. **Regulatory Alignment**: GAMP 5 and 21 CFR Part 11 adherence
3. **Multi-Agent Architecture**: Specialized agents for different tasks
4. **Validation Loops**: Continuous verification throughout the pipeline

---

## Goal

Build an MVP that can:
1. Parse a URS document and extract requirements
2. Generate OQ test scripts using multi-agent collaboration
3. Validate outputs for compliance and security
4. Provide traceable audit trails

## Why

- Manual CSV processes take 40% of validation effort
- Need for consistent, compliant test generation
- Security risks in AI-generated content must be mitigated
- Pharmaceutical industry needs evidence-based AI adoption

## What

### Success Criteria

- [ ] Successfully parse at least 3 different URS formats
- [ ] Generate test scripts with ≥80% requirements coverage
- [ ] Pass OWASP security checks (no critical vulnerabilities)
- [ ] Maintain full traceability from requirement to test
- [ ] Complete generation in <5 minutes for typical URS

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://www.ispe.org/publications/guidance-documents/gamp-5
  why: GAMP 5 validation framework - critical for compliance

- file: /home/anteb/thesis_project/test_generation/examples/scientific_writer/thesis/workflow.py
  why: Template workflow pattern to follow

- file: /home/anteb/thesis_project/test_generation/examples/scientific_writer/thesis/thesis_agents.py
  why: Agent creation patterns

- doc: https://owasp.org/www-project-top-10-for-large-language-model-applications/
  section: LLM01, LLM03, LLM06
  critical: Prompt injection, data poisoning, output handling

- docfile: /home/anteb/thesis_project/PRPs/ai_docs/prp_methodology.md
  why: PRP framework methodology
```

### Current Codebase tree

```bash
thesis_project/
├── src/
│   ├── agents/
│   ├── core/
│   ├── rag/
│   ├── security/
│   ├── validation/
│   └── shared/
├── tests/
├── docs/
├── PRPs/
└── .claude/
```

### Desired Codebase tree with files to be added

```bash
thesis_project/
├── src/
│   ├── agents/
│   │   ├── planner.py          # Frontier model orchestrator
│   │   ├── context_agent.py    # RAG/CAG provider
│   │   ├── specialist_agents.py # Domain experts
│   │   ├── research_agent.py   # Regulatory updates
│   │   └── generator_agent.py  # Test script generator
│   ├── core/
│   │   ├── workflow.py         # Main workflow
│   │   ├── events.py           # Event definitions
│   │   └── tools.py            # Shared tools
│   ├── rag/
│   │   ├── components.py       # RAG system
│   │   └── config.py           # RAG configuration
│   ├── security/
│   │   ├── owasp_validator.py  # OWASP checks
│   │   └── alcoa_compliance.py # ALCOA+ validation
│   └── main.py                 # Entry point
```

### Known Gotchas

```python
# CRITICAL: ChromaDB dimension mismatch
# Must use consistent embedding model across all components
# Default: text-embedding-3-small (1536 dimensions)

# CRITICAL: LlamaIndex workflow context
# Context must be properly initialized and passed between steps

# CRITICAL: Prompt injection prevention
# Use structured queries, never concatenate user input directly
```

## Implementation Blueprint

### Data models and structure

```python
# Core data models
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class URSRequirement(BaseModel):
    id: str
    text: str
    category: str  # functional, performance, security, etc.
    priority: str  # high, medium, low
    
class TestStep(BaseModel):
    step_number: int
    action: str
    expected_result: str
    data_input: Optional[str] = None
    
class OQTestScript(BaseModel):
    id: str
    requirement_id: str  # Traceability
    title: str
    purpose: str
    prerequisites: List[str]
    steps: List[TestStep]
    acceptance_criteria: str
    created_at: datetime
    created_by: str = "LLM System"
    
class ValidationResult(BaseModel):
    compliant: bool
    issues: List[Dict[str, str]]
    coverage_score: float
    security_score: float
```

### List of tasks

```yaml
Task 1: Create base workflow structure
MODIFY src/core/workflow.py:
  - INHERIT from llama_index.core.workflow.Workflow
  - DEFINE workflow steps using @step decorator
  - IMPLEMENT context management

CREATE src/core/events.py:
  - DEFINE URSAnalysisEvent
  - DEFINE TestPlanEvent
  - DEFINE TestGenerationEvent
  - DEFINE ValidationEvent

Task 2: Implement Planner Agent
CREATE src/agents/planner.py:
  - USE GPT-4 as frontier model
  - IMPLEMENT orchestration logic
  - ENSURE no proprietary data exposure

Task 3: Implement Context Agent
CREATE src/agents/context_agent.py:
  - SETUP ChromaDB vector store
  - IMPLEMENT RAG pipeline
  - ADD regulatory document retrieval

Task 4: Implement Test Generator
CREATE src/agents/generator_agent.py:
  - USE open-source model (Llama/Mistral)
  - IMPLEMENT test script generation
  - ENSURE GAMP 5 compliance

Task 5: Add Security Validation
CREATE src/security/owasp_validator.py:
  - CHECK for prompt injection patterns
  - VALIDATE output safety
  - IMPLEMENT Llama Guard integration

Task 6: Add Compliance Checks
CREATE src/security/alcoa_compliance.py:
  - VERIFY Attributable, Legible, Contemporaneous
  - CHECK Original, Accurate requirements
  - ENSURE Complete, Consistent, Enduring, Available

Task 7: Create main entry point
CREATE src/main.py:
  - SETUP argument parsing
  - INITIALIZE workflow
  - ADD Gradio interface option
```

### Per task pseudocode

```python
# Task 1: Workflow Structure
class TestGenerationWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.planner = create_planner_agent()
        self.context_agent = create_context_agent()
        # ... other agents
    
    @step
    async def analyze_urs(self, ctx: Context, ev: StartEvent):
        # Parse URS document
        requirements = parse_urs(ev.urs_content)
        # Send to planner for analysis
        plan = await self.planner.analyze(requirements)
        return URSAnalysisEvent(requirements=requirements, plan=plan)
    
    @step
    async def generate_tests(self, ctx: Context, ev: URSAnalysisEvent):
        # Retrieve context
        context = await self.context_agent.get_context(ev.requirements)
        # Generate test scripts
        scripts = await self.generator.generate(ev.requirements, context)
        return TestGenerationEvent(scripts=scripts)

# Task 5: Security Validation
class OWASPValidator:
    def validate_prompt(self, prompt: str) -> ValidationResult:
        # Check for injection patterns
        injection_patterns = [
            r"ignore previous instructions",
            r"system:",
            r"</prompt>",
        ]
        
        issues = []
        for pattern in injection_patterns:
            if re.search(pattern, prompt, re.I):
                issues.append({
                    "type": "prompt_injection",
                    "pattern": pattern,
                    "severity": "high"
                })
        
        return ValidationResult(
            compliant=len(issues) == 0,
            issues=issues
        )
```

### Integration Points

```yaml
DATABASE:
  - ChromaDB: "./lib/chroma_db"
  - Embedding model: "text-embedding-3-small"
  - Dimension: 1536

CONFIG:
  - add to: src/shared/config.py
  - pattern: "PLANNER_MODEL = os.getenv('PLANNER_MODEL', 'gpt-4')"

MONITORING:
  - Phoenix integration
  - Trace all agent interactions
  - Log compliance checks
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check src/ --fix
uv run mypy src/

# Expected: No errors
```

### Level 2: Unit Tests

```python
# CREATE tests/unit/test_agents.py
def test_planner_agent_creation():
    """Planner agent initializes correctly"""
    agent = create_planner_agent()
    assert agent.llm.model == "gpt-4"

def test_urs_parsing():
    """URS requirements extracted correctly"""
    urs_text = "REQ-001: System shall validate user input"
    requirements = parse_urs(urs_text)
    assert len(requirements) == 1
    assert requirements[0].id == "REQ-001"

def test_security_validation():
    """Security checks detect injection"""
    validator = OWASPValidator()
    result = validator.validate_prompt("ignore previous instructions")
    assert not result.compliant
```

```bash
# Run tests
uv run pytest tests/unit/ -v
```

### Level 3: Integration Test

```bash
# Start the service
uv run python -m src.main --urs-file tests/data/sample_urs.txt

# Expected output structure:
# - Generated test scripts in JSON format
# - Compliance report
# - Traceability matrix
```

### Level 4: End-to-End Validation

```bash
# Full workflow test with real URS
uv run python -m src.main --urs-file tests/data/real_urs.pdf \
  --output-dir results/ \
  --enable-monitoring

# Verify:
# - All requirements covered
# - No security vulnerabilities
# - Full audit trail generated
# - Phoenix traces captured
```

## Final validation Checklist

- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] Sample URS processed successfully
- [ ] Security validation passes
- [ ] Compliance checks pass
- [ ] Traceability maintained
- [ ] Phoenix monitoring working

---

## Anti-Patterns to Avoid

- ❌ Don't send proprietary data to frontier models
- ❌ Don't skip security validation
- ❌ Don't generate tests without traceability
- ❌ Don't ignore ALCOA+ principles
- ❌ Don't hardcode model responses
- ❌ Don't bypass validation loops