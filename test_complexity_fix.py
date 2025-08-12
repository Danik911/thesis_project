#!/usr/bin/env python3
"""
Test script for the fixed complexity calculator.
"""

import sys
import os

# Add datasets directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'datasets'))

from datasets.metrics.complexity_calculator import URSComplexityCalculator, analyze_urs_corpus
import pandas as pd
import json
from pathlib import Path

def test_complexity_calculator():
    """Test the fixed complexity calculator on the URS corpus."""
    
    print("Testing Fixed Complexity Calculator")
    print("=" * 50)
    
    try:
        # Test single document first
        calculator = URSComplexityCalculator()
        test_file = "datasets/urs_corpus/category_3/URS-001.md"
        
        print(f"Testing single document: {test_file}")
        result = calculator.analyze_urs_document(test_file)
        
        print(f"Document ID: {result['document_id']}")
        print(f"Complexity Score: {result['composite_complexity_score']:.4f}")
        print(f"Readability Score: {result['readability_score']:.2f}")
        print(f"Total Requirements: {result['requirement_counts']['total']}")
        print()
        
        # Test full corpus analysis
        print("Analyzing full URS corpus...")
        corpus_results = analyze_urs_corpus("datasets/urs_corpus")
        
        print(f"Successfully analyzed {len(corpus_results)} documents")
        
        # Generate metrics.csv
        print("Generating metrics.csv...")
        
        # Flatten the metrics for CSV output
        csv_data = []
        for doc in corpus_results:
            # Determine GAMP category from file path
            if 'category_3' in doc['file_path']:
                gamp_category = 3
            elif 'category_4' in doc['file_path']:
                gamp_category = 4
            elif 'category_5' in doc['file_path']:
                gamp_category = 5
            else:
                gamp_category = 'ambiguous'
            
            row = {
                'doc_id': doc['document_id'],
                'file_path': doc['file_path'],
                'gamp_category': gamp_category,
                'total_requirements': doc['requirement_counts']['total'],
                'functional_requirements': doc['requirement_counts']['functional'],
                'performance_requirements': doc['requirement_counts']['performance'],
                'regulatory_requirements': doc['requirement_counts']['regulatory'],
                'integration_requirements': doc['requirement_counts']['integration'],
                'technical_requirements': doc['requirement_counts']['technical'],
                'readability_score': doc['readability_score'],
                'integration_density': doc['integration_complexity']['integration_density'],
                'dependency_density': doc['dependency_density'],
                'ambiguity_rate': doc['ambiguity_rate'],
                'custom_rate': doc['custom_indicators']['custom_rate'],
                'composite_complexity_score': doc['composite_complexity_score']
            }
            csv_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df = df.sort_values('doc_id')  # Sort by document ID
        
        metrics_path = "datasets/metrics/metrics.csv"
        df.to_csv(metrics_path, index=False)
        print(f"Saved metrics to: {metrics_path}")
        
        # Display summary statistics
        print("\nComplexity Score Distribution:")
        print(df['composite_complexity_score'].describe())
        
        print("\nBy GAMP Category:")
        category_stats = df.groupby('gamp_category')['composite_complexity_score'].agg(['count', 'mean', 'std'])
        print(category_stats)
        
        # Generate synthetic baseline timings
        print("\nGenerating baseline timing estimates...")
        
        baseline_data = []
        for _, row in df.iterrows():
            # Formula: baseline_hours = 10 + (30 × complexity_score)
            # This assumes 10 hours minimum + complexity scaling
            baseline_hours = 10 + (30 * row['composite_complexity_score'])
            
            baseline_row = {
                'doc_id': row['doc_id'],
                'gamp_category': row['gamp_category'],
                'complexity_score': row['composite_complexity_score'],
                'estimated_baseline_hours': round(baseline_hours, 1),
                'estimation_method': 'synthetic_complexity_based',
                'assumptions': '10 base hours + 30 hours per complexity point'
            }
            baseline_data.append(baseline_row)
        
        baseline_df = pd.DataFrame(baseline_data)
        baseline_path = "datasets/baselines/baseline_timings.csv"
        baseline_df.to_csv(baseline_path, index=False)
        print(f"Saved baseline timings to: {baseline_path}")
        
        print("\nBaseline Timing Summary:")
        print(f"Average baseline hours: {baseline_df['estimated_baseline_hours'].mean():.1f}")
        print(f"Range: {baseline_df['estimated_baseline_hours'].min():.1f} - {baseline_df['estimated_baseline_hours'].max():.1f} hours")
        
        # Generate dataset manifest
        print("\nGenerating dataset manifest...")
        
        manifest = {
            "dataset_info": {
                "name": "URS Complexity Analysis Dataset",
                "version": "1.0.0",
                "created_date": pd.Timestamp.now().isoformat(),
                "description": "Complexity metrics for 17 URS documents organized by GAMP-5 categories",
                "total_documents": len(corpus_results)
            },
            "gamp_categories": {
                "category_3": {
                    "description": "Standard Software",
                    "document_count": len([d for d in corpus_results if 'category_3' in d['file_path']]),
                    "complexity_range": [
                        float(df[df['gamp_category'] == 3]['composite_complexity_score'].min()),
                        float(df[df['gamp_category'] == 3]['composite_complexity_score'].max())
                    ]
                },
                "category_4": {
                    "description": "Configured Software", 
                    "document_count": len([d for d in corpus_results if 'category_4' in d['file_path']]),
                    "complexity_range": [
                        float(df[df['gamp_category'] == 4]['composite_complexity_score'].min()),
                        float(df[df['gamp_category'] == 4]['composite_complexity_score'].max())
                    ]
                },
                "category_5": {
                    "description": "Custom Software",
                    "document_count": len([d for d in corpus_results if 'category_5' in d['file_path']]),
                    "complexity_range": [
                        float(df[df['gamp_category'] == 5]['composite_complexity_score'].min()),
                        float(df[df['gamp_category'] == 5]['composite_complexity_score'].max())
                    ]
                },
                "ambiguous": {
                    "description": "Ambiguous categorization for testing",
                    "document_count": len([d for d in corpus_results if 'ambiguous' in d['file_path']]),
                    "complexity_range": [
                        float(df[df['gamp_category'] == 'ambiguous']['composite_complexity_score'].min()),
                        float(df[df['gamp_category'] == 'ambiguous']['composite_complexity_score'].max())
                    ]
                }
            },
            "files": {
                "metrics": "datasets/metrics/metrics.csv",
                "baseline_timings": "datasets/baselines/baseline_timings.csv",
                "urs_documents": "datasets/urs_corpus/**/*.md"
            },
            "metrics_description": {
                "composite_complexity_score": "Weighted score combining requirement counts, readability, integration complexity, dependency density, ambiguity rate, and custom indicators",
                "readability_score": "Flesch-Kincaid Grade Level calculated using custom implementation",
                "baseline_estimation_formula": "10 + (30 × complexity_score) hours"
            }
        }
        
        manifest_path = "datasets/dataset_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Saved dataset manifest to: {manifest_path}")
        
        print("\n" + "=" * 50)
        print("SUCCESS: All dataset files generated!")
        print("✓ Fixed complexity calculator (no textstat dependency)")
        print("✓ Generated metrics.csv with 17 documents")
        print("✓ Generated baseline_timings.csv with synthetic estimates")
        print("✓ Generated dataset_manifest.json with metadata")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complexity_calculator()
    sys.exit(0 if success else 1)