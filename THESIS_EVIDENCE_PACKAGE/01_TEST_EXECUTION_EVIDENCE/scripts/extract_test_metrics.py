#!/usr/bin/env python3
"""
Test Metrics Extraction Script
Analyzes test suite JSON files to extract complexity and quality metrics
"""

import json
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime

class TestMetricsExtractor:
    def __init__(self, test_suites_path):
        """Initialize with path to test suites directory"""
        self.test_suites_path = Path(test_suites_path)
        self.test_suites = []
        self.load_test_suites()
    
    def load_test_suites(self):
        """Load all test suite JSON files"""
        # Find all test suite files
        patterns = [
            "category_3/*.json",
            "category_4/*.json",
            "category_5/*.json",
            "ambiguous/*.json"
        ]
        
        for pattern in patterns:
            files = glob.glob(str(self.test_suites_path / pattern))
            for file_path in files:
                with open(file_path, 'r') as f:
                    suite_data = json.load(f)
                    suite_data['file_path'] = file_path
                    suite_data['category_folder'] = Path(file_path).parent.name
                    self.test_suites.append(suite_data)
        
        print(f"Loaded {len(self.test_suites)} test suites")
    
    def extract_test_complexity(self, test_case):
        """Extract complexity metrics from a single test case"""
        metrics = {
            "test_id": test_case.get("test_id"),
            "test_name": test_case.get("test_name"),
            "num_steps": len(test_case.get("test_steps", [])),
            "num_prerequisites": len(test_case.get("prerequisites", [])),
            "num_acceptance_criteria": len(test_case.get("acceptance_criteria", [])),
            "num_urs_requirements": len(test_case.get("urs_requirements", [])),
            "num_related_tests": len(test_case.get("related_tests", [])),
            "num_regulatory_basis": len(test_case.get("regulatory_basis", [])),
            "estimated_duration_minutes": test_case.get("estimated_duration_minutes", 0),
            "risk_level": test_case.get("risk_level", "unknown"),
            "test_category": test_case.get("test_category", "unknown"),
            "gamp_category": test_case.get("gamp_category", 0),
            "data_retention_period": test_case.get("data_retention_period", "unknown")
        }
        
        # Count data capture points across all steps
        data_capture_points = 0
        verification_methods = []
        for step in test_case.get("test_steps", []):
            data_capture_points += len(step.get("data_to_capture", []))
            verification_methods.append(step.get("verification_method", "unknown"))
        
        metrics["num_data_capture_points"] = data_capture_points
        metrics["unique_verification_methods"] = len(set(verification_methods))
        metrics["verification_methods_list"] = list(set(verification_methods))
        
        # Check for decision points (conditional logic)
        decision_points = 0
        for step in test_case.get("test_steps", []):
            action = step.get("action", "").lower()
            expected = step.get("expected_result", "").lower()
            if any(word in action + expected for word in ["if", "when", "verify", "check", "confirm"]):
                decision_points += 1
        
        metrics["num_decision_points"] = decision_points
        
        # Calculate complexity score (weighted sum)
        complexity_score = (
            metrics["num_steps"] * 2 +
            metrics["num_prerequisites"] * 1 +
            metrics["num_acceptance_criteria"] * 1.5 +
            metrics["num_data_capture_points"] * 0.5 +
            metrics["num_decision_points"] * 1.5
        )
        metrics["complexity_score"] = complexity_score
        
        return metrics
    
    def extract_suite_metrics(self, suite):
        """Extract metrics from a complete test suite"""
        suite_metrics = {
            "suite_id": suite.get("suite_id"),
            "document_name": suite.get("document_name"),
            "gamp_category": suite.get("gamp_category"),
            "category_folder": suite.get("category_folder"),
            "num_test_cases": len(suite.get("test_cases", [])),
            "test_complexities": []
        }
        
        # Extract metrics for each test case
        total_steps = 0
        total_duration = 0
        risk_levels = []
        test_categories = []
        
        for test_case in suite.get("test_cases", []):
            test_metrics = self.extract_test_complexity(test_case)
            suite_metrics["test_complexities"].append(test_metrics)
            
            total_steps += test_metrics["num_steps"]
            total_duration += test_metrics["estimated_duration_minutes"]
            risk_levels.append(test_metrics["risk_level"])
            test_categories.append(test_metrics["test_category"])
        
        # Suite-level aggregations
        suite_metrics["total_steps"] = total_steps
        suite_metrics["avg_steps_per_test"] = total_steps / len(suite.get("test_cases", [])) if suite.get("test_cases") else 0
        suite_metrics["total_estimated_duration"] = total_duration
        suite_metrics["risk_distribution"] = dict(Counter(risk_levels))
        suite_metrics["test_category_distribution"] = dict(Counter(test_categories))
        
        # Calculate suite complexity
        suite_complexity = sum(tc["complexity_score"] for tc in suite_metrics["test_complexities"])
        suite_metrics["suite_complexity_score"] = suite_complexity
        suite_metrics["avg_test_complexity"] = suite_complexity / len(suite.get("test_cases", [])) if suite.get("test_cases") else 0
        
        return suite_metrics
    
    def analyze_all_suites(self):
        """Analyze all loaded test suites"""
        all_metrics = []
        for suite in self.test_suites:
            metrics = self.extract_suite_metrics(suite)
            all_metrics.append(metrics)
        return all_metrics
    
    def calculate_quality_scores(self, suite_metrics):
        """Calculate quality scores for test suites"""
        quality_scores = []
        
        for suite in suite_metrics:
            score = {
                "suite_id": suite["suite_id"],
                "document_name": suite["document_name"],
                "completeness_score": 0,
                "traceability_score": 0,
                "clarity_score": 0,
                "overall_quality_score": 0
            }
            
            # Completeness score (based on presence of key fields)
            completeness_factors = []
            for test in suite["test_complexities"]:
                test_completeness = (
                    (1 if test["num_prerequisites"] > 0 else 0) +
                    (1 if test["num_acceptance_criteria"] > 0 else 0) +
                    (1 if test["num_urs_requirements"] > 0 else 0) +
                    (1 if test["num_regulatory_basis"] > 0 else 0) +
                    (1 if test["estimated_duration_minutes"] > 0 else 0)
                ) / 5
                completeness_factors.append(test_completeness)
            score["completeness_score"] = np.mean(completeness_factors) * 100 if completeness_factors else 0
            
            # Traceability score (URS requirements mapping)
            traceability_factors = []
            for test in suite["test_complexities"]:
                has_requirements = 1 if test["num_urs_requirements"] > 0 else 0
                traceability_factors.append(has_requirements)
            score["traceability_score"] = np.mean(traceability_factors) * 100 if traceability_factors else 0
            
            # Clarity score (based on structure and detail)
            clarity_factors = []
            for test in suite["test_complexities"]:
                test_clarity = (
                    min(test["num_steps"] / 3, 1) * 0.3 +  # Adequate steps
                    min(test["num_data_capture_points"] / test["num_steps"], 1) * 0.3 if test["num_steps"] > 0 else 0 +  # Data capture ratio
                    (1 if test["unique_verification_methods"] > 0 else 0) * 0.2 +  # Has verification
                    min(test["num_acceptance_criteria"] / 2, 1) * 0.2  # Adequate acceptance criteria
                )
                clarity_factors.append(test_clarity)
            score["clarity_score"] = np.mean(clarity_factors) * 100 if clarity_factors else 0
            
            # Overall quality score (weighted average)
            score["overall_quality_score"] = (
                score["completeness_score"] * 0.35 +
                score["traceability_score"] * 0.35 +
                score["clarity_score"] * 0.30
            )
            
            quality_scores.append(score)
        
        return quality_scores
    
    def generate_statistics_summary(self, suite_metrics):
        """Generate overall statistics summary"""
        summary = {
            "total_suites": len(suite_metrics),
            "total_tests": sum(s["num_test_cases"] for s in suite_metrics),
            "total_steps": sum(s["total_steps"] for s in suite_metrics),
            "total_estimated_duration_minutes": sum(s["total_estimated_duration"] for s in suite_metrics)
        }
        
        # Category distribution
        category_counts = defaultdict(int)
        for suite in suite_metrics:
            category_counts[suite["gamp_category"]] += 1
        summary["gamp_category_distribution"] = dict(category_counts)
        
        # Complexity statistics
        all_complexities = []
        for suite in suite_metrics:
            all_complexities.extend([tc["complexity_score"] for tc in suite["test_complexities"]])
        
        summary["complexity_statistics"] = {
            "mean": np.mean(all_complexities) if all_complexities else 0,
            "median": np.median(all_complexities) if all_complexities else 0,
            "std": np.std(all_complexities) if all_complexities else 0,
            "min": np.min(all_complexities) if all_complexities else 0,
            "max": np.max(all_complexities) if all_complexities else 0,
            "q25": np.percentile(all_complexities, 25) if all_complexities else 0,
            "q75": np.percentile(all_complexities, 75) if all_complexities else 0
        }
        
        # Steps per test statistics
        all_steps = []
        for suite in suite_metrics:
            all_steps.extend([tc["num_steps"] for tc in suite["test_complexities"]])
        
        summary["steps_per_test_statistics"] = {
            "mean": np.mean(all_steps) if all_steps else 0,
            "median": np.median(all_steps) if all_steps else 0,
            "std": np.std(all_steps) if all_steps else 0,
            "min": np.min(all_steps) if all_steps else 0,
            "max": np.max(all_steps) if all_steps else 0
        }
        
        # Risk level distribution
        all_risks = []
        for suite in suite_metrics:
            all_risks.extend([tc["risk_level"] for tc in suite["test_complexities"]])
        summary["risk_level_distribution"] = dict(Counter(all_risks))
        
        # Verification methods distribution
        all_methods = []
        for suite in suite_metrics:
            for tc in suite["test_complexities"]:
                all_methods.extend(tc["verification_methods_list"])
        summary["verification_methods_distribution"] = dict(Counter(all_methods))
        
        return summary
    
    def save_analysis(self, output_path):
        """Run complete analysis and save results"""
        # Extract metrics
        suite_metrics = self.analyze_all_suites()
        quality_scores = self.calculate_quality_scores(suite_metrics)
        statistics_summary = self.generate_statistics_summary(suite_metrics)
        
        # Combine results
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics_summary": statistics_summary,
            "quality_scores": quality_scores,
            "suite_details": suite_metrics
        }
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # Save to JSON
        report_converted = convert_numpy_types(report)
        with open(output_path, 'w') as f:
            json.dump(report_converted, f, indent=2)
        
        print(f"\nTest metrics analysis saved to {output_path}")
        
        # Print summary
        print("\n=== Test Metrics Summary ===")
        print(f"Total Test Suites: {statistics_summary['total_suites']}")
        print(f"Total Test Cases: {statistics_summary['total_tests']}")
        print(f"Total Test Steps: {statistics_summary['total_steps']}")
        print(f"Total Estimated Duration: {statistics_summary['total_estimated_duration_minutes']} minutes")
        
        print("\n=== GAMP Category Distribution ===")
        for category, count in statistics_summary['gamp_category_distribution'].items():
            print(f"Category {category}: {count} suites")
        
        print("\n=== Complexity Statistics ===")
        print(f"Mean Complexity Score: {statistics_summary['complexity_statistics']['mean']:.2f}")
        print(f"Median Complexity Score: {statistics_summary['complexity_statistics']['median']:.2f}")
        print(f"Complexity Range: {statistics_summary['complexity_statistics']['min']:.2f} - {statistics_summary['complexity_statistics']['max']:.2f}")
        
        print("\n=== Quality Scores (Average) ===")
        avg_completeness = np.mean([q["completeness_score"] for q in quality_scores])
        avg_traceability = np.mean([q["traceability_score"] for q in quality_scores])
        avg_clarity = np.mean([q["clarity_score"] for q in quality_scores])
        avg_overall = np.mean([q["overall_quality_score"] for q in quality_scores])
        
        print(f"Completeness: {avg_completeness:.1f}%")
        print(f"Traceability: {avg_traceability:.1f}%")
        print(f"Clarity: {avg_clarity:.1f}%")
        print(f"Overall Quality: {avg_overall:.1f}%")
        
        print("\n=== Risk Distribution ===")
        for risk, count in statistics_summary['risk_level_distribution'].items():
            print(f"{risk}: {count} tests")


if __name__ == "__main__":
    # Path to test suites directory
    test_suites_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/main_cv_execution")
    output_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/test_metrics_analysis.json")
    
    # Run analysis
    extractor = TestMetricsExtractor(test_suites_path)
    extractor.save_analysis(output_path)