# Data Collection Requirements for Complete Thesis Evidence

**Date**: 2025-08-19  
**Purpose**: Define exactly what data needs to be collected for comprehensive statistical analysis  
**Current Status**: 18 test suites analyzed, revealing critical data gaps

## Executive Summary

Our analysis of 18 test suites reveals we can extract **basic quality metrics** but are missing **critical performance and cost data**. The real ALCOA+ score is **4.88/10** (not 8.06 or 9.78 as claimed), and verification method diversity completely failed (100% visual_inspection).

---

## 1. Currently Collectible Data ✅

### From Test Suite JSON Files
```python
available_metrics = {
    "structural": {
        "test_count": int,              # ✅ 6.67 avg
        "steps_per_test": float,        # ✅ 2.5 avg
        "data_points": int,             # ✅ 4.2 per test
        "prerequisites": int,           # ✅ 2.4 per test
        "estimated_duration": int       # ✅ 315 min total
    },
    
    "quality": {
        "acceptance_criteria_specificity": float,  # ✅ 57.9%
        "verification_method_diversity": float,    # ✅ 0% (FAILED)
        "action_verb_variety": float,             # ✅ 32%
        "technical_term_density": float,          # ✅ 11.15%
        "measurement_precision": float            # ✅ 7.84%
    },
    
    "compliance": {
        "alcoa_field_presence": dict,    # ✅ Measured per field
        "alcoa_overall_score": float,    # ✅ 4.88/10 actual
        "regulatory_references": int,     # ✅ CFR citations
        "risk_categorization": dict      # ✅ High/Medium/Low
    },
    
    "consistency": {
        "id_pattern_uniformity": bool,   # ✅ 94% consistent
        "field_completeness": float,     # ✅ 72% complete
        "format_validity": bool          # ✅ 100% valid JSON
    }
}
```

---

## 2. Critical Missing Data ❌

### 2.1 Performance Metrics (REQUIRED)
```python
missing_performance_data = {
    "generation_timing": {
        "start_timestamp": datetime,     # When generation began
        "end_timestamp": datetime,       # When generation completed
        "time_to_first_test": float,    # Latency measurement
        "inter_test_delays": list,      # Delays between tests
        "total_elapsed_seconds": float   # End-to-end time
    },
    
    "api_metrics": {
        "request_count": int,            # Number of API calls
        "retry_attempts": int,           # Failed attempts
        "error_codes": list,            # API error responses
        "rate_limit_hits": int          # Throttling events
    }
}
```

### 2.2 Cost Metrics (CRITICAL)
```python
missing_cost_data = {
    "token_usage": {
        "prompt_tokens": int,            # Input token count
        "completion_tokens": int,        # Output token count
        "total_tokens": int,            # Sum of all tokens
        "token_price_per_1k": float    # Actual pricing
    },
    
    "cost_calculation": {
        "prompt_cost": float,           # Input cost
        "completion_cost": float,       # Output cost
        "total_api_cost": float,       # Total per generation
        "cost_per_test": float         # Averaged per test
    }
}
```

### 2.3 Human Validation Metrics
```python
missing_human_metrics = {
    "review_process": {
        "review_start_time": datetime,
        "review_end_time": datetime,
        "total_review_minutes": float,
        "corrections_made": int,
        "acceptance_decision": bool
    },
    
    "quality_assessment": {
        "expert_alcoa_score": float,    # Human-assigned score
        "identified_issues": list,       # Problems found
        "improvement_suggestions": list  # Recommendations
    }
}
```

---

## 3. Data Collection Implementation Plan

### 3.1 Minimal Viable Instrumentation
```python
# Add to test generation workflow
def collect_minimal_metrics(suite_generation):
    metrics = {
        "metadata": {
            "suite_id": suite_generation.id,
            "timestamp": datetime.now(),
            "document_source": suite_generation.source,
            "model_version": "deepseek/deepseek-chat"
        },
        
        "performance": {
            "start_time": time.time(),
            # ... generation happens ...
            "end_time": time.time(),
            "duration_seconds": end_time - start_time
        },
        
        "tokens": {
            # Hook into API response
            "usage": response.usage.dict() if hasattr(response, 'usage') else {}
        },
        
        "quality": {
            # Extract from generated suite
            "test_count": len(suite.test_cases),
            "alcoa_score": calculate_alcoa_score(suite),
            "specificity": calculate_specificity(suite)
        }
    }
    
    # Save metrics alongside suite
    metrics_file = f"metrics_{suite_id}.json"
    save_json(metrics, metrics_file)
    
    return metrics
```

