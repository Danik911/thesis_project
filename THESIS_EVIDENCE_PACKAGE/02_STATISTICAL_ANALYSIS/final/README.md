# Statistical Analysis - Final N=30 Results

## Overview
This folder contains the comprehensive statistical analysis from the cross-validation study of 30 pharmaceutical URS documents processed by the multi-agent LLM system.

## Key Files

### Master Analysis
- **N30_MASTER_STATISTICAL_ANALYSIS.md** - Complete statistical report with hypothesis testing
- **N30_MASTER_STATISTICAL_ANALYSIS.json** - Raw statistical data in JSON format
- **n30_statistical_aggregation.py** - Python script used for analysis

## Key Metrics (N=30)

### Success Metrics
- **Overall Success Rate**: 76.7% (23/30 documents)
- **95% Confidence Interval**: [59.1%, 88.2%]
- **Categorization Accuracy**: 91.3% (21/23 successful)
- **Recovery Rate with Retries**: 96.7% (29/30)

### Statistical Tests
| Hypothesis | Target | Achieved | p-value | Result |
|------------|--------|----------|---------|--------|
| Success Rate ≥85% | 85% | 76.7% | 0.153 | Conditional |
| Cost Reduction ≥90% | 90% | 91% | N/A | ✓ Supported |
| GAMP-5 ≥95% | 95% | 91.3% | 0.321 | Conditional |
| Categorization ≥80% | 80% | 91.3% | 0.960 | ✓ Supported |

### Power Analysis
- **Achieved Power**: 0.50 (below 0.80 target)
- **Sample for 80% Power**: n=114 required
- **Effect Size**: 0.329 (small)

## Corpus Distribution
- **Corpus 1**: 17 documents (56.7% weight)
- **Corpus 2**: 8 documents (26.7% weight)  
- **Corpus 3**: 5 documents (16.7% weight)

## Temporal Improvement
Clear progression observed: 64.7% → 87.5% → 100%

## Statistical Methods Used
- Bootstrap analysis (10,000 iterations)
- One-sample t-tests
- Chi-square independence tests
- Weighted averaging
- Binomial confidence intervals

## Date Generated
August 21, 2025

## Related Documents
- Individual corpus analyses in ../corpus_specific/
- Old partial analysis (n=17) in ../archive/
- Full thesis chapter in ../../05_THESIS_DOCUMENTS/chapter_4/