# AI Agent Testing & Evaluation Guide

## Purpose
This guide is designed for AI agents (Claude, GPT-4, etc.) who will test and evaluate the pharmaceutical test generation system. It provides step-by-step instructions for running tests, validating results, and ensuring GAMP-5 compliance.

## Table of Contents
1. [System Overview](#system-overview)
2. [Environment Setup](#environment-setup)
3. [Testing Files Overview](#testing-files-overview)
4. [Running Tests](#running-tests)
5. [Evaluating Results](#evaluating-results)
6. [Critical Validation Points](#critical-validation-points)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Reporting Requirements](#reporting-requirements)

---

## System Overview

This is a GAMP-5 compliant pharmaceutical test generation system using multi-agent LLM architecture. Key principles:
- **NO FALLBACKS**: System must fail explicitly rather than generate synthetic data
- **Full Traceability**: All actions must be logged with audit trails
- **Real API Calls**: No mock data or simulations in production testing
- **DeepSeek V3 Model**: Primary LLM via OpenRouter ($0.14/1M input, $0.28/1M output)

### Architecture Components
```
main/
├── src/
│   ├── core/                  # Core workflow orchestration
│   ├── agents/                 # Multi-agent system
│   ├── cross_validation/       # CV framework
│   └── monitoring/             # Phoenix observability
├── tests/                      # Test suites
├── output/                     # Generated outputs
└── analysis/                   # Statistical analysis
```

---

## Environment Setup

### 1. Verify Environment Variables
```bash
# Check if .env file exists and contains required keys
cat C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.env | grep -E "OPENROUTER_API_KEY|OPENAI_API_KEY"
```

**Required API Keys:**
- `OPENROUTER_API_KEY`: For DeepSeek V3 model access
- `OPENAI_API_KEY`: For embeddings and backup model
- `PHOENIX_API_KEY`: For observability (optional but recommended)

### 2. Verify Dependencies
```bash
# Check Python environment
python --version  # Should be 3.11+

# Check key packages
pip list | grep -E "llama-index|phoenix|chromadb|pandas"
```

### 3. Start Phoenix Monitoring (Optional)
```bash
# Start Phoenix server for observability
phoenix serve --port 6006
# Access at http://localhost:6006
```

---

## Testing Files Overview

### Key Test Files

#### 1. **validate_fixes.py** - Comprehensive Validation Script
**Location**: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\validate_fixes.py`
**Purpose**: Validates all critical system components
**Usage**:
```bash
python validate_fixes.py
```
**Validates**:
- Cost calculations ($0.00056 per document)
- ROI calculations (535.7M%)
- Test persistence
- Statistical analysis
- No fallbacks policy

#### 2. **test_basic_cv.py** - Cross-Validation Test
**Location**: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\test_basic_cv.py`
**Purpose**: Tests cross-validation framework
**Usage**:
```bash
python test_basic_cv.py
```
**Tests**:
- Environment variable loading
- Fold management
- Metrics collection
- Workflow imports

#### 3. **run_cross_validation.py** - Full Cross-Validation
**Location**: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\run_cross_validation.py`
**Purpose**: Executes complete cross-validation
**Usage**:
```bash
# Dry run (no API calls)
python run_cross_validation.py --dry-run

# Full execution with real API calls
python run_cross_validation.py --experiment-id TEST_RUN_001 --timeout 1800

# Limited parallel processing
python run_cross_validation.py --experiment-id TEST_RUN_002 --max-parallel 1
```

#### 4. **test_env_fix.py** - Environment Loading Test
**Location**: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\test_env_fix.py`
**Purpose**: Verifies environment variable loading
**Usage**:
```bash
python test_env_fix.py
```

---

## Running Tests

### Step 1: Basic System Validation
```bash
# Run comprehensive validation
python validate_fixes.py

# Expected output:
# [PASS]: Cost Calculation
# [PASS]: ROI Calculation  
# [PASS]: Test Persistence
# [PASS]: Statistical Analysis
# [PASS]: No Fallbacks Policy
```

### Step 2: Test Cross-Validation Framework
```bash
# Test basic CV components
python test_basic_cv.py

# Expected: All 4 tests pass
```

### Step 3: Run Limited Cross-Validation
```bash
# Process 3 documents for quick validation
python -c "
import json
from pathlib import Path

# Create limited manifest
manifest = {
    'documents': [
        {'id': 'URS-002', 'path': 'datasets/urs_corpus/category_4/URS-002.md', 'category': 'category_4'},
        {'id': 'URS-003', 'path': 'datasets/urs_corpus/category_3/URS-003.md', 'category': 'category_3'},
        {'id': 'URS-004', 'path': 'datasets/urs_corpus/category_5/URS-004.md', 'category': 'category_5'}
    ],
    'folds': {
        'fold_1': {'train': [], 'validation': ['URS-002', 'URS-003', 'URS-004']}
    }
}
Path('datasets/urs_corpus/test_manifest.json').write_text(json.dumps(manifest, indent=2))
print('Test manifest created')
"

# Run with test manifest
python run_cross_validation.py --experiment-id AGENT_TEST --timeout 900
```

### Step 4: Verify Real API Calls
```bash
# Check for real execution evidence
python -c "
import json
from pathlib import Path

# Check CV results
results_file = Path('main/output/cross_validation/structured_logs/AGENT_TEST_urs_processing.jsonl')
if results_file.exists():
    with open(results_file) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                print(f\"Document: {data['document_id']}\")
                print(f\"  Success: {data['success']}\")
                print(f\"  Cost: ${data.get('cost_usd', 0):.6f}\")
                print(f\"  Tokens: {data.get('token_usage', {}).get('total_tokens', 0)}\")
                print(f\"  Time: {data.get('processing_time_seconds', 0):.2f}s\")
"
```

---

## Evaluating Results

### 1. Check Success Rate
```python
# Evaluate cross-validation success rate
import json
from pathlib import Path

def evaluate_cv_results(experiment_id):
    results_file = Path(f'main/output/cross_validation/structured_logs/{experiment_id}_urs_processing.jsonl')
    
    if not results_file.exists():
        return "No results found"
    
    total = 0
    successful = 0
    total_cost = 0.0
    total_tokens = 0
    
    with open(results_file) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                total += 1
                if data['success']:
                    successful += 1
                    total_cost += data.get('cost_usd', 0)
                    total_tokens += data.get('token_usage', {}).get('total_tokens', 0)
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"Success Rate: {success_rate:.1f}% ({successful}/{total})")
    print(f"Total Cost: ${total_cost:.6f}")
    print(f"Total Tokens: {total_tokens:,}")
    print(f"Avg Cost per Success: ${total_cost/successful:.6f}" if successful > 0 else "N/A")
    
    return success_rate >= 50  # Pass if >= 50% success

# Run evaluation
evaluate_cv_results('AGENT_TEST')
```

### 2. Verify Cost Accuracy
```python
# Verify cost calculations are correct
def verify_cost_accuracy(tokens_used, cost_reported):
    """Verify DeepSeek V3 cost calculation"""
    # Assume 2:1 prompt:completion ratio
    prompt_tokens = int(tokens_used * 0.67)
    completion_tokens = tokens_used - prompt_tokens
    
    # DeepSeek V3 pricing
    expected_cost = (prompt_tokens / 1_000_000 * 0.14 + 
                    completion_tokens / 1_000_000 * 0.28)
    
    # Allow 10% variance for rounding
    variance = abs(cost_reported - expected_cost) / expected_cost
    
    if variance <= 0.1:
        print(f"✅ Cost accurate: ${cost_reported:.6f} (expected ${expected_cost:.6f})")
        return True
    else:
        print(f"❌ Cost error: ${cost_reported:.6f} vs ${expected_cost:.6f} ({variance:.1%} variance)")
        return False

# Example verification
verify_cost_accuracy(3000, 0.00056)
```

### 3. Check Test Quality
```python
# Evaluate generated test quality
import json
from pathlib import Path

def evaluate_test_quality(test_suite_file):
    """Evaluate OQ test suite quality"""
    with open(test_suite_file) as f:
        suite = json.load(f)
    
    metadata = suite.get('metadata', {})
    tests = suite.get('test_cases', [])
    
    quality_checks = {
        'test_count': len(tests) >= 15,
        'has_metadata': bool(metadata),
        'gamp_category': metadata.get('gamp_category') in [3, 4, 5],
        'has_objectives': all(t.get('objective') for t in tests),
        'has_prerequisites': all(t.get('prerequisites') for t in tests),
        'has_acceptance_criteria': all(t.get('expected_results') for t in tests),
        'risk_levels': all(t.get('risk_level') in ['low', 'medium', 'high', 'critical'] for t in tests),
        'regulatory_basis': metadata.get('regulatory_basis', {}).get('cfr_part_11') == True
    }
    
    passed = sum(quality_checks.values())
    total = len(quality_checks)
    
    print(f"Test Quality Score: {passed}/{total}")
    for check, result in quality_checks.items():
        print(f"  {'✅' if result else '❌'} {check}")
    
    return passed >= 6  # Pass if 6/8 checks pass

# Example evaluation
test_file = Path('output/test_suites/test_suite_OQ-SUITE-1103_20250812_120328.json')
if test_file.exists():
    evaluate_test_quality(test_file)
```

---

## Critical Validation Points

### 1. NO FALLBACKS Verification
```python
def verify_no_fallbacks(log_file):
    """Ensure system fails explicitly without fallbacks"""
    with open(log_file) as f:
        content = f.read()
    
    # Check for explicit failures
    has_explicit_failures = 'NO FALLBACK ALLOWED' in content
    has_error_diagnostics = 'error_message' in content or 'ERROR' in content
    no_synthetic_data = 'synthetic' not in content.lower() and 'mock' not in content.lower()
    
    print(f"✅ Explicit failures: {has_explicit_failures}")
    print(f"✅ Error diagnostics: {has_error_diagnostics}")
    print(f"✅ No synthetic data: {no_synthetic_data}")
    
    return all([has_explicit_failures or has_error_diagnostics, no_synthetic_data])
```

### 2. GAMP-5 Compliance Check
```python
def check_gamp5_compliance(result_data):
    """Verify GAMP-5 compliance requirements"""
    compliance = {
        'category_detection': result_data.get('gamp_category_detected') in [3, 4, 5],
        'confidence_score': result_data.get('confidence_score', 0) > 0,
        'audit_trail': 'processing_timestamp' in result_data,
        'error_handling': result_data.get('error_message') is not None if not result_data['success'] else True,
        'data_integrity': result_data.get('random_seed') == 42  # Reproducibility
    }
    
    return all(compliance.values())
```

### 3. ROI Validation
```python
def validate_roi():
    """Verify ROI calculation is correct"""
    manual_cost = 3000.00
    automated_cost = 0.00056
    
    expected_roi = ((manual_cost - automated_cost) / automated_cost) * 100
    
    # Should be approximately 535.7M%
    roi_millions = expected_roi / 1_000_000
    
    if 535 <= roi_millions <= 536:
        print(f"✅ ROI correct: {roi_millions:.1f}M%")
        return True
    else:
        print(f"❌ ROI wrong: {roi_millions:.1f}M%")
        return False
```

---

## Common Issues & Solutions

### Issue 1: Missing API Key
**Error**: `OPENROUTER_API_KEY not found in environment`
**Solution**:
```bash
# Ensure .env file is loaded
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('OPENROUTER_API_KEY present:', bool(os.getenv('OPENROUTER_API_KEY')))
"
```

### Issue 2: Test Output Not Saved
**Error**: Generated tests not found on disk
**Solution**:
```python
# Check both possible output locations
from pathlib import Path

locations = [
    'output/test_suites/',
    'main/output/test_suites/'
]

for loc in locations:
    path = Path(loc)
    if path.exists():
        files = list(path.glob('test_suite_OQ-SUITE-*.json'))
        print(f"{loc}: {len(files)} test files found")
```

### Issue 3: Cost Calculation Mismatch
**Error**: Cost doesn't match expected value
**Solution**:
```python
# Verify pricing constants
from main.src.cross_validation.pricing_constants import (
    DEEPSEEK_V3_INPUT_COST_PER_1M,
    DEEPSEEK_V3_OUTPUT_COST_PER_1M,
    calculate_deepseek_v3_cost
)

print(f"Input cost: ${DEEPSEEK_V3_INPUT_COST_PER_1M}/1M")
print(f"Output cost: ${DEEPSEEK_V3_OUTPUT_COST_PER_1M}/1M")

# Test calculation
cost = calculate_deepseek_v3_cost(2000, 1000)
print(f"Test: 2000+1000 tokens = ${cost:.6f}")
assert abs(cost - 0.00056) < 0.000001, "Cost calculation error"
```

### Issue 4: Phoenix Monitoring Not Working
**Error**: Phoenix traces not captured
**Solution**:
```bash
# Install missing dependencies
pip install arize-phoenix openinference-instrumentation-llama-index openinference-instrumentation-openai

# Verify Phoenix is running
curl http://localhost:6006/health
```

---

## Reporting Requirements

### Test Report Template
When completing testing, create a report with:

```markdown
# Test Execution Report

## Test Information
- **Tester**: [AI Agent Name/Version]
- **Date**: [YYYY-MM-DD]
- **Experiment ID**: [e.g., AGENT_TEST_001]
- **Environment**: [Development/Production]

## Test Results Summary
- **Documents Processed**: X/Y
- **Success Rate**: XX%
- **Total Cost**: $X.XXXXX
- **Average Processing Time**: XXX seconds
- **Total Tokens Used**: X,XXX

## Validation Checks
- [ ] Cost calculations accurate (±10%)
- [ ] ROI calculation correct (~535.7M%)
- [ ] Test outputs persisted to disk
- [ ] No fallback logic detected
- [ ] GAMP-5 compliance maintained
- [ ] Audit trails complete

## Issues Found
1. [Issue description and severity]
2. [Steps to reproduce]
3. [Suggested fix]

## Data Integrity Verification
- **Real API Calls Made**: Yes/No
- **Token Usage Recorded**: Yes/No
- **Error Handling**: Explicit/Masked
- **Phoenix Traces**: Available/Missing

## Recommendations
[Based on test results]

## Evidence Files
- Cross-validation logs: `main/output/cross_validation/logs/[experiment_id].log`
- Processing results: `main/output/cross_validation/structured_logs/[experiment_id]_urs_processing.jsonl`
- Test outputs: `output/test_suites/test_suite_OQ-SUITE-*.json`
- Phoenix traces: `logs/traces/all_spans_*.jsonl`
```

### Critical Metrics to Report
1. **Success Rate**: Must be ≥50% for system validation
2. **Cost Accuracy**: Within 10% of expected ($0.00056/doc)
3. **Processing Time**: 200-300 seconds per document typical
4. **Test Quality**: ≥15 tests per document
5. **Compliance**: 100% GAMP-5 adherence required

### Red Flags to Report Immediately
- Any synthetic or mock data generation
- Fallback values used instead of failures
- Cost calculations off by >10%
- ROI not approximately 535.7M%
- Missing audit trails or timestamps
- Test outputs not persisted
- API keys exposed in logs

---

## Conclusion

This testing framework ensures the pharmaceutical test generation system maintains:
- **Data Integrity**: 100% real execution data
- **Regulatory Compliance**: Full GAMP-5 and 21 CFR Part 11 adherence
- **Cost Accuracy**: Precise DeepSeek V3 pricing calculations
- **Quality Assurance**: Comprehensive test generation and validation

For questions or issues, refer to:
- Technical documentation: `main/docs/guides/`
- Task implementation: `.taskmaster/tasks/`
- System logs: `main/output/cross_validation/logs/`

Remember: **NO FALLBACKS** - Always fail explicitly with full diagnostics rather than generating synthetic data.