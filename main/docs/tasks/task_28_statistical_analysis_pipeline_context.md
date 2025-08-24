# Task 28: Implement Statistical Analysis Pipeline - Implementation Context

## Executive Summary

Task 28 implements a comprehensive statistical analysis pipeline that extends the existing StatisticalAnalyzer with ANOVA capabilities, integrates with Task 27's validation framework output, and provides pharmaceutical-grade statistical validation for thesis claims. The pipeline must achieve p<0.05 significance for thesis validation while handling small sample sizes (17 documents across 5 folds) appropriately.

**Critical Requirements**:
- **ANOVA Implementation**: One-way ANOVA for GAMP categories (3, 4, 5) comparison
- **Post-hoc Testing**: Tukey HSD or Games-Howell for pairwise comparisons
- **Small Sample Methods**: Bootstrap confidence intervals, effect size calculations
- **Task 27 Integration**: Seamless connection to validation framework output
- **Thesis Validation**: Must achieve p<0.05 significance for research claims
- **NO FALLBACKS**: Explicit statistical inference only, no mock values

## Research and Context (by context-collector)

### Current Statistical Infrastructure Analysis

#### 1. Existing StatisticalAnalyzer ✅ Comprehensive Foundation

**Located**: `main/src/cross_validation/statistical_analyzer.py`

**Current Capabilities**:
```python
class StatisticalAnalyzer:
    # ✅ Already implemented
    - paired_t_test(): Parametric paired comparisons
    - wilcoxon_signed_rank_test(): Non-parametric alternative
    - calculate_confidence_interval(): Bootstrap, t-distribution, normal methods
    - test_normality(): Shapiro-Wilk, Jarque-Bera tests
    - apply_multiple_comparison_correction(): Bonferroni, Holm-Bonferroni, FDR
    - comprehensive_analysis(): Full statistical workflow
    - Statistical power calculations for paired t-tests
    - Effect size calculations (Cohen's d)
    
    # ❌ Missing for Task 28
    - One-way ANOVA for multiple groups
    - Post-hoc tests (Tukey HSD, Games-Howell)
    - ANOVA effect size (eta-squared, omega-squared)
    - ANOVA assumptions testing (Levene's test)
    - Integration with validation framework data
```

#### 2. Quality Metrics with F-Statistic ✅ Partial ANOVA

**Located**: `main/src/cross_validation/quality_metrics.py`

**Current Implementation**:
```python
# Line 448: Basic F-statistic for fold comparisons
def compare_fold_quality(self, fold_reports: list[QualityReport]) -> dict[str, Any]:
    if len(accuracies) > 2:
        try:
            f_stat, f_p_value = stats.f_oneway(*[[acc] for acc in accuracies])
            comparison["statistical_tests"] = {
                "f_statistic": float(f_stat),
                "f_p_value": float(f_p_value),
                "significant_difference": float(f_p_value) < 0.05
            }
```

**Gap Analysis**: Basic F-test exists but needs enhancement for:
- Proper GAMP category grouping
- Post-hoc testing integration
- Effect size calculations
- Assumptions validation

#### 3. Task 27 Validation Framework Integration ✅ Data Available

**Metrics Collector**: `main/src/validation/framework/metrics_collector.py`
```python
class ValidationMetricsCollector:
    async def collect_fold_metrics(self, fold_number: int, processing_results: Dict[str, Any]) -> FoldMetrics:
        # Provides per-fold performance data
        - categorization_accuracy by category
        - confidence_scores by category
        - success_rates by fold
        - category_distribution per fold
```

**Results Aggregator**: `main/src/validation/framework/results_aggregator.py`
```python
class ResultsAggregator:
    async def aggregate_results(self, fold_results: Dict[str, Any], comprehensive_metrics: Dict[str, Any]) -> AggregatedResults:
        # Provides cross-fold statistical analysis
        - performance_metrics: Dict[str, StatisticalSummary]
        - category_analysis: Dict[str, CategoryPerformance] 
        - statistical_tests: Dict[str, Any]  # ← Integration point for Task 28
```

