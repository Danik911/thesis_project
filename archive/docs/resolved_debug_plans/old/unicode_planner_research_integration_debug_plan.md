# Debug Plan: Unicode Encoding, Planner Workflow Configuration, and Research Agent Integration Issues

## Root Cause Analysis

### Issue 1: Unicode Encoding Error (CRITICAL)
**Root Cause**: Duplicate `setup_unicode_support()` functions in main.py (lines 31 and 108) with incompatible console encoding on Windows systems.

**Evidence**:
- Two duplicate function definitions create confusion and potential conflicts
- Windows console defaults to cp1252 encoding, cannot handle Unicode emoji characters (🔭, 🧑‍⚕️, etc.)
- Error: `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f52d'`
- Prevents normal system startup

**Impact**: SHOWSTOPPER - System cannot start normally on Windows

### Issue 2: Planner Workflow Configuration Error (HIGH)
**Root Cause**: PlannerAgentWorkflow expects GAMPCategorizationEvent but unified_workflow.py calls `planner_workflow.run()` without parameters.

**Evidence**:
- Line 259 in unified_workflow.py: `planning_result = await planner_workflow.run()` 
- PlannerAgentWorkflow.start_planning step expects GAMPCategorizationEvent
- LlamaIndex workflow.run() emits StartEvent, but no step accepts StartEvent
- Error: "At least one Event of type StartEvent must be received by any step"

**Impact**: HIGH - Prevents complete workflow execution, blocks planner integration

### Issue 3: Research Agent Not Integrated (MEDIUM)
**Root Cause**: Research Agent implementation complete but not connected to active workflow execution path.

**Evidence**:
- Research Agent fully implemented with FDA API integration
- Parallel coordination requests not being generated in planner workflow
- No agent coordination results in workflow execution traces
- Research Agent not included in agent factory or workflow routing

**Impact**: MEDIUM - Missing key functionality, regulatory research capabilities unused

## Solution Steps

### Step 1: Fix Unicode Encoding Issues (URGENT - 1 hour)

1. **Remove Duplicate Function Definition**
   - Remove first `setup_unicode_support()` function (lines 31-70)
   - Keep enhanced version (lines 108-163) with better error handling
   - Verify no other references to duplicate function

2. **Enhance Unicode Configuration**
   - Improve Windows console encoding detection
   - Add fallback mechanism without emojis for non-UTF8 terminals
   - Test with both Windows Terminal (UTF-8) and Command Prompt (cp1252)

3. **Validation**
   - Test main.py startup on Windows with different terminal types
   - Verify Phoenix initialization without Unicode crashes
   - Confirm all Unicode characters display properly in UTF-8 terminals

### Step 2: Fix Planner Workflow Configuration (HIGH - 2 hours)

1. **Add StartEvent Handler to PlannerAgentWorkflow**
   - Add step to accept StartEvent and extract GAMPCategorizationEvent
   - OR modify unified_workflow.py to pass categorization event directly

2. **Fix Workflow Parameter Passing**
   - Modify unified_workflow.py line 259 to pass categorization event
   - Update PlannerAgentWorkflow.run() call with proper parameters
   - Ensure event routing works correctly

3. **Validation**
   - Test planner workflow execution independently
   - Verify categorization event flows correctly through workflow
   - Confirm planning results are generated properly

### Step 3: Integrate Research Agent into Workflow (MEDIUM - 3 hours)

1. **Update PlannerAgentWorkflow Coordination**
   - Modify planner agent to generate Research Agent coordination requests
   - Add Research Agent to coordination_requests in planning phase
   - Ensure Research Agent request events are properly created

2. **Add Research Agent to Workflow Factory**
   - Update agent factory to include Research Agent creation
   - Ensure Research Agent is available for coordination
   - Add proper initialization with FDA API configuration

3. **Test Agent Coordination Flow**
   - Verify Research Agent receives coordination requests
   - Test FDA API integration during workflow execution
   - Confirm Research Agent results are aggregated properly

## Risk Assessment

### Implementation Risks
- **Unicode Fix**: Low risk - well-understood encoding issue with clear solution
- **Planner Fix**: Medium risk - requires understanding of LlamaIndex workflow event routing
- **Research Integration**: Medium risk - requires coordination between multiple workflow components

### Rollback Plans
- **Unicode**: Revert to original main.py version, remove Unicode characters temporarily
- **Planner**: Revert unified_workflow.py changes, use categorization-only mode for testing
- **Research**: Disable parallel coordination in workflow configuration

## Compliance Validation

### GAMP-5 Implications
- **Unicode Fix**: No impact on pharmaceutical compliance - improves system reliability
- **Planner Fix**: Essential for complete GAMP-5 test generation workflow
- **Research Integration**: Enhances regulatory compliance by providing current FDA guidance

### Audit Requirements
- All fixes maintain NO FALLBACKS principle
- Error conditions fail explicitly with full diagnostic information
- Audit trails preserved throughout workflow execution
- No masking of system failures or regulatory compliance issues

## Iteration Log

### Iteration 1: Unicode Encoding Fix
**Objective**: Resolve console encoding issues and duplicate function definitions
**Success Criteria**: main.py starts successfully on Windows systems
**Testing**: Multiple terminal types (Command Prompt, PowerShell, Windows Terminal)

### Iteration 2: Planner Workflow Configuration
**Objective**: Fix planner workflow event routing and parameter passing
**Success Criteria**: Complete workflow execution from categorization through planning
**Testing**: End-to-end workflow execution with planning phase

### Iteration 3: Research Agent Integration
**Objective**: Activate Research Agent in workflow execution path
**Success Criteria**: Research Agent receives requests and provides regulatory insights
**Testing**: Workflow execution with Research Agent coordination and results

### Iteration 4: Integration Testing
**Objective**: Verify all components work together correctly
**Success Criteria**: Complete workflow with categorization, planning, and research coordination
**Testing**: Full end-to-end testing with Phoenix observability

### Iteration 5: Performance Validation
**Objective**: Ensure fixes don't impact system performance
**Success Criteria**: Workflow execution time remains within acceptable bounds
**Testing**: Performance benchmarking against baseline metrics

## Expected Outcomes

### Immediate (After Step 1)
- System starts normally on Windows without Unicode crashes
- Phoenix observability initializes successfully
- Basic workflow execution possible

### Short-term (After Step 2)
- Complete workflow execution from categorization through planning
- Planner agent generates test strategies successfully
- Workflow coordination events flow correctly

### Long-term (After Step 3)
- Research Agent actively participates in workflow execution
- FDA regulatory insights integrated into test planning
- Complete pharmaceutical test generation workflow operational

## Monitoring and Validation

### Phoenix Observability
- All workflow steps instrumented and traced
- Event routing visible in Phoenix UI
- Performance metrics captured for optimization

### System Integration Tests
- Complete workflow execution tests
- Agent coordination verification
- Error handling validation

### Regulatory Compliance Checks
- NO FALLBACKS principle maintained
- Error conditions fail explicitly
- Audit trails complete and accessible

---

**Created**: 2025-08-01  
**Priority**: URGENT (Unicode), HIGH (Planner), MEDIUM (Research)  
**Estimated Completion**: 6 hours total effort  
**Next Action**: Begin Step 1 - Unicode encoding fixes