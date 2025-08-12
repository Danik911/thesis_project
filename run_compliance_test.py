#!/usr/bin/env python3
"""
Run real compliance assessment to verify Task 18 implementation
"""

import sys
import tempfile
from pathlib import Path

# Add main to path
sys.path.insert(0, 'main')

try:
    from src.compliance_validation.evidence_collector import EvidenceCollector
    from src.compliance_validation.alcoa_scorer import ALCOAScorer
    from src.compliance_validation.gamp5_assessor import GAMP5Assessor
    from src.core.events import GAMPCategory
    
    # Create temp directory for outputs
    output_dir = Path(tempfile.mkdtemp())
    
    print('Initializing compliance components...')
    evidence_collector = EvidenceCollector(output_directory=output_dir)
    alcoa_scorer = ALCOAScorer(evidence_collector=evidence_collector)
    gamp5_assessor = GAMP5Assessor(evidence_collector=evidence_collector)
    
    print('\n' + '='*60)
    print('ALCOA+ Assessment with 2x Weighting')
    print('='*60)
    
    # Create realistic test data
    test_data = []
    for i in range(1, 6):
        test_data.append({
            'id': f'TEST-{i:03d}',
            'timestamp': f'2025-08-12T12:{i:02d}:00',
            'user': f'user_{i}',
            'original_record': i % 2 == 0,  # 40% original
            'validated': True,
            'audit_trail': i % 3 != 0,  # 67% have audit trail  
            'changes': [] if i % 4 == 0 else [f'change_{i}'],
            'signature': 'digital_sig' if i % 2 == 0 else None
        })
    
    # Run ALCOA+ assessment
    result = alcoa_scorer.assess_system_data_integrity(
        data_samples=test_data,
        system_name='Pharmaceutical Test Generation System',
        assessment_scope='Task 18 Real Validation'
    )
    
    print(f'Overall Score: {result.overall_score:.2f}/10')
    print(f'Target Score: {result.target_score}')
    print(f'Meets Target (>9.0): {result.meets_target}')
    print(f'Compliance Status: {result.compliance_status}')
    print(f'Data Samples: {result.data_samples_assessed}')
    
    # Show individual scores with weights
    print('\nAttribute Scores (with weights):')
    print('-' * 50)
    for attr_name, scoring in result.attribute_scores.items():
        weight_indicator = ' (2x)' if scoring.weight == 2.0 else ''
        print(f'{attr_name:15s}: {scoring.score:.2f} x {scoring.weight:.1f}{weight_indicator} = {scoring.weighted_score:.2f}')
    
    print('-' * 50)
    print(f'Total Weighted: {result.total_actual_score:.2f}/{result.total_possible_score:.2f}')
    
    # Verify 2x weighting
    original = result.attribute_scores.get('original')
    accurate = result.attribute_scores.get('accurate')
    
    print('\n2x Weighting Verification:')
    if original:
        status = 'PASS' if original.weight == 2.0 else 'FAIL'
        print(f'[{status}] Original weight: {original.weight}x (expected 2.0)')
    if accurate:
        status = 'PASS' if accurate.weight == 2.0 else 'FAIL'
        print(f'[{status}] Accurate weight: {accurate.weight}x (expected 2.0)')
    
    print('\n' + '='*60)
    print('GAMP-5 Categorization Assessment')
    print('='*60)
    
    gamp_result = gamp5_assessor.assess_system_categorization(
        predicted_category=GAMPCategory.CATEGORY_5,
        expected_category=GAMPCategory.CATEGORY_5,
        confidence_score=0.95,
        system_name='Pharmaceutical Test Generation System',
        categorization_rationale='Custom multi-agent LLM system for pharmaceutical test generation with GAMP-5 compliance framework'
    )
    
    print(f'Compliance Status: {gamp_result["compliance_status"]}')
    print(f'Validation Score: {gamp_result.get("validation_score", 0):.2f}')
    print(f'Validation Strategy: {gamp_result.get("strategy", {}).get("validation_rigor", "unknown")}')
    print(f'Category Match: {gamp_result.get("category_match", False)}')
    print(f'Confidence Score: {gamp_result.get("confidence_score", 0):.2f}')
    
    # Save results
    import json
    results_file = Path('task_18_real_results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'alcoa_score': result.overall_score,
            'alcoa_meets_target': result.meets_target,
            'alcoa_status': str(result.compliance_status),
            'gamp5_status': gamp_result["compliance_status"],
            'gamp5_validation_score': gamp_result.get("validation_score", 0),
            'gamp5_category_match': gamp_result.get("category_match", False),
            'original_weight': original.weight if original else None,
            'accurate_weight': accurate.weight if accurate else None
        }, f, indent=2)
    
    print(f'\n[SAVED] Results saved to: {results_file}')
    print('\n' + '='*60)
    print('REAL COMPLIANCE ASSESSMENT COMPLETED SUCCESSFULLY')
    print('='*60)
    
except ImportError as e:
    print(f'Import error: {e}')
    print('Make sure you are in the project root directory')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()