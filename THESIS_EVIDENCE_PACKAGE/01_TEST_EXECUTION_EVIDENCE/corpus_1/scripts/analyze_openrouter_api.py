#!/usr/bin/env python3
"""
OpenRouter API Analytics Script
Analyzes API call data from OpenRouter CSV export for thesis evaluation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

class OpenRouterAnalyzer:
    def __init__(self, csv_path):
        """Initialize analyzer with CSV data"""
        self.df = pd.read_csv(csv_path)
        self.df['created_at'] = pd.to_datetime(self.df['created_at'])
        self.df['generation_time_seconds'] = self.df['generation_time_ms'] / 1000
        self.df['tokens_total'] = self.df['tokens_prompt'] + self.df['tokens_completion']
        
    def basic_statistics(self):
        """Calculate basic statistics from API calls"""
        stats = {
            "total_api_calls": len(self.df),
            "total_cost": self.df['cost_total'].sum(),
            "avg_cost_per_call": self.df['cost_total'].mean(),
            "std_cost_per_call": self.df['cost_total'].std(),
            "total_tokens": self.df['tokens_total'].sum(),
            "total_prompt_tokens": self.df['tokens_prompt'].sum(),
            "total_completion_tokens": self.df['tokens_completion'].sum(),
            "avg_tokens_per_call": self.df['tokens_total'].mean(),
            "avg_generation_time_seconds": self.df['generation_time_seconds'].mean(),
            "median_generation_time_seconds": self.df['generation_time_seconds'].median(),
            "avg_time_to_first_token_ms": self.df['time_to_first_token_ms'].mean()
        }
        return stats
    
    def provider_analysis(self):
        """Analyze performance by provider"""
        providers = {}
        for provider in self.df['provider_name'].unique():
            provider_df = self.df[self.df['provider_name'] == provider]
            providers[provider] = {
                "calls": len(provider_df),
                "percentage": len(provider_df) / len(self.df) * 100,
                "avg_cost": provider_df['cost_total'].mean(),
                "total_cost": provider_df['cost_total'].sum(),
                "avg_generation_time": provider_df['generation_time_seconds'].mean(),
                "median_generation_time": provider_df['generation_time_seconds'].median(),
                "avg_tokens": provider_df['tokens_total'].mean(),
                "failure_rate": (provider_df['finish_reason_normalized'] != 'stop').mean() * 100
            }
        return providers
    
    def token_economics(self):
        """Analyze token usage and economics"""
        economics = {
            "prompt_completion_ratio": self.df['tokens_completion'].sum() / self.df['tokens_prompt'].sum(),
            "cost_per_1k_tokens": (self.df['cost_total'].sum() / self.df['tokens_total'].sum()) * 1000,
            "tokens_distribution": {
                "prompt": {
                    "mean": self.df['tokens_prompt'].mean(),
                    "median": self.df['tokens_prompt'].median(),
                    "std": self.df['tokens_prompt'].std(),
                    "min": self.df['tokens_prompt'].min(),
                    "max": self.df['tokens_prompt'].max(),
                    "q25": self.df['tokens_prompt'].quantile(0.25),
                    "q75": self.df['tokens_prompt'].quantile(0.75)
                },
                "completion": {
                    "mean": self.df['tokens_completion'].mean(),
                    "median": self.df['tokens_completion'].median(),
                    "std": self.df['tokens_completion'].std(),
                    "min": self.df['tokens_completion'].min(),
                    "max": self.df['tokens_completion'].max(),
                    "q25": self.df['tokens_completion'].quantile(0.25),
                    "q75": self.df['tokens_completion'].quantile(0.75)
                }
            },
            "generation_efficiency": {
                "tokens_per_second": self.df['tokens_completion'].sum() / self.df['generation_time_seconds'].sum(),
                "avg_tokens_per_second": (self.df['tokens_completion'] / self.df['generation_time_seconds']).mean()
            }
        }
        return economics
    
    def temporal_analysis(self):
        """Analyze temporal patterns in API usage"""
        self.df['hour'] = self.df['created_at'].dt.hour
        self.df['minute'] = self.df['created_at'].dt.minute
        
        # Calculate time between calls
        self.df['time_since_last_call'] = self.df['created_at'].diff().dt.total_seconds()
        
        temporal = {
            "execution_window": {
                "start": str(self.df['created_at'].min()),
                "end": str(self.df['created_at'].max()),
                "duration_minutes": (self.df['created_at'].max() - self.df['created_at'].min()).total_seconds() / 60
            },
            "calls_per_minute": len(self.df) / ((self.df['created_at'].max() - self.df['created_at'].min()).total_seconds() / 60),
            "avg_time_between_calls_seconds": self.df['time_since_last_call'].mean(),
            "peak_usage_hour": self.df.groupby('hour').size().idxmax(),
            "calls_by_hour": self.df.groupby('hour').size().to_dict()
        }
        return temporal
    
    def cost_variance_analysis(self):
        """Analyze cost variance and identify outliers"""
        cost_analysis = {
            "cost_variance": self.df['cost_total'].var(),
            "cost_std": self.df['cost_total'].std(),
            "cost_cv": self.df['cost_total'].std() / self.df['cost_total'].mean(),  # Coefficient of variation
            "cost_percentiles": {
                "p10": self.df['cost_total'].quantile(0.10),
                "p25": self.df['cost_total'].quantile(0.25),
                "p50": self.df['cost_total'].quantile(0.50),
                "p75": self.df['cost_total'].quantile(0.75),
                "p90": self.df['cost_total'].quantile(0.90),
                "p95": self.df['cost_total'].quantile(0.95),
                "p99": self.df['cost_total'].quantile(0.99)
            },
            "outliers": {
                "count": len(self.df[np.abs(stats.zscore(self.df['cost_total'])) > 3]),
                "percentage": len(self.df[np.abs(stats.zscore(self.df['cost_total'])) > 3]) / len(self.df) * 100
            }
        }
        
        # Identify cost drivers
        correlation_matrix = self.df[['cost_total', 'tokens_prompt', 'tokens_completion', 'generation_time_seconds']].corr()
        cost_analysis['cost_correlations'] = {
            "prompt_tokens": correlation_matrix.loc['cost_total', 'tokens_prompt'],
            "completion_tokens": correlation_matrix.loc['cost_total', 'tokens_completion'],
            "generation_time": correlation_matrix.loc['cost_total', 'generation_time_seconds']
        }
        
        return cost_analysis
    
    def performance_patterns(self):
        """Identify performance patterns and bottlenecks"""
        patterns = {
            "latency_analysis": {
                "p50": self.df['generation_time_ms'].quantile(0.50),
                "p75": self.df['generation_time_ms'].quantile(0.75),
                "p90": self.df['generation_time_ms'].quantile(0.90),
                "p95": self.df['generation_time_ms'].quantile(0.95),
                "p99": self.df['generation_time_ms'].quantile(0.99)
            },
            "throughput": {
                "calls_per_minute_max": self.df.groupby(self.df['created_at'].dt.floor('min')).size().max(),
                "calls_per_minute_avg": self.df.groupby(self.df['created_at'].dt.floor('min')).size().mean()
            },
            "efficiency_metrics": {
                "fast_calls_percentage": (self.df['generation_time_ms'] < 10000).mean() * 100,
                "slow_calls_percentage": (self.df['generation_time_ms'] > 30000).mean() * 100,
                "very_slow_calls_percentage": (self.df['generation_time_ms'] > 60000).mean() * 100
            }
        }
        return patterns
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "basic_statistics": self.basic_statistics(),
            "provider_analysis": self.provider_analysis(),
            "token_economics": self.token_economics(),
            "temporal_analysis": self.temporal_analysis(),
            "cost_variance": self.cost_variance_analysis(),
            "performance_patterns": self.performance_patterns()
        }
        
        # Calculate thesis-specific metrics
        thesis_metrics = {
            "cost_per_document": report['basic_statistics']['total_cost'] / 17,  # 17 documents
            "api_calls_per_document": report['basic_statistics']['total_api_calls'] / 17,
            "tokens_per_document": report['basic_statistics']['total_tokens'] / 17,
            "actual_vs_target_cost_ratio": (report['basic_statistics']['total_cost'] / 17) / 0.00056,  # vs target
            "execution_efficiency": {
                "total_time_minutes": report['temporal_analysis']['execution_window']['duration_minutes'],
                "avg_time_per_document": report['temporal_analysis']['execution_window']['duration_minutes'] / 17
            }
        }
        report['thesis_metrics'] = thesis_metrics
        
        return report
    
    def save_report(self, output_path):
        """Save analysis report to JSON"""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report saved to {output_path}")
        
        # Print summary
        print("\n=== OpenRouter API Analysis Summary ===")
        print(f"Total API Calls: {report['basic_statistics']['total_api_calls']}")
        print(f"Total Cost: ${report['basic_statistics']['total_cost']:.4f}")
        print(f"Cost per Document: ${report['thesis_metrics']['cost_per_document']:.4f}")
        print(f"Cost vs Target Ratio: {report['thesis_metrics']['actual_vs_target_cost_ratio']:.1f}x")
        print(f"Execution Time: {report['thesis_metrics']['execution_efficiency']['total_time_minutes']:.1f} minutes")
        
        print("\n=== Provider Distribution ===")
        for provider, stats in report['provider_analysis'].items():
            print(f"{provider}: {stats['calls']} calls ({stats['percentage']:.1f}%), "
                  f"avg cost: ${stats['avg_cost']:.4f}, avg time: {stats['avg_generation_time']:.1f}s")
        
        print("\n=== Token Economics ===")
        print(f"Total Tokens: {report['basic_statistics']['total_tokens']:,}")
        print(f"Cost per 1K Tokens: ${report['token_economics']['cost_per_1k_tokens']:.4f}")
        print(f"Prompt/Completion Ratio: {report['token_economics']['prompt_completion_ratio']:.2f}")
        print(f"Generation Speed: {report['token_economics']['generation_efficiency']['tokens_per_second']:.1f} tokens/sec")


if __name__ == "__main__":
    # Path to OpenRouter CSV file
    csv_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/openrouter_activity_2025-08-20.csv")
    output_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/openrouter_analysis_report.json")
    
    # Run analysis
    analyzer = OpenRouterAnalyzer(csv_path)
    analyzer.save_report(output_path)