**Real Data Available**: `logs/validation/reports/real_cv_test_real_cv_test_20250813_181651.json`
```json
{
  "fold_results": {
    "fold_1": {
      "categorization_results": {
        "confidence_scores": [0.706, 0.735, 0.923, 0.708]
      },
      "metrics": {
        "category_distribution": {
          "Category 3": 2,
          "Category 4": 2, 
          "Category 5": 1
        }
      }
    }
  }
}
```

### ANOVA Implementation Research

#### 1. Pharmaceutical Statistical Validation Requirements

**Regulatory Framework** (GAMP-5, FDA, ICH Q2(R2)):
- **Statistical Rigor**: Must demonstrate both statistical and practical significance
- **Small Sample Robustness**: Methods must be valid for pharmaceutical sample sizes
- **Assumption Testing**: All statistical assumptions must be verified and documented
- **Effect Size Reporting**: Clinical/practical significance assessment required
- **Multiple Comparison Control**: Family-wise error rate control essential
- **Audit Trail**: Complete traceability of statistical decisions

**ICH Q2(R2) Statistical Requirements**:
```python
# Analytical method validation statistical criteria
- Precision: RSD ≤ 2.0% (Category 3), ≤ 3.0% (Category 4), ≤ 5.0% (Category 5)
- Accuracy: 98-102% recovery for all categories
- Robustness: Statistical demonstration of method stability
- Intermediate Precision: ANOVA-based variance component analysis
```

#### 2. One-Way ANOVA for GAMP Categories

**Research Findings**: Pharmaceutical validation commonly uses one-way ANOVA to compare performance across GAMP categories due to different complexity and validation requirements.

**Implementation Pattern**:
```python
def one_way_anova_gamp_categories(self, 
                                 category_3_metrics: list[float],
                                 category_4_metrics: list[float], 
                                 category_5_metrics: list[float],
                                 metric_name: str = "categorization_accuracy") -> ANOVAResult:
    """
    Perform one-way ANOVA comparing performance across GAMP categories.
    
    H0: μ₃ = μ₄ = μ₅ (no difference between categories)
    H1: At least one mean differs significantly
    
    Args:
        category_3_metrics: Performance metrics for Category 3 documents
        category_4_metrics: Performance metrics for Category 4 documents
        category_5_metrics: Performance metrics for Category 5 documents
        metric_name: Name of the metric being analyzed
    
    Returns:
        ANOVAResult with F-statistic, p-value, effect size, and post-hoc tests
    """
```

**SciPy Implementation**:
```python
from scipy import stats
from scipy.stats import f_oneway

# Perform one-way ANOVA
f_statistic, p_value = f_oneway(category_3_metrics, category_4_metrics, category_5_metrics)

# Calculate effect size (eta-squared)
# η² = SS_between / SS_total
ss_total = sum([(x - grand_mean)**2 for group in all_groups for x in group])
ss_between = sum([len(group) * (np.mean(group) - grand_mean)**2 for group in all_groups])
eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

# Interpretation of effect size
# η² = 0.01 (small), 0.06 (medium), 0.14 (large)
```

#### 3. Post-Hoc Testing Implementation

**Tukey HSD vs Games-Howell Decision Tree**:
```python
def select_posthoc_test(self, group_data: List[List[float]]) -> str:
    """Select appropriate post-hoc test based on assumptions."""
    
    # Test homogeneity of variance (Levene's test)
    _, levene_p = stats.levene(*group_data)
    
    # Test sample size balance
    group_sizes = [len(group) for group in group_data]
    is_balanced = len(set(group_sizes)) == 1
    
    if levene_p > 0.05 and is_balanced and all(len(g) >= 5 for g in group_data):
        return "tukey_hsd"  # Classic Tukey HSD
    elif not is_balanced or levene_p <= 0.05:
        return "games_howell"  # Robust to unequal variances/sizes
    else:
        return "tukey_kramer"  # Tukey-Kramer for unequal sizes with equal variances
```

