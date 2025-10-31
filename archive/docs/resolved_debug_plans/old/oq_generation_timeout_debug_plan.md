# Debug Plan: OQ Generation Timeout Issue

## Root Cause Analysis

### Sequential Thinking Analysis Results

**Primary Root Cause: Model Configuration Mismatch**
- Environment file specifies: `LLM_MODEL=gpt-4.1-mini-2025-04-14`
- Code hard-codes: `model="gpt-4o-mini"` in `unified_workflow.py` line 275
- OpenAI client rejects requests due to invalid model name, triggering immediate retries

**Secondary Root Cause: Massive Prompt Size**
- URS content: 154 lines of detailed pharmaceutical requirements
- Prompt template: Base system + category-specific + parameters + requirements
- Total estimated prompt size: >12,000 tokens (even with 8000 char truncation)
- Category 5 requirements: 25-30 complex test cases requested
- Exceeds practical limits for reliable generation

**Third Root Cause: Complex Output Schema**
- LLMTextCompletionProgram generates nested OQTestSuite Pydantic models
- Each test case has multiple fields: steps, criteria, traceability, compliance
- For Category 5: 25-30 test cases × complex schema = massive expected output
- Combined input+output size overwhelms model capabilities

**Fourth Root Cause: Timeout Configuration Chain**
- Workflow timeout: 600s (line 964 in unified_workflow.py)
- Generation timeout: 480s (80% of workflow timeout)
- OpenAI client timeout: Not properly configured
- Request immediately fails before reaching any timeout

## Solution Steps

### 1. Fix Model Configuration (HIGH PRIORITY)
**Problem**: Hard-coded model name doesn't match environment
**Fix**: Update `unified_workflow.py` to use environment variables

**Code Change Required**:
```python
# In unified_workflow.py line 274-277, replace:
self.llm = llm or OpenAI(
    model="gpt-4o-mini",  # ❌ Hard-coded
    temperature=0.1
)

# With:
import os
self.llm = llm or OpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),  # ✅ Environment-aware
    temperature=0.1,
    request_timeout=int(os.getenv("OPENAI_TIMEOUT", "600"))
)
```

### 2. Reduce Prompt Size (HIGH PRIORITY)
**Problem**: Prompt exceeds practical token limits
**Fix**: Implement aggressive content truncation and simplification

**Code Changes Required**:
```python
# In templates.py line 227, reduce URS truncation:
{urs_content[:3000]}  # Reduced from 8000 to 3000

# Simplify prompt templates by removing verbose sections
# Focus on essential requirements only
```

### 3. Optimize Output Schema (MEDIUM PRIORITY)
**Problem**: Requesting too many complex test cases at once
**Fix**: Implement progressive generation strategy

**Code Changes Required**:
```python
# In templates.py lines 49-51, adjust Category 5 limits:
GAMPCategory.CATEGORY_5: {
    "min_tests": 15,  # Reduced from 25
    "max_tests": 20,  # Reduced from 30
    # ... rest unchanged
}
```

### 4. Configure Proper Timeouts (LOW PRIORITY)
**Problem**: Timeout configurations not properly aligned
**Fix**: Ensure consistent timeout handling

## Risk Assessment

**High Risk - System Cannot Function**
- No OQ test generation possible with current configuration
- Pharmaceutical compliance workflow completely blocked
- User cannot proceed with any Category 5 testing

**Medium Risk - Performance Impact**
- Large prompts cause API rate limiting
- Expensive token usage if generation succeeds
- Potential for incomplete test coverage

**Low Risk - User Experience**
- Confusing error messages
- Long wait times before failure
- No clear remediation path

## Compliance Validation

**GAMP-5 Implications**:
- System cannot generate required OQ tests for Category 5 validation
- Audit trail incomplete due to generation failures
- Regulatory compliance documentation cannot be produced

**ALCOA+ Impact**:
- Complete (C): Test generation incomplete
- Available (A): No test outputs available for review

## Iteration Log

### Iteration 1: Model Configuration Fix
- **Target**: Fix environment variable usage
- **Expected**: Eliminate immediate API rejections
- **Test**: Run workflow and verify OpenAI requests succeed
- **Rollback**: Revert to hard-coded model if environment issues

### Iteration 2: Prompt Size Reduction
- **Target**: Reduce prompt to manageable size
- **Expected**: Successful API calls without immediate timeouts
- **Test**: Monitor request/response sizes in logs
- **Rollback**: Increase limits if content quality suffers

### Iteration 3: Test Count Optimization
- **Target**: Generate smaller but complete test suites
- **Expected**: Successful OQ generation for Category 5
- **Test**: Verify JSON output files are created
- **Rollback**: Adjust test counts based on success rate

### Iteration 4: Timeout Alignment
- **Target**: Consistent timeout handling across components
- **Expected**: Proper error messages when legitimate timeouts occur
- **Test**: Artificial timeout scenarios
- **Rollback**: Previous timeout values if stability issues

## Next Steps

1. **IMMEDIATE**: Apply model configuration fix
2. **URGENT**: Implement prompt size reduction
3. **IMPORTANT**: Test with simplified Category 5 requirements
4. **MONITOR**: Verify end-to-end workflow completion
5. **VALIDATE**: Ensure generated test suites meet quality standards

## Success Criteria

- [ ] OQ generation completes without timeout for Category 5
- [ ] JSON test suite files are generated in output/test_suites/
- [ ] Test suites contain minimum required test count (15+ for Category 5)
- [ ] Pharmaceutical compliance metadata is properly included
- [ ] Workflow completes within 10 minutes total time
- [ ] No fallback logic violations detected