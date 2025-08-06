# Debug Plan: OQ Generation System Failure

## Root Cause Analysis

### Sequential Thinking Analysis Results
The pharmaceutical multi-agent system fails at the OQ test generation step due to three distinct but interconnected issues:

1. **O3 Model Response Size Limitation (PRIMARY)**
   - **Location**: `main/src/agents/oq_generator/generator_v2.py`
   - **Issue**: GAMP Category 5 requires 25-30 tests (max: 30), but o3-2025-04-16 model cannot generate 30 detailed OQ tests in a single response
   - **Evidence**: Error "No JSON found in o3 model response" indicates truncated/incomplete response
   - **Impact**: Complete workflow failure at final step

2. **SME Agent Schema Error (SECONDARY)**
   - **Location**: `main/src/agents/parallel/sme_agent.py`, line 473
   - **Issue**: Code accesses `sme_response.validation_points` but SMEAgentResponse class doesn't define this attribute
   - **Evidence**: AttributeError: 'SMEAgentResponse' object has no attribute 'validation_points'
   - **Impact**: SME agent fails during parallel execution

3. **Workflow Orchestration Bug (TERTIARY)**
   - **Location**: `main/src/core/unified_workflow.py`, lines 974-997
   - **Issue**: Code treats ConsultationRequiredEvent as dictionary when handling OQ generation failures
   - **Evidence**: Incorrect `.get("status")` calls on object instead of dictionary
   - **Impact**: Wrong error handling path, confusing error messages

## Solution Steps

### Step 1: Implement Progressive Generation for O3 Model
**Priority**: CRITICAL
**File**: `main/src/agents/oq_generator/generator_v2.py`
**Validation**: Generate 30 tests successfully in 3 batches of 10

1.1. Add progressive generation method `_generate_with_progressive_o3_model()`
1.2. Update main generation logic to detect when progressive generation is needed
1.3. Implement batch merging logic to combine results into single OQTestSuite
1.4. Add appropriate timeouts and error handling for each batch

### Step 2: Fix SME Agent Response Schema
**Priority**: HIGH
**File**: `main/src/agents/parallel/sme_agent.py`
**Validation**: SME agent executes without AttributeError

2.1. Add missing `validation_points: list[str]` field to SMEAgentResponse class
2.2. Update default factory and field description
2.3. Ensure backward compatibility with existing code

### Step 3: Fix Workflow Orchestration Error Handling
**Priority**: HIGH  
**File**: `main/src/core/unified_workflow.py`
**Validation**: Proper error messages when OQ generation fails

3.1. Add isinstance() check for ConsultationRequiredEvent before treating as dictionary
3.2. Extract error details properly from event object attributes
3.3. Provide clear error messages with diagnostic information

### Step 4: Integration Testing and Validation
**Priority**: MEDIUM
**Validation**: Full end-to-end workflow executes successfully

4.1. Test progressive generation with actual o3 model
4.2. Verify SME agent integration works correctly
4.3. Test error recovery mechanisms
4.4. Validate GAMP-5 compliance maintained

## Risk Assessment

### Potential Impacts and Rollback Plan

**Implementation Risks:**
- API rate limits during progressive generation → Add configurable delays between batches
- Batch consistency issues → Implement test ID coordination across batches  
- Memory usage with large test suites → Stream batches instead of accumulating

**Rollback Plan:**
- Keep original generator_v2.py as generator_v2_backup.py
- If progressive generation fails, temporarily switch CATEGORY_5 to use "gpt-4o" model
- Maintain audit logs of all changes for regulatory compliance

**Dependency Risks:**
- O3 model availability → Fallback to gpt-4o for Category 5
- OpenAI API changes → Version pinning and monitoring
- Pydantic model validation → Comprehensive testing of schema changes

## Compliance Validation

### GAMP-5 Implications and Audit Requirements

**Regulatory Impact:**
- ✅ NO FALLBACKS: All fixes fail explicitly with full diagnostic information
- ✅ Audit Trail: Complete change tracking in version control
- ✅ Data Integrity: Progressive generation maintains test uniqueness and traceability
- ✅ Validation: Each batch validated independently, then merged result validated

**21 CFR Part 11 Compliance:**
- Electronic records integrity maintained across batch generation
- Tamper evidence through comprehensive logging
- Audit trail includes batch-level execution details

**Documentation Requirements:**
- Update model compatibility matrix
- Document progressive generation approach
- Maintain error handling decision tree
- Record API timeout and retry policies

## Iteration Log

### Iteration 1: Progressive Generation Implementation
**Status**: COMPLETED ✅
**Approach**: Implemented core progressive generation logic
**Implementation Details**:
- Added `_generate_with_progressive_o3_model()` method for batch processing
- Modified main generation logic to detect when progressive generation needed (o3 model + >10 tests)
- Added helper methods: `_build_progressive_o3_prompt()`, `_parse_o3_batch_response()`, `_merge_progressive_batches()`
- Included `clean_unicode_characters()` function for robust JSON parsing
- Added proper timeout distribution and rate limit handling
**Next**: Validation testing

### Iteration 2: SME Agent Schema Fix  
**Status**: COMPLETED ✅
**Approach**: Added missing validation_points field to response model
**Implementation Details**:
- Added `validation_points: list[str] = Field(default_factory=list)` to SMEAgentResponse
- Maintained backward compatibility with existing code
- Added proper field description for regulatory compliance
**Next**: Integration testing to verify fix

### Iteration 3: Workflow Orchestration Fix
**Status**: COMPLETED ✅  
**Approach**: Proper ConsultationRequiredEvent handling
**Implementation Details**:
- Added isinstance() check for ConsultationRequiredEvent before dict operations
- Added proper error message extraction from event object attributes
- Added support for OQTestSuiteEvent direct handling
- Maintained backward compatibility with dictionary format
- Clear diagnostic error messages with full context
**Next**: End-to-end workflow testing

### Iteration 4: Full Integration Testing
**Status**: PLANNED
**Approach**: End-to-end testing with real o3 model
**Success Criteria**: 30 OQ tests generated successfully for Category 5
**Rollback Trigger**: System performance degrades or compliance violations

### Iteration 5: Performance Optimization
**Status**: PLANNED
**Approach**: Optimize batch timing and memory usage
**Success Criteria**: Total execution time < 3 minutes for 30 tests
**Rollback Trigger**: API rate limits or timeout issues

---

**Debug Plan Created**: August 6, 2025
**Estimated Implementation Time**: 4-6 hours across 2 days
**Risk Level**: Medium (core system changes)
**Compliance Review Required**: Yes (GAMP-5 validation approach change)