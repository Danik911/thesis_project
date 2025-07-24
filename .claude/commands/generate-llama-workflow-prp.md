# Generate LlamaIndex Workflow PRP

Generate a comprehensive PRP for LlamaIndex workflow-based multi-agent features with thorough research and critical gotchas documentation.

## Feature file: $ARGUMENTS

Generate a complete PRP for implementing a multi-agent workflow feature in the thesis project. Read the feature file first to understand what needs to be created.

## Research Process (CRITICAL - USE MCP TOOLS)

1. **LlamaIndex Documentation Research**
   - **ALWAYS USE context7 first**: `mcp__context7__resolve-library-id` with "llama-index"
   - Then use `mcp__context7__get-library-docs` with topics:
     - "workflow events step"
     - "workflow context collect_events"
     - "workflow parallel execution"
     - "workflow human loop"
     - "workflow timeout errors"
     - "workflow rate limiting"
   - Document ALL workflow patterns found

2. **External Research with MCP Tools**
   - **USE one-search**: `mcp__one-search-mcp__one_search` for:
     - "llama-index workflow multi-agent example"
     - "llama-index workflow event collection pattern"
     - "llama-index human in the loop workflow"
     - "llama-index workflow infinite loop fix"
     - "llama-index rate limit exhaustion"
     - "llama-index vector database corruption"
   - **USE perplexity for complex questions**: `mcp__perplexity-mcp__reason` for:
     - "How to implement multi-agent coordination with LlamaIndex workflows?"
     - "Best practices for event-driven agent communication in LlamaIndex"
     - "How to prevent infinite loops in LlamaIndex workflows?"
     - "How to handle rate limits and API costs in LlamaIndex RAG systems?"
     - "GAMP-5 software categorization for pharmaceutical validation"

3. **Codebase Analysis**
   - Search `/home/anteb/thesis_project/test_generation/examples/` for workflow patterns
   - Study `consultation.py` for human-in-the-loop pattern
   - Review `thesis/workflow.py` for complex workflow structure
   - Note event definitions and step decorators

4. **Pharmaceutical Domain Research**
   - **USE perplexity**: `mcp__perplexity-mcp__deep_research` for:
     - "GAMP-5 software categories and validation requirements"
     - "21 CFR Part 11 compliance for test generation"
     - "ALCOA+ principles in pharmaceutical testing"
   - Document compliance requirements thoroughly

## PRP Generation Structure

### 1. Overview Section
- Clear description of the multi-agent workflow feature
- How it fits into the thesis project architecture
- Reference to GAMP-5 categorization as entry point

### 2. Critical Context (MUST INCLUDE)
- **LlamaIndex Documentation URLs**: From context7 research
- **Code Examples**: Real workflow patterns from research
- **Event Definitions**: Complete event class structures
- **Workflow Architecture**: Step-by-step flow diagram
- **Compliance Requirements**: GAMP-5, 21 CFR Part 11, ALCOA+

### 3. Implementation Blueprint
```python
# Pseudocode showing workflow structure with error handling
class TestGenerationWorkflow(Workflow):
    def __init__(self, max_iterations=50, timeout=900):
        super().__init__(timeout=timeout)
        self.max_iterations = max_iterations
        self.api_manager = WorkflowAPIManager(max_expensive_calls=3)
    
    # GAMP-5 categorization MUST be first
    @step
    async def categorize_gamp5(self, ctx: Context, ev: StartEvent) -> GAMPCategorizationEvent:
        # Rate limit protection
        # Input validation
        # Error handling
    
    # Parallel agent execution with worker limits
    @step(num_workers=3)
    async def parallel_agents(self, ctx: Context, ev: AgentRequestEvent) -> AgentResultEvent:
        # Timeout handling
        # Failure recovery
    
    # Human-in-the-loop consultation with timeout
    @step
    async def human_consultation(self, ctx: Context, ev: ConsultationEvent) -> UserDecisionEvent:
        # Human timeout handling
        # Default fallback choices
    
    # Event collection and synchronization
    @step
    async def collect_results(self, ctx: Context, ev: CollectionEvent) -> StopEvent:
        # Handle partial results
        # Validate completeness
```

### 4. Task List (In Order)
1. Create event definitions for all agent communications
2. Implement GAMP-5 categorization step (CRITICAL - FIRST)
3. Create planner agent workflow step
4. Implement parallel agent execution (context, SME, research)
5. Add human-in-the-loop consultation step
6. Create test generation step with validation
7. Add compliance validation (ALCOA+)
8. Implement error handling and retry logic
9. Create comprehensive tests
10. Add monitoring and audit trail

### 5. CRITICAL GOTCHAS AND SOLUTIONS

#### A. RAG System Issues
- **Rate Limit Exhaustion**: LlamaIndex extractors default to expensive models
  - Solution: Use cheaper models for metadata extraction
  - Implementation: Configure extractors with cost-effective models
- **Transaction Failures**: RAG ingestion failing mid-way
  - Solution: Implement transactional ingestion with resume capability
  - Implementation: Cache processed chunks, support incremental processing
- **Embedding Cache Inefficiencies**: Slow startup times
  - Solution: Intelligent embedding cache with SHA-256 content hashing
  - Implementation: Persist cache to disk, check content hash before API calls
- **Vector Database Corruption**: Mismatched embedding dimensions
  - Solution: Database integrity checks, clear and re-index when needed
  - Implementation: Validate model consistency before operations

#### B. Agent Workflow Issues
- **Infinite Loops**: Workflow getting stuck, max iterations reached
  - Solution: Increase iteration limits, robust tool error handling
  - Implementation: Clear agent handoff instructions, fallback logic
- **Timeout Failures**: Workflows terminating prematurely
  - Solution: Configurable timeouts, per-source timeouts for research
  - Implementation: Workflow-scoped API call manager with caching
- **Tool Usage Errors**: Faulty output handling
  - Solution: Content extraction framework with fallback parsing
  - Implementation: Validation steps before saving content
- **Inter-Agent Communication**: Data handoff failures
  - Solution: Fix parameter propagation, data conversion logic
  - Implementation: Strict agent initialization checks

#### C. Environment & Configuration Issues
- **UTF-16 Encoding Issues**: .env files causing Unicode decode errors
  - Solution: Always use UTF-8 encoding, recreate files if needed
  - Implementation: Validation scripts to check file encoding
- **API Key Recognition**: Environmental variables not loading
  - Solution: Verify file location, validate configuration
  - Implementation: Built-in validation script with clear error messages
- **Invalid Model Names**: OpenAI API errors from typos
  - Solution: Centralized configuration, model name validation
  - Implementation: Configuration discipline and error checking

#### D. Large Output & Tooling Issues
- **String Length Errors**: Claude Code crashing from massive output
  - Solution: Reduced default logging, truncated stream handlers
  - Implementation: Safe output functions, environment-based controls
- **JSON Corruption**: Truncated content, malformed responses
  - Solution: Robust content extraction, chunking for large content
  - Implementation: Validation steps, fallback parsing logic

### 6. Validation Gates (EXECUTABLE)
```bash
# Level 1: Syntax & Type Checking
uv run ruff check --fix src/
uv run mypy src/

# Level 2: Unit Tests
uv run pytest tests/unit/ -v

# Level 3: Integration Tests  
uv run pytest tests/integration/ -v

# Level 4: Compliance Validation
uv run python -m src.validation.gamp5_check
uv run python -m src.validation.alcoa_validator

# Level 5: Gotcha Prevention Checks
uv run python -m src.validation.vector_db_integrity
uv run python -m src.validation.api_limit_monitor
uv run python -m src.validation.output_size_check
```

### 7. Error Prevention Patterns
```python
# Rate limit management
@rate_limit_protection
async def expensive_operation():
    pass

# Transaction safety
@transactional_operation
async def ingest_documents():
    pass

# Output size management
@handle_large_output_error
async def generate_content():
    pass

# Agent communication validation
@validate_agent_handoff
async def pass_data_between_agents():
    pass
```

## Quality Checklist
- [ ] Used context7 for ALL LlamaIndex documentation
- [ ] Used one-search for real-world examples AND error solutions
- [ ] Used perplexity for complex architectural questions AND debugging strategies
- [ ] Included complete event definitions
- [ ] Referenced thesis project examples
- [ ] Added GAMP-5 categorization as first step
- [ ] Included human-in-the-loop pattern
- [ ] Added all validation gates including gotcha prevention
- [ ] Documented ALL critical gotchas with solutions
- [ ] Included error prevention patterns
- [ ] Added monitoring and recovery mechanisms

## Critical Success Factors
1. **MCP Tool Usage**: MUST use all three MCP tools extensively for both implementation AND debugging
2. **Workflow Patterns**: Include ALL patterns from research
3. **Compliance First**: GAMP-5 categorization drives everything
4. **Event-Driven**: Every agent interaction via events
5. **Human-in-Loop**: Critical decisions require human input
6. **Error Prevention**: All known gotchas must be addressed proactively
7. **Recovery Mechanisms**: Every failure mode needs a recovery path

## Output
Save as: `PRPs/llama-workflow-{feature-name}.md`

Score the PRP on scale 1-10 for one-pass implementation success.

**REMEMBER**: The AI agent executing this PRP only has access to what you provide. Make the context comprehensive and include ALL research findings, URLs, examples, AND all gotchas with their solutions. This is a production system that must handle real-world failure modes.