**SciPy Tukey HSD Implementation** (SciPy 1.16+):
```python
from scipy.stats import tukey_hsd

def perform_tukey_hsd(self, 
                     category_3_metrics: list[float],
                     category_4_metrics: list[float],
                     category_5_metrics: list[float]) -> PostHocResult:
    """
    Perform Tukey HSD post-hoc test for pairwise comparisons.
    Controls family-wise error rate at α = 0.05.
    """
    
    # Standard Tukey HSD (equal variances assumed)
    result = tukey_hsd(category_3_metrics, category_4_metrics, category_5_metrics)
    
    # Extract pairwise comparisons
    comparisons = []
    group_names = ["Category 3", "Category 4", "Category 5"]
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            comparison = {
                "group_1": group_names[i],
                "group_2": group_names[j],
                "mean_diff": result.statistic[i][j],
                "p_value": result.pvalue[i][j],
                "confidence_interval": (result.confidence_interval.low[i][j], 
                                      result.confidence_interval.high[i][j]),
                "significant": result.pvalue[i][j] < 0.05
            }
            comparisons.append(comparison)
    
    return PostHocResult(
        test_name="tukey_hsd",
        comparisons=comparisons,
        family_wise_error_rate=0.05,
        significant_pairs=[c for c in comparisons if c["significant"]]
    )
```

**Games-Howell for Unequal Variances**:
```python
# When Levene's test indicates unequal variances
result_gh = tukey_hsd(category_3_metrics, category_4_metrics, category_5_metrics, 
                      equal_var=False)  # Enables Games-Howell procedure
```

#### 4. Small Sample Considerations (17 Documents)

**Challenge**: 17 documents across 5 folds ≈ 3-4 documents per fold
- Traditional ANOVA assumes normality (challenging to verify with n<5 per group)
- Unequal group sizes across folds
- Limited power to detect medium effect sizes

**Bootstrap ANOVA Approach**:
```python
def bootstrap_anova(self, 
                   category_data: Dict[str, List[float]], 
                   n_bootstrap: int = 10000) -> BootstrapANOVAResult:
    """
    Bootstrap-based ANOVA for small samples.
    Provides robust inference without distributional assumptions.
    """
    
    def anova_statistic(data_dict):
        """Calculate F-statistic for bootstrap resampling."""
        groups = list(data_dict.values())
        f_stat, _ = stats.f_oneway(*groups)
        return f_stat
    
    # Original F-statistic
    observed_f = anova_statistic(category_data)
    
    # Bootstrap resampling
    bootstrap_f_stats = []
    all_values = [val for group in category_data.values() for val in group]
    group_sizes = [len(group) for group in category_data.values()]
    
    for _ in range(n_bootstrap):
        # Resample under null hypothesis (no group differences)
        resampled = np.random.choice(all_values, size=sum(group_sizes), replace=True)
        
        # Reconstruct groups
        bootstrap_groups = {}
        start_idx = 0
        for i, (cat_name, size) in enumerate(zip(category_data.keys(), group_sizes)):
            bootstrap_groups[cat_name] = resampled[start_idx:start_idx + size].tolist()
            start_idx += size
        
        bootstrap_f_stats.append(anova_statistic(bootstrap_groups))
    
    # Calculate p-value
    p_value_bootstrap = np.mean(np.array(bootstrap_f_stats) >= observed_f)
    
    # Bootstrap confidence interval for F-statistic
    f_ci_lower = np.percentile(bootstrap_f_stats, 2.5)
    f_ci_upper = np.percentile(bootstrap_f_stats, 97.5)
    
    return BootstrapANOVAResult(
        observed_f_statistic=observed_f,
        bootstrap_p_value=p_value_bootstrap,
        bootstrap_ci=(f_ci_lower, f_ci_upper),
        bootstrap_distribution=bootstrap_f_stats,
        significant=p_value_bootstrap < 0.05
    )
```

#### 5. Effect Size Calculations

