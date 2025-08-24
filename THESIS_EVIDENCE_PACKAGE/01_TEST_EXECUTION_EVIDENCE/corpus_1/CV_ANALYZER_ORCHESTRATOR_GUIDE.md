# CV-Analyzer Orchestrator Guide
## Multi-Agent Parallel Analysis Framework

### 🎯 Mission Overview
You are an orchestrator AI agent responsible for launching and coordinating multiple cv-analyzer subagents to perform comprehensive parallel analysis of cross-validation test results. Each analyzer focuses on a specific domain, and you consolidate their findings into a unified thesis-quality report.

---

## 📋 Prerequisites & Setup

### Required Files and Directories
```
C:\Users\anteb\Desktop\Courses\Projects\thesis_project\
├── THESIS_EVIDENCE_PACKAGE\
│   ├── 01_TEST_EXECUTION_EVIDENCE\
│   │   ├── main_cv_execution\         # Test suites and traces
│   │   ├── openrouter_activity_*.csv  # API logs
│   │   ├── *phoenix_ui.csv           # Phoenix UI exports
│   │   └── scripts\                   # Analysis scripts
│   │       ├── analyze_openrouter_api.py
│   │       ├── extract_test_metrics.py
│   │       ├── trace_deep_analysis.py
│   │       ├── statistical_validation.py
│   │       └── run_comprehensive_analysis.py
│   └── 05_THESIS_DOCUMENTS\
│       └── chapter_4\                 # Thesis chapter for validation
└── .claude\agents\
    └── cv-analyzer.md                  # Subagent specification
```

### Required Python Scripts Status
✅ All scripts have been tested and debugged
✅ JSON serialization issues fixed
✅ Unicode/encoding issues resolved
✅ Master analysis script available

---

## 🚀 Orchestration Strategy

### Phase 1: Launch Three Parallel CV-Analyzers

#### **Analyzer 1: Test Suite Analysis**
```markdown
Task: Analyze all 17 test suites for quality and complexity metrics
Focus Areas:
- Test complexity scoring (steps, decision points, data capture)
- Quality assessment (completeness, traceability, clarity)
- GAMP category distribution
- Risk level analysis
- Requirement coverage mapping

Input Directory: 
C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\main_cv_execution\

Required Outputs:
- test_suite_analysis.md (detailed markdown report)
- test_suite_metrics.json (structured data)

Script to Use:
python extract_test_metrics.py
```

#### **Analyzer 2: Trace & API Analysis**
```markdown
Task: Analyze Phoenix traces, OpenRouter API logs, and Phoenix UI data
Focus Areas:
- Agent performance breakdown (latency, throughput, errors)
- API cost analysis (provider comparison, token economics)
- Workflow bottlenecks and critical paths
- ChromaDB query patterns
- Parallel execution efficiency

Input Files:
- main_cv_execution\**\traces\*.jsonl (Phoenix traces)
- openrouter_activity_2025-08-20.csv (API logs)
- 20_08_2025_final_test_launch_phoenix_ui.csv (UI export)

Required Outputs:
- trace_api_analysis.md (detailed markdown report)
- performance_metrics.json (structured data)

Scripts to Use:
python trace_deep_analysis.py
python analyze_openrouter_api.py
```

#### **Analyzer 3: Statistical Validation**
```markdown
Task: Perform comprehensive statistical analysis and hypothesis testing
Focus Areas:
- Confusion matrix and classification metrics
- Inter-rater reliability (Cohen's Kappa, ICC)
- Matthews Correlation Coefficient
- Bootstrap confidence intervals
- Hypothesis testing (accuracy, cost, performance)
- Correlation analysis

Input Data:
- Expected vs actual categorization results
- Performance metrics from other analyzers
- Cost data from API analysis

Required Outputs:
- statistical_validation.md (detailed markdown report)
- statistical_results.json (structured data)

Script to Use:
python statistical_validation.py
```

---

## 📊 Phase 2: Consolidation Agent

