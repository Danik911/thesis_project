# SME Agent Timeout & Workflow Orchestration Debug Plan

## ISSUE SUMMARY
- SME Agent consistently times out after 120 seconds 
- Workflow orchestration has StartEvent attribute access issues
- Generated tests are templates rather than detailed content
- API keys are now configured but timeouts still occurring

## ROOT CAUSE ANALYSIS

### 1. Timeout Configuration Hierarchy
Current timeout settings (from timeout_config.py):
- OpenRouter API: 300 seconds (5 minutes)
- SME Agent: 360 seconds (6 minutes)  
- OQ Generator: 480 seconds (8 minutes)
- Unified Workflow: 1800 seconds (30 minutes)

### 2. StartEvent Compatibility
Already patched in unified_workflow.py lines 27-37 with monkey patching.

### 3. Potential Issues Identified

#### HTTP Client Level Timeouts
The OpenRouter compatibility layer may have lower-level HTTP timeouts that override agent timeouts.

#### LLM Request Timeout Chain
```
HTTP Client (unknown) → OpenRouter API (300s) → SME Agent (360s) → Workflow (1800s)
```

If any layer in the chain has a lower timeout, it will cause premature failures.

## COMPREHENSIVE FIXES

### Fix 1: Increase and Validate All Timeout Levels

#### File: `main/src/config/timeout_config.py`
Add timeout validation and increase minimums:

```python
# Enhanced default timeouts for robust operation
DEFAULT_TIMEOUTS = {
    "openrouter_api": 420,      # Increased from 300s to 7 minutes
    "sme_agent": 480,           # Increased from 360s to 8 minutes  
    "oq_generator": 600,        # Increased from 480s to 10 minutes
    "context_provider": 240,    # Increased from 180s to 4 minutes
    "research_agent": 300,      # Increased from 240s to 5 minutes
    "categorization": 180,      # Increased from 120s to 3 minutes
    "unified_workflow": 2400,   # Increased from 1800s to 40 minutes
}
```

#### File: `main/src/llms/openrouter_compat.py`
Ensure HTTP client respects timeout:

```python
# In _make_openrouter_request method
response = requests.post(
    self.api_base + "/chat/completions",
    headers=headers,
    json=payload,
    timeout=api_timeout  # Explicit HTTP client timeout
)
```

### Fix 2: Enhanced Timeout Error Handling

#### File: `main/src/agents/parallel/sme_agent.py`
Add timeout debugging in process_request:

```python
except TimeoutError:
    processing_time = (datetime.now(UTC) - start_time).total_seconds()
    timeout_hierarchy = {
        "api_timeout": TimeoutConfig.get_timeout("openrouter_api"),
        "sme_timeout": TimeoutConfig.get_timeout("sme_agent"),
        "request_timeout": request_data.timeout_seconds,
        "actual_duration": processing_time
    }
    
    error_msg = (
        f"SME analysis timeout after {processing_time:.1f}s. "
        f"Timeout hierarchy: {timeout_hierarchy}. "
        f"Check if lower-level timeouts are causing premature failure."
    )
    
    self.logger.error(error_msg)
    
    # Add diagnostic span attributes
    if current_span and current_span.is_recording():
        current_span.set_attribute("timeout.hierarchy", str(timeout_hierarchy))
        current_span.set_attribute("timeout.failure_level", "sme_agent")
        current_span.set_status(Status(StatusCode.ERROR, error_msg))
```

### Fix 3: Test Generation Quality Enhancement

#### File: `main/src/agents/oq_generator/generator.py`
Add explicit content validation:

```python
def validate_test_content_quality(self, test_cases: List[Dict]) -> None:
    """
    Validate that generated tests contain real content, not templates.
    
    Raises:
        RuntimeError: If tests appear to be templates rather than real content
    """
    template_indicators = [
        "[insert", "{{", "}}", "TBD", "TODO", "placeholder",
        "example", "template", "sample_value", "your_value"
    ]
    
    issues = []
    for i, test_case in enumerate(test_cases):
        # Check test description
        description = test_case.get("description", "").lower()
        for indicator in template_indicators:
            if indicator in description:
                issues.append(f"Test {i+1} description contains template indicator: '{indicator}'")
        
        # Check test procedure
        procedure = test_case.get("test_procedure", [])
        if isinstance(procedure, list):
            for j, step in enumerate(procedure):
                if isinstance(step, str):
                    for indicator in template_indicators:
                        if indicator in step.lower():
                            issues.append(f"Test {i+1} step {j+1} contains template: '{indicator}'")
    
    if issues:
        raise RuntimeError(
            f"Generated tests contain template content instead of real pharmaceutical tests:\n" +
            "\n".join(issues[:10]) +  # Show first 10 issues
            f"\n... ({len(issues)} total issues found)" if len(issues) > 10 else ""
        )
```