**Eta-squared (η²)** - Proportion of total variance explained:
```python
def calculate_effect_sizes(self, category_data: Dict[str, List[float]]) -> Dict[str, float]:
    """Calculate ANOVA effect sizes for practical significance assessment."""
    
    groups = list(category_data.values())
    all_values = [val for group in groups for val in group]
    grand_mean = np.mean(all_values)
    n_total = len(all_values)
    k_groups = len(groups)
    
    # Sum of squares calculations
    ss_total = sum([(x - grand_mean)**2 for x in all_values])
    ss_between = sum([len(group) * (np.mean(group) - grand_mean)**2 for group in groups])
    ss_within = ss_total - ss_between
    
    # Effect sizes
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
    
    # Omega-squared (less biased estimate)
    ms_between = ss_between / (k_groups - 1)
    ms_within = ss_within / (n_total - k_groups)
    omega_squared = (ss_between - (k_groups - 1) * ms_within) / (ss_total + ms_within)
    omega_squared = max(0.0, omega_squared)  # Cannot be negative
    
    # Cohen's f (alternative effect size)
    cohens_f = np.sqrt(eta_squared / (1 - eta_squared)) if eta_squared < 1 else np.inf
    
    return {
        "eta_squared": eta_squared,
        "eta_squared_interpretation": interpret_eta_squared(eta_squared),
        "omega_squared": omega_squared,
        "cohens_f": cohens_f,
        "cohens_f_interpretation": interpret_cohens_f(cohens_f)
    }

def interpret_eta_squared(eta_squared: float) -> str:
    """Interpret eta-squared effect size using Cohen's criteria."""
    if eta_squared < 0.01:
        return "negligible"
    elif eta_squared < 0.06:
        return "small"
    elif eta_squared < 0.14:
        return "medium"
    else:
        return "large"
```

### Integration Architecture

#### 1. Task 27 Data Pipeline Integration

**Data Flow**:
```
Task 27 ValidationMetricsCollector → Task 28 Statistical Pipeline → Enhanced ResultsAggregator
```

**Integration Pattern**:
```python
class StatisticalAnalysisPipeline:
    """Enhanced statistical analysis pipeline integrating with Task 27 validation framework."""
    
    def __init__(self, statistical_analyzer: StatisticalAnalyzer):
        self.analyzer = statistical_analyzer
        self.logger = logging.getLogger(__name__)
    
    async def analyze_validation_results(self, 
                                       validation_results: Dict[str, Any]) -> EnhancedStatisticalReport:
        """
        Main pipeline entry point - analyze Task 27 validation results.
        
        Args:
            validation_results: Output from Task 27 validation framework
            
        Returns:
            Enhanced statistical report with ANOVA results
        """
        
        # Extract category-grouped metrics from Task 27 data
        category_metrics = self._extract_category_metrics(validation_results)
        
        # Perform ANOVA analysis
        anova_results = await self._perform_anova_analysis(category_metrics)
        
        # Integrate with existing statistical analysis
        comprehensive_analysis = await self._integrate_with_existing_analysis(
            validation_results, anova_results
        )
        
        return EnhancedStatisticalReport(
            anova_results=anova_results,
            comprehensive_analysis=comprehensive_analysis,
            thesis_validation=self._assess_thesis_claims(anova_results)
        )
```

**Data Extraction from Task 27**:
```python
def _extract_category_metrics(self, validation_results: Dict[str, Any]) -> Dict[str, List[float]]:
    """Extract performance metrics grouped by GAMP category from Task 27 results."""
    
    category_metrics = {
        "Category 3": [],
        "Category 4": [], 
        "Category 5": []
    }
    
    # Process fold results
    for fold_key, fold_result in validation_results.get("fold_results", {}).items():
        
        # Extract document-level results
        for doc_detail in fold_result.get("document_details", []):
            category = self._normalize_category_name(doc_detail.get("category", ""))
            confidence = doc_detail.get("confidence", 0.0)
            success = doc_detail.get("success", False)
            
            if category in category_metrics and success:
                category_metrics[category].append(confidence)
    
    # Remove empty categories
    return {k: v for k, v in category_metrics.items() if len(v) > 0}
```

#### 2. Enhanced Results Aggregation