### Master Consolidator Task
```markdown
Task: Synthesize all three analyzer reports into comprehensive thesis documentation

Required Sections:
1. Executive Summary
   - Key metrics dashboard
   - Success/failure assessment
   - Thesis validation verdict

2. Detailed Findings
   - Performance analysis (from Analyzer 2)
   - Quality assessment (from Analyzer 1)
   - Statistical validation (from Analyzer 3)
   - Cost-benefit analysis

3. Critical Issues
   - 81.7x cost overrun explanation
   - 54.9% clarity score analysis
   - Performance bottlenecks
   - Categorization errors

4. Recommendations
   - Immediate actions (critical)
   - Short-term improvements (1-2 weeks)
   - Long-term optimization (1+ month)

5. Thesis Validation
   - Objectives met/not met
   - Statistical significance
   - Academic rigor assessment

Required Outputs:
- MASTER_THESIS_ANALYSIS.md (comprehensive markdown)
- MASTER_METRICS_CONSOLIDATED.json (all metrics)
- EXECUTIVE_SUMMARY.md (2-page summary)
```

---

## 💻 Implementation Commands

### Step 1: Launch Analyzer 1 (Test Suites)
```python
# Prompt for cv-analyzer subagent 1
"""
Navigate to: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\scripts

Run test metrics extraction:
python extract_test_metrics.py

Analyze the results and create two reports:
1. test_suite_analysis.md - Detailed markdown report with:
   - Test complexity analysis
   - Quality score breakdown
   - GAMP category performance
   - Risk distribution
   - Improvement recommendations

2. test_suite_metrics.json - Structured metrics

Focus on explaining why clarity is only 54.9% and provide specific examples.
"""
```

### Step 2: Launch Analyzer 2 (Traces & API)
```python
# Prompt for cv-analyzer subagent 2
"""
Navigate to: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\scripts

Run both analyses:
python trace_deep_analysis.py
python analyze_openrouter_api.py

Also analyze the Phoenix UI export:
C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\20_08_2025_final_test_launch_phoenix_ui.csv

Create two reports:
1. trace_api_analysis.md - Detailed analysis covering:
   - Agent performance bottlenecks
   - API cost breakdown and optimization opportunities
   - Token usage patterns
   - Provider efficiency comparison

2. performance_metrics.json - All performance data

Explain the 81.7x cost overrun with specific evidence.
"""
```

### Step 3: Launch Analyzer 3 (Statistical)
```python
# Prompt for cv-analyzer subagent 3
"""
Navigate to: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\scripts

Run statistical validation:
python statistical_validation.py

Create two reports:
1. statistical_validation.md - Comprehensive statistical analysis:
   - Confusion matrix interpretation
   - Inter-rater reliability assessment
   - Hypothesis test results with p-values
   - Correlation analysis with visualizations
   - Confidence intervals

2. statistical_results.json - All statistical metrics

Provide academic-quality interpretation of Cohen's Kappa = 0.817 and MCC = 0.831.
"""
```

### Step 4: Launch Master Consolidator
```python
# Prompt for final consolidation
"""
Consolidate all reports from the three analyzers:
- test_suite_analysis.md & test_suite_metrics.json
- trace_api_analysis.md & performance_metrics.json  
- statistical_validation.md & statistical_results.json

Create final deliverables:

1. MASTER_THESIS_ANALYSIS.md
   Structure:
   # Comprehensive Cross-Validation Analysis
   ## Executive Summary
   ## 1. Test Quality Analysis (from Analyzer 1)
   ## 2. Performance & Cost Analysis (from Analyzer 2)
   ## 3. Statistical Validation (from Analyzer 3)
   ## 4. Integrated Findings
   ## 5. Critical Issues & Root Causes
   ## 6. Recommendations
   ## 7. Thesis Validation Assessment
   ## Appendices

2. MASTER_METRICS_CONSOLIDATED.json
   Merge all JSON files with proper structure

3. EXECUTIVE_SUMMARY.md
   2-page summary for thesis committee
"""
```