### 3.2 Comprehensive Instrumentation
```python
# Enhanced data collection
class ComprehensiveMetricsCollector:
    def __init__(self):
        self.metrics = {
            "session": {},
            "performance": {},
            "quality": {},
            "cost": {},
            "errors": []
        }
    
    def start_generation(self, document):
        self.metrics["session"] = {
            "document": document,
            "start_time": datetime.now(),
            "model": self.get_model_config()
        }
    
    def log_api_call(self, request, response):
        self.metrics["performance"]["api_calls"] = \
            self.metrics["performance"].get("api_calls", 0) + 1
        
        if hasattr(response, 'usage'):
            tokens = self.metrics["cost"].get("tokens", {"prompt": 0, "completion": 0})
            tokens["prompt"] += response.usage.prompt_tokens
            tokens["completion"] += response.usage.completion_tokens
            self.metrics["cost"]["tokens"] = tokens
    
    def log_error(self, error):
        self.metrics["errors"].append({
            "timestamp": datetime.now(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        })
    
    def calculate_costs(self):
        tokens = self.metrics["cost"].get("tokens", {})
        # DeepSeek pricing: $0.14/1M input, $0.28/1M output
        prompt_cost = tokens.get("prompt", 0) * 0.00000014
        completion_cost = tokens.get("completion", 0) * 0.00000028
        self.metrics["cost"]["total_cost"] = prompt_cost + completion_cost
    
    def finalize(self, generated_suite):
        self.metrics["session"]["end_time"] = datetime.now()
        self.metrics["session"]["duration"] = (
            self.metrics["session"]["end_time"] - 
            self.metrics["session"]["start_time"]
        ).total_seconds()
        
        self.calculate_costs()
        self.metrics["quality"] = self.analyze_suite_quality(generated_suite)
        
        return self.metrics
```

---

## 4. For Complete 17-Document Analysis

### 4.1 Required Data Points Per Document
```yaml
per_document_metrics:
  identification:
    - document_name: str
    - document_type: str  # URS, SRS, etc.
    - gamp_category: int
    - complexity_score: float
  
  generation:
    - start_timestamp: datetime
    - end_timestamp: datetime
    - total_seconds: float
    - api_calls: int
    - retry_count: int
  
  tokens:
    - input_tokens: int
    - output_tokens: int
    - total_tokens: int
    - cost_usd: float
  
  quality:
    - tests_generated: int
    - alcoa_score: float  # Real score
    - specificity_score: float
    - verification_diversity: float
    - error_count: int
  
  validation:
    - human_review_time: float
    - corrections_required: int
    - accepted: bool
    - expert_notes: str
```

### 4.2 Statistical Power Requirements

For statistically valid conclusions with 17 documents:

```python
statistical_requirements = {
    "minimum_metrics": {
        "generation_time": True,      # Can detect large effects
        "token_count": True,          # Can detect large effects  
        "test_count": True,           # Can detect medium effects
        "quality_score": True,        # Can detect medium effects
        "cost_per_doc": True         # Can detect large effects
    },
    
    "statistical_tests_possible": {
        "descriptive": True,          # Mean, median, stdev
        "correlation": True,          # Between 2 variables
        "regression": False,          # Need n>30
        "anova": False,              # Need n>30
        "significance": "Limited"     # Only for large effects
    },
    
    "confidence_intervals": {
        "achievable": "Wide",         # ±30-40% margins
        "bootstrap": "Possible",      # But limited power
        "parametric": "Risky"        # Normality assumptions
    }
}
```

---

## 5. Implementation Checklist

### Before Running 17-Document Analysis:

- [ ] **Implement token counting** in generation workflow
- [ ] **Add timestamp logging** at start/end of generation
- [ ] **Create metrics collection class** 
- [ ] **Hook into API responses** for usage data
- [ ] **Set up error logging** with full details
- [ ] **Create human review timer** 
- [ ] **Define expert scoring rubric**
- [ ] **Set up metrics database/storage**
- [ ] **Create real-time monitoring dashboard**
- [ ] **Implement cost calculation logic**

### During Analysis:

- [ ] **Log every API call**
- [ ] **Capture all errors with context**
- [ ] **Time each phase of generation**
- [ ] **Count tokens for each request**
- [ ] **Track retry attempts**
- [ ] **Record human review time**
- [ ] **Document corrections made**
- [ ] **Save intermediate states**

### After Analysis:

- [ ] **Calculate real costs** (not estimates)
- [ ] **Compute actual ALCOA+ scores** (not inflated)
- [ ] **Generate honest visualizations**
- [ ] **Document all limitations**
- [ ] **Report actual sample size**
- [ ] **Acknowledge statistical power limits**

---

## 6. Expected Outcomes with Proper Instrumentation

### What We'll Be Able to Claim:
- Exact generation time per document
- Precise cost per test suite
- Real ALCOA+ compliance scores
- Actual token usage patterns
- True error rates and types
- Validated quality metrics

### What We Still Won't Be Able to Claim:
- Statistical significance (n=17 too small)
- Generalizability beyond tested documents
- Performance under different conditions
- Long-term reliability
- Scalability projections

---

## 7. Recommendations

1. **Priority 1**: Implement token counting immediately
2. **Priority 2**: Add comprehensive timestamp logging  
3. **Priority 3**: Create metrics collection infrastructure
4. **Priority 4**: Set up human validation tracking
5. **Priority 5**: Build real-time monitoring

**Critical**: Do NOT proceed with 17-document analysis until at least Priorities 1-3 are implemented. Without this data, the thesis evidence will remain incomplete and claims unsubstantiated.

---

**Data Integrity Commitment**: All metrics must be collected directly from system operations with no estimation, interpolation, or inflation. Only measured values should be reported.