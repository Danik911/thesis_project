# Task 26: Cross-Validation Dataset Context

## Research and Context (by context-collector)

### Dataset Analysis - Current State

**Dataset Structure Confirmed:**
- **17 URS documents** total (exactly as expected)
- **442 total requirements** across all documents
- **5 Category 3**, **5 Category 4**, **5 Category 5**, **2 Ambiguous**
- **Complexity range: 0.18-0.90** with mean 0.504 ± 0.235
- **Cross-validation already implemented** in `datasets/cross_validation/fold_assignments.json`

**File Locations:**
- `datasets/urs_corpus/category_3/` - URS-001, URS-006, URS-007, URS-008, URS-009
- `datasets/urs_corpus/category_4/` - URS-002, URS-010, URS-011, URS-012, URS-013  
- `datasets/urs_corpus/category_5/` - URS-003, URS-014, URS-015, URS-016, URS-017
- `datasets/urs_corpus/ambiguous/` - URS-004 (3/4), URS-005 (4/5)

**Existing Implementation:**
- `datasets/prepare_cross_validation.py` - Complete stratified k-fold implementation
- `datasets/metrics/complexity_calculator.py` - Complexity scoring system
- `datasets/cross_validation/fold_assignments.json` - Pre-generated 5-fold splits

### Statistical Validation Requirements for Small Pharmaceutical Datasets

**Critical Finding:** Studies with sample sizes <1000 consistently show optimistically biased performance estimates with standard k-fold cross-validation. Our 17-document dataset requires specialized approaches:

**1. Stratified K-Fold Necessity:**
- **Standard k-fold bias**: Produces strongly biased performance estimates with small samples
- **Stratified advantage**: Maintains class proportion across folds, essential for imbalanced pharmaceutical data
- **Nested cross-validation**: Superior for controlling feature selection bias (recommended for final validation)

**2. Multi-Criteria Stratification:**
- **GAMP category stratification**: Essential for regulatory compliance
- **Complexity score stratification**: Ensures balanced difficulty distribution
- **Implementation challenge**: Scikit-learn StratifiedKFold supports single criterion only
- **Solution**: Combined stratification labels or custom splitter implementation

**3. Small Sample Statistical Considerations:**
- **Minimum fold size**: Each category needs adequate representation in each fold
- **Bootstrap confidence intervals**: Required for performance uncertainty quantification
- **Repeated cross-validation**: Multiple runs with different seeds for stability assessment
- **Power analysis**: 17 documents requires careful interpretation of performance differences

### LlamaIndex 0.12.0+ Workflow Integration Patterns

**Multi-Agent Cross-Validation Architecture:**

**1. Event-Driven Workflow Components:**
```python
class CrossValidationEvent(Event):
    fold_id: str
    train_documents: List[URSDocument]
    test_documents: List[URSDocument]

class ValidationResultEvent(Event):
    fold_id: str
    performance_metrics: Dict[str, float]
    predictions: List[Dict]
```

**2. Workflow Step Pattern:**
```python
class CrossValidationWorkflow(Workflow):
    @step
    async def prepare_folds(self, ctx: Context, ev: StartEvent) -> CrossValidationEvent:
        # Load fold assignments and create events for each fold
        
    @step  
    async def validate_fold(self, ctx: Context, ev: CrossValidationEvent) -> ValidationResultEvent:
        # Train/test on specific fold
        
    @step
    async def aggregate_results(self, ctx: Context, ev: ValidationResultEvent) -> StopEvent:
        # Collect and analyze results across all folds
```

**3. Multi-Agent Coordination:**
- **FoldExecutorAgent**: Handles individual fold training/testing
- **MetricsCollectorAgent**: Aggregates performance across folds
- **ComplianceValidatorAgent**: Ensures GAMP-5 validation requirements
- **ResultsAnalyzerAgent**: Statistical analysis and reporting

**4. Context Management:**
```python
# Store fold assignments in workflow context
await ctx.store.set("fold_assignments", fold_config)
await ctx.store.set("performance_results", [])

# Parallel fold execution with collect pattern
evs = ctx.collect_events(ev, [ValidationResultEvent] * num_folds)
```

### Implementation Best Practices

**1. Scikit-Learn Integration:**
```python
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, roc_auc_score

# Custom multi-criteria stratification
stratify_labels = [f"{doc.normalized_category}_{doc.complexity_level}" 
                  for doc in documents]

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, stratify_labels)):
    # Execute fold validation
```

**2. Nested Cross-Validation for Unbiased Estimates:**
```python
# Outer loop: Performance estimation
# Inner loop: Hyperparameter optimization + feature selection
from sklearn.model_selection import cross_val_score, GridSearchCV

outer_cv = StratifiedKFold(n_splits=5, random_state=42)
inner_cv = StratifiedKFold(n_splits=3, random_state=42)

scores = cross_val_score(
    GridSearchCV(estimator, param_grid, cv=inner_cv),
    X, y, cv=outer_cv, scoring='roc_auc'
)
```

