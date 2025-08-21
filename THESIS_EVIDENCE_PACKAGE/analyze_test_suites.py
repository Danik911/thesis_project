#!/usr/bin/env python3
"""
Comprehensive Test Suite Analysis Script
Analyzes all 17 test suites from cross-validation execution
"""

import json
import glob
from pathlib import Path
from collections import defaultdict, Counter
import statistics

class TestSuiteAnalyzer:
    def __init__(self):
        self.base_path = Path(r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\01_TEST_EXECUTION_EVIDENCE\main_cv_execution")
        self.test_suites = []
        self.metrics = {
            "total_suites": 0,
            "total_tests": 0,
            "category_distribution": defaultdict(int),
            "category_accuracy": defaultdict(lambda: {"expected": 0, "actual": 0, "mismatched": []}),
            "test_complexity": [],
            "clarity_issues": [],
            "quality_scores": [],
            "duplicate_tests": [],
            "risk_distribution": defaultdict(int)
        }
        
    def load_all_suites(self):
        """Load all test suite JSON files"""
        patterns = [
            ("category_3", 3, ["URS-001", "URS-006", "URS-007", "URS-008", "URS-009"]),
            ("category_4", 4, ["URS-002", "URS-010", "URS-011", "URS-012", "URS-013"]),
            ("category_5", 5, ["URS-003", "URS-014", "URS-015", "URS-016", "URS-017"]),
            ("ambiguous", "ambiguous", ["URS-004", "URS-005"])
        ]
        
        for folder, expected_cat, expected_docs in patterns:
            folder_path = self.base_path / folder
            for doc in expected_docs:
                file_pattern = f"{doc}_test_suite.json"
                file_path = folder_path / file_pattern
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        suite = json.load(f)
                        suite['expected_category'] = expected_cat
                        suite['folder'] = folder
                        suite['document'] = doc
                        self.test_suites.append(suite)
                        print(f"Loaded: {doc} from {folder}")
                else:
                    print(f"WARNING: Missing {file_path}")
                    
        self.metrics["total_suites"] = len(self.test_suites)
        print(f"\nTotal suites loaded: {self.metrics['total_suites']}")
        
    def analyze_category_accuracy(self):
        """Analyze GAMP category assignment accuracy"""
        for suite in self.test_suites:
            expected = suite['expected_category']
            actual = suite.get('gamp_category', 'missing')
            doc = suite['document']
            
            if expected == "ambiguous":
                # Ambiguous docs can be 3, 4, or 5
                self.metrics["category_accuracy"]["ambiguous"]["expected"] += 1
                if actual in [3, 4, 5]:
                    self.metrics["category_accuracy"]["ambiguous"]["actual"] += 1
                else:
                    self.metrics["category_accuracy"]["ambiguous"]["mismatched"].append(f"{doc}: got {actual}")
            else:
                self.metrics["category_accuracy"][expected]["expected"] += 1
                if actual == expected:
                    self.metrics["category_accuracy"][expected]["actual"] += 1
                else:
                    self.metrics["category_accuracy"][expected]["mismatched"].append(f"{doc}: got {actual}")
                    
            self.metrics["category_distribution"][actual] += 1
            
    def analyze_test_complexity(self):
        """Analyze test complexity and quality"""
        for suite in self.test_suites:
            suite_metrics = {
                "suite_id": suite.get("suite_id"),
                "document": suite['document'],
                "num_tests": len(suite.get("test_cases", [])),
                "total_steps": 0,
                "clarity_score": 0,
                "completeness_score": 0,
                "issues": []
            }
            
            test_cases = suite.get("test_cases", [])
            self.metrics["total_tests"] += len(test_cases)
            
            for test in test_cases:
                # Count steps
                steps = test.get("test_steps", [])
                suite_metrics["total_steps"] += len(steps)
                
                # Check for clarity issues
                clarity_issues = []
                
                # Issue 1: Generic acceptance criteria
                for criteria in test.get("acceptance_criteria", []):
                    if "Result matches expected outcome" in criteria:
                        clarity_issues.append("Generic acceptance criteria")
                        break
                        
                # Issue 2: Vague test steps
                for step in steps:
                    action = step.get("action", "")
                    expected = step.get("expected_result", "")
                    if len(action) < 20:  # Too brief
                        clarity_issues.append(f"Brief action: '{action[:50]}'")
                    if "successfully" in expected.lower() and len(expected) < 30:
                        clarity_issues.append(f"Vague expected result: '{expected[:50]}'")
                        
                # Issue 3: Missing or generic verification methods
                verification_methods = set()
                for step in steps:
                    method = step.get("verification_method", "")
                    verification_methods.add(method)
                
                if len(verification_methods) == 1 and "visual_inspection" in verification_methods:
                    clarity_issues.append("Only uses visual_inspection")
                    
                # Issue 4: Duplicate test names (checking within suite)
                test_name = test.get("test_name", "")
                if test_name:
                    for other_test in test_cases:
                        if other_test != test and other_test.get("test_name") == test_name:
                            clarity_issues.append(f"Duplicate test name: {test_name}")
                            break
                            
                # Issue 5: Missing critical fields
                if not test.get("urs_requirements"):
                    clarity_issues.append("No URS requirements linked")
                if not test.get("regulatory_basis"):
                    clarity_issues.append("No regulatory basis")
                if test.get("estimated_duration_minutes", 0) == 0:
                    clarity_issues.append("No duration estimate")
                    
                # Track risk levels
                risk = test.get("risk_level", "unknown")
                self.metrics["risk_distribution"][risk] += 1
                
                if clarity_issues:
                    self.metrics["clarity_issues"].append({
                        "document": suite['document'],
                        "test_id": test.get("test_id"),
                        "test_name": test.get("test_name"),
                        "issues": clarity_issues
                    })
                    
            # Calculate suite scores
            if test_cases:
                avg_steps = suite_metrics["total_steps"] / len(test_cases)
                suite_metrics["avg_steps_per_test"] = avg_steps
                
                # Clarity score calculation
                clarity_deductions = len([i for i in self.metrics["clarity_issues"] if i["document"] == suite['document']])
                clarity_score = max(0, 100 - (clarity_deductions * 5))  # Deduct 5% per issue
                suite_metrics["clarity_score"] = clarity_score
                
                # Completeness score
                completeness_factors = []
                for test in test_cases:
                    has_prereq = 1 if test.get("prerequisites") else 0
                    has_urs = 1 if test.get("urs_requirements") else 0
                    has_regulatory = 1 if test.get("regulatory_basis") else 0
                    has_duration = 1 if test.get("estimated_duration_minutes", 0) > 0 else 0
                    has_acceptance = 1 if test.get("acceptance_criteria") else 0
                    
                    test_completeness = (has_prereq + has_urs + has_regulatory + has_duration + has_acceptance) / 5
                    completeness_factors.append(test_completeness)
                    
                suite_metrics["completeness_score"] = statistics.mean(completeness_factors) * 100 if completeness_factors else 0
                
            self.metrics["test_complexity"].append(suite_metrics)
            self.metrics["quality_scores"].append({
                "document": suite['document'],
                "clarity": suite_metrics["clarity_score"],
                "completeness": suite_metrics["completeness_score"]
            })
            
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE ANALYSIS REPORT")
        print("="*80)
        
        print("\n1. DOCUMENT COVERAGE")
        print("-" * 40)
        print(f"Total Documents Analyzed: {self.metrics['total_suites']}/17")
        if self.metrics['total_suites'] < 17:
            print(f"WARNING: Missing {17 - self.metrics['total_suites']} documents!")
            
        print("\n2. GAMP CATEGORY ACCURACY")
        print("-" * 40)
        total_correct = 0
        total_expected = 0
        
        for cat in [3, 4, 5, "ambiguous"]:
            data = self.metrics["category_accuracy"][cat]
            if data["expected"] > 0:
                accuracy = (data["actual"] / data["expected"]) * 100
                total_correct += data["actual"]
                total_expected += data["expected"]
                print(f"Category {cat}: {data['actual']}/{data['expected']} correct ({accuracy:.1f}%)")
                if data["mismatched"]:
                    for mismatch in data["mismatched"]:
                        print(f"  X {mismatch}")
                        
        overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
        print(f"\nOverall Category Accuracy: {overall_accuracy:.1f}%")
        
        print("\n3. TEST METRICS")
        print("-" * 40)
        print(f"Total Test Cases: {self.metrics['total_tests']}")
        
        if self.metrics["test_complexity"]:
            total_steps = sum(m["total_steps"] for m in self.metrics["test_complexity"])
            avg_tests_per_suite = self.metrics["total_tests"] / len(self.metrics["test_complexity"])
            avg_steps_per_test = total_steps / self.metrics["total_tests"] if self.metrics["total_tests"] > 0 else 0
            
            print(f"Average Tests per Suite: {avg_tests_per_suite:.1f}")
            print(f"Average Steps per Test: {avg_steps_per_test:.1f}")
            print(f"Total Test Steps: {total_steps}")
            
        print("\n4. QUALITY ANALYSIS")
        print("-" * 40)
        
        if self.metrics["quality_scores"]:
            clarity_scores = [q["clarity"] for q in self.metrics["quality_scores"]]
            completeness_scores = [q["completeness"] for q in self.metrics["quality_scores"]]
            
            avg_clarity = statistics.mean(clarity_scores)
            avg_completeness = statistics.mean(completeness_scores)
            
            print(f"Average Clarity Score: {avg_clarity:.1f}%")
            print(f"Average Completeness Score: {avg_completeness:.1f}%")
            
            # Explain why clarity is low
            print("\n5. CLARITY ISSUES BREAKDOWN (Why only ~55% clarity)")
            print("-" * 40)
            
            issue_types = defaultdict(int)
            for issue_entry in self.metrics["clarity_issues"]:
                for issue in issue_entry["issues"]:
                    if "Generic acceptance" in issue:
                        issue_types["Generic acceptance criteria"] += 1
                    elif "Brief action" in issue:
                        issue_types["Brief/vague action descriptions"] += 1
                    elif "Vague expected" in issue:
                        issue_types["Vague expected results"] += 1
                    elif "visual_inspection" in issue:
                        issue_types["Only visual inspection verification"] += 1
                    elif "Duplicate" in issue:
                        issue_types["Duplicate test names"] += 1
                    elif "No URS" in issue:
                        issue_types["Missing URS requirements"] += 1
                    elif "No regulatory" in issue:
                        issue_types["Missing regulatory basis"] += 1
                    elif "No duration" in issue:
                        issue_types["Missing duration estimates"] += 1
                        
            print("Issue Type Frequency:")
            for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {issue_type}: {count} occurrences")
                
            # Show specific examples
            print("\nSpecific Examples of Clarity Issues:")
            examples_shown = 0
            for issue_entry in self.metrics["clarity_issues"][:5]:  # Show first 5
                print(f"\n  Document: {issue_entry['document']}, Test: {issue_entry['test_id']}")
                print(f"  Test Name: {issue_entry['test_name']}")
                print("  Issues:")
                for issue in issue_entry["issues"][:3]:  # Show up to 3 issues per test
                    print(f"    - {issue}")
                examples_shown += 1
                
        print("\n6. RISK DISTRIBUTION")
        print("-" * 40)
        for risk, count in sorted(self.metrics["risk_distribution"].items()):
            percentage = (count / self.metrics["total_tests"] * 100) if self.metrics["total_tests"] > 0 else 0
            print(f"{risk.capitalize()}: {count} tests ({percentage:.1f}%)")
            
        print("\n7. ACTUAL vs THEORETICAL COMPARISON")
        print("-" * 40)
        print("Theoretical Targets:")
        print("  - 10 tests per document")
        print("  - 5-7 steps per test")
        print("  - 100% URS traceability")
        print("  - 100% regulatory basis coverage")
        
        print("\nActual Achievement:")
        if self.metrics["test_complexity"]:
            avg_tests = self.metrics["total_tests"] / len(self.metrics["test_complexity"])
            print(f"  - {avg_tests:.1f} tests per document (vs 10 target)")
            
            total_steps = sum(m["total_steps"] for m in self.metrics["test_complexity"])
            avg_steps = total_steps / self.metrics["total_tests"] if self.metrics["total_tests"] > 0 else 0
            print(f"  - {avg_steps:.1f} steps per test (vs 5-7 target)")
            
            # Check URS coverage
            urs_coverage = 0
            regulatory_coverage = 0
            for suite in self.test_suites:
                for test in suite.get("test_cases", []):
                    if test.get("urs_requirements"):
                        urs_coverage += 1
                    if test.get("regulatory_basis"):
                        regulatory_coverage += 1
                        
            urs_percentage = (urs_coverage / self.metrics["total_tests"] * 100) if self.metrics["total_tests"] > 0 else 0
            regulatory_percentage = (regulatory_coverage / self.metrics["total_tests"] * 100) if self.metrics["total_tests"] > 0 else 0
            
            print(f"  - {urs_percentage:.1f}% URS traceability (vs 100% target)")
            print(f"  - {regulatory_percentage:.1f}% regulatory basis (vs 100% target)")
            
        return self.metrics

if __name__ == "__main__":
    analyzer = TestSuiteAnalyzer()
    analyzer.load_all_suites()
    analyzer.analyze_category_accuracy()
    analyzer.analyze_test_complexity()
    metrics = analyzer.generate_report()
    
    # Save metrics to JSON
    output_path = Path(r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE\test_suite_metrics.json")
    
    # Clean metrics for JSON serialization
    clean_metrics = {
        "total_suites": metrics["total_suites"],
        "total_tests": metrics["total_tests"],
        "category_distribution": dict(metrics["category_distribution"]),
        "category_accuracy": {str(k): dict(v) for k, v in metrics["category_accuracy"].items()},
        "risk_distribution": dict(metrics["risk_distribution"]),
        "quality_scores": metrics["quality_scores"],
        "clarity_issues_count": len(metrics["clarity_issues"]),
        "test_complexity_summary": {
            "suites_analyzed": len(metrics["test_complexity"]),
            "avg_tests_per_suite": metrics["total_tests"] / len(metrics["test_complexity"]) if metrics["test_complexity"] else 0,
            "total_steps": sum(m["total_steps"] for m in metrics["test_complexity"])
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(clean_metrics, f, indent=2)
    
    print(f"\n\nMetrics saved to: {output_path}")