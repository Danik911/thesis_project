# Debug Plan: Cross-Validation Framework Execution Issues

## Root Cause Analysis

**Problem**: Task 17 cross-validation framework has NEVER been successfully executed due to multiple critical execution blockers.

**Issues Identified**:
1. **pdfplumber dependency missing**: Research and SME agents fail with ImportError
2. **Component initialization errors**: Runtime failures despite correct code signatures  
3. **No execution evidence**: Framework never run to completion, no results generated
4. **Agent failures**: Silent failures preventing workflow progression

**Sequential Analysis Results**:
- Code review shows components have correct constructor signatures
- Required paths exist (`datasets/cross_validation/`, `datasets/urs_corpus/`)  
- pdfplumber listed in pyproject.toml but may not be installed in current environment
- Agents fail silently without proper error handling

## Solution Steps  

### Step 1: Dependency Verification and Installation
**Objective**: Fix pdfplumber dependency that prevents Research and SME agents from executing

**Actions**:
1. Test if pdfplumber is installed in current environment
2. Install if missing using UV package manager  
3. Verify agents can import required dependencies

**Expected Outcome**: pdfplumber imports successfully, agents can execute

### Step 2: Dry Run Component Testing  
**Objective**: Validate component initialization without full execution

**Actions**:
1. Run `python run_cross_validation.py --dry-run` to test setup
2. Identify actual constructor signature mismatches
3. Fix any parameter discrepancies

**Expected Outcome**: All components initialize successfully in dry-run mode

### Step 3: Single Document Processing Test
**Objective**: Execute one document through complete workflow  

**Actions**:
1. Create minimal test script for single document processing
2. Process one URS document through full pipeline
3. Verify results generation and persistence

**Expected Outcome**: One document processed successfully with results saved

### Step 4: Single Fold Completion
**Objective**: Complete one full cross-validation fold

**Actions**:
1. Execute one fold with multiple documents
2. Generate fold-level metrics
3. Verify statistical analysis components

**Expected Outcome**: One fold completed with metrics and analysis

### Step 5: Full Framework Integration
**Objective**: Complete multi-fold cross-validation experiment

**Actions**:
1. Execute full 5-fold cross-validation
2. Generate comprehensive statistical analysis
3. Validate results persistence and reporting

**Expected Outcome**: Complete cross-validation results with statistical confidence intervals

## Risk Assessment

- **Low Risk**: Dependency installation and dry-run testing
- **Medium Risk**: Agent execution fixes (may require graceful dependency handling)
- **High Risk**: Full framework execution (complex multi-agent coordination)

## Rollback Plan
If fixes fail after 5 iterations:
1. Document exact failure points with full stack traces
2. Recommend architectural simplification 
3. Suggest component-by-component mock-based testing

## Compliance Validation

**GAMP-5 Requirements**: 
- NO FALLBACK logic allowed - all failures must be explicit
- Full audit trail maintenance in all components
- Statistical analysis integrity preserved
- Error handling with complete diagnostic information

## Iteration Log

### Iteration 1: Dependency Resolution ✅ COMPLETED
**Status**: Fixed
**Actions**: Fixed pdfplumber import handling in regulatory_data_sources.py
**Changes Made**:
- Added conditional import for pdfplumber with explicit error handling
- Modified `_extract_pdf_content` to fail explicitly if pdfplumber missing
- NO FALLBACKS - clear error message with installation instructions
**Files Modified**: `main/src/agents/parallel/regulatory_data_sources.py`
**Success Criteria**: Agents import without ModuleNotFoundError ✅

### Iteration 2: Component Initialization  
**Status**: Ready to Test
**Actions**: Run dry-run, verify constructor signatures work correctly
**Test Commands**:
- `python check_pdfplumber.py` - Check pdfplumber installation status
- `python test_pdfplumber_fix.py` - Validate fix works
- `python run_cross_validation.py --dry-run` - Test actual dry-run
**Success Criteria**: All components initialize successfully

### Iteration 3: Single Document Test
**Status**: Pending
**Actions**: Process one document end-to-end
**Success Criteria**: Document results persisted to disk

### Iteration 4: Fold Completion
**Status**: Pending  
**Actions**: Complete one full fold
**Success Criteria**: Fold metrics generated and saved

### Iteration 5: Full Integration
**Status**: Pending
**Actions**: Multi-fold cross-validation
**Success Criteria**: Statistical analysis and comprehensive results

## Success Criteria Checklist
- [x] pdfplumber dependency issue resolved (explicit error handling implemented)
- [x] Research and SME agents import without ModuleNotFoundError  
- [ ] Dry run completes without component initialization failures
- [ ] At least one document processes completely
- [ ] Fold-level results generated and persisted
- [ ] Statistical confidence intervals calculated
- [ ] Complete experiment results saved to `main/output/cross_validation/`

## Implementation Timeline
- **Iterations 1-2**: Environment fixes (45 minutes max)
- **Iterations 3-4**: Single document and fold testing (60 minutes max)  
- **Iteration 5**: Full integration (90 minutes max)
- **Total Debug Time**: 3.25 hours maximum

## Escalation Criteria
After 5 iterations, if framework cannot complete one fold:
1. Architectural review required
2. Component mocking approach recommended
3. Incremental testing strategy needed