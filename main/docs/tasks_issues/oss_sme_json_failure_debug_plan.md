# Debug Plan: OSS Model SME JSON Generation Failure

## Root Cause Analysis

Based on systematic analysis using sequential thinking methodology:

### Primary Issue: OSS Model JSON Generation Failure
**Error**: `SME Agent error: SME analysis failed: CRITICAL: Recommendations generation LLM call failed.`
**Specific**: `CRITICAL: LLM recommendations generation failed to return valid JSON.`

### Root Causes Identified:

1. **Token Limitation**: Current max_tokens=2000 is insufficient for complex pharmaceutical validation JSON responses
2. **OSS Model Behavior**: `openai/gpt-oss-120b` has different response patterns compared to OpenAI models
3. **JSON Formatting**: OSS models struggle with consistent structured output format
4. **Complex Prompts**: Pharmaceutical validation prompts are highly complex and technical

### Technical Analysis:
- ✅ OpenRouter compatibility wrapper working (LLM calls are being made)
- ✅ JSON extraction logic is robust (works with OpenAI models)
- ❌ OSS model returning malformed/incomplete JSON responses
- ❌ Token limits causing response truncation

## Solution Steps

### Step 1: Increase Token Limits for OSS Model
**Implementation**: 
- Increase max_tokens from 2000 to 4000 for OpenRouter/OSS models
- Keep OpenAI at 2000 to maintain cost efficiency
- Update both LLMConfig and OpenRouterCompat wrapper

### Step 2: Enhance JSON Prompting for OSS Models
**Implementation**:
- Add OSS-specific prompting strategies
- Include explicit JSON format examples
- Add response format instructions
- Implement retry logic with simplified prompts

### Step 3: Add Comprehensive Debug Logging
**Implementation**:
- Log actual LLM responses before JSON parsing
- Add response length and format diagnostics
- Track specific parsing failure points
- Enable model-specific debugging

### Step 4: Implement OSS Model-Specific Handling
**Implementation**:
- Detect OSS model usage in SME agent
- Use simplified prompts for OSS models
- Add multiple parsing attempts with degradation
- Maintain NO FALLBACKS policy with explicit failures

## Risk Assessment
- **Low Risk**: Token limit increase (just configuration)  
- **Medium Risk**: Prompting changes may affect response quality
- **Low Risk**: Debug logging doesn't affect functionality
- **Medium Risk**: OSS-specific handling adds complexity

## Compliance Validation
- ✅ Maintains NO FALLBACKS policy (explicit failures only)
- ✅ Preserves pharmaceutical audit requirements
- ✅ Enhanced debugging improves regulatory traceability
- ✅ Token limit increase supports more comprehensive responses

## Implementation Plan

### Files to Modify:
1. `main/src/config/llm_config.py` - Increase OSS model token limits
2. `main/src/llms/openrouter_compat.py` - Update max_tokens default
3. `main/src/agents/parallel/sme_agent.py` - Add OSS model handling
4. Create comprehensive test script for validation

### Success Criteria:
- ✅ SME agent generates valid JSON with OSS model
- ✅ OQ generation workflow completes end-to-end
- ✅ No fallback logic implemented (explicit failures only)
- ✅ Pharmaceutical compliance maintained throughout

## Iteration Log

### Iteration 1: Root Cause Analysis ✅ 
- ✅ Identified token limitation as primary blocker
- ✅ Confirmed OSS model JSON formatting issues
- ✅ Analyzed SME agent failure points
- ✅ Created systematic solution approach

### Iteration 2: Token Limits & Configuration ✅
- ✅ **Increased Token Limits**: Updated max_tokens from 2000 to 4000 for OSS models
  - `main/src/config/llm_config.py`: Updated OpenRouter configuration
  - `main/src/llms/openrouter_compat.py`: Updated default and factory function
- ✅ **Preserved OpenAI Efficiency**: Kept OpenAI at 2000 tokens for cost control
- ✅ **Configuration Tested**: LLMConfig validation updated

### Iteration 3: Enhanced SME Agent OSS Handling ✅
- ✅ **OSS Model Detection**: Added `_detect_oss_model()` method to identify OSS models
- ✅ **Enhanced Prompting**: Added `_enhance_prompt_for_oss()` with explicit JSON format instructions
- ✅ **Comprehensive Debug Logging**: Added `_log_llm_response_debug()` for detailed response analysis
- ✅ **Updated Recommendation Generation**: Enhanced `_generate_recommendations()` with OSS prompting
- ✅ **Updated Compliance Assessment**: Enhanced `_assess_compliance()` with OSS prompting

### Iteration 4: Testing Infrastructure ✅
- ✅ **Test Script Created**: `main/test_oss_sme_fix.py` for comprehensive validation
  - Environment configuration validation
  - Basic LLM functionality testing
  - SME agent creation and OSS detection
  - Simple SME request processing
  - Optional workflow integration testing

### Files Modified:
1. ✅ `main/src/config/llm_config.py` - Increased OSS token limits to 4000
2. ✅ `main/src/llms/openrouter_compat.py` - Updated defaults to 4000 tokens
3. ✅ `main/src/agents/parallel/sme_agent.py` - Added OSS model handling, enhanced prompting, debug logging
4. ✅ `main/test_oss_sme_fix.py` - Comprehensive test suite created
5. ✅ `main/docs/tasks_issues/oss_sme_json_failure_debug_plan.md` - This debug plan

### Key Improvements Implemented:
- **4000 Token Limit**: Supports complex pharmaceutical JSON responses
- **OSS-Specific Prompting**: Explicit JSON format instructions for OSS models
- **Enhanced Debug Logging**: Detailed response analysis and format diagnostics
- **Model Detection**: Automatic OSS model detection and handling
- **NO FALLBACKS**: All improvements maintain pharmaceutical compliance requirements

### Next Steps:
- 🔄 **Execute Test Script**: Run `python test_oss_sme_fix.py` to validate fixes
- 🔄 **Integration Testing**: Test full workflow with OSS model
- 🔄 **Performance Validation**: Verify OQ generation completes successfully