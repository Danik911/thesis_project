# GAMP-5 Supplier Assessment: DeepSeek V3

## Supplier Information
- **Supplier Name**: DeepSeek
- **Product**: DeepSeek-V3 Large Language Model
- **Version**: V3 (671B Mixture-of-Experts)
- **Access Method**: OpenRouter API
- **Assessment Date**: August 2025

## Risk Assessment
- **Risk Level**: Low to Medium
- **Criticality**: High (core test generation)
- **GxP Impact**: Direct (generates validation test scripts)

## Validation Evidence
1. **Performance Metrics**:
   - Test generation accuracy: 88.2% requirement coverage
   - GAMP-5 categorization: 100% accuracy
   - Processing time: 5.57 minutes per document

2. **Quality Controls**:
   - Temperature setting: 0.1 (deterministic outputs)
   - Max tokens: 30,000 (comprehensive responses)
   - Structured output: JSON with Pydantic validation

3. **Audit Trail**:
   - All API calls logged
   - Input/output captured
   - Phoenix observability traces

## Approval
- **Status**: Approved for pharmaceutical test generation
- **Conditions**: VALIDATION_MODE controls for testing
- **Review Period**: Annual