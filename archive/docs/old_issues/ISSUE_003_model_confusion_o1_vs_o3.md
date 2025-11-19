# Issue #003: Model Name Confusion (o1 vs o3)

**Status**: RESOLVED  
**Severity**: Critical  
**First Observed**: August 6, 2025  
**Components Affected**: OQ Test Generator, model configuration

## Problem Description

Significant confusion about which models to use for OQ test generation:
- Initial code mixed o1-mini and o3-mini models
- o1 models don't exist in our setup
- ONLY o3-mini should be used for ALL OQ generation
- Other agents use gpt-4.1-mini-2025-04-14

## Root Cause Analysis

1. **Historical confusion**: OpenAI has o1 models, but we use o3-mini
2. **Mixed configuration**: Different categories mapped to different models
3. **Documentation inconsistency**: Some docs mentioned o1, others o3
4. **No validation**: System didn't reject invalid model names

## Evidence

```python
# WRONG (initial configuration):
self.model_mapping = {
    GAMPCategory.CATEGORY_1: "gpt-4o-mini",  # Wrong model name
    GAMPCategory.CATEGORY_3: "gpt-4o-mini",  # Wrong model name
    GAMPCategory.CATEGORY_4: "o1-mini",      # o1 doesn't exist!
    GAMPCategory.CATEGORY_5: "o3-mini"       # Only this was correct
}

# CORRECT (fixed configuration):
self.model_mapping = {
    GAMPCategory.CATEGORY_1: "o3-mini",
    GAMPCategory.CATEGORY_3: "o3-mini", 
    GAMPCategory.CATEGORY_4: "o3-mini",
    GAMPCategory.CATEGORY_5: "o3-mini"  # ALL use o3-mini
}
```

## Impact

- **Generation Failures**: o1 models returning empty responses
- **Confusion**: Developers unsure which model to use
- **Debugging Time**: Hours spent debugging non-existent model issues
- **Inconsistent Behavior**: Different categories behaving differently

## Solution Applied

### Configuration Standardization

```python
# In generator_v2.py
class OQTestGeneratorV2:
    def __init__(self):
        # Model selection - o3-mini for ALL OQ test generation
        self.model_mapping = {
            GAMPCategory.CATEGORY_1: "o3-mini",
            GAMPCategory.CATEGORY_3: "o3-mini", 
            GAMPCategory.CATEGORY_4: "o3-mini",
            GAMPCategory.CATEGORY_5: "o3-mini"  # o3 for ALL categories
        }
        
        # o3 models REQUIRE reasoning_effort parameter
        self.reasoning_effort_mapping = {
            GAMPCategory.CATEGORY_1: "low",
            GAMPCategory.CATEGORY_3: "medium",
            GAMPCategory.CATEGORY_4: "medium",
            GAMPCategory.CATEGORY_5: "high"
        }
```

### Code Updates

All references to o1 changed to o3:
- Function names: `_generate_with_o1_model` → `_generate_with_o3_model`
- Prompts: `_build_o1_prompt` → `_build_o3_prompt`
- Comments and documentation updated
- Error messages updated

## Verification

```python
# Test that only o3 is used
def test_model_configuration():
    generator = OQTestGeneratorV2()
    
    for category in GAMPCategory:
        model = generator.model_mapping[category]
        assert model == "o3-mini", f"Category {category} should use o3-mini, not {model}"
    
    print("✅ All categories correctly use o3-mini")
```

## Prevention

1. **Model Validation**:
```python
VALID_MODELS = {
    "o3-mini",  # For OQ generation
    "gpt-4.1-mini-2025-04-14",  # For other agents
}

def validate_model(model_name):
    if model_name not in VALID_MODELS:
        raise ValueError(
            f"Invalid model: {model_name}\n"
            f"Valid models are: {', '.join(VALID_MODELS)}\n"
            f"Note: We use o3-mini, NOT o1 models!"
        )
```

2. **Configuration Testing**:
```python
# Add to test suite
def test_all_models_valid():
    """Ensure all configured models are valid."""
    generator = OQTestGeneratorV2()
    for category, model in generator.model_mapping.items():
        validate_model(model)
```

3. **Clear Documentation**:
```markdown
# Model Configuration Guide

## OQ Test Generation
**ALWAYS use o3-mini for ALL categories**
- Do NOT use o1 models (they don't exist in our setup)
- Do NOT use gpt-4o-mini (wrong name format)
- Do NOT mix models for different categories

## Other Agents
**Use gpt-4.1-mini-2025-04-14**
- Categorization Agent
- Context Provider Agent
- SME Agent
- Research Agent
```

## Lessons Learned

1. **Consistency is Key**: Use same model for all similar operations
2. **Validate Early**: Check model names at configuration time
3. **Clear Naming**: Avoid similar names that cause confusion
4. **Document Clearly**: State explicitly what NOT to use

## Related Issues

- o3 model configuration (reasoning_effort parameter)
- Progressive generation logic
- Model timeout configurations

## References

- OpenAI model documentation
- o3 model requirements
- Configuration file: `main/src/agents/oq_generator/generator_v2.py`

## Resolution Status

✅ **RESOLVED**: All OQ generation now uses o3-mini exclusively. Code updated, documentation clarified, and working successfully in production.