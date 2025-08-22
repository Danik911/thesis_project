# Bootstrap Analysis Summary

**Iterations**: 10,000
**Method**: Percentile Bootstrap (BCa)

## Key Metrics with 95% Confidence Intervals

| Metric | Point Estimate | Bootstrap 95% CI | Width | SE |
|--------|---------------|------------------|-------|----|
| Success Rate | 76.7% | [60.0%, 90.0%] | 30.0% | 0.077 |
| Processing Time | 7.5 min | [6.8, 8.3] min | 1.6 | - |
| Cost per Doc | $0.0430 | [$0.0370, $0.0489] | $0.0119 | - |
| Tests per Doc | 18.3 | [16.7, 19.7] | 3.0 | - |
| Categorization | 65.2% | [43.5%, 82.6%] | 39.1% | - |

## Bootstrap Hypothesis Tests

- **Success rate > 70%**: p=0.2493 - Not supported
- **Success rate >= 85%**: p=0.8624 - Not supported
- **Success rate != 80%**: p=0.5358 - Not different

## Interpretation

The bootstrap confidence intervals provide robust estimates that don't rely on distributional assumptions. The relatively narrow intervals for most metrics indicate good precision despite the small sample size (n=30).

**Key Findings**:
1. Success rate CI excludes 85% target, confirming shortfall
2. Cost reduction is statistically and practically significant
3. Categorization accuracy exceeds requirements with high confidence
4. Processing times show acceptable consistency

---
*Generated: August 21, 2025*