**Extension of Existing ResultsAggregator**:
```python
# Modification to main/src/validation/framework/results_aggregator.py
async def _perform_statistical_tests(self, successful_folds: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced statistical tests including ANOVA analysis."""
    
    statistical_tests = {}
    
    # ✅ Existing tests (keep all current functionality)
    # ... existing normality tests, t-tests, etc.
    
    # ➕ NEW: ANOVA analysis for Task 28
    if hasattr(self, 'statistical_pipeline'):
        try:
            # Extract category-grouped data
            category_data = self._extract_category_performance_data(successful_folds)
            
            if len(category_data) >= 2:  # Need at least 2 categories for ANOVA
                anova_result = await self.statistical_pipeline.perform_anova(category_data)
                statistical_tests["anova_analysis"] = {
                    "f_statistic": anova_result.f_statistic,
                    "p_value": anova_result.p_value,
                    "effect_size": anova_result.effect_size,
                    "significant": anova_result.p_value < 0.05,
                    "post_hoc_tests": anova_result.post_hoc_results,
                    "thesis_validation": anova_result.p_value < 0.05
                }
                
        except Exception as e:
            self.logger.warning(f"ANOVA analysis failed: {e}")
    
    return statistical_tests
```

#### 3. Thesis Claims Validation

**Hypothesis Testing Framework**:
```python
def assess_thesis_claims(self, anova_results: ANOVAResult) -> ThesisValidationResult:
    """
    Assess specific thesis claims based on ANOVA results.
    Must achieve p < 0.05 for statistical significance.
    """
    
    claims_validation = {}
    
    # Claim 1: GAMP categories show different performance characteristics
    claims_validation["category_performance_differences"] = {
        "hypothesis": "H1: μ₃ ≠ μ₄ ≠ μ₅ (GAMP categories show different performance)",
        "statistical_test": "One-way ANOVA",
        "p_value": anova_results.p_value,
        "significant": anova_results.p_value < 0.05,
        "effect_size": anova_results.effect_size,
        "practical_significance": anova_results.effect_size["eta_squared"] > 0.06,  # Medium effect
        "conclusion": "SUPPORTED" if anova_results.p_value < 0.05 else "NOT SUPPORTED"
    }
    
    # Claim 2: Specific pairwise differences exist
    if anova_results.post_hoc_results:
        for comparison in anova_results.post_hoc_results.comparisons:
            claim_key = f"{comparison['group_1']}_vs_{comparison['group_2']}"
            claims_validation[claim_key] = {
                "hypothesis": f"H1: μ_{comparison['group_1']} ≠ μ_{comparison['group_2']}",
                "statistical_test": anova_results.post_hoc_results.test_name,
                "p_value": comparison["p_value"],
                "significant": comparison["significant"],
                "mean_difference": comparison["mean_diff"],
                "confidence_interval": comparison["confidence_interval"],
                "conclusion": "SIGNIFICANT DIFFERENCE" if comparison["significant"] else "NO SIGNIFICANT DIFFERENCE"
            }
    
    # Overall thesis validation
    overall_significance = any(claim["significant"] for claim in claims_validation.values())
    
    return ThesisValidationResult(
        claims_validation=claims_validation,
        overall_statistical_significance=overall_significance,
        minimum_p_value=min(claim.get("p_value", 1.0) for claim in claims_validation.values()),
        thesis_supported=overall_significance,
        regulatory_compliance=self._assess_regulatory_compliance(anova_results)
    )
```

### Library Requirements and Implementation

#### Core Statistical Libraries

**SciPy 1.16.0+** (ANOVA and Post-hoc):
```python
# Required imports
from scipy import stats
from scipy.stats import f_oneway, tukey_hsd, levene

# Key functions
- f_oneway(*groups): One-way ANOVA
- tukey_hsd(*groups, equal_var=True): Tukey HSD post-hoc test
- tukey_hsd(*groups, equal_var=False): Games-Howell post-hoc test  
- levene(*groups): Test homogeneity of variance assumption
```

**Statsmodels 0.14.0+** (Advanced ANOVA):
```python
# Alternative ANOVA implementation with more diagnostics
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# More detailed ANOVA with residual analysis
model = ols('performance ~ C(category)', data=df).fit()
anova_table = anova_lm(model, typ=2)  # Type II ANOVA
```

