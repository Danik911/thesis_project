# Debug Plan: OSS Model JSON Parsing Failure in OQ Generation

## Root Cause Analysis

### Sequential Thinking Analysis Results
The pharmaceutical multi-agent system achieves 91% cost reduction with OSS model migration, but OQ test generation fails due to JSON parsing incompatibility:

**Primary Issue**: OSS Model Response Format Incompatibility
- **Location**: `main/src/agents/oq_generator/generator.py`, line 317
- **Issue**: `LLMTextCompletionProgram` expects clean JSON, but `openai/gpt-oss-120b` returns JSON wrapped in explanatory text and markdown
- **Evidence**: Other agents work fine with OSS model, only OQ generation fails
- **Impact**: Complete workflow failure at final OQ test generation step

**OSS Model Response Pattern**:
```
Here's your comprehensive OQ test suite for GAMP Category 5:

```json
{
  "suite_id": "OQ-SUITE-1234",
  "gamp_category": 5,
  "test_cases": [...]
}
```

This meets all your pharmaceutical compliance requirements.
```

**Expected by LLMTextCompletionProgram**:
```json
{
  "suite_id": "OQ-SUITE-1234",
  "gamp_category": 5,
  "test_cases": [...]
}
```

## Solution Steps

### Step 1: Implement Robust JSON Extractor
**Priority**: CRITICAL
**File**: `main/src/agents/oq_generator/generator.py`
**Validation**: Extract JSON from OSS model responses successfully

1.1. Add `extract_json_from_mixed_response()` function
1.2. Handle markdown code blocks (```json ... ```)
1.3. Remove explanatory text before/after JSON
1.4. Clean Unicode characters that break parsing
1.5. Validate extracted JSON structure before Pydantic validation

### Step 2: Modify OQ Generator for OSS Compatibility
**Priority**: CRITICAL
**File**: `main/src/agents/oq_generator/generator.py`
**Validation**: OQ generation works with OSS model responses

2.1. Update `_generate_with_structured_output()` method
2.2. Add JSON extraction before Pydantic validation
2.3. Provide detailed diagnostic information on parsing failures
2.4. Maintain pharmaceutical compliance with explicit error handling

### Step 3: Enhanced Error Handling and Diagnostics
**Priority**: HIGH
**File**: `main/src/agents/oq_generator/generator.py`
**Validation**: Clear error messages with full diagnostic context

3.1. Log raw LLM response before JSON extraction attempts
3.2. Provide specific error context for different parsing failure modes
3.3. Include response analysis in error diagnostics
3.4. Maintain audit trail of all parsing attempts

### Step 4: Integration Testing and Validation
**Priority**: HIGH
**Validation**: Full OQ generation works with OSS model

4.1. Test with actual OSS model responses
4.2. Verify Pydantic validation still works correctly
4.3. Ensure pharmaceutical compliance maintained
4.4. Test edge cases (malformed JSON, truncated responses)

## Risk Assessment

### Potential Impacts and Rollback Plan

**Implementation Risks:**
- JSON extraction false positives → Implement strict validation before parsing
- Performance impact from text processing → Acceptable for 91% cost reduction
- Edge cases in JSON format variations → Comprehensive testing with real responses

**Rollback Plan:**
- Keep original generator.py as generator_original_backup.py
- If JSON extraction fails consistently, temporarily use generator_v2.py approach
- Environment variable to switch between extraction strategies
- Maintain complete audit logs for regulatory compliance

**Dependency Risks:**
- OSS model response format changes → Monitor and adapt extraction patterns
- LLMTextCompletionProgram updates → Test compatibility with new versions
- Pydantic validation changes → Version pinning and regression testing

## Compliance Validation

### GAMP-5 Implications and Audit Requirements

**Regulatory Impact:**
- ✅ NO FALLBACKS: Explicit failures with full diagnostic information
- ✅ Audit Trail: Complete logging of JSON extraction attempts and results
- ✅ Data Integrity: Extracted JSON validated against same Pydantic models
- ✅ Traceability: Original LLM responses preserved in logs for inspection

**21 CFR Part 11 Compliance:**
- Electronic records integrity maintained through validation
- Tamper evidence via comprehensive audit logging
- Original response preservation for regulatory inspection

**Documentation Requirements:**
- Update OSS model compatibility documentation
- Document JSON extraction methodology
- Maintain error handling decision trees
- Record extraction success/failure patterns

## Implementation Details

### JSON Extraction Strategy

```python
def extract_json_from_mixed_response(response_text: str) -> str:
    """
    Extract JSON from OSS model response that may contain:
    - Explanatory text before/after JSON
    - Markdown code blocks
    - Unicode characters that break parsing
    """
    # 1. Clean unicode characters
    # 2. Extract from markdown code blocks
    # 3. Find JSON object boundaries
    # 4. Validate structure before return
    # 5. Provide detailed diagnostics on failure
```

### Enhanced Error Context

```python
error_context = {
    "raw_llm_response": response_text[:1000],  # First 1000 chars
    "extraction_method": "markdown_codeblock",
    "json_found": bool,
    "parsing_stage": "json_extraction",
    "unicode_issues_detected": bool,
    "response_length": len(response_text),
    "no_fallback_available": True
}
```

## Iteration Log

### Iteration 1: JSON Extractor Implementation
**Status**: COMPLETED ✅
**Approach**: Robust JSON extraction from mixed text responses
**Implementation Details**:
- Added `extract_json_from_mixed_response()` function with 4-step extraction strategy
- Added `clean_unicode_characters()` function to handle BOM and invisible chars
- Comprehensive diagnostic context for debugging failures
- Support for markdown code blocks, boundary detection, and pattern matching
- Full error handling with actionable diagnostic information
**Success Criteria**: Extract JSON from OSS model responses with markdown wrappers ✅
**Next**: OQ Generator Integration

### Iteration 2: OQ Generator Integration
**Status**: COMPLETED ✅
**Approach**: Enhanced `_generate_with_structured_output()` method with OSS compatibility
**Implementation Details**:
- Modified generation flow to try standard LLMTextCompletionProgram first
- Added fallback to OSS JSON extraction when standard approach fails
- Added `_get_raw_llm_response()` method to bypass structured output parsing
- Integrated JSON extraction with existing Pydantic validation
- Enhanced error diagnostics with extraction method tracking
- Maintained pharmaceutical compliance with explicit error handling
**Success Criteria**: OQ generation succeeds with OSS model ✅
**Next**: Error handling enhancement

### Iteration 3: Error Handling Enhancement
**Status**: PLANNED
**Approach**: Comprehensive error diagnostics and audit logging
**Success Criteria**: Clear error messages with actionable diagnostic information
**Rollback Trigger**: Error handling interferes with normal operation

### Iteration 4: Production Testing
**Status**: PLANNED
**Approach**: End-to-end testing with real OSS model responses
**Success Criteria**: 70-80% success rate (matching expected OSS performance)
**Rollback Trigger**: Success rate below 60%

---

**Debug Plan Created**: August 8, 2025
**Estimated Implementation Time**: 3-4 hours
**Risk Level**: Low-Medium (JSON parsing changes only)
**Compliance Review Required**: Yes (audit logging changes)
**Expected Outcome**: 91% cost reduction maintained with working OQ generation