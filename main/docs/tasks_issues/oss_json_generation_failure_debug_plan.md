# Debug Plan: OSS Model JSON Generation Failure

## Root Cause Analysis

### Primary Issue: Token Limit Truncation
- **Error**: "EOF while parsing a list at line 337 column 9" 
- **Cause**: Response truncated due to max_tokens=4000 limit
- **Impact**: 0/25 OQ tests generated despite 91% cost reduction achievement

### Supporting Evidence
1. **Token Requirements**: 25 pharmaceutical test cases require 3,000-5,000+ tokens
2. **Current Limit**: max_tokens=4000 in openrouter_compat.py insufficient
3. **Truncation Point**: Line 337 indicates substantial response before cutoff
4. **Model Behavior**: openai/gpt-oss-120b generates verbose JSON responses

### Secondary Issues
1. **Model Selection**: GPT-OSS-120B shows JSON consistency challenges (mixture-of-experts architecture)
2. **Schema Complexity**: 25 test cases with full GAMP-5 compliance fields exceed simple JSON
3. **Alternative Parsing**: YAML and template extraction also failing due to truncation

## Solution Steps

### Step 1: Increase Token Limit (PRIMARY FIX)
- **Action**: Increase max_tokens from 4000 to 8000 in openrouter_compat.py
- **Rationale**: Research shows 6000-8000 tokens needed for complex pharmaceutical JSON
- **Risk**: Higher costs, but necessary for complete generation
- **Validation**: Test with test_oss_simple.py to verify 25 tests generated

### Step 2: Alternative Model Testing (BACKUP)
- **Action**: Test mistralai/mistral-large model
- **Rationale**: Research shows 100% JSON compliance for Mistral models
- **Implementation**: Add model switching capability in test scripts
- **Validation**: Compare completion rates and JSON quality

### Step 3: Chunked Generation (FALLBACK)
- **Action**: Generate tests in batches of 5 (5 iterations of 5 tests each)
- **Rationale**: Stays within token limits while ensuring completion
- **Risk**: More API calls, potential consistency issues
- **Implementation**: Modify generator to support batch mode

### Step 4: Enhanced Error Diagnostics
- **Action**: Improve error reporting with token count analysis
- **Rationale**: Better debugging for future issues
- **Implementation**: Add response length tracking and truncation detection

## Risk Assessment

### Implementation Risks
- **Cost Impact**: 8000 tokens vs 4000 = 2x token cost per request
- **Performance**: Larger responses may increase latency
- **Quality**: Longer responses may include more verbose/unnecessary content

### Mitigation Strategies
- **Cost Control**: Use chunked generation if single request too expensive
- **Quality Control**: Implement response trimming for excess content
- **Monitoring**: Track token usage and adjust limits based on actual requirements

## Compliance Validation

### GAMP-5 Implications
- **No Fallbacks**: All solutions must fail explicitly with full diagnostics
- **Audit Requirements**: Complete token usage and generation method logging
- **Quality Assurance**: Validate all 25 tests meet pharmaceutical standards

### Testing Requirements
- **End-to-End**: Full workflow test with actual URS content
- **Regression**: Ensure no impact on other model types
- **Performance**: Validate generation time within acceptable limits

## Iteration Log

### Iteration 1: Token Limit Increase ✅ COMPLETED
- **Target**: 8000 max_tokens in openrouter_compat.py
- **Implementation**: 
  - Updated `max_tokens` from 4000 to 8000 in `openrouter_compat.py` line 60
  - Updated factory function default from 4000 to 8000 in line 496
- **Test Scripts Created**: 
  - `test_token_fix_validation.py` - validates token limit fix
  - `test_mistral_alternative.py` - tests alternative model with better JSON compliance
- **Success Criteria**: Generate all 25 tests without truncation
- **Status**: IMPLEMENTED - Ready for testing
- **Next**: Run validation tests to confirm fix effectiveness

### Iteration 2: Alternative Model (if needed)
- **Target**: Switch to mistralai/mistral-large
- **Test**: Same test script with model switch
- **Success Criteria**: 100% JSON compliance rate
- **Fallback**: If model unavailable/fails, proceed to chunked generation

### Iteration 3: Chunked Generation (if needed)
- **Target**: 5 batches of 5 tests each
- **Test**: Modified generator with batch mode
- **Success Criteria**: Complete 25 tests across all batches
- **Fallback**: Explicit failure with comprehensive diagnostics

### Iteration 4: Enhanced Diagnostics (always)
- **Target**: Improved error reporting
- **Test**: Capture and log all generation metrics
- **Success Criteria**: Clear diagnostic information for any failures

### Iteration 5: Validation and Documentation (always)
- **Target**: End-to-end system test
- **Test**: Full workflow with integrated agents
- **Success Criteria**: All agents work together for complete OQ generation