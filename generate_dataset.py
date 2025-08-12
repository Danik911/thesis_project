#!/usr/bin/env python3
"""
Generate the complete dataset for Task 16 - complexity metrics and baseline timings.
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add datasets to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datasets'))

def main():
    print("Generating Task 16 Dataset Files")
    print("=" * 50)
    
    try:
        # Import the fixed complexity calculator
        from datasets.metrics.complexity_calculator import URSComplexityCalculator, analyze_urs_corpus
        print("✓ Successfully imported complexity calculator")
        
        # Analyze the URS corpus
        corpus_dir = os.path.join(os.path.dirname(__file__), "datasets", "urs_corpus")
        print(f"Analyzing URS corpus: {corpus_dir}")
        
        results = analyze_urs_corpus(corpus_dir)
        print(f"✓ Successfully analyzed {len(results)} documents")
        
        # Generate metrics.csv
        print("\nGenerating metrics.csv...")
        csv_data = []
        
        for doc in results:
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
        
        # Create and save metrics DataFrame
        df = pd.DataFrame(csv_data)
        df = df.sort_values('doc_id')
        
        metrics_path = os.path.join(os.path.dirname(__file__), "datasets", "metrics", "metrics.csv")
        df.to_csv(metrics_path, index=False)
        print(f"✓ Saved metrics to: {metrics_path}")
        
        # Generate baseline timings
        print("\nGenerating baseline_timings.csv...")
        baseline_data = []
        
        for _, row in df.iterrows():
            # Formula: baseline_hours = 10 + (30 × complexity_score)
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
        baseline_path = os.path.join(os.path.dirname(__file__), "datasets", "baselines", "baseline_timings.csv")
        baseline_df.to_csv(baseline_path, index=False)
        print(f"✓ Saved baseline timings to: {baseline_path}")
        
        # Generate dataset manifest
        print("\nGenerating dataset_manifest.json...")
        
        manifest = {
            "dataset_info": {
                "name": "URS Complexity Analysis Dataset",
                "version": "1.0.0",
                "created_date": pd.Timestamp.now().isoformat(),
                "description": "Complexity metrics for 17 URS documents organized by GAMP-5 categories",
                "total_documents": len(results)
            },
            "gamp_categories": {
                "category_3": {
                    "description": "Standard Software",
                    "document_count": len([d for d in results if 'category_3' in d['file_path']]),
                    "avg_complexity": float(df[df['gamp_category'] == 3]['composite_complexity_score'].mean())
                },
                "category_4": {
                    "description": "Configured Software", 
                    "document_count": len([d for d in results if 'category_4' in d['file_path']]),
                    "avg_complexity": float(df[df['gamp_category'] == 4]['composite_complexity_score'].mean())
                },
                "category_5": {
                    "description": "Custom Software",
                    "document_count": len([d for d in results if 'category_5' in d['file_path']]),
                    "avg_complexity": float(df[df['gamp_category'] == 5]['composite_complexity_score'].mean())
                },
                "ambiguous": {
                    "description": "Ambiguous categorization for testing",
                    "document_count": len([d for d in results if 'ambiguous' in d['file_path']]),
                    "avg_complexity": float(df[df['gamp_category'] == 'ambiguous']['composite_complexity_score'].mean())
                }
            },
            "files": {
                "metrics": "datasets/metrics/metrics.csv",
                "baseline_timings": "datasets/baselines/baseline_timings.csv",
                "urs_documents": "datasets/urs_corpus/**/*.md"
            },
            "baseline_estimation": {
                "formula": "10 + (30 × complexity_score) hours",
                "methodology": "Synthetic estimates based on complexity scaling",
                "assumptions": ["10 hours minimum base time", "30 hours per complexity point", "Linear scaling model"]
            }
        }
        
        manifest_path = os.path.join(os.path.dirname(__file__), "datasets", "dataset_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"✓ Saved dataset manifest to: {manifest_path}")
        
        # Print summary statistics
        print("\n" + "=" * 50)
        print("DATASET GENERATION SUMMARY")
        print("=" * 50)
        
        print(f"Total documents analyzed: {len(results)}")
        print(f"Complexity score range: {df['composite_complexity_score'].min():.4f} - {df['composite_complexity_score'].max():.4f}")
        print(f"Average complexity: {df['composite_complexity_score'].mean():.4f}")
        
        print("\nBy GAMP Category:")
        for category in [3, 4, 5, 'ambiguous']:
            cat_data = df[df['gamp_category'] == category]
            if not cat_data.empty:
                print(f"  Category {category}: {len(cat_data)} docs, avg complexity: {cat_data['composite_complexity_score'].mean():.4f}")
        
        print("\nBaseline Timing Summary:")
        print(f"Average baseline hours: {baseline_df['estimated_baseline_hours'].mean():.1f}")
        print(f"Range: {baseline_df['estimated_baseline_hours'].min():.1f} - {baseline_df['estimated_baseline_hours'].max():.1f} hours")
        
        print("\n✓ SUCCESS: All Task 16 dataset files generated!")
        print("✓ Fixed complexity calculator (no textstat dependency)")
        print("✓ Generated metrics.csv with complexity analysis")
        print("✓ Generated baseline_timings.csv with synthetic estimates")
        print("✓ Generated dataset_manifest.json with complete metadata")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nDataset generation completed successfully!")
    else:
        print("\nDataset generation failed!")
        sys.exit(1)