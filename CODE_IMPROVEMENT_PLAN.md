# Code Improvement Plan - Pharmaceutical Test Generation System

**Date**: 2025-10-31
**Status**: Analysis Complete - Implementation Pending
**Methodology**: Ultrathink Deep Analysis

---

## Executive Summary

This plan identifies opportunities to improve code quality, reduce redundancy, and enhance maintainability across the pharmaceutical test generation system. The analysis covers **75,299 lines of Python code** across the main application.

**Key Metrics:**
- **Backup files to delete**: 5 files (~2,652 lines)
- **Code duplication**: ~200 lines in main.py alone
- **Large files requiring refactoring**: 8 files (>1,000 lines each)
- **Potential line reduction**: ~15-20% through consolidation
- **Estimated improvement time**: 2-3 days for Phase 1

---

## Table of Contents

1. [Critical Issues - Immediate Action Required](#1-critical-issues---immediate-action-required)
2. [Code Duplication & Consolidation Opportunities](#2-code-duplication--consolidation-opportunities)
3. [File Structure & Organization](#3-file-structure--organization)
4. [Large File Refactoring](#4-large-file-refactoring)
5. [Utility Module Extraction](#5-utility-module-extraction)
6. [Implementation Phases](#6-implementation-phases)
7. [Risk Assessment](#7-risk-assessment)
8. [Success Metrics](#8-success-metrics)

---

## 1. Critical Issues - Immediate Action Required

### 1.1 Backup Files Cleanup (HIGH PRIORITY)

**Issue**: Multiple backup and deprecated files increase codebase complexity and confusion.

**Files to Delete:**
```bash
# Location: main/src/core/
- unified_workflow_backup.py (884 lines)
- unified_workflow_original.py (884 lines)

# Location: main/src/monitoring/
- phoenix_enhanced_broken.py
- phoenix_enhanced_old.py

# Location: main/src/agents/parallel/
- context_provider.py.backup

# Total: ~2,652 lines of dead code
```

**Action Steps:**
1. Verify no active imports reference these files
2. Confirm with git history that current versions supersede these backups
3. Delete files and commit with clear message
4. Update any documentation referencing these files

**Risk**: Low - These are clearly backup files
**Impact**: Immediate 3.5% reduction in codebase size
**Estimated Time**: 30 minutes

---

## 2. Code Duplication & Consolidation Opportunities

### 2.1 Main Entry Point Duplication (main.py)

**File**: `main/main.py` (763 lines)

**Issue**: Duplicate result display logic between `run_with_event_logging()` and `run_without_logging()`

**Duplication Analysis:**

```python
# Lines 308-376 (run_with_event_logging)
# DUPLICATE BLOCK 1 (~68 lines)
if result:
    if workflow_type == "categorization":
        summary = result.get("summary", {})
        safe_print("\n[SUCCESS] Categorization Complete!")
        safe_print(f"  - Category: {summary.get('category', 'Unknown')}")
        # ... ~60 more similar lines
    else:
        # Unified workflow results - ~60 lines
        summary = result.get("summary", {})
        categorization = result.get("categorization", {})
        # ... display logic

# Lines 422-464 (run_without_logging)
# DUPLICATE BLOCK 2 (nearly identical ~68 lines)
if result:
    if args.categorization_only:
        summary = result.get("summary", {})
        safe_print("\n[SUCCESS] Categorization Complete!")
        # ... identical display logic
```

**Proposed Solution:**

Create a new module: `main/src/cli/result_display.py`

```python
def display_workflow_results(
    result: dict[str, Any],
    workflow_type: str,
    event_handler: EventStreamHandler | None = None
) -> None:
    """
    Display workflow results in a consistent format.

    Args:
        result: Workflow result dictionary
        workflow_type: Type of workflow ("categorization" or "unified")
        event_handler: Optional event handler for statistics
    """
    if not result:
        safe_print("\n[ERROR] Workflow failed to produce results")
        return

    if workflow_type == "categorization":
        _display_categorization_results(result)
    else:
        _display_unified_results(result)

    # Display event statistics if available
    if event_handler:
        _display_event_statistics(event_handler)
```

**Files to Modify:**
- `main/main.py`: Remove duplicate blocks, import `display_workflow_results()`
- **New file**: `main/src/cli/result_display.py`

**Impact**: Reduces main.py by ~120 lines (16% reduction)
**Risk**: Low - Pure extraction with no logic changes
**Estimated Time**: 2 hours

---

### 2.2 Consultation Interface Extraction

**File**: `main/main.py`

**Issue**: Human consultation CLI functions (3 functions, ~160 lines) clutter the main entry point.

**Functions to Extract:**
1. `run_consultation_interface()` - Lines 471-517
2. `list_active_consultations()` - Lines 519-532
3. `view_consultation_details()` - Lines 534-574
4. `respond_to_consultation()` - Lines 576-656

**Proposed Solution:**

Create: `main/src/cli/consultation_interface.py`

```python
"""Human Consultation Command-Line Interface."""

from src.core.human_consultation import HumanConsultationManager
from src.shared.output_manager import safe_print

class ConsultationCLI:
    """Command-line interface for human consultation system."""

    def __init__(self, manager: HumanConsultationManager):
        self.manager = manager

    async def run(self) -> None:
        """Run interactive consultation interface."""
        # Move run_consultation_interface logic here

    async def list_active(self) -> None:
        """List active consultations."""
        # Move list_active_consultations logic here

    async def view_details(self) -> None:
        """View consultation details."""
        # Move view_consultation_details logic here

    async def respond(self) -> None:
        """Respond to consultation."""
        # Move respond_to_consultation logic here
```

**Impact**: Reduces main.py by ~160 lines (21% reduction)
**Risk**: Low - Clear module boundary
**Estimated Time**: 2 hours

---

### 2.3 Context Management Utilities Extraction

**File**: `main/src/core/unified_workflow.py` (2,348 lines)

**Issue**: Helper functions for context management are embedded in workflow file.

**Functions to Extract (Lines 158-409):**
1. `safe_context_get()` - Lines 158-208 (~50 lines)
2. `safe_context_set()` - Lines 211-347 (~136 lines)
3. `validate_workflow_state()` - Lines 350-381 (~31 lines)
4. `log_state_operation()` - Lines 384-409 (~25 lines)

**Proposed Solution:**

Create: `main/src/core/context_utils.py`

```python
"""Workflow Context Management Utilities.

Provides GAMP-5 compliant context storage with comprehensive audit logging.
NO FALLBACKS - All failures are explicit with full diagnostic information.
"""

from llama_index.core.workflow import Context
from src.core.audit_trail import get_audit_trail
import logging

logger = logging.getLogger(__name__)


async def safe_context_get(ctx: Context, key: str, default=None):
    """
    Safe context retrieval with persistent storage and explicit error handling.

    Args:
        ctx: Workflow context
        key: Context key to retrieve
        default: Default value if key not found or error occurs

    Returns:
        Retrieved value or default

    Raises:
        RuntimeError: If critical state retrieval fails with no fallback allowed
    """
    # Move implementation here


async def safe_context_set(ctx: Context, key: str, value):
    """Safe context storage with audit logging."""
    # Move implementation here


async def validate_workflow_state(ctx: Context, required_keys: list[str]) -> bool:
    """Validate all required workflow state keys exist."""
    # Move implementation here


async def log_state_operation(operation: str, key: str, success: bool, error: str = None):
    """Log state operations for GAMP-5 audit trail."""
    # Move implementation here
```

**Impact**: Reduces unified_workflow.py by ~242 lines (10% reduction)
**Risk**: Low - Pure utility extraction
**Estimated Time**: 2 hours

---

### 2.4 Progress Display Utilities Extraction

**File**: `main/src/core/unified_workflow.py`

**Issue**: Progress display function embedded in workflow (Lines 93-154)

**Function to Extract:**
- `show_progress_during_wait()` (~61 lines)
- `flush_output()` (~3 lines)

**Proposed Solution:**

Create: `main/src/shared/progress_utils.py`

```python
"""Progress Display Utilities for Long-Running Operations."""

import asyncio
import sys
import time
from typing import Awaitable, TypeVar

T = TypeVar('T')


def flush_output():
    """Ensure terminal output is displayed immediately."""
    sys.stdout.flush()
    sys.stderr.flush()


async def show_progress_during_wait(
    coro: Awaitable[T],
    timeout: int,
    operation_name: str = "Operation",
    agent_type: str = "agent"
) -> T:
    """
    Execute coroutine with progress indicators.

    Enhanced with faster updates and immediate flush for better UX
    during human consultation workflows.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name of operation for display
        agent_type: Type of agent for logging

    Returns:
        Result of the coroutine
    """
    # Move implementation here
```

**Impact**: Reduces unified_workflow.py by ~64 lines
**Risk**: Low - Pure utility extraction
**Estimated Time**: 1 hour

---

## 3. File Structure & Organization

### 3.1 Create CLI Module Package

**Current Issue**: CLI-related code scattered in main.py

**Proposed Structure:**

```
main/src/cli/
├── __init__.py
├── result_display.py     # Result display formatting
├── consultation_interface.py  # Human consultation CLI
└── argument_parser.py    # CLI argument parsing (optional)
```

**Benefits:**
- Clearer separation of concerns
- Easier testing of CLI components
- Reusable display logic
- Better organization

**Estimated Time**: 1 hour (directory creation + init file)

---

### 3.2 Consolidate Test Files

**Issue**: Test/debug files scattered in project root

**Files in Root Directory:**
```
main/
├── test_workflow_validation.py
├── test_single_urs_real.py
├── test_workflow_debug.py
├── test_openrouter_debug.py
├── test_callback_fix.py
├── focused_oss_test.py
├── minimal_api_debug.py
├── debug_validation_mode.py
├── direct_fix_test.py
└── run_cross_validation.py
```

**Proposed Action:**

Move to organized structure:
```
main/tests/
├── debug/              # Already exists
│   ├── debug_categorization_loop.py  # Already there
│   ├── test_workflow_debug.py       # MOVE HERE
│   ├── test_openrouter_debug.py     # MOVE HERE
│   ├── debug_validation_mode.py     # MOVE HERE
│   └── minimal_api_debug.py         # MOVE HERE
├── integration/
│   ├── test_workflow_validation.py  # MOVE HERE
│   ├── test_single_urs_real.py     # MOVE HERE
│   └── focused_oss_test.py         # MOVE HERE
└── scripts/
    └── run_cross_validation.py     # MOVE HERE
```

**Impact**: Cleaner project root, better test organization
**Risk**: Low - Tests are standalone
**Estimated Time**: 30 minutes

---

## 4. Large File Refactoring

### 4.1 Unified Workflow Decomposition (PRIORITY)

**File**: `main/src/core/unified_workflow.py` (2,348 lines)

**Current Structure:**
- 1 massive class with 18+ methods
- Helper functions mixed with workflow logic
- Hard to navigate and test

**Proposed Decomposition:**

#### Phase 1: Extract Helper Modules

```
main/src/core/
├── unified_workflow.py          # Main workflow (reduce to ~1,400 lines)
├── context_utils.py             # NEW - Context management (~250 lines)
├── workflow_helpers.py          # NEW - Workflow utilities (~200 lines)
└── consultation_workflows.py    # NEW - Consultation logic (~400 lines)
```

**Extracted Components:**

1. **context_utils.py** (~250 lines):
   - `safe_context_get()`
   - `safe_context_set()`
   - `validate_workflow_state()`
   - `log_state_operation()`

2. **workflow_helpers.py** (~200 lines):
   - `_create_planning_event_from_categorization()`
   - `_build_consultation_prompt()`
   - `_check_user_access()`
   - Event creation utilities

3. **consultation_workflows.py** (~400 lines):
   - `check_consultation_required()`
   - `handle_consultation()`
   - `handle_consultation_bypassed()`
   - Consultation-specific logic

**Remaining in unified_workflow.py** (~1,400 lines):
- Main workflow class
- Core workflow steps:
  - `start_unified_workflow()`
  - `categorize_document()`
  - `run_planning_workflow()`
  - `execute_agent_request()`
  - `collect_agent_results()`
  - `generate_oq_tests()`
  - `complete_workflow()`

**Impact**: 40% reduction in main file size, much better organization
**Risk**: Medium - Requires careful import management
**Estimated Time**: 1 day

---

### 4.2 Large Agent Files (OPTIONAL - Phase 2)

**Files over 1,500 lines:**
1. `categorization/agent.py` (1,764 lines)
2. `context_provider.py` (1,677 lines)
3. `sme_agent.py` (1,553 lines)
4. `research_agent.py` (1,395 lines)
5. `generator_v2.py` (1,404 lines)

**Recommendation**:
- **Don't refactor immediately** - These are agent implementations
- Each agent is a cohesive unit (single responsibility)
- Consider refactoring if adding significant new features
- Priority: LOW (functional as-is)

**If refactoring needed:**
- Extract prompt templates to separate files
- Extract utility functions to agent-specific helpers
- Consider builder pattern for complex agent initialization

---

## 5. Utility Module Extraction

### 5.1 Shared Utilities Consolidation

**Current State**: Utilities spread across files

**Proposed Additions to `main/src/shared/`:**

```
main/src/shared/
├── __init__.py           # Already exists
├── config.py             # Already exists
├── utils.py              # Already exists
├── event_logging.py      # Already exists
├── progress_utils.py     # NEW - Progress display
└── output_manager.py     # Already exists
```

**New Utility Modules:**

1. **progress_utils.py**:
   - `flush_output()`
   - `show_progress_during_wait()`
   - Other progress-related utilities

---

### 5.2 Result Display Utilities

**Create**: `main/src/cli/result_display.py`

**Purpose**: Centralize all result formatting and display logic

**Contents**:
- `display_workflow_results()` - Main display function
- `_display_categorization_results()` - Categorization display
- `_display_unified_results()` - Unified workflow display
- `_display_event_statistics()` - Event logging stats
- `_display_compliance_statistics()` - Compliance stats

---

## 6. Implementation Phases

### Phase 1: Immediate Cleanup (1-2 days)

**Priority**: HIGH
**Risk**: LOW
**Impact**: HIGH

1. **Delete Backup Files** (30 min)
   - unified_workflow_backup.py
   - unified_workflow_original.py
   - phoenix_enhanced_broken.py
   - phoenix_enhanced_old.py
   - context_provider.py.backup

2. **Extract Result Display Logic** (2 hours)
   - Create `src/cli/result_display.py`
   - Refactor main.py to use it
   - Test both event logging modes

3. **Extract Consultation Interface** (2 hours)
   - Create `src/cli/consultation_interface.py`
   - Refactor main.py consultation commands
   - Test CLI functionality

4. **Organize Test Files** (30 min)
   - Move test files from root to appropriate directories
   - Update any import paths
   - Verify tests still run

**Expected Outcome**:
- main.py reduced from 763 → ~450 lines (41% reduction)
- Cleaner project structure
- Better testability

---

### Phase 2: Context & Progress Utilities (1 day)

**Priority**: MEDIUM
**Risk**: LOW
**Impact**: MEDIUM

1. **Extract Context Utilities** (2 hours)
   - Create `src/core/context_utils.py`
   - Move context management functions
   - Update unified_workflow.py imports

2. **Extract Progress Utilities** (1 hour)
   - Create `src/shared/progress_utils.py`
   - Move progress display functions
   - Update unified_workflow.py imports

3. **Testing & Validation** (2 hours)
   - Test workflow execution
   - Verify context management works
   - Ensure progress display unchanged

**Expected Outcome**:
- unified_workflow.py reduced from 2,348 → ~2,042 lines (13% reduction)
- Reusable utility modules
- Better code organization

---

### Phase 3: Workflow Decomposition (1-2 days)

**Priority**: MEDIUM
**Risk**: MEDIUM
**Impact**: HIGH

1. **Extract Workflow Helpers** (3 hours)
   - Create `src/core/workflow_helpers.py`
   - Move helper methods
   - Update imports

2. **Extract Consultation Workflows** (4 hours)
   - Create `src/core/consultation_workflows.py`
   - Move consultation logic
   - Ensure consultation still works

3. **Comprehensive Testing** (3 hours)
   - Full workflow execution tests
   - Edge case testing
   - Consultation flow testing

**Expected Outcome**:
- unified_workflow.py reduced to ~1,400 lines (40% total reduction)
- Modular, maintainable code
- Easier to understand and test

---

### Phase 4: Optional Enhancements (Future)

**Priority**: LOW
**Risk**: VARIABLE
**Impact**: MEDIUM

1. **Agent Refactoring** (if needed)
   - Extract prompt templates
   - Create agent builders
   - Consolidate common patterns

2. **Additional Utilities**
   - Enhanced error handling
   - Logging improvements
   - Performance optimizations

---

## 7. Risk Assessment

### Low Risk Changes (Safe to implement immediately)

✅ **Backup File Deletion**
- No active dependencies
- Clear redundancy
- Git history preserved

✅ **Result Display Extraction**
- Pure formatting logic
- No business logic changes
- Easy to test

✅ **Test File Organization**
- No code changes
- Path updates only
- Easy to verify

---

### Medium Risk Changes (Requires careful testing)

⚠️ **Context Utilities Extraction**
- Core workflow dependency
- State management critical for GAMP-5 compliance
- **Mitigation**: Comprehensive testing, verify audit trail integrity

⚠️ **Workflow Decomposition**
- Large-scale refactoring
- Multiple file dependencies
- **Mitigation**: Phased approach, extensive testing, backup before changes

---

### High Risk Changes (Defer or avoid)

🔴 **Agent Refactoring**
- Complex business logic
- Working implementations
- **Recommendation**: Only if adding new features

---

## 8. Success Metrics

### Quantitative Metrics

**Before Implementation:**
- Total Lines: 75,299
- main.py: 763 lines
- unified_workflow.py: 2,348 lines
- Backup files: 5 files (~2,652 lines)
- Utility modules: 4 modules

**After Phase 1:**
- Total Lines: ~72,000 (3,000 line reduction)
- main.py: ~450 lines (41% reduction)
- Dead code removed: 2,652 lines
- New CLI modules: 3 modules

**After Phase 3:**
- Total Lines: ~71,500 (5% reduction overall)
- main.py: ~450 lines (41% reduction)
- unified_workflow.py: ~1,400 lines (40% reduction)
- Utility modules: 7 modules (3 new)
- Code reusability: +30%

---

### Qualitative Metrics

**Code Quality:**
- ✅ Reduced duplication
- ✅ Better separation of concerns
- ✅ Improved testability
- ✅ Clearer module boundaries

**Maintainability:**
- ✅ Easier navigation
- ✅ Faster onboarding for new developers
- ✅ Simplified debugging
- ✅ Better documentation opportunities

**Regulatory Compliance:**
- ✅ Maintained GAMP-5 compliance
- ✅ Preserved audit trail integrity
- ✅ No fallback logic introduced
- ✅ Explicit error handling preserved

---

## 9. Files Modified Summary

### Phase 1: Immediate Cleanup

**Files to Delete (5):**
```
main/src/core/unified_workflow_backup.py
main/src/core/unified_workflow_original.py
main/src/monitoring/phoenix_enhanced_broken.py
main/src/monitoring/phoenix_enhanced_old.py
main/src/agents/parallel/context_provider.py.backup
```

**Files to Create (3):**
```
main/src/cli/__init__.py
main/src/cli/result_display.py
main/src/cli/consultation_interface.py
```

**Files to Modify (1):**
```
main/main.py (reduce from 763 → ~450 lines)
```

**Files to Move (10):**
```
# Move from main/ to main/tests/debug/
test_workflow_debug.py
test_openrouter_debug.py
debug_validation_mode.py
minimal_api_debug.py

# Move from main/ to main/tests/integration/
test_workflow_validation.py
test_single_urs_real.py
focused_oss_test.py
test_callback_fix.py
direct_fix_test.py

# Move from main/ to main/tests/scripts/
run_cross_validation.py
```

---

### Phase 2: Utilities Extraction

**Files to Create (2):**
```
main/src/core/context_utils.py
main/src/shared/progress_utils.py
```

**Files to Modify (1):**
```
main/src/core/unified_workflow.py (reduce from 2,348 → ~2,042 lines)
```

---

### Phase 3: Workflow Decomposition

**Files to Create (2):**
```
main/src/core/workflow_helpers.py
main/src/core/consultation_workflows.py
```

**Files to Modify (1):**
```
main/src/core/unified_workflow.py (reduce from ~2,042 → ~1,400 lines)
```

---

## 10. Testing Strategy

### Phase 1 Testing

**Unit Tests:**
- Test result display formatting
- Test consultation interface commands
- Verify all test files run from new locations

**Integration Tests:**
- Run full workflow with event logging enabled
- Run full workflow without event logging
- Test consultation interface end-to-end

**Validation:**
- Compare output before/after refactoring
- Ensure no functional changes
- Verify GAMP-5 compliance maintained

---

### Phase 2 Testing

**Unit Tests:**
- Test context get/set operations
- Test state validation
- Test progress display

**Integration Tests:**
- Full workflow execution
- Context persistence across workflow steps
- Progress display during long operations

**Validation:**
- Audit trail integrity
- State management correctness
- No regression in functionality

---

### Phase 3 Testing

**Comprehensive Testing:**
- All workflow paths (categorization, planning, generation)
- Consultation triggers and handling
- Error recovery scenarios
- Parallel agent coordination

**Regression Testing:**
- Run existing test suite
- Verify all agents function correctly
- Ensure compliance validation works

---

## 11. Rollback Plan

### For Each Phase:

1. **Before Changes:**
   - Create git branch: `refactor/phase-{N}-{description}`
   - Tag current state: `pre-refactor-phase-{N}`
   - Document baseline metrics

2. **During Changes:**
   - Commit frequently with clear messages
   - Run tests after each major change
   - Document any issues encountered

3. **If Issues Found:**
   - Stop implementation
   - Revert to last working commit
   - Analyze root cause
   - Adjust plan if needed

4. **Rollback Command:**
   ```bash
   git checkout pre-refactor-phase-{N}
   git checkout -b refactor/phase-{N}-retry
   ```

---

## 12. Next Steps

### Recommended Implementation Order:

1. **Week 1: Phase 1 (Immediate Cleanup)**
   - Day 1: Delete backups, extract result display
   - Day 2: Extract consultation interface, organize tests
   - Day 3: Testing and validation

2. **Week 2: Phase 2 (Utilities)**
   - Day 1: Extract context utilities
   - Day 2: Extract progress utilities
   - Day 3: Testing and validation

3. **Week 3: Phase 3 (Workflow Decomposition)**
   - Day 1-2: Extract workflow helpers and consultation workflows
   - Day 3: Comprehensive testing

4. **Week 4: Documentation & Review**
   - Update documentation
   - Code review
   - Performance analysis

---

## 13. Conclusion

This plan provides a **systematic, low-risk approach** to improving code quality while maintaining GAMP-5 compliance and system functionality. The phased implementation allows for:

✅ **Incremental progress** with frequent validation
✅ **Easy rollback** if issues arise
✅ **Maintained compliance** throughout refactoring
✅ **Improved maintainability** for future development

**Estimated Total Time**: 5-6 days
**Estimated Line Reduction**: ~5,000 lines (6.6%)
**Risk Level**: LOW to MEDIUM (with proper testing)
**Business Value**: HIGH (improved maintainability, easier onboarding)

---

## Appendix A: File Dependency Map

```
main.py
├── src.core.categorization_workflow (GAMPCategorizationWorkflow)
├── src.core.unified_workflow (UnifiedTestGenerationWorkflow)
├── src.core.events (HumanResponseEvent)
├── src.core.human_consultation (HumanConsultationManager)
├── src.shared (config, event_logging)
├── src.monitoring.phoenix_config (setup_phoenix)
└── src.shared.output_manager (safe_print, TruncatedStreamHandler)

unified_workflow.py
├── src.core.categorization_workflow (GAMPCategorizationWorkflow)
├── src.agents.oq_generator.workflow (OQGenerationWorkflow)
├── src.compliance.* (Part 11 systems)
├── src.config.llm_config (LLMConfig)
├── src.core.events (all event types)
└── src.monitoring.phoenix_config (setup_phoenix)

categorization_workflow.py
├── src.agents.categorization (create_gamp_categorization_agent)
├── src.core.events (GAMPCategorizationEvent, etc.)
└── src.monitoring.phoenix_config (enhance_workflow_span_with_compliance)
```

---

## Appendix B: Code Complexity Metrics

**Current Top 10 Most Complex Files:**

| Rank | File | Lines | Functions/Classes | Complexity |
|------|------|-------|-------------------|------------|
| 1 | unified_workflow.py | 2,348 | 1 class, 18+ methods | Very High |
| 2 | categorization/agent.py | 1,764 | Multiple classes | High |
| 3 | context_provider.py | 1,677 | 1 main class | High |
| 4 | sme_agent.py | 1,553 | 1 main class | High |
| 5 | generator_v2.py | 1,404 | Multiple functions | High |
| 6 | research_agent.py | 1,395 | 1 main class | High |
| 7 | cfr_part11_verifier.py | 1,321 | Multiple classes | Medium |
| 8 | remediation_planner.py | 1,285 | Multiple classes | Medium |
| 9 | compliance_workflow.py | 1,097 | 1 workflow class | Medium |
| 10 | alcoa_scorer.py | 1,067 | 1 main class | Medium |

**Target After Refactoring:**

| File | Current | Target | Reduction |
|------|---------|--------|-----------|
| main.py | 763 | ~450 | 41% |
| unified_workflow.py | 2,348 | ~1,400 | 40% |
| **Dead code** | 2,652 | 0 | 100% |

---

**END OF PLAN**
