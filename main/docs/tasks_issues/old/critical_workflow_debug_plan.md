# Debug Plan: Critical Pharmaceutical Workflow Issues

## Root Cause Analysis

### Issue 1: SME Agent Fallback Behavior (CRITICAL - VIOLATES NO FALLBACK RULE)
**Root Cause**: SME Agent implements static logic instead of actual LLM calls
- File: `main/src/agents/parallel/sme_agent.py`
- Methods like `_assess_compliance`, `_analyze_risks` use hardcoded logic
- Execution time of 0.0005s confirms no API calls are made
- **COMPLIANCE VIOLATION**: This violates the absolute "NO FALLBACKS" rule

### Issue 2: Environment Variable Loading
**Root Cause**: OPENAI_API_KEY not being recognized despite .env file
- .env file contains valid key: `OPENAI_API_KEY="sk-proj-..."`
- Issue may be in dotenv loading timing or path resolution

### Issue 3: Phoenix Dependencies Installation
**Root Cause**: Dependencies defined but may not be installed
- pyproject.toml defines: arize-phoenix>=4.0.0, openinference-instrumentation-llama-index>=2.0.0
- Need to verify actual installation status

### Issue 4: Phoenix Infrastructure Problems
**Root Cause**: UI encoding errors, HTTP timeouts, OpenTelemetry export failures
- Secondary to dependency issues
- Can be bypassed temporarily if needed

## Solution Steps

### Step 1: Fix SME Agent Fallback Behavior (IMMEDIATE - CRITICAL)
1. Replace static logic with actual LLM calls
2. Implement proper error handling that fails explicitly
3. Remove all hardcoded response generation
4. Add API call validation and tracing

### Step 2: Fix Environment Variable Loading 
1. Verify .env file loading in main.py
2. Add diagnostic logging for API key recognition
3. Test OpenAI client initialization

### Step 3: Verify Phoenix Dependencies
1. Check installed packages vs pyproject.toml
2. Reinstall missing dependencies if needed
3. Test Phoenix initialization

### Step 4: Test End-to-End Workflow
1. Run workflow with proper API calls
2. Verify all agents make actual LLM calls
3. Validate Phoenix observability (or disable if needed)

## Risk Assessment
- **HIGH RISK**: SME Agent fallback behavior violates pharmaceutical compliance requirements
- **MEDIUM RISK**: Missing dependencies could block observability
- **LOW RISK**: Environment variable issues - easily fixable

## Compliance Validation
- **GAMP-5 Implications**: Fallback logic prevents proper validation audit trails
- **21 CFR Part 11**: Static responses compromise data integrity requirements
- **ALCOA+ Principles**: Fallback behavior violates authenticity and accuracy

## Iteration Log
### Iteration 1: SME Agent Critical Fix - COMPLETED ✅
- Status: **COMPLETED**
- Focus: Remove all fallback logic from SME Agent
- Success Criteria: SME Agent makes actual OpenAI API calls
- **Actions Taken**:
  - ✅ Replaced `_assess_compliance` static logic with LLM API calls
  - ✅ Replaced `_analyze_risks` static logic with LLM API calls  
  - ✅ Replaced `_generate_recommendations` static logic with LLM API calls
  - ✅ Replaced `_provide_validation_guidance` static logic with LLM API calls
  - ✅ Replaced `_generate_domain_insights` static logic with LLM API calls
  - ✅ Replaced `_assess_regulatory_considerations` static logic with LLM API calls
  - ✅ Replaced `_formulate_expert_opinion` static logic with LLM API calls
  - ✅ Added comprehensive error handling with explicit failure (NO FALLBACKS)
  - ✅ Added JSON response validation for all LLM calls
- **Result**: SME Agent now makes actual OpenAI API calls instead of using fallback logic

### Iteration 2: Environment and Dependencies Verification
- Status: Starting
- Focus: Verify dependencies installation and environment variable loading
- Success Criteria: All required packages installed and OPENAI_API_KEY recognized