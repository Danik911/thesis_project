# O3 Model Progressive Generation Implementation Plan

## Executive Summary
The pharmaceutical multi-agent system's OQ test generator fails when using the o3-2025-04-16 model for GAMP Category 5 systems due to response size limitations. The o3 model cannot generate 30 detailed OQ tests in a single response. This document provides a comprehensive implementation plan for progressive generation (Option B) to resolve this issue.

## Current Issues Analysis

### 1. Primary Issue: O3 Model Response Size Limitation
**Location**: `main/src/agents/oq_generator/generator_v2.py`
**Evidence**: 
```
"Due to the size of the JSON structure containing 30 fully-detailed Operational Qualification tests, 
the response exceeds the platform's single-message character limit."
```
- O3 model works correctly but has output token limitations
- Cannot generate 30 tests in one response
- Model suggests reducing to ≤10 tests per request

### 2. Workflow Orchestration Bug
**Location**: `main/src/core/unified_workflow.py` lines 974-997
**Issue**: 
- `oq_workflow.run()` returns `ConsultationRequiredEvent` object when OQ generation fails
- Code incorrectly tries to access it as dictionary with `.get("status")`
- Causes RuntimeError: "OQ generation requires consultation: oq_generation_system_error"

### 3. SME Agent Schema Error
**Location**: `main/src/agents/parallel/sme_agent.py`
**Issue**: 
- `SMEAgentResponse` object missing 'validation_points' attribute
- Causes AttributeError during parallel agent execution

## Progressive Generation Solution Design

### Architecture Overview
```
┌─────────────────────────────────────────────┐
│         OQ Test Generator V2                 │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │   Progressive Generation Manager     │    │
│  │                                      │    │
│  │  • Batch Size: 10 tests             │    │
│  │  • Total Target: 30 tests           │    │
│  │  • Iterations: 3                    │    │
│  └─────────────────────────────────────┘    │
│                    │                         │
│         ┌──────────┴──────────┐              │
│         ▼          ▼          ▼              │
│    Batch 1    Batch 2    Batch 3            │
│    (1-10)     (11-20)    (21-30)            │
│         │          │          │              │
│         └──────────┬──────────┘              │
│                    ▼                         │
│         Test Suite Aggregator                │
│                    │                         │
│                    ▼                         │
│         Complete OQTestSuite                 │
│         (30 tests merged)                    │
└─────────────────────────────────────────────┘
```

### Implementation Steps

## Phase 1: Progressive Generation Manager
**File**: `main/src/agents/oq_generator/generator_v2.py`

### 1.1 Add Progressive Generation Method
```python
async def _generate_with_progressive_o3_model(
    self,
    llm: OpenAI,
    gamp_category: GAMPCategory,
    urs_content: str,
    document_name: str,
    total_tests: int,
    context_data: dict[str, Any] = None
) -> OQTestSuite:
    """
    Progressive generation for o3 model to handle response size limitations.
    Generates tests in batches of 10, then merges results.
    """
    batch_size = 10  # O3 model limitation
    num_batches = (total_tests + batch_size - 1) // batch_size
    
    all_test_cases = []
    batch_timeouts = []
    
    self.logger.info(
        f"Starting progressive generation: {total_tests} tests in {num_batches} batches"
    )
    
    for batch_num in range(num_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, total_tests)
        batch_count = batch_end - batch_start
        
        self.logger.info(f"Generating batch {batch_num + 1}/{num_batches}: Tests {batch_start + 1}-{batch_end}")
        
        # Generate batch with context from previous batches
        batch_context = {
            "batch_number": batch_num + 1,
            "total_batches": num_batches,
            "previous_tests": [t.test_id for t in all_test_cases],
            "test_id_start": batch_start + 1,
            "test_id_end": batch_end,
            "original_context": context_data
        }
        
        try:
            # Build batch-specific prompt
            batch_prompt = self._build_progressive_o3_prompt(
                gamp_category=gamp_category,
                urs_content=urs_content,
                document_name=document_name,
                test_count=batch_count,
                batch_context=batch_context
            )
            
            # Execute batch generation with appropriate timeout
            batch_timeout = self.timeout_mapping[gamp_category] // num_batches
            async with asyncio.timeout(batch_timeout):
                response = await llm.acomplete(batch_prompt)
                
                # Parse batch response
                batch_suite = self._parse_o3_batch_response(
                    response.text, 
                    batch_num,
                    batch_start
                )
                
                # Add tests to collection
                all_test_cases.extend(batch_suite.test_cases)
                
                # Brief delay between batches to avoid rate limits
                if batch_num < num_batches - 1:
                    await asyncio.sleep(2)
                    
        except asyncio.TimeoutError:
            raise TestGenerationFailure(
                f"Batch {batch_num + 1} timed out after {batch_timeout}s",
                {"batch": batch_num + 1, "timeout": batch_timeout}
            )
        except Exception as e:
            raise TestGenerationFailure(
                f"Batch {batch_num + 1} generation failed: {e}",
                {"batch": batch_num + 1, "error": str(e)}
            )
    
    # Merge all batches into final test suite
    return self._merge_progressive_batches(
        all_test_cases,
        gamp_category,
        document_name,
        context_data
    )
```

