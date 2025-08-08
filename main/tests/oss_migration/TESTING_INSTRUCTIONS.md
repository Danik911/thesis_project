# OSS Migration Testing Instructions

## Current Status: READY FOR REAL API TESTING

### What Has Been Completed ✅

1. **Code Migration**: All agents migrated to use centralized `LLMConfig`
   - 18 files successfully migrated
   - Only LLM initialization changed (minimal impact)
   - No business logic modifications

2. **Migrated Components**:
   - ✅ Unified Workflow (`unified_workflow.py`)
   - ✅ Categorization Agent (`categorization/agent.py`)
   - ✅ Context Provider (`parallel/context_provider.py`)
   - ✅ SME Agent (`parallel/sme_agent.py`)
   - ✅ Research Agent (`parallel/research_agent.py`)
   - ✅ OQ Generator (`oq_generator/generator_v2.py`)
   - ✅ Planner Agent (`planner/agent.py`)
   - ✅ All supporting workflows

3. **Test Infrastructure**:
   - ✅ Real API test suite created
   - ✅ Test data prepared from GAMP-5 documents
   - ✅ Status check utility ready
   - ✅ Comprehensive test report template

### How to Run Real Tests

#### Step 1: Set Environment Variables

```bash
# For Windows Command Prompt:
set OPENROUTER_API_KEY=your-api-key-here
set LLM_PROVIDER=openrouter

# For Windows PowerShell:
$env:OPENROUTER_API_KEY="your-api-key-here"
$env:LLM_PROVIDER="openrouter"

# For Git Bash/WSL:
export OPENROUTER_API_KEY='your-api-key-here'
export LLM_PROVIDER=openrouter
```

#### Step 2: Verify Configuration

```bash
cd main
uv run python tests/oss_migration/test_oss_quick_check.py
```

Expected output:
```
OPENROUTER_API_KEY: [OK] SET
LLM_PROVIDER: openrouter
Model: openai/gpt-oss-120b
[OK] Configuration is valid
```

#### Step 3: Run Full Test Suite

```bash
cd main
uv run python tests/oss_migration/test_real_oss_migration.py
```

This will:
1. Test LLM initialization with real API
2. Test categorization with 3 GAMP-5 documents
3. Test unified workflow end-to-end
4. Generate detailed report with metrics

### What to Expect

#### Success Metrics:
- **Categorization Accuracy**: 70-80% (vs 95% with OpenAI)
- **Response Time**: 3-8 seconds (vs 2-5s with OpenAI)
- **Cost**: ~$0.09 per 1M tokens (vs $10-30 with OpenAI)

#### Expected Failures (NORMAL):
- 20-30% JSON parsing failures
- Some low confidence scores (<0.7)
- Occasional timeouts on complex queries
- Human consultation triggers

### Test Results Location

After running tests, check:
- `tests/oss_migration/oss_test_report_[timestamp].json` - Detailed results
- Console output for immediate feedback
- Phoenix traces (if configured) at http://localhost:6006

### Rollback Instructions

If tests fail critically:

```bash
# Switch back to OpenAI
set LLM_PROVIDER=openai
set OPENAI_API_KEY=your-openai-key

# Or in code, change default in llm_config.py:
PROVIDER = ModelProvider(os.getenv("LLM_PROVIDER", "openai"))
```

### Critical Validation Points

Before declaring success:

1. **Verify API Calls Are Real**
   - Check network traffic
   - Verify API usage in OpenRouter dashboard
   - Confirm no mock responses

2. **Check Categorization Results**
   - Category 3: Should identify "vendor software without modification"
   - Category 4: Should identify "configured commercial software"
   - Category 5: Should identify "custom developed software"

3. **Validate Cost Reduction**
   - Check token usage in responses
   - Calculate actual cost per test
   - Verify >90% reduction achieved

4. **Document All Failures**
   - Record exact error messages
   - Note confidence scores
   - Track response times

### Support & Troubleshooting

Common issues:

1. **"OPENROUTER_API_KEY not found"**
   - Ensure environment variable is set
   - Restart terminal/IDE after setting

2. **"Model not available"**
   - Check OpenRouter account has access to `openai/gpt-oss-120b`
   - Try alternative model like `qwen/qwen-72b-chat`

3. **Timeout errors**
   - Normal for OSS models (slower than GPT-4)
   - Increase timeout in config if needed

4. **JSON parsing failures**
   - Expected with OSS models
   - System will trigger human consultation

### Final Checklist

- [ ] API key set in environment
- [ ] LLM_PROVIDER set to "openrouter"
- [ ] Quick check shows configuration valid
- [ ] Real API test executed
- [ ] Results documented in report
- [ ] Cost reduction verified
- [ ] Failures honestly reported

---

**Remember**: The goal is HONEST testing with REAL APIs. Report all issues transparently. A 70% success rate with 99% cost reduction is a WIN!