**Pingouin 0.5.0+** (User-friendly statistical tests):
```python
# Clean, pharmaceutical-friendly API
import pingouin as pg

# One-way ANOVA with effect size
anova_result = pg.anova(data=df, dv='performance', between='category')
# Includes eta-squared automatically

# Post-hoc tests  
posthoc_result = pg.pairwise_tukey(data=df, dv='performance', between='category')
```

#### Integration Libraries

**NumPy 1.24.0+**: Array operations and statistical calculations
**Pandas 2.0.0+**: Data manipulation and organization
**Matplotlib 3.7.0+**: Statistical visualization
**Seaborn 0.12.0+**: Statistical plotting (box plots, violin plots)

#### Implementation Priority

**Phase 1 - Core ANOVA Implementation**:
```python
# Extend existing StatisticalAnalyzer class
class EnhancedStatisticalAnalyzer(StatisticalAnalyzer):
    def one_way_anova(self, category_data: Dict[str, List[float]]) -> ANOVAResult
    def perform_post_hoc_tests(self, category_data: Dict[str, List[float]], anova_result: ANOVAResult) -> PostHocResult
    def calculate_anova_effect_sizes(self, category_data: Dict[str, List[float]]) -> Dict[str, float]
```

**Phase 2 - Task 27 Integration**:
```python
# New statistical analysis pipeline
class StatisticalAnalysisPipeline:
    def analyze_validation_results(self, validation_results: Dict[str, Any]) -> EnhancedStatisticalReport
    def extract_category_metrics(self, validation_results: Dict[str, Any]) -> Dict[str, List[float]]
    def assess_thesis_claims(self, anova_results: ANOVAResult) -> ThesisValidationResult
```

**Phase 3 - Results Integration**:
```python
# Enhance existing ResultsAggregator
# Add ANOVA results to statistical_tests section
# Integrate thesis validation conclusions
# Generate comprehensive pharmaceutical compliance report
```

### Implementation Gotchas

#### 1. Small Sample Size Handling
- **Challenge**: 17 documents ≈ 3-4 per fold, may violate ANOVA assumptions
- **Solution**: Bootstrap ANOVA for robust inference + assumption testing
- **Documentation**: Must clearly state limitations and confidence bounds

#### 2. Unequal Group Sizes
- **Challenge**: Folds may have different numbers of documents per category  
- **Solution**: Use Tukey-Kramer or Games-Howell tests for unequal group sizes
- **Validation**: Test homogeneity of variance assumption with Levene's test

#### 3. Multiple Testing Corrections
- **Challenge**: Multiple pairwise comparisons inflate Type I error rate
- **Solution**: Tukey HSD naturally controls family-wise error rate
- **Documentation**: Report both uncorrected and corrected p-values

#### 4. Integration with Existing Code
- **Challenge**: StatisticalAnalyzer has extensive existing functionality
- **Solution**: Extend rather than replace - maintain backwards compatibility
- **Testing**: Ensure existing comprehensive_analysis() still works

#### 5. Real vs Mock Data
- **Challenge**: Must work with actual Task 27 validation data
- **Solution**: Flexible data extraction that handles real validation output format  
- **Compliance**: NO FALLBACK VALUES - explicit handling of missing data only

### Regulatory Compliance

#### GAMP-5 Statistical Validation
- **Predefined Acceptance Criteria**: Define statistical thresholds before analysis
- **Complete Audit Trail**: Log all statistical decisions and their justification
- **Reproducibility**: Same input data must produce identical results
- **Assumption Validation**: Test and document all statistical assumptions

#### FDA/ICH Statistical Requirements  
- **Effect Size Reporting**: Clinical significance alongside statistical significance
- **Confidence Intervals**: Report precision of estimates, not just p-values
- **Multiple Comparison Handling**: Appropriate control of false positive rates
- **Small Sample Limitations**: Acknowledge and address analysis limitations

---

**Implementation Priority**: High (Critical for thesis validation)
**Integration Dependencies**: Task 27 validation framework ✅
**Statistical Significance Target**: p < 0.05 for thesis claims
**Compliance**: GAMP-5 pharmaceutical validation standards