### Fix 4: Workflow Orchestration Robustness

#### File: `main/src/core/unified_workflow.py`
Enhanced StartEvent handling:

```python
@step
async def start_workflow(self, ctx: Context, ev: StartEvent) -> DocumentProcessedEvent:
    """
    Start the workflow with enhanced error handling and timeout management.
    """
    self.current_step = "document_processing"
    self.start_time = datetime.now()
    
    # Enhanced timeout and state management
    try:
        # Safe access to StartEvent attributes with debugging
        document_path = getattr(ev, 'document_path', None)
        
        # Validate timeout configuration before proceeding
        timeout_validation = TimeoutConfig.validate_timeouts()
        if not timeout_validation["valid"]:
            self.logger.error("Invalid timeout configuration detected:")
            for issue in timeout_validation["issues"]:
                self.logger.error(f"  - {issue}")
            raise RuntimeError(
                f"Timeout configuration validation failed: {timeout_validation['issues']}"
            )
        
        # Log timeout hierarchy for debugging
        timeouts = TimeoutConfig.get_all_timeouts()
        self.logger.info("Active timeout configuration:")
        for service, timeout_val in timeouts.items():
            self.logger.info(f"  {service}: {timeout_val}s")
        
        # Continue with document processing...
```

### Fix 5: Environment Variable Override Support

Create or update `.env` file with explicit timeout overrides:

```bash
# Pharmaceutical workflow timeouts (in seconds)
OPENROUTER_API_TIMEOUT=420      # 7 minutes for API calls
SME_AGENT_TIMEOUT=480           # 8 minutes for SME analysis  
OQ_GENERATOR_TIMEOUT=600        # 10 minutes for test generation
UNIFIED_WORKFLOW_TIMEOUT=2400   # 40 minutes total workflow

# API Configuration
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
LLM_PROVIDER=openrouter
```

## VALIDATION TESTING

### Test 1: Timeout Hierarchy Validation
```python
def test_timeout_hierarchy():
    """Validate that timeouts are properly ordered"""
    timeouts = TimeoutConfig.get_all_timeouts()
    
    assert timeouts["openrouter_api"] < timeouts["sme_agent"]
    assert timeouts["sme_agent"] < timeouts["oq_generator"] 
    assert timeouts["oq_generator"] < timeouts["unified_workflow"]
    
    print("✅ Timeout hierarchy is correct")
```

### Test 2: SME Agent Timeout Test
```python
async def test_sme_agent_timeout():
    """Test SME agent with known long-running request"""
    from src.agents.parallel.sme_agent import create_sme_agent
    
    agent = create_sme_agent(verbose=True)
    
    request = AgentRequestEvent(
        request_id=str(uuid4()),
        agent_type="sme_agent", 
        request_data={
            "specialty": "pharmaceutical_validation",
            "test_focus": "operational_qualification",
            "compliance_level": "gamp_5",
            "timeout_seconds": TimeoutConfig.get_timeout("sme_agent")
        }
    )
    
    start_time = time.time()
    result = await agent.process_request(request)
    duration = time.time() - start_time
    
    print(f"SME agent completed in {duration:.1f}s")
    print(f"Success: {result.success}")
    
    if not result.success:
        print(f"Error: {result.error_message}")
```

## IMPLEMENTATION CHECKLIST

- [ ] Update timeout configuration values
- [ ] Add timeout validation to workflow startup
- [ ] Enhance SME agent timeout error reporting
- [ ] Add test content quality validation
- [ ] Create environment variable documentation
- [ ] Test timeout hierarchy validation
- [ ] Run end-to-end workflow test with extended timeouts
- [ ] Monitor Phoenix traces for timeout bottlenecks

## ESCALATION PATH

If timeouts still occur after these fixes:

1. **Check Network/API Issues**: OpenRouter API may have server-side delays
2. **Model Performance**: Switch to faster model (e.g., qwen-2.5-72b instead of deepseek)
3. **Simplify Prompts**: Reduce complexity to decrease processing time
4. **Async Optimization**: Implement request batching or streaming responses

## SUCCESS CRITERIA

- [ ] SME agent completes analysis within 8 minutes without timeout
- [ ] Generated tests contain detailed pharmaceutical content (not templates)
- [ ] Workflow orchestration completes without StartEvent errors
- [ ] Phoenix traces show proper timeout hierarchy
- [ ] End-to-end test generates 23-33 detailed OQ tests successfully

## MONITORING

After implementation, monitor:
- SME agent completion rates vs timeout rates
- Average processing times across timeout hierarchy  
- Quality scores of generated test content
- Phoenix trace data for bottleneck identification