---

## 📝 Report Templates

### Markdown Report Structure
```markdown
# [Analysis Title]
**Date**: [ISO timestamp]
**Analyzer Version**: cv-analyzer v2.0
**Data Sources**: [List sources]

## Executive Summary
[2-3 paragraph overview]

## Key Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| ... | ... | ... | ✅/❌ |

## Detailed Analysis

### Section 1: [Topic]
[Analysis with evidence]

### Section 2: [Topic]
[Analysis with evidence]

## Findings
1. **Critical**: [Finding with impact]
2. **Important**: [Finding with recommendation]

## Recommendations
- **Immediate**: [Action items]
- **Short-term**: [Improvements]
- **Long-term**: [Strategic changes]

## Statistical Evidence
[Tables, correlations, p-values]

## Appendices
[Supporting data]
```

### JSON Structure
```json
{
  "metadata": {
    "timestamp": "ISO-8601",
    "analyzer": "name",
    "version": "2.0",
    "data_sources": []
  },
  "summary_metrics": {
    "key_metric_1": value,
    "key_metric_2": value
  },
  "detailed_results": {
    "category_1": {},
    "category_2": {}
  },
  "statistical_analysis": {
    "tests": [],
    "correlations": {},
    "confidence_intervals": {}
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "category": "cost",
      "action": "...",
      "expected_impact": "..."
    }
  ]
}
```

---

## ⚠️ Critical Considerations

### Known Issues to Address
1. **Cost Overrun (81.7x)**: Requires deep analysis of token usage patterns
2. **Clarity Score (54.9%)**: Need specific examples of unclear tests
3. **Performance Bottlenecks**: OQ Generator taking >100 seconds
4. **Category 4 Over-prediction**: 2 false positives affecting accuracy

### Quality Checkpoints
- ✅ All metrics have confidence intervals
- ✅ All findings backed by statistical evidence
- ✅ All recommendations have expected impact
- ✅ Cross-reference between analyzers for consistency
- ✅ Validate against thesis objectives

### Success Criteria
- [ ] All 3 analyzers complete successfully
- [ ] All 6 report files generated (3 MD + 3 JSON)
- [ ] Master consolidation includes all findings
- [ ] Executive summary is concise (2 pages max)
- [ ] Thesis validation verdict is clear

---

## 🎯 Expected Outcomes

### Deliverables Checklist
- [ ] test_suite_analysis.md
- [ ] test_suite_metrics.json
- [ ] trace_api_analysis.md
- [ ] performance_metrics.json
- [ ] statistical_validation.md
- [ ] statistical_results.json
- [ ] MASTER_THESIS_ANALYSIS.md
- [ ] MASTER_METRICS_CONSOLIDATED.json
- [ ] EXECUTIVE_SUMMARY.md

### Quality Metrics
- Reports use academic language and rigor
- All statistics include significance tests
- Visualizations support key findings
- Recommendations are actionable and specific
- Thesis alignment is explicitly validated

---

## 📚 Reference Information

### Key Statistics (Current Baseline)
- **Accuracy**: 88.2% (target: 90%)
- **Cohen's Kappa**: 0.817
- **MCC**: 0.831
- **Cost per Document**: $0.0457 (target: $0.00056)
- **API Calls**: 686 total (40.4 per document)
- **Execution Time**: 952.7 minutes total
- **Test Clarity**: 54.9% (critical issue)
- **Test Suites**: 17
- **Total Tests**: 330
- **Total Spans**: 517

### File Locations
- Test Suites: `main_cv_execution\category_*\*.json`
- Traces: `main_cv_execution\category_*\traces\*.jsonl`
- OpenRouter: `openrouter_activity_2025-08-20.csv`
- Phoenix UI: `20_08_2025_final_test_launch_phoenix_ui.csv`
- Scripts: `scripts\*.py`

---

*This guide ensures systematic, parallel analysis with academic rigor for thesis validation*