**3. Pharmaceutical Compliance Integration:**
```python
class GAMP5ValidationMetrics:
    """Pharmaceutical-specific validation metrics"""
    
    def calculate_category_performance(self, predictions, true_labels, gamp_categories):
        # Per-category performance analysis
        
    def generate_compliance_report(self, cv_results):
        # ALCOA+ compliance documentation
        
    def validate_audit_trail(self, fold_assignments, random_states):
        # 21 CFR Part 11 traceability requirements
```

### Implementation Gotchas

**1. Data Leakage Prevention:**
```python
# WRONG: Feature selection on full dataset
selector.fit(X, y)  # Uses test data!
X_selected = selector.transform(X)

# CORRECT: Feature selection within each fold
for train_idx, test_idx in cv.split(X, y):
    X_train, X_test = X[train_idx], X[test_idx]
    selector.fit(X_train, y_train)  # Train data only
    X_train_selected = selector.transform(X_train)
    X_test_selected = selector.transform(X_test)
```

**2. Stratification Edge Cases:**
```python
# Check minimum samples per stratum
from collections import Counter
strata_counts = Counter(stratify_labels)
min_samples_per_stratum = min(strata_counts.values())

if min_samples_per_stratum < n_splits:
    raise ValueError(f"Insufficient samples for {n_splits}-fold CV")
```

**3. Random State Management:**
```python
# Ensure reproducibility across runs
BASE_RANDOM_STATE = 42
fold_random_states = [BASE_RANDOM_STATE + i for i in range(n_splits)]

# Document for regulatory compliance
cv_metadata = {
    "random_states": fold_random_states,
    "stratification_method": "GAMP_category_complexity",
    "validation_timestamp": datetime.now().isoformat()
}
```

### Regulatory Considerations

**FDA GMLP Compliance Requirements:**
1. **Representative Datasets**: Stratification must ensure demographic and clinical representativeness
2. **Independence**: Strict train/test separation with documented procedures
3. **Transparency**: Clear documentation of stratification logic and fold assignments
4. **Monitoring**: Baseline performance establishment for post-deployment monitoring

**GAMP-5 Validation Framework:**
- **Category-specific validation**: Different validation rigor based on GAMP categorization
- **Risk-based approach**: Higher-risk categories require more stringent validation
- **Audit trail**: Complete documentation of validation procedures and results
- **Change control**: Version-controlled cross-validation configurations

### Performance Optimization

**1. Computational Efficiency:**
- **Parallel fold execution**: Use `n_jobs=-1` in scikit-learn cross-validation
- **Memory optimization**: Process folds sequentially for large datasets
- **Caching**: Store preprocessed features to avoid repeated computation

**2. LlamaIndex Workflow Optimization:**
- **Async execution**: Leverage async/await for non-blocking operations  
- **Context sharing**: Minimize data serialization between workflow steps
- **Event batching**: Group related events for efficient processing

### Integration with Existing System

**File Dependencies:**
- `datasets/cross_validation/fold_assignments.json` - Pre-generated folds (ready to use)
- `datasets/metrics/complexity_calculator.py` - Complexity scoring (working)
- `datasets/prepare_cross_validation.py` - Fold generation script (complete)
- `main/src/core/unified_workflow.py` - Master workflow integration point

**Next Steps for Implementation:**
1. **Load existing fold assignments** from JSON file
2. **Integrate with LlamaIndex workflow** using event-driven pattern
3. **Implement nested CV** for unbiased performance estimates
4. **Add pharmaceutical compliance** metrics and documentation
5. **Enable parallel fold execution** for efficiency

### Recommended Libraries and Versions

**Core Dependencies:**
- `scikit-learn>=1.4.0` - StratifiedKFold, performance metrics
- `numpy>=1.24.0` - Array operations, statistical functions
- `pandas>=2.0.0` - Data manipulation, results aggregation
- `llamaindex>=0.12.0` - Workflow orchestration, multi-agent coordination

**Statistical Analysis:**
- `scipy>=1.11.0` - Statistical tests, confidence intervals
- `statsmodels>=0.14.0` - Advanced statistical modeling
- `seaborn>=0.12.0` - Visualization for validation results

**Pharmaceutical Compliance:**
- `pydantic>=2.0.0` - Data validation, type safety
- `jsonschema>=4.19.0` - Configuration validation
- `cryptography>=41.0.0` - Digital signatures for audit trails

This context provides the complete foundation for implementing Task 26 with proper statistical validation, regulatory compliance, and technical implementation guidance for pharmaceutical cross-validation systems.