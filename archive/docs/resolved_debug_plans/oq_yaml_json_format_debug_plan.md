# Debug Plan: OQ Generator YAML vs JSON Format Issue

## Root Cause Analysis

**CONFIRMED ROOT CAUSE**: The OQ generator system is configured to generate YAML format but the downstream system expects JSON format.

### Evidence:
1. **Templates Configuration** (`main/src/agents/oq_generator/templates.py`):
   - Line 78: `BASE_SYSTEM_PROMPT = """Generate {test_count} complete OQ test cases in YAML format`
   - Line 236: `Return complete YAML document with proper formatting."`
   - The prompts explicitly request YAML format from DeepSeek V3

2. **Generator Implementation** (`main/src/agents/oq_generator/generator.py`):
   - Lines 506-508: Uses `extract_yaml_from_response()` and `validate_yaml_data()`
   - Line 483: Comment states "Generate test suite using YAML as primary format for OSS model compatibility"

3. **Cross-Validation Errors** (from logs):
   - All documents failing with "Error in step 'generate_oq_tests': OQ generation failed: oq_test_generation_failure"
   - 0% success rate across all test runs
   - Error type: "oq_test_generation_failure" or "oq_generation_system_error"

4. **System Expectation Mismatch**:
   - The workflow system expects JSON format for processing
   - YAML parsing creates format incompatibilities downstream

## Solution Steps

### Step 1: Convert Prompt Templates to JSON Format
**File**: `main/src/agents/oq_generator/templates.py`
- Change BASE_SYSTEM_PROMPT from "YAML format" to "JSON format" 
- Update example structure from YAML to JSON syntax
- Modify instructions to specify JSON output requirements for DeepSeek V3

### Step 2: Update Generator to Use JSON Parsing
**File**: `main/src/agents/oq_generator/generator.py`
- Replace YAML parsing logic with JSON parsing in `_generate_with_structured_output()`
- Use the existing `extract_json_from_mixed_response()` function (lines 64-213)
- Remove YAML dependency and switch to JSON-first approach

### Step 3: Verify DeepSeek V3 JSON Compatibility  
**File**: `main/src/agents/oq_generator/generator.py`
- Test that DeepSeek V3 can produce valid JSON with the new prompts
- Validate JSON extraction works with DeepSeek V3's response format
- Ensure no formatting issues with the model's output

### Step 4: Update Workflow Configuration
**File**: `main/src/agents/oq_generator/workflow.py`
- Verify workflow uses updated generator with JSON parsing
- Ensure no YAML references remain in comments or documentation

### Step 5: Integration Testing
- Run single document test to verify JSON generation works
- Test with Category 5 documents (25-30 tests expected)
- Validate full cross-validation pipeline

## Risk Assessment

**LOW RISK**: This is a format conversion issue, not a logic change
- Existing JSON parsing functions are already available
- DeepSeek V3 model supports JSON output
- No pharmaceutical compliance impact (same data, different format)
- Change is isolated to OQ generator module

## Rollback Plan
If issues occur:
1. Revert template changes to YAML format
2. Revert generator changes to YAML parsing  
3. Original system state restored

## Compliance Validation

**GAMP-5 Impact**: NONE - Format change only, same test content generated
**ALCOA+ Impact**: NONE - No change to data integrity or audit trail
**Regulatory Impact**: NONE - Same validation tests, just JSON instead of YAML

## Implementation Priority
**HIGH** - Blocking all OQ test generation currently

## Verification Criteria
- [ ] Single document test generates valid JSON
- [ ] 25-30 tests generated for Category 5 documents
- [ ] Cross-validation success rate > 80%
- [ ] No format errors in generated test suites
- [ ] Phoenix monitoring shows successful trace capture