### 1.2 Update Main Generation Logic
```python
async def generate_oq_test_suite(
    self,
    gamp_category: GAMPCategory,
    urs_content: str,
    document_name: str,
    context_data: dict[str, Any] = None,
    config: OQGenerationConfig | None = None
) -> OQTestSuite:
    """Enhanced generation with progressive support for o3."""
    
    # Get model and configuration
    model_name = self.model_mapping.get(gamp_category, "o1-mini")
    
    # Check if progressive generation needed
    if model_name.startswith("o3") and test_count > 10:
        self.logger.info(
            f"Using progressive generation for o3 model with {test_count} tests"
        )
        return await self._generate_with_progressive_o3_model(
            llm=llm,
            gamp_category=gamp_category,
            urs_content=urs_content,
            document_name=document_name,
            total_tests=test_count,
            context_data=context_data
        )
    
    # Standard generation for other models or small test counts
    # ... existing logic ...
```

## Phase 2: Workflow Orchestration Fix
**File**: `main/src/core/unified_workflow.py`

### 2.1 Fix ConsultationRequiredEvent Handling
```python
@step
async def generate_oq_tests(
    self,
    ctx: Context,
    ev: AgentResultsEvent
) -> OQTestSuiteEvent:
    """Generate OQ test suite with proper error handling."""
    
    try:
        self.logger.info("Running OQ test generation workflow...")
        oq_result = await oq_workflow.run()
        
        # CRITICAL FIX: Check result type first
        if isinstance(oq_result, ConsultationRequiredEvent):
            # Handle consultation event properly
            self.logger.warning(
                f"OQ generation returned consultation request: {oq_result.consultation_type}"
            )
            
            # Extract error details
            error_context = oq_result.context
            error_type = error_context.get('consultation_type', 'unknown')
            
            # Re-raise with proper context
            raise RuntimeError(
                f"OQ generation requires consultation: {error_type}",
                {"consultation_event": oq_result, "context": error_context}
            )
        
        # Handle OQTestSuiteEvent directly
        if isinstance(oq_result, OQTestSuiteEvent):
            self.logger.info(
                f"[OQ] Generated {oq_result.test_suite.total_test_count} OQ tests successfully"
            )
            return oq_result
        
        # Handle dictionary result (legacy format)
        if hasattr(oq_result, "result"):
            oq_data = oq_result.result
        else:
            oq_data = oq_result
            
        # Process dictionary result
        if isinstance(oq_data, dict):
            if oq_data.get("status") == "completed_successfully":
                oq_event = oq_data.get("full_event")
                if oq_event and isinstance(oq_event, OQTestSuiteEvent):
                    return oq_event
            
            # Handle consultation in dictionary format
            consultation = oq_data.get("consultation", {})
            raise RuntimeError(
                f"OQ generation failed: {consultation.get('consultation_type', 'unknown')}"
            )
        
        # Unexpected result type
        raise ValueError(
            f"Unexpected OQ workflow result type: {type(oq_result)}"
        )
        
    except Exception as e:
        self.logger.error(f"OQ generation failed: {e}")
        raise
```

## Phase 3: SME Agent Fix
**File**: `main/src/agents/parallel/sme_agent.py`

