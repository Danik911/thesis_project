# Debug Plan: OQ Generation YAML Integration

## Root Cause Analysis

**Issue**: OQ generator failing with "oq_generation_system_error" and "oq_test_generation_failure" at 100% failure rate.

**Root Cause**: DeepSeek V3 model returns YAML format responses but the `_parse_o3_batch_response` method in `generator_v2.py` only attempts JSON parsing. The existing `yaml_parser.py` module is completely disconnected from the main parsing flow.

**Evidence**:
1. Cross-validation logs show 100% failure rate with generic system errors
2. No Phoenix traces captured (suggests early parsing failure)
3. `yaml_parser.py` exists with comprehensive YAML parsing capabilities but is not imported in `generator_v2.py`
4. `_parse_o3_batch_response` only calls `_parse_json_robustly` - no YAML fallback

## Solution Steps

### Step 1: Integrate YAML Parser Import
- Add import for `yaml_parser` module in `generator_v2.py`
- Ensure proper error handling and logging integration

### Step 2: Modify _parse_o3_batch_response Method
- Add YAML parsing fallback when JSON parsing fails
- Maintain existing JSON-first approach for compatibility
- Preserve NO FALLBACKS policy - fail explicitly if both formats fail
- Add comprehensive diagnostic logging

### Step 3: Update Error Handling
- Enhance error messages to distinguish between JSON vs YAML parsing failures
- Preserve full diagnostic information for regulatory compliance
- Maintain existing `TestGenerationFailure` exception structure

### Step 4: Validation Testing
- Test with known YAML response format
- Verify JSON parsing still works for existing successful cases
- Validate error handling maintains GAMP-5 compliance

## Risk Assessment

**Low Risk Changes**:
- Adding YAML parser import (no side effects)
- Fallback logic preserves existing behavior when JSON works

**Medium Risk Changes**:
- Modifying core parsing logic in `_parse_o3_batch_response`
- Need to ensure no regression in existing JSON parsing

**Mitigation Strategy**:
- Incremental implementation with JSON-first approach
- Comprehensive error logging for both formats
- Rollback plan: revert to JSON-only if integration fails

## Compliance Validation

**GAMP-5 Implications**:
- Enhanced parser maintains deterministic behavior
- NO FALLBACKS policy preserved - explicit failures required
- Full audit trail of parsing attempts and results
- Response format variations properly documented

**ALCOA+ Requirements**:
- Complete diagnostic information preserved
- Parsing method clearly identified in logs
- No data manipulation or artificial confidence scores

## Implementation Code Changes

### File: `main/src/agents/oq_generator/generator_v2.py`

**Location**: Lines 1106-1147 (`_parse_o3_batch_response` method)

**Change Type**: Add YAML fallback after JSON parsing failure

**Specific Changes**:
1. Add import: `from .yaml_parser import extract_yaml_from_response, validate_yaml_data`
2. Modify exception handling to try YAML parsing before raising `TestGenerationFailure`
3. Add diagnostic logging to identify which parsing method succeeded
4. Ensure both parsers maintain the same output format for `OQTestSuite` compatibility

## Iteration Log

### Iteration 1: Analysis Complete ✅
- **Status**: Root cause identified with complete evidence
- **Finding**: yaml_parser.py exists but is not integrated into main parsing flow
- **Next**: Implement YAML integration with fallback logic
- **Risk Level**: Low - well-defined change with clear fallback strategy

### Iteration 2: Implementation Complete ✅
- **Status**: YAML fallback integration implemented in both parsing flows
- **Changes Made**:
  1. Added `from .yaml_parser import extract_yaml_from_response, validate_yaml_data` to generator_v2.py
  2. Modified `_parse_o3_batch_response` exception handling to add YAML fallback
  3. Modified main generation exception handling to add YAML fallback
  4. Enhanced error reporting with dual-parser failure diagnostics
- **Testing**: Created test_yaml_integration.py for validation
- **Risk Level**: Minimal - JSON-first approach maintains backward compatibility

## Success Criteria

1. **Functional**: Cross-validation success rate improves from 0% to >80%
2. **Phoenix Traces**: Successful OQ generation appears in Phoenix monitoring
3. **Format Support**: Both JSON and YAML responses handled correctly
4. **Compliance**: NO FALLBACKS policy maintained with explicit error reporting
5. **Audit Trail**: Clear logging of parsing method used for each response

## Rollback Plan

If integration fails:
1. Remove yaml_parser import
2. Revert `_parse_o3_batch_response` to JSON-only logic
3. Maintain existing error handling behavior
4. Document DeepSeek V3 format incompatibility for model selection decisions