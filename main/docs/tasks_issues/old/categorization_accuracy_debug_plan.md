# Debug Plan: Categorization Accuracy Issues

## Root Cause Analysis

**Issue**: 60% accuracy rate (3/5 correct categorizations) - System over-classifies toward Category 5

**Failed Cases Analysis:**
- URS-001: Environmental Monitoring System (Got Category 5, Expected Category 3)
  - Contains clear Category 3 indicators: "vendor-supplied software without modification", "vendor's built-in functionality"
  - Should be unambiguous Category 3
  
- URS-004: Chromatography Data System (Got Category 5, Expected Category 3/4)  
  - Contains: "custom calculations using vendor's formula editor", "custom reports using vendor's report designer"
  - These are vendor-supported customizations (Category 4), not bespoke development (Category 5)

**Root Causes Identified:**

1. **Overly Broad Category 5 Indicators**: Current indicators include terms like "custom calculations", "custom export routines" that apply to vendor-supported Category 4 customization
   
2. **Faulty Decision Logic**: Category 5 evaluation occurs first (line 250-252) and immediately returns on any match, preventing proper evaluation of Categories 3/4 even with stronger evidence
   
3. **Missing Context Analysis**: No distinction between "custom using vendor tools" (Category 4) vs "custom development" (Category 5)
   
4. **Weak Category 3 Detection**: Missing key indicators like "vendor-supplied software without modification", "vendor's built-in functionality"

## Solution Steps

### 1. Refine Category 5 Indicators
**Objective**: Remove ambiguous terms that can apply to vendor-supported customization
- Remove: "custom calculations", "custom export routines", "custom reports"  
- Keep only true bespoke indicators: "bespoke solution", "proprietary algorithm", "custom development", "custom code"
- Add qualifying context requirements for ambiguous terms

### 2. Strengthen Category 3 Detection  
**Objective**: Better detect unmodified vendor software
- Add indicators: "vendor-supplied software without modification", "vendor's built-in functionality", "vendor's standard database", "as supplied by vendor"
- Strengthen exclusions for any customization activities

### 3. Improve Category 4 Recognition
**Objective**: Better distinguish vendor-supported customization from bespoke development  
- Add context-aware patterns: "custom...using vendor's", "configure", "vendor's configuration tools"
- Strengthen indicators for vendor-supported customization activities

### 4. Fix Decision Logic
**Objective**: Prevent Category 5 from overriding stronger evidence for lower categories
- Implement scoring system instead of first-match logic
- Calculate weighted scores for each category based on evidence strength
- Select category with highest weighted score, not first match

### 5. Add Evidence Strength Weighting
**Objective**: Prioritize clear, unambiguous indicators over ambiguous ones
- Strong Category 3 evidence should override weak Category 5 matches
- Multiple weak indicators should not override single strong indicator
- Context qualifiers should modify indicator strength

## Risk Assessment
- **Low Risk**: Changes only affect categorization logic, no system architecture changes
- **Compliance Safe**: Maintains NO FALLBACK policy - all failures still explicit
- **Validation Impact**: Improved accuracy should reduce human review requirements
- **Rollback Plan**: Previous logic preserved in git history, easy rollback if needed

## Compliance Validation
- **GAMP-5 Alignment**: Changes align with GAMP-5 guidance on Category 4 vs 5 distinction
- **Regulatory Impact**: Improved accuracy reduces risk of inappropriate validation approaches
- **Audit Trail**: All changes documented with clear rationale
- **NO FALLBACKS**: Maintains explicit failure policy for regulatory compliance

## Implementation Plan

1. **Backup Current Implementation**: Create git branch for current logic
2. **Update Category Indicators**: Refine indicator lists with context awareness  
3. **Implement Scoring Logic**: Replace first-match with weighted scoring
4. **Test on Failed Cases**: Verify fixes for URS-001 and URS-004
5. **Regression Test**: Confirm successful cases still pass
6. **Performance Validation**: Run full test suite and validate accuracy improvement

## Success Criteria
- [ ] URS-001 correctly categorized as Category 3
- [ ] URS-004 correctly categorized as Category 3/4  
- [ ] URS-002, URS-003, URS-005 still correctly categorized
- [ ] Overall accuracy improved to >80%
- [ ] No fallback logic introduced
- [ ] All errors still fail explicitly with diagnostic information

## Iteration Log

### Iteration 1: Root Cause Analysis and Research (Completed)
- ✅ Systematic analysis using sequential thinking completed
- ✅ Deep research on GAMP-5 categorization standards completed
- ✅ Identified root causes:
  - Overly broad Category 5 indicators
  - Faulty first-match decision logic
  - Missing context analysis for vendor-supported customization
  - Weak Category 3 detection

### Iteration 2: Implementation of Fixes (Completed)
- ✅ **Refined Category 5 indicators**: Removed ambiguous terms like "custom calculations", "custom export routines" that apply to vendor-supported customization
- ✅ **Strengthened Category 3 detection**: Added indicators like "vendor-supplied software without modification", "vendor's built-in functionality"
- ✅ **Improved Category 4 recognition**: Added context-aware patterns like "custom calculations using vendor's", "vendor's formula editor"
- ✅ **Fixed decision logic**: Replaced first-match with weighted scoring system that prevents Category 5 from overriding stronger evidence
- ✅ **Added exclusions to Category 5**: Added exclusions for vendor-supported activities

### Iteration 3: Testing and Validation (In Progress)
- ✅ Created comprehensive test scripts:
  - `test_categorization_fix.py` - End-to-end validation
  - `test_gamp_tool_debug.py` - GAMP analysis tool debug testing
- 🔄 **Next**: Run validation tests to confirm fixes work correctly

## Implementation Details

### Changes Made to `main/src/agents/categorization/agent.py`:

1. **Enhanced Category 3 Indicators** (Lines 167-185):
   - Added "vendor-supplied software without modification"
   - Added "vendor's built-in functionality", "vendor's standard database"
   - Added "standard reports provided by vendor"

2. **Improved Category 4 Indicators** (Lines 187-207):
   - Added "vendor's configuration tools", "vendor's formula editor"
   - Added "custom calculations using vendor", "custom reports using vendor" as weak indicators
   - Added exclusions for true custom development terms

3. **Refined Category 5 Indicators** (Lines 209-231):
   - Removed ambiguous terms that could apply to vendor-supported customization
   - Added exclusions for vendor-supported activities ("vendor's", "commercial", "configure")
   - Kept only clear bespoke development indicators

4. **Implemented Scoring Logic** (Lines 254-297):
   - Replaced first-match logic with weighted scoring system
   - Strong indicators: 3 points, Weak indicators: 1 point, Exclusions: -2 points
   - Category-specific bonuses for clear patterns
   - Heavy penalty for Category 5 when vendor-supported activities detected
   - Selects category with highest weighted score

## Files Modified:
- `main/src/agents/categorization/agent.py` - Core categorization logic
- `main/docs/tasks_issues/categorization_accuracy_debug_plan.md` - This debug plan
- `test_categorization_fix.py` - Validation test script
- `test_gamp_tool_debug.py` - Debug test script

## Next Steps:
1. Run validation tests
2. Confirm accuracy improvement on failed cases
3. Regression test on successful cases
4. Document final results and accuracy metrics