### 3.1 Add Missing Attribute
```python
class SMEAgentResponse(BaseModel):
    """SME Agent response model with all required fields."""
    
    # Existing fields
    compliance_assessment: dict[str, Any]
    risk_analysis: dict[str, Any]
    recommendations: list[str]
    validation_guidance: dict[str, Any]
    domain_insights: dict[str, Any]
    regulatory_considerations: list[str]
    confidence_score: float
    processing_metadata: dict[str, Any]
    
    # CRITICAL FIX: Add missing field
    validation_points: list[str] = Field(
        default_factory=list,
        description="Key validation points identified by SME analysis"
    )
```

## Phase 4: Testing Strategy

### 4.1 Unit Tests
```python
# test_progressive_generation.py
async def test_progressive_o3_generation():
    """Test progressive generation splits correctly."""
    generator = OQTestGeneratorV2()
    
    # Mock o3 model responses
    mock_llm = Mock()
    mock_llm.acomplete.side_effect = [
        Mock(text='{"test_cases": [...10 tests...]}'),
        Mock(text='{"test_cases": [...10 tests...]}'),
        Mock(text='{"test_cases": [...10 tests...]}')
    ]
    
    result = await generator._generate_with_progressive_o3_model(
        llm=mock_llm,
        gamp_category=GAMPCategory.CATEGORY_5,
        urs_content="test content",
        document_name="test.md",
        total_tests=30
    )
    
    assert len(result.test_cases) == 30
    assert mock_llm.acomplete.call_count == 3
```

### 4.2 Integration Test
```bash
# Full workflow test with o3 model
cd main
uv run python main.py tests/test_data/gamp5_test_data/testing_data.md --verbose
```

## Implementation Timeline

### Day 1: Core Implementation (4-6 hours)
1. Implement progressive generation manager in generator_v2.py
2. Add batch merging logic
3. Create progressive prompt builder
4. Test with mock responses

### Day 2: Integration (3-4 hours)
1. Fix workflow orchestration in unified_workflow.py
2. Fix SME agent schema
3. Integration testing with actual o3 model
4. Performance optimization

### Day 3: Validation (2-3 hours)
1. Full end-to-end testing
2. Monitor trace analysis
3. Documentation update
4. Deploy to production

## Risk Mitigation

### 1. API Rate Limits
- Add configurable delays between batches
- Implement exponential backoff on rate limit errors
- Monitor API usage metrics

### 2. Batch Consistency
- Pass previous test IDs to ensure uniqueness
- Maintain context between batches
- Validate no duplicate test IDs

### 3. Timeout Management
- Split timeout proportionally across batches
- Add batch-level retry logic
- Implement partial result recovery

## Success Metrics

1. **Functional Success**
   - ✅ Generate 30 OQ tests for Category 5 using o3 model
   - ✅ All tests have unique IDs (OQ-001 through OQ-030)
   - ✅ Complete workflow executes without errors

2. **Performance Metrics**
   - Total execution time < 3 minutes for 30 tests
   - Each batch completes within allocated timeout
   - No API rate limit violations

3. **Quality Metrics**
   - All generated tests pass Pydantic validation
   - Test coverage across all required categories
   - GAMP-5 compliance maintained

## Fallback Strategy

If progressive generation fails:
1. **Immediate**: Switch to gpt-4o model for Category 5
2. **Short-term**: Reduce test count to 10 for o3 model
3. **Long-term**: Investigate o3 model fine-tuning for larger outputs

## Conclusion

This implementation plan addresses the o3 model's response size limitations through progressive generation while maintaining pharmaceutical compliance and test quality. The solution is robust, scalable, and maintains the system's NO FALLBACK principle by failing explicitly when issues occur.

## Appendix: Key File Locations

- `main/src/agents/oq_generator/generator_v2.py` - Progressive generation implementation
- `main/src/core/unified_workflow.py` - Workflow orchestration fix
- `main/src/agents/parallel/sme_agent.py` - SME response schema fix
- `main/logs/traces/` - Trace files for monitoring
- `main/tests/test_data/gamp5_test_data/testing_data.md` - Test document

## Contact & Support

For implementation support or questions:
- Review trace files in `main/logs/traces/`
- Check Phoenix UI at http://localhost:6006
- Monitor spans in `all_spans_*.jsonl` files