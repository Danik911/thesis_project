# URS Cross-Validation Dataset

## Overview

This dataset contains 30 User Requirements Specifications (URS) documents designed for k-fold cross-validation testing of LLM-driven pharmaceutical test generation systems. The dataset supports GAMP-5 compliance validation and provides baseline metrics for evaluating automated test generation performance.

**Dataset Version**: 1.1  
**Creation Date**: August 2025  
**GAMP-5 Compliance**: Full compliance with pharmaceutical validation standards  
**Intended Use**: Cross-validation testing of automated OQ test generation systems  

## Dataset Composition

### Document Distribution

| GAMP Category | Count | Complexity Levels | Domains Covered |
|---------------|-------|-------------------|-----------------|
| **Category 3** (Standard Software) | 7 | Low | Environmental Control, Warehouse Management, Document Management, Laboratory Operations, Quality Analytics, Quality Management |
| **Category 4** (Configured Products) | 9 | Medium, Medium-High, High | Quality Control, Enterprise Management, Quality Assurance, Supply Chain, Process Control, Stability Management, Serialization, Clinical Operations |
| **Category 5** (Custom Applications) | 7 | High, Very High | Manufacturing Operations, Process Analytics, Regulatory Affairs, Supply Chain Analytics, R&D/Computational Chemistry |
| **Ambiguous** (3/4 or 4/5) | 6 | Medium, High | Analytical Chemistry, Clinical Operations, Precision Medicine / Cell & Gene Therapy |
| **Special Cases** (Migration/Legacy) | 1 | High | Enterprise IT / Quality Systems |
| **Total** | **30** | **Varied** | **15+ Domains** |

### Document Sources

- **5 documents**: Extracted and enhanced from existing test data (`main/tests/test_data/gamp5_test_data/testing_data.md`)
- **25 documents**: Newly authored synthetic URS documents with pharmaceutical domain expertise
- **All documents**: Anonymized, consistent formatting, complete requirement coverage

## Directory Structure

```
datasets/
├── DATASET_README.md                 # This file
├── urs_corpus/                       # Original URS document collection (n=17)
│   ├── category_3/
│   │   ├── URS-001.md               # Environmental Monitoring System
│   │   ├── URS-006.md               # Standard Inventory Management
│   │   ├── URS-007.md               # Basic Temperature Monitoring
│   │   ├── URS-008.md               # Standard Document Control
│   │   └── URS-009.md               # Basic Laboratory Equipment Integration
│   ├── category_4/
│   │   ├── URS-002.md               # LIMS
│   │   ├── URS-010.md               # Configured ERP System
│   │   ├── URS-011.md               # Configured Quality Management
│   │   ├── URS-012.md               # Configured Warehouse Management
│   │   └── URS-013.md               # Configured Process Control System
│   ├── category_5/
│   │   ├── URS-003.md               # Manufacturing Execution System
│   │   ├── URS-014.md               # Custom Batch Release System
│   │   ├── URS-015.md               # Custom PAT System
│   │   ├── URS-016.md               # Custom Regulatory Submission Platform
│   │   └── URS-017.md               # Custom Supply Chain Optimization
│   └── ambiguous/
│       ├── URS-004.md               # Chromatography Data System (3/4)
│       └── URS-005.md               # Clinical Trial Management System (4/5)
├── urs_corpus_v2/                   # Expanded corpus (n=8)
│   ├── category_3/
│   │   ├── URS-020.md               # SPC Dashboard (QA Labs)
│   │   └── URS-021.md               # Document Acknowledgment Tracker
│   ├── category_4/
│   │   ├── URS-022.md               # Configured Deviation Management
│   │   ├── URS-023.md               # Configured Stability Study Manager
│   │   └── URS-024.md               # Configured Serialization Aggregation
│   ├── category_5/
│   │   └── URS-025.md               # Custom Batch Release Orchestrator
│   └── ambiguous/
│       ├── URS-018.md               # Chromatography Sample Scheduling (3/4)
│       └── URS-019.md               # eTMF Index Harmonization (4/5)
├── corpus_3/                        # Latest additions (n=5)
│   ├── category_4/
│   │   └── URS-027.md               # Clinical Trial Management System (CTMS)
│   ├── category_5/
│   │   └── URS-029.md               # Novel Drug Discovery AI System
│   ├── ambiguous/
│   │   ├── URS-026.md               # Pharmaceutical Data Analytics Platform (3/4)
│   │   └── URS-028.md               # Personalized Medicine Orchestration (4/5)
│   └── special_cases/
│       └── URS-030.md               # Legacy System Migration (Mainframe→Cloud)
├── metrics/
│   └── complexity_calculator.py     # Metrics calculation module
├── baselines/
│   └── timing_protocol.md           # Manual timing methodology
└── cross_validation/
    └── fold_assignments.json        # 5-fold stratified assignments
```

## Document Format and Structure

### Standard URS Template

Each URS document follows a consistent structure:

```markdown
# URS-XXX: [System Name]
**GAMP Category**: [3/4/5/Ambiguous]
**System Type**: [Brief technical description]
**Domain**: [Pharmaceutical domain area]
**Complexity Level**: [Low/Medium/Medium-High/High/Very High]

## 1. Introduction
[System context and purpose]

## 2. Functional Requirements
[12-38 functional requirements with URS-XXX-### IDs]

## 3. Regulatory Requirements
[5-12 regulatory and compliance requirements]

## 4. Performance Requirements
[6-15 performance and non-functional specifications]

## 5. Integration Requirements
[Integration and interface specifications]

## 6. Technical Architecture Requirements (Category 5 only)
[Technical implementation requirements for custom systems]
```

### Requirement ID Format

- **Functional**: `URS-[SYSTEM]-001` to `URS-[SYSTEM]-050`
- **Regulatory**: Continuation of functional sequence
- **Performance**: Continuation of functional sequence
- **Integration**: Continuation of functional sequence
- **Technical**: Continuation of functional sequence (Category 5 only)

### GAMP Category Indicators

**Category 3 (Standard Software)**:
- "vendor-supplied software without modification"
- "standard reports provided by vendor"
- "vendor's built-in functionality"
- "commercial off-the-shelf"

**Category 4 (Configured Products)**:
- "configure workflows using vendor's configuration tools"
- "implement custom business rules using vendor's scripting"
- "configured templates and parameters"
- "vendor's standard reporting engine with configured templates"

**Category 5 (Custom Applications)**:
- "custom-developed", "proprietary algorithms"
- "develop custom interfaces/APIs"
- "bespoke", "proprietary data structures"
- "custom mobile application", "proprietary analytics"

## Complexity Metrics

### Calculated Metrics

The `complexity_calculator.py` module computes the following metrics for each URS:

1. **Requirement Counts**
   - Functional requirements: 9-35 per document
   - Performance requirements: 3-16 per document  
   - Regulatory requirements: 3-12 per document
   - Integration requirements: 2-8 per document
   - Total requirements: 12-40 per document

2. **Readability Scores**
   - Flesch-Kincaid Grade Level for technical complexity
   - Average sentence length and syllable complexity
   - Technical vocabulary density

3. **Integration Complexity**
   - Integration keyword density
   - External system dependencies
   - Interface complexity indicators

4. **Dependency Density**
   - Cross-reference frequency within documents
   - Requirement interdependency mapping
   - Traceability link complexity

5. **Ambiguity Rate**
   - Ambiguous keyword frequency ("TBD", "should", "enhanced")
   - Specification clarity assessment
   - Implementation uncertainty indicators

6. **Custom Development Indicators**
   - Custom/proprietary keyword frequency
   - Development complexity markers
   - Implementation effort indicators

7. **Composite Complexity Score**
   - Weighted combination of all metrics (0.0-1.0 scale)
   - Pharmaceutical industry calibration
   - GAMP category correlation validation

### Complexity Distribution

| Complexity Level | Score Range | Document Count | GAMP Categories |
|-------------------|-------------|----------------|-----------------|
| **Low** | 0.0-0.3 | 5 | Category 3 |
| **Medium** | 0.3-0.5 | 4 | Category 4, Ambiguous |
| **Medium-High** | 0.5-0.7 | 2 | Category 4 |
| **High** | 0.7-0.9 | 4 | Category 4, Category 5, Ambiguous |
| **Very High** | 0.9-1.0 | 3 | Category 5 |

## Manual Baseline Measurements

### Baseline Timing Protocol

The manual baseline follows standardized procedures documented in `baselines/timing_protocol.md`:

**Target Average**: 40 hours per URS document
**Activities Tracked**:
- Requirements Analysis: 8-12 hours
- Test Case Design: 20-25 hours  
- Traceability Matrix: 3-5 hours
- Documentation: 6-8 hours
- Review/QA: 3-5 hours

**Deliverables Required**:
- Minimum 20 test cases per URS
- Complete requirements traceability matrix
- Test execution procedures
- Quality assessment report

**Quality Metrics**:
- Requirement coverage: 100% target
- Test case clarity and specificity
- Traceability completeness
- Regulatory compliance alignment

### Reviewer Qualifications

- **Junior** (3-5 years): Basic pharmaceutical testing experience
- **Senior** (5-10 years): Extensive URS analysis experience  
- **Expert** (10+ years): Lead validation project experience

## Cross-Validation Configuration

### 5-Fold Stratified Split

The dataset uses stratified k-fold cross-validation with the following characteristics:

**Stratification Criteria**:
- GAMP category balance across folds
- Complexity level distribution
- Domain diversity maintenance

**Fold Configuration**:
- **5 folds** total
- **24 training documents** per fold (80%)
- **6 test documents** per fold (20%)
- **Balanced representation** of all GAMP categories and special cases

**Validation Checks**:
- No document appears in multiple test sets
- Each document appears exactly once as test data
- GAMP category distribution maintained across folds
- Complexity levels balanced within constraints

### Cross-Validation Usage

```python
# Load fold assignments
import json
with open('cross_validation/fold_assignments.json', 'r') as f:
    folds = json.load(f)

# Access specific fold
fold_1 = folds['folds']['fold_1']
train_docs = fold_1['train_documents']
test_docs = fold_1['test_documents']

# Validate stratification
for fold_id, fold_data in folds['folds'].items():
    print(f"{fold_id}: Train={fold_data['train_count']}, Test={fold_data['test_count']}")
```

## Data Quality Assurance

### Content Validation

**Completeness Checks**:
- All required sections present in each URS
- Requirement counts within target ranges (12-40 per document)
- GAMP category alignment validated
- Metadata consistency verified

**Quality Metrics**:
- Pharmaceutical domain accuracy
- Technical specification completeness
- Regulatory requirement coverage
- Integration specification adequacy

**Anonymization Standards**:
- No real company or product names
- Generic pharmaceutical terminology
- Consistent naming conventions
- Privacy-compliant content

### Statistical Validation

**Distribution Analysis**:
- Requirement count distributions
- Complexity score distributions  
- GAMP category balance verification
- Domain coverage assessment

**Correlation Analysis**:
- Complexity vs. GAMP category alignment
- Requirement count vs. complexity correlation
- Cross-validation balance verification

## Usage Guidelines

### For System Testing

1. **Load URS Documents**:
   ```python
   from pathlib import Path
   
   def load_urs_documents(corpus_path="datasets/urs_corpus"):
       documents = {}
       for urs_file in Path(corpus_path).rglob("URS-*.md"):
           with open(urs_file, 'r', encoding='utf-8') as f:
               documents[urs_file.stem] = f.read()
       return documents
   ```

2. **Calculate Complexity Metrics**:
   ```python
   from metrics.complexity_calculator import URSComplexityCalculator
   
   calculator = URSComplexityCalculator()
   metrics = calculator.analyze_urs_document("datasets/urs_corpus/category_3/URS-001.md")
   print(f"Complexity Score: {metrics['composite_complexity_score']:.3f}")
   ```

3. **Cross-Validation Setup**:
   ```python
   import json
   
   # Load fold assignments
   with open('datasets/cross_validation/fold_assignments.json', 'r') as f:
       cv_config = json.load(f)
   
   # Iterate through folds
   for fold_name, fold_data in cv_config['folds'].items():
       train_files = [doc['file_path'] for doc in fold_data['train_documents']]
       test_files = [doc['file_path'] for doc in fold_data['test_documents']]
       # Run your test generation system
   ```

### For Manual Baseline Studies

1. **Follow Timing Protocol**: Use `baselines/timing_protocol.md` for consistent measurement
2. **Document Results**: Record all timing and quality metrics
3. **Validate Coverage**: Ensure 100% requirement coverage in test cases
4. **Quality Assessment**: Apply pharmaceutical domain validation

### For Performance Evaluation

**Speed Metrics**:
- Time per URS document processing
- Time per test case generation
- Throughput (documents per hour)

**Quality Metrics**:
- Requirement coverage percentage
- Test case quality scores
- GAMP categorization accuracy
- Regulatory compliance alignment

**Comparison Framework**:
- Manual baseline vs. automated system
- Cross-fold performance consistency
- Complexity impact on performance
- GAMP category impact assessment

## Regulatory Compliance

### GAMP-5 Alignment

**Category Definitions**:
- Strict adherence to ISPE GAMP-5 categorization
- Clear category indicators in each document
- Validation against pharmaceutical industry standards

**Compliance Features**:
- 21 CFR Part 11 requirements addressed
- ALCOA+ data integrity principles
- Audit trail considerations
- Electronic signature requirements

### Validation Requirements

**System Validation**:
- Test case coverage validation
- Requirement traceability verification
- Quality assurance procedures
- Change control considerations

**Documentation Standards**:
- Complete validation documentation
- Risk assessment integration
- Regulatory submission readiness
- Industry best practices alignment

## Maintenance and Updates

### Version Control

- **Semantic Versioning**: Major.Minor.Patch
- **Change Documentation**: All modifications logged
- **Backward Compatibility**: API stability maintained
- **Validation Impact**: Assessment of changes on existing results

### Future Enhancements

Planned improvements include:
- Additional URS documents for larger sample sizes
- International regulatory requirement variations
- Advanced complexity metrics incorporation
- Multi-language support for global pharmaceutical companies

## Support and Contact

For questions, issues, or contributions related to this dataset:

- **Technical Issues**: Check complexity calculator implementation
- **Data Quality**: Validate against pharmaceutical domain expertise
- **Cross-Validation**: Ensure stratification meets research requirements
- **Compliance**: Verify GAMP-5 alignment with industry standards

## Citation

When using this dataset in research or publications, please cite:

```
URS Cross-Validation Dataset for Pharmaceutical Test Generation Systems
Version 1.1, August 2025
GAMP-5 Compliant User Requirements Specifications for LLM-Driven Test Automation
```

## License and Terms

This dataset is provided for research and development purposes in pharmaceutical software validation. Users must ensure compliance with applicable pharmaceutical regulations and quality standards when using this dataset in production systems.