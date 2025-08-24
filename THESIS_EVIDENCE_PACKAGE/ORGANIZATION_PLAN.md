# THESIS EVIDENCE PACKAGE - Organization Plan

## Current Structure Issues
1. **Duplication**: Statistical and compliance files exist in multiple locations
2. **Old Analysis**: Folders 02 and 03 contain analysis from August 14-20 (before Corpus 2 & 3)
3. **New Analysis**: Today's comprehensive n=30 analysis is in folder 01/unified_analysis
4. **Inconsistent Organization**: Mixed old and new data without clear separation

## Proposed Reorganization

### Folder Structure
```
THESIS_EVIDENCE_PACKAGE/
├── 01_TEST_EXECUTION_EVIDENCE/       # Raw test data and traces
│   ├── corpus_1/                     # 17 documents (Aug 11-14)
│   ├── corpus_2/                     # 8 documents (Aug 21)
│   ├── corpus_3/                     # 5 documents (Aug 21)
│   └── archive/                      # Old analysis before n=30
│
├── 02_STATISTICAL_ANALYSIS/          # Final n=30 statistical analysis
│   ├── final/                        # Today's comprehensive analysis
│   │   ├── N30_MASTER_STATISTICAL_ANALYSIS.md
│   │   ├── N30_MASTER_STATISTICAL_ANALYSIS.json
│   │   ├── performance_metrics_n30.csv
│   │   ├── statistical_validation_n30.json
│   │   └── power_analysis_n30.md
│   ├── corpus_specific/              # Individual corpus analyses
│   │   ├── corpus_1_analysis.md
│   │   ├── corpus_2_analysis.md
│   │   └── corpus_3_analysis.md
│   └── archive/                      # Old partial analysis (n=17)
│
├── 03_COMPLIANCE_DOCUMENTATION/      # Regulatory compliance evidence
│   ├── final/                        # n=30 compliance assessment
│   │   ├── gamp5_compliance_n30.json
│   │   ├── cfr_part11_audit_trail.md
│   │   ├── alcoa_plus_assessment.md
│   │   └── human_consultation_log.md
│   └── archive/                      # Old compliance docs
│
├── 04_PERFORMANCE_METRICS/           # System performance data
│   ├── final/                        # Aggregated n=30 metrics
│   │   ├── api_usage_summary.json
│   │   ├── cost_analysis_n30.csv
│   │   ├── phoenix_traces_summary.json
│   │   └── execution_time_analysis.md
│   ├── openrouter/                   # API usage logs
│   └── phoenix_traces/               # Observability data
│
├── 05_THESIS_DOCUMENTS/              # Final thesis content
│   ├── chapter_4/
│   │   ├── CHAPTER_4_RESULTS_FINAL.md
│   │   └── tables/                   # All tables in multiple formats
│   ├── appendices/
│   └── supplementary_materials/
│
└── 06_UNIFIED_ANALYSIS/              # Today's comprehensive analysis
    ├── reports/                       # Master reports
    ├── scripts/                       # Analysis scripts
    └── tables/                        # Generated tables
```

## Migration Actions Required

### Step 1: Archive Old Analysis
- Move current 02_STATISTICAL_ANALYSIS files to archive/
- Move current 03_COMPLIANCE_DOCUMENTATION files to archive/
- Move old corpus_1 analysis to archive/

### Step 2: Consolidate New Analysis
- Copy unified_analysis/final_reports to 02_STATISTICAL_ANALYSIS/final/
- Generate compliance documentation from n=30 analysis
- Update performance metrics with aggregated data

### Step 3: Create Master Index
- Generate README.md in each folder explaining contents
- Create EVIDENCE_INDEX.md listing all key files with descriptions
- Add timestamps and version information

### Step 4: Validate Completeness
- Ensure all 30 documents have test suites
- Verify all Phoenix traces are captured
- Confirm statistical analysis covers all hypotheses
- Check compliance documentation completeness

## File Movement Plan

### From 01_TEST_EXECUTION_EVIDENCE/unified_analysis/
→ **TO 02_STATISTICAL_ANALYSIS/final/**
- N30_MASTER_STATISTICAL_ANALYSIS.md
- N30_MASTER_STATISTICAL_ANALYSIS.json
- n30_statistical_aggregation.py

→ **TO 06_UNIFIED_ANALYSIS/**
- reports/* (keep copy here)
- scripts/* (keep here)
- thesis_outputs/* (keep here)

### From 01_TEST_EXECUTION_EVIDENCE/corpus_*/
→ **TO 02_STATISTICAL_ANALYSIS/corpus_specific/**
- CORPUS_1_DEEP_ANALYSIS.md
- CORPUS_2_DEEP_ANALYSIS.md
- CORPUS_3_DEEP_ANALYSIS.md

### Current Files to Archive
→ **TO 02_STATISTICAL_ANALYSIS/archive/**
- performance_metrics.csv (old, from Aug 14)
- statistical_results.json (old, from Aug 20)
- statistical_validation.md (old)
- statistical_validation_report.json (old)

→ **TO 03_COMPLIANCE_DOCUMENTATION/archive/**
- compliance_metrics.json (old, from Aug 20)
- compliance_validation.md (old, from Aug 20)

## Benefits of Reorganization
1. **Clear Separation**: Old vs new analysis clearly separated
2. **Complete Evidence**: All n=30 analysis in one place
3. **Thesis Ready**: Chapter 4 has all supporting data organized
4. **Audit Trail**: Easy to trace evolution of analysis
5. **Reproducibility**: Scripts and data co-located

## Implementation Priority
1. **HIGH**: Move n=30 analysis to proper folders
2. **HIGH**: Archive old partial analysis
3. **MEDIUM**: Create index files
4. **LOW**: Clean up duplicates

---
*Created: August 21, 2025*
*Purpose: Organize thesis evidence for final submission*