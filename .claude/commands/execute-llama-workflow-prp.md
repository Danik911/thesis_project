# Execute LlamaIndex Workflow PRP

Implement a LlamaIndex workflow-based multi-agent system using the PRP file with comprehensive error handling and gotcha prevention.

## PRP File: $ARGUMENTS

## Execution Process

1. **Load PRP and Research First**
   - Read the specified LlamaIndex workflow PRP file
   - Understand ALL requirements, especially GAMP-5 categorization
   - **USE context7**: Get latest LlamaIndex workflow documentation
     - `mcp__context7__get-library-docs` for "workflow", "events", "step"
     - Research error patterns and debugging strategies
   - Review provided examples from `/home/anteb/thesis_project/test_generation/examples/`

2. **ULTRATHINK Before Implementation**
   - Think deeply about the multi-agent architecture
   - Plan event flow between agents
   - Consider GAMP-5 categorization impact on workflow
   - **CRITICALLY**: Plan for all known gotchas and failure modes
   - Use TodoWrite to break down implementation into steps
   - **USE perplexity**: `mcp__perplexity-mcp__reason` if you encounter architectural challenges

3. **Execute Implementation Plan with Error Prevention**
   
   ### A. Event Definitions (FIRST) - With Validation
   ```python
   # src/events.py - Define ALL workflow events with proper validation
   from llama_index.core.workflow import Event
   from pydantic import validator
   
   class GAMPCategorizationEvent(Event):
       """CRITICAL: First event - determines validation rigor"""
       category: int  # 3, 4, or 5
       rationale: str
       urs_summary: str
       confidence_score: float
       
       @validator('category')
       def validate_category(cls, v):
           if v not in [3, 4, 5]:
               raise ValueError('GAMP category must be 3, 4, or 5')
           return v
   
   class ErrorRecoveryEvent(Event):
       """Event for handling failures and retries"""
       original_event: str
       error_type: str
       retry_count: int
       fallback_strategy: str
   ```
   
   ### B. Workflow Structure with Comprehensive Error Handling
   ```python
   # src/workflows/test_generation.py
   from llama_index.core.workflow import Workflow, step, Context
   import asyncio
   from typing import Union
   
   class TestGenerationWorkflow(Workflow):
       def __init__(self, timeout=900, max_iterations=50):
           super().__init__(timeout=timeout)
           self.max_iterations = max_iterations
           self.api_manager = WorkflowAPIManager(max_expensive_calls=3)
           self.retry_counts = {}
           
       @step
       async def categorize_gamp5(self, ctx: Context, ev: StartEvent) -> GAMPCategorizationEvent:
           """MUST BE FIRST - categorizes software per GAMP-5 with error handling"""
           try:
               # Rate limit protection
               await self.api_manager.check_limits("gamp_categorization")
               
               # Input validation
               if not hasattr(ev, 'urs_content') or not ev.urs_content:
                   raise ValueError("URS content is required for GAMP-5 categorization")
               
               # Implement categorization logic with fallbacks
               result = await self._perform_gamp5_categorization(ev.urs_content)
               
               # Validate result
               if not result or result.category not in [3, 4, 5]:
                   # Fallback to conservative category 5
                   result = GAMPCategorizationEvent(
                       category=5,
                       rationale="Defaulted to most rigorous validation due to uncertainty",
                       urs_summary="Could not analyze URS content",
                       confidence_score=0.0
                   )
               
               return result
               
           except Exception as e:
               # Log error and provide fallback
               await ctx.set("gamp5_error", str(e))
               return GAMPCategorizationEvent(
                   category=5,  # Most conservative approach
                   rationale=f"Error in categorization: {str(e)}, defaulted to category 5",
                   urs_summary="Error in analysis",
                   confidence_score=0.0
               )
   ```
   
   ### C. Multi-Agent Implementation with Gotcha Prevention
   ```python
   @step(num_workers=3)
   async def parallel_agents(self, ctx: Context, ev: AgentRequestEvent) -> Union[AgentResultEvent, ErrorRecoveryEvent]:
       """Parallel agent execution with comprehensive error handling"""
       try:
           # Check for agent initialization failures
           agents = await ctx.get("agents", {})
           if not agents or any(agent is None for agent in agents.values()):
               raise ValueError("One or more agents failed to initialize")
           
           # Timeout protection
           tasks = []
           for agent_type, request in ev.agent_requests.items():
               task = asyncio.create_task(
                   self._run_agent_with_timeout(agents[agent_type], request, timeout=300)
               )
               tasks.append((agent_type, task))
           
           # Collect results with partial failure handling
           results = {}
           failed_agents = []
           
           for agent_type, task in tasks:
               try:
                   result = await task
                   results[agent_type] = result
               except asyncio.TimeoutError:
                   failed_agents.append(f"{agent_type}: timeout")
               except Exception as e:
                   failed_agents.append(f"{agent_type}: {str(e)}")
           
           # Handle partial failures
           if failed_agents and len(results) == 0:
               # Complete failure
               return ErrorRecoveryEvent(
                   original_event="parallel_agents",
                   error_type="complete_agent_failure",
                   retry_count=self.retry_counts.get("parallel_agents", 0),
                   fallback_strategy="use_default_responses"
               )
           elif failed_agents:
               # Partial failure - continue with available results
               await ctx.set("agent_failures", failed_agents)
           
           return AgentResultEvent(results=results, partial_failure=bool(failed_agents))
           
       except Exception as e:
           return ErrorRecoveryEvent(
               original_event="parallel_agents", 
               error_type="system_error",
               retry_count=self.retry_counts.get("parallel_agents", 0),
               fallback_strategy=str(e)
           )
   
   @step
   async def human_consultation(self, ctx: Context, ev: ConsultationRequiredEvent) -> UserDecisionEvent:
       """Human-in-the-loop with timeout and default handling"""
       try:
           # Present options to user
           ctx.write_event_to_stream(ev)
           
           # Wait for user response with timeout
           try:
               response = await asyncio.wait_for(
                   ctx.wait_for_event(UserResponseEvent),
                   timeout=300  # 5 minutes
               )
               return UserDecisionEvent(
                   decisions=response.decisions,
                   source="human_input"
               )
           except asyncio.TimeoutError:
               # Default to conservative choices
               default_decisions = self._get_conservative_defaults(ev.options)
               await ctx.set("human_timeout", True)
               return UserDecisionEvent(
                   decisions=default_decisions,
                   source="timeout_default"
               )
               
       except Exception as e:
           # Fallback to safe defaults
           return UserDecisionEvent(
               decisions=self._get_safe_defaults(),
               source="error_fallback"
           )
   ```
   
   ### D. Error Recovery and Monitoring
   ```python
   @step
   async def handle_error_recovery(self, ctx: Context, ev: ErrorRecoveryEvent) -> Union[StopEvent, Any]:
       """Handle errors and implement recovery strategies"""
       self.retry_counts[ev.original_event] = ev.retry_count + 1
       
       if ev.retry_count >= 3:
           # Max retries reached, fail gracefully
           return StopEvent(
               result={
                   "status": "failed",
                   "error": f"Max retries reached for {ev.original_event}",
                   "partial_results": await ctx.get("partial_results", {})
               }
           )
       
       # Implement recovery strategies based on error type
       if ev.error_type == "rate_limit":
           await asyncio.sleep(60)  # Wait before retry
           # Trigger retry of original step
           
       elif ev.error_type == "agent_failure":
           # Reinitialize agents
           await self._reinitialize_agents(ctx)
           
       # Continue workflow with recovery
       return await self._retry_step(ctx, ev.original_event)
   ```

4. **Validate Implementation with Gotcha Checks**
   - **RAG System Validation**:
     - Check embedding model consistency
     - Verify vector database integrity
     - Test rate limit protection
     - Validate transaction completeness
   - **Workflow Validation**:
     - Test infinite loop prevention
     - Verify timeout handling
     - Check agent initialization
     - Test error recovery paths
   - **Configuration Validation**:
     - Check .env file encoding (UTF-8)
     - Verify API key recognition
     - Test model name validity
   - **Output Validation**:
     - Check for JSON corruption
     - Verify content completeness
     - Test large output handling
   - **USE one-search**: `mcp__one-search-mcp__one_search` to find testing patterns if needed

5. **Compliance Verification with Audit Trail**
   - Ensure ALCOA+ principles in generated tests
   - Verify 21 CFR Part 11 compliance
   - Check audit trail completeness
   - Validate GAMP-5 categorization accuracy
   - **USE perplexity**: `mcp__perplexity-mcp__deep_research` for compliance questions

6. **Complete and Document with Monitoring**
   - Ensure all PRP checklist items completed
   - Add comprehensive docstrings
   - Create usage examples with error scenarios
   - Document any deviations from PRP
   - Implement monitoring and alerting
   - Read PRP again to ensure nothing missed

## LlamaIndex Workflow-Specific Patterns with Error Handling

### Event-Driven Architecture with Validation
```python
# Always validate events and handle failures
try:
    ctx.send_event(ContextRequestEvent(query="...", retry_count=0))
    ctx.send_event(SMERequestEvent(domain="...", fallback_enabled=True))
    ctx.send_event(ResearchRequestEvent(topic="...", timeout=300))
except Exception as e:
    # Log error and send recovery event
    ctx.send_event(ErrorRecoveryEvent(error_type="event_dispatch", original_event="parallel_dispatch"))

# Collect parallel results with partial failure handling
results = ctx.collect_events(ev, [ContextResultEvent, SMEResultEvent, ResearchResultEvent])
if results is None:
    # Not all events received - check for partial results
    partial_results = ctx.get_partial_events([ContextResultEvent, SMEResultEvent, ResearchResultEvent])
    if len(partial_results) > 0:
        # Continue with partial results
        results = partial_results
```

### Rate Limit and Cost Management
```python
class WorkflowAPIManager:
    def __init__(self, max_expensive_calls=3):
        self.expensive_call_count = 0
        self.max_expensive_calls = max_expensive_calls
        self.call_history = []
    
    async def check_limits(self, operation_type):
        if operation_type in ["research", "analysis"] and self.expensive_call_count >= self.max_expensive_calls:
            raise RateLimitError(f"Exceeded maximum expensive calls: {self.max_expensive_calls}")
        
        if operation_type in ["research", "analysis"]:
            self.expensive_call_count += 1
```

### Human-in-the-Loop with Timeout
```python
# Based on consultation.py pattern with error handling
try:
    ctx.write_event_to_stream(ConsultationRequiredEvent(
        options=numbered_options,
        prompt="Select options (e.g., 1;3;5):",
        timeout=300
    ))
    response = await asyncio.wait_for(
        ctx.wait_for_event(UserDecisionEvent),
        timeout=300
    )
except asyncio.TimeoutError:
    # Use conservative defaults
    response = UserDecisionEvent(decisions=get_conservative_defaults())
```

### GAMP-5 Driven Logic with Fallbacks
```python
# Categorization determines entire workflow with error handling
try:
    gamp_category = await ctx.get("gamp_category")
    if gamp_category == 5:
        # Most rigorous validation
        await ctx.set("validation_level", "comprehensive")
    elif gamp_category == 4:
        # Configured validation
        await ctx.set("validation_level", "configured")
    else:
        # Default to comprehensive for unknown categories
        await ctx.set("validation_level", "comprehensive")
except Exception:
    # Always default to most rigorous validation
    await ctx.set("validation_level", "comprehensive")
```

## MCP Tool Usage During Implementation

1. **When stuck on workflow patterns**:
   - `mcp__context7__get-library-docs` with specific topics including error handling
   - `mcp__one-search-mcp__one_search` for examples AND debugging solutions

2. **When facing architectural decisions**:
   - `mcp__perplexity-mcp__reason` for best practices AND error prevention strategies
   - Include your specific challenge in the query

3. **For compliance questions**:
   - `mcp__perplexity-mcp__deep_research` on regulatory topics
   - Focus on GAMP-5, 21 CFR Part 11, ALCOA+

4. **For debugging and error resolution**:
   - `mcp__one-search-mcp__one_search` for "llama-index [specific error]"
   - `mcp__perplexity-mcp__reason` for complex debugging scenarios
   - `mcp__context7__get-library-docs` for error handling patterns

## Critical Requirements with Error Prevention

- ✅ GAMP-5 categorization MUST be the first step (with fallback to category 5)
- ✅ ALL agents communicate via events only (with validation)
- ✅ Human consultation for critical decisions (with timeout defaults)
- ✅ Parallel execution where possible (with partial failure handling)
- ✅ Complete audit trail of all actions (with error logging)
- ✅ Compliance validation at every stage (with recovery mechanisms)
- ✅ Rate limit protection for all expensive operations
- ✅ Comprehensive error handling for all known gotchas
- ✅ Monitoring and alerting for system health

## Error Patterns to Handle (COMPREHENSIVE)

### RAG System Errors
- **Rate limit exhaustion** → Use cheaper models, implement batching
- **Transaction failures** → Transactional ingestion with resume capability
- **Embedding cache misses** → Intelligent caching with content hashing
- **Vector DB corruption** → Integrity checks, automatic re-indexing

### Workflow Errors  
- **Infinite loops** → Iteration limits, clear handoff instructions
- **Timeouts** → Configurable timeouts, parallel processing
- **Tool failures** → Robust error handling, fallback implementations
- **Agent communication failures** → Parameter validation, schema conversion

### Environment Errors
- **Encoding issues** → UTF-8 validation, file recreation
- **API key problems** → Configuration validation, clear error messages
- **Dependency conflicts** → Clean installation procedures
- **Model name errors** → Centralized configuration, validation

### Output Errors
- **Large output crashes** → Truncated handlers, safe output functions
- **JSON corruption** → Robust parsing, content extraction
- **Content truncation** → Chunking strategies, validation steps

## Success Verification Checklist

- [ ] All known gotchas are addressed with specific solutions
- [ ] Error recovery paths are implemented for every failure mode
- [ ] Rate limiting and cost controls are in place
- [ ] Human timeout handling works correctly
- [ ] Agent failures don't crash the entire workflow
- [ ] Configuration issues are caught early with clear messages
- [ ] Large outputs are handled safely
- [ ] Compliance requirements are met even in error scenarios
- [ ] Monitoring and alerting provide visibility into system health

Note: This is a production-ready LlamaIndex Workflow implementation that handles real-world failure modes. Every known gotcha must be addressed proactively, not reactively.