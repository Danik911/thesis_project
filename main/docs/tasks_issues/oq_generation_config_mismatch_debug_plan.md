# Debug Plan: OQ Generation Configuration Mismatch

## Root Cause Analysis

### Problem Summary
The OQ generation workflow fails with the error: "GAMP Category 5 (Custom applications) requires minimum 25 tests, but only 20 provided. NO fallback values available"

### Root Cause Identified
**Configuration mismatch between two authoritative sources:**

1. **templates.py (lines 49-51)**: GAMP Category 5 configured with:
   - `"min_tests": 15`
   - `"max_tests": 20`

2. **models.py (lines 144)**: GAMP Category 5 configured with:
   - `"min": 25`
   - `"max": 30`

### Failure Flow
1. `generator_v2.py` uses `GAMPCategoryConfig.get_category_config()` from templates.py
2. Requests `max_tests = 20` for Category 5 (line 139 in generator_v2.py)
3. o3 model successfully generates 20 tests (as requested)
4. Pydantic validation in `OQTestSuite.validate_category_test_count()` (models.py) expects minimum 25 tests
5. Validation fails with compliance error - system correctly enforces NO FALLBACKS policy

### Evidence
- ✅ o3 model is working correctly (generates requested 20 tests)
- ✅ Validation logic is working correctly (enforces compliance)
- ❌ Configuration inconsistency between templates.py and models.py

## Solution Steps

### Step 1: Align Configuration Values
Update `templates.py` GAMP Category 5 configuration to match `models.py`:
- Change `"min_tests": 15` → `"min_tests": 25`
- Change `"max_tests": 20` → `"max_tests": 30`

### Step 2: Verify Other Categories
Check and align all GAMP categories between templates.py and models.py:
- Category 1: 3-5 tests (verify alignment)
- Category 3: 5-10 tests (verify alignment)  
- Category 4: 15-20 tests (verify alignment)
- Category 5: 25-30 tests (fix required)

### Step 3: Strengthen O3 Prompt
Update the o3 prompt in `generator_v2.py` to emphasize generating the FULL required count for Category 5:
- Line 348: Ensure prompt clearly states 25+ tests required
- Add emphasis on comprehensive testing for custom applications

### Step 4: Test and Validate
Run the workflow with GAMP Category 5 to ensure:
- o3 model generates 25+ tests
- Pydantic validation passes
- No compliance errors occur

## Risk Assessment

### Low Risk Fix
- Configuration alignment is straightforward
- No breaking changes to core logic
- Maintains pharmaceutical compliance standards
- Follows NO FALLBACKS policy correctly

### Pharmaceutical Compliance Impact
- ✅ Aligns with actual GAMP-5 Category 5 requirements (25-30 tests appropriate for custom applications)
- ✅ Maintains strict validation without fallbacks
- ✅ Preserves audit trail and compliance enforcement

## Implementation Plan

### Files to Modify
1. `main/src/agents/oq_generator/templates.py` - Update Category 5 config
2. `main/src/agents/oq_generator/generator_v2.py` - Review prompt emphasis (if needed)

### Validation Steps
1. Compare all category configurations between templates.py and models.py
2. Update templates.py to match models.py values
3. Test Category 5 workflow end-to-end
4. Verify no regressions in other categories

## Expected Outcome
- GAMP Category 5 workflows generate 25-30 tests successfully
- o3 model receives correct test count requirements
- Pydantic validation passes without compliance errors
- System maintains NO FALLBACKS policy integrity

## Rollback Plan
If issues arise, revert templates.py changes and investigate whether models.py requirements need adjustment instead.