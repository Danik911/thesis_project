#!/usr/bin/env python3
"""
Realistic Test Suite Analysis Script
Analyzes actual measurable metrics from generated pharmaceutical test suites
"""

import json
import glob
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import statistics

class TestSuiteAnalyzer:
    """Analyzes test suites for measurable quality and compliance metrics"""
    
    def __init__(self):
        self.results = {
            "metadata": {},
            "basic_metrics": {},
            "quality_metrics": {},
            "alcoa_compliance": {},
            "linguistic_analysis": {},
            "consistency_analysis": {},
            "detailed_findings": []
        }
        
    def analyze_test_suite(self, suite_path: str) -> Dict[str, Any]:
        """Analyze a single test suite JSON file"""
        try:
            with open(suite_path, 'r', encoding='utf-8') as f:
                suite = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return {"error": f"Failed to load {suite_path}: {str(e)}"}
        
        suite_id = suite.get('suite_id', 'unknown')
        
        analysis = {
            "suite_id": suite_id,
            "file_path": suite_path,
            "basic_metrics": self._extract_basic_metrics(suite),
            "quality_metrics": self._analyze_quality(suite),
            "alcoa_compliance": self._assess_alcoa_compliance(suite),
            "linguistic_metrics": self._analyze_language(suite),
            "consistency_metrics": self._check_consistency(suite)
        }
        
        return analysis
    
    def _extract_basic_metrics(self, suite: Dict) -> Dict:
        """Extract basic countable metrics"""
        test_cases = suite.get('test_cases', [])
        
        # Count test steps
        total_steps = 0
        steps_per_test = []
        data_points_total = 0
        prerequisites_total = 0
        
        for test in test_cases:
            test_steps = test.get('test_steps', [])
            num_steps = len(test_steps)
            total_steps += num_steps
            steps_per_test.append(num_steps)
            
            # Count data capture points
            for step in test_steps:
                data_points_total += len(step.get('data_to_capture', []))
            
            # Count prerequisites
            prerequisites_total += len(test.get('prerequisites', []))
        
        # Risk level distribution
        risk_levels = [test.get('risk_level', 'unspecified') for test in test_cases]
        risk_distribution = dict(Counter(risk_levels))
        
        # Test categories
        test_categories = [test.get('test_category', 'unspecified') for test in test_cases]
        category_distribution = dict(Counter(test_categories))
        
        return {
            "test_count": len(test_cases),
            "total_steps": total_steps,
            "avg_steps_per_test": statistics.mean(steps_per_test) if steps_per_test else 0,
            "min_steps": min(steps_per_test) if steps_per_test else 0,
            "max_steps": max(steps_per_test) if steps_per_test else 0,
            "total_data_points": data_points_total,
            "avg_data_points_per_test": data_points_total / len(test_cases) if test_cases else 0,
            "total_prerequisites": prerequisites_total,
            "avg_prerequisites_per_test": prerequisites_total / len(test_cases) if test_cases else 0,
            "risk_distribution": risk_distribution,
            "category_distribution": category_distribution,
            "gamp_category": suite.get('gamp_category', 'unspecified'),
            "estimated_total_duration_minutes": sum(
                test.get('estimated_duration_minutes', 0) for test in test_cases
            )
        }
    
    def _analyze_quality(self, suite: Dict) -> Dict:
        """Analyze quality of test content"""
        test_cases = suite.get('test_cases', [])
        
        # Acceptance criteria analysis
        acceptance_criteria_stats = {
            "empty": 0,
            "generic": 0,
            "specific": 0,
            "total": 0
        }
        
        # Verification method distribution
        verification_methods = []
        
        # Action verb analysis
        action_verbs = []
        
        for test in test_cases:
            # Test-level acceptance criteria
            test_criteria = test.get('acceptance_criteria', [])
            for criterion in test_criteria:
                acceptance_criteria_stats["total"] += 1
                if not criterion or criterion == "":
                    acceptance_criteria_stats["empty"] += 1
                elif "matches expected" in criterion.lower() or "as expected" in criterion.lower():
                    acceptance_criteria_stats["generic"] += 1
                else:
                    acceptance_criteria_stats["specific"] += 1
            
            # Step-level analysis
            for step in test.get('test_steps', []):
                # Acceptance criteria at step level
                step_criteria = step.get('acceptance_criteria', '')
                if step_criteria:
                    acceptance_criteria_stats["total"] += 1
                    if step_criteria == "" or not step_criteria:
                        acceptance_criteria_stats["empty"] += 1
                    elif "matches expected" in step_criteria.lower() or "result matches" in step_criteria.lower():
                        acceptance_criteria_stats["generic"] += 1
                    else:
                        acceptance_criteria_stats["specific"] += 1
                
                # Verification methods
                method = step.get('verification_method', 'unspecified')
                verification_methods.append(method)
                
                # Extract action verb (first word of action)
                action = step.get('action', '')
                if action:
                    first_word = action.split()[0].lower() if action.split() else ''
                    if first_word:
                        action_verbs.append(first_word)
        
        # Calculate verification diversity
        method_counts = Counter(verification_methods)
        total_methods = len(verification_methods)
        diversity_index = len(method_counts) / 4.0 if total_methods > 0 else 0  # 4 expected types
        
        # Calculate action verb diversity
        verb_counts = Counter(action_verbs)
        unique_verbs = len(verb_counts)
        total_verbs = len(action_verbs)
        verb_diversity = unique_verbs / total_verbs if total_verbs > 0 else 0
        
        # Specificity score
        specificity_score = acceptance_criteria_stats["specific"] / acceptance_criteria_stats["total"] \
            if acceptance_criteria_stats["total"] > 0 else 0
        
        return {
            "acceptance_criteria_analysis": acceptance_criteria_stats,
            "specificity_score": round(specificity_score, 3),
            "verification_methods": dict(method_counts),
            "verification_diversity_index": round(diversity_index, 3),
            "unique_action_verbs": unique_verbs,
            "total_action_verbs": total_verbs,
            "verb_diversity_ratio": round(verb_diversity, 3),
            "top_5_verbs": dict(verb_counts.most_common(5))
        }
    
    def _assess_alcoa_compliance(self, suite: Dict) -> Dict:
        """Assess ALCOA+ compliance based on field presence and quality"""
        test_cases = suite.get('test_cases', [])
        
        compliance_checks = {
            "attributable": {
                "performed_by_present": 0,
                "reviewed_by_present": 0,
                "total_checks": 0
            },
            "legible": {
                "clear_format": True,  # JSON is inherently legible
                "score": 1.0
            },
            "contemporaneous": {
                "timestamp_required": 0,
                "execution_timestamp": 0,
                "total_checks": 0
            },
            "original": {
                "data_integrity_specified": 0,
                "total_checks": len(test_cases)
            },
            "accurate": {
                "specific_criteria": 0,
                "measurable_criteria": 0,
                "total_criteria": 0
            },
            "complete": {
                "all_required_fields": 0,
                "missing_fields": [],
                "total_checks": 0
            },
            "consistent": {
                "format_consistency": True,
                "naming_consistency": True
            },
            "enduring": {
                "retention_period_specified": 0,
                "total_checks": len(test_cases)
            },
            "available": {
                "accessible_format": True,
                "score": 1.0
            }
        }
        
        required_test_fields = [
            'test_id', 'test_name', 'objective', 'test_steps', 
            'acceptance_criteria', 'regulatory_basis'
        ]
        
        for test in test_cases:
            # Attributable
            if test.get('reviewed_by'):
                compliance_checks["attributable"]["reviewed_by_present"] += 1
            compliance_checks["attributable"]["total_checks"] += 1
            
            # Check steps for performed_by
            for step in test.get('test_steps', []):
                if step.get('performed_by'):
                    compliance_checks["attributable"]["performed_by_present"] += 1
                compliance_checks["attributable"]["total_checks"] += 1
                
                # Contemporaneous
                if step.get('timestamp_required'):
                    compliance_checks["contemporaneous"]["timestamp_required"] += 1
                compliance_checks["contemporaneous"]["total_checks"] += 1
            
            # Original - check for data integrity requirements
            if test.get('data_integrity_requirements'):
                compliance_checks["original"]["data_integrity_specified"] += 1
            
            # Accurate - analyze acceptance criteria
            for criterion in test.get('acceptance_criteria', []):
                compliance_checks["accurate"]["total_criteria"] += 1
                # Check if criterion contains measurable values
                if any(char.isdigit() for char in criterion):
                    compliance_checks["accurate"]["measurable_criteria"] += 1
                if criterion and "matches expected" not in criterion.lower():
                    compliance_checks["accurate"]["specific_criteria"] += 1
            
            # Complete - check required fields
            compliance_checks["complete"]["total_checks"] += 1
            missing = [field for field in required_test_fields if field not in test]
            if not missing:
                compliance_checks["complete"]["all_required_fields"] += 1
            else:
                compliance_checks["complete"]["missing_fields"].extend(missing)
            
            # Enduring - retention period
            if test.get('data_retention_period'):
                compliance_checks["enduring"]["retention_period_specified"] += 1
            
            # Execution timestamp
            if test.get('execution_timestamp_required'):
                compliance_checks["contemporaneous"]["execution_timestamp"] += 1
        
        # Calculate scores
        scores = {}
        
        # Attributable
        if compliance_checks["attributable"]["total_checks"] > 0:
            scores["attributable"] = (
                compliance_checks["attributable"]["performed_by_present"] + 
                compliance_checks["attributable"]["reviewed_by_present"]
            ) / (compliance_checks["attributable"]["total_checks"] * 2)
        else:
            scores["attributable"] = 0
        
        # Legible - JSON format is inherently legible
        scores["legible"] = 0.9
        
        # Contemporaneous
        if compliance_checks["contemporaneous"]["total_checks"] > 0:
            scores["contemporaneous"] = (
                compliance_checks["contemporaneous"]["timestamp_required"] +
                compliance_checks["contemporaneous"]["execution_timestamp"]
            ) / (compliance_checks["contemporaneous"]["total_checks"] * 2)
        else:
            scores["contemporaneous"] = 0
        
        # Original
        scores["original"] = compliance_checks["original"]["data_integrity_specified"] / \
            compliance_checks["original"]["total_checks"] if compliance_checks["original"]["total_checks"] > 0 else 0
        
        # Accurate
        if compliance_checks["accurate"]["total_criteria"] > 0:
            scores["accurate"] = (
                compliance_checks["accurate"]["specific_criteria"] * 0.5 +
                compliance_checks["accurate"]["measurable_criteria"] * 0.5
            ) / compliance_checks["accurate"]["total_criteria"]
        else:
            scores["accurate"] = 0
        
        # Complete
        scores["complete"] = compliance_checks["complete"]["all_required_fields"] / \
            compliance_checks["complete"]["total_checks"] if compliance_checks["complete"]["total_checks"] > 0 else 0
        
        # Consistent - binary check
        scores["consistent"] = 0.8 if compliance_checks["consistent"]["format_consistency"] else 0.4
        
        # Enduring
        scores["enduring"] = compliance_checks["enduring"]["retention_period_specified"] / \
            compliance_checks["enduring"]["total_checks"] if compliance_checks["enduring"]["total_checks"] > 0 else 0
        
        # Available - JSON format
        scores["available"] = 0.9
        
        # Calculate overall score
        overall_score = statistics.mean(scores.values())
        
        return {
            "individual_scores": {k: round(v, 2) for k, v in scores.items()},
            "overall_score": round(overall_score * 10, 2),  # Convert to 0-10 scale
            "detailed_checks": compliance_checks
        }
    
    def _analyze_language(self, suite: Dict) -> Dict:
        """Analyze linguistic quality of test content"""
        test_cases = suite.get('test_cases', [])
        
        # Collect all text
        all_text = []
        technical_terms = []
        measurement_terms = []
        
        # Common technical/pharmaceutical terms
        tech_keywords = [
            'gmp', 'validation', 'qualification', 'calibration', 'deviation',
            'audit', 'compliance', 'temperature', 'humidity', 'pressure',
            'specification', 'tolerance', 'accuracy', 'precision', 'system'
        ]
        
        # Measurement indicators
        measure_patterns = [
            r'\d+\s*°[CF]',  # Temperature
            r'\d+\s*%',  # Percentage
            r'±\s*\d+',  # Tolerance
            r'\d+\s*(minutes?|hours?|seconds?)',  # Time
            r'\d+\s*(mg|g|kg|ml|l)',  # Weight/volume
        ]
        
        for test in test_cases:
            # Collect text from various fields
            all_text.append(test.get('test_name', ''))
            all_text.append(test.get('objective', ''))
            all_text.extend(test.get('acceptance_criteria', []))
            
            for step in test.get('test_steps', []):
                all_text.append(step.get('action', ''))
                all_text.append(step.get('expected_result', ''))
                all_text.append(step.get('acceptance_criteria', ''))
        
        # Join all text for analysis
        combined_text = ' '.join(filter(None, all_text)).lower()
        word_count = len(combined_text.split())
        
        # Count technical terms
        for term in tech_keywords:
            count = combined_text.count(term.lower())
            if count > 0:
                technical_terms.extend([term] * count)
        
        # Find measurement terms
        for pattern in measure_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            measurement_terms.extend(matches)
        
        # Calculate metrics
        tech_density = len(technical_terms) / word_count if word_count > 0 else 0
        measurement_density = len(measurement_terms) / word_count if word_count > 0 else 0
        
        # Analyze clarity (presence of vague terms)
        vague_terms = ['appropriate', 'adequate', 'suitable', 'proper', 'reasonable', 'acceptable']
        vague_count = sum(combined_text.count(term) for term in vague_terms)
        clarity_score = 1 - (vague_count / word_count) if word_count > 0 else 1
        
        return {
            "total_word_count": word_count,
            "technical_term_count": len(technical_terms),
            "technical_density": round(tech_density, 4),
            "measurement_term_count": len(measurement_terms),
            "measurement_density": round(measurement_density, 4),
            "vague_term_count": vague_count,
            "clarity_score": round(clarity_score, 3),
            "top_technical_terms": dict(Counter(technical_terms).most_common(5))
        }
    
    def _check_consistency(self, suite: Dict) -> Dict:
        """Check consistency within the test suite"""
        test_cases = suite.get('test_cases', [])
        
        consistency_metrics = {
            "id_pattern_consistent": True,
            "naming_convention_consistent": True,
            "field_presence_consistent": True,
            "formatting_issues": []
        }
        
        # Check ID patterns
        test_ids = [test.get('test_id', '') for test in test_cases]
        id_patterns = set()
        for test_id in test_ids:
            if test_id:
                # Extract pattern (e.g., "OQ-001" -> "XX-NNN")
                pattern = re.sub(r'[0-9]', 'N', re.sub(r'[A-Z]', 'X', test_id))
                id_patterns.add(pattern)
        
        if len(id_patterns) > 1:
            consistency_metrics["id_pattern_consistent"] = False
            consistency_metrics["formatting_issues"].append(f"Multiple ID patterns found: {id_patterns}")
        
        # Check field presence consistency
        field_presence = []
        for test in test_cases:
            fields = set(test.keys())
            field_presence.append(fields)
        
        if field_presence:
            common_fields = field_presence[0]
            for fields in field_presence[1:]:
                common_fields = common_fields.intersection(fields)
            
            # Check if all tests have same fields
            for i, fields in enumerate(field_presence):
                if fields != field_presence[0]:
                    consistency_metrics["field_presence_consistent"] = False
                    break
        
        # Calculate consistency score
        consistency_score = sum([
            consistency_metrics["id_pattern_consistent"],
            consistency_metrics["naming_convention_consistent"],
            consistency_metrics["field_presence_consistent"]
        ]) / 3
        
        return {
            "consistency_score": round(consistency_score, 2),
            "id_patterns": list(id_patterns),
            "common_field_count": len(common_fields) if field_presence else 0,
            "consistency_checks": consistency_metrics
        }
    
    def analyze_all_suites(self, pattern: str = None) -> Dict:
        """Analyze all test suites matching the pattern"""
        if pattern is None:
            pattern = "output/test_suites/test_suite_*.json"
        
        suite_files = glob.glob(pattern)
        
        if not suite_files:
            return {"error": f"No test suite files found matching pattern: {pattern}"}
        
        all_results = []
        aggregate_metrics = defaultdict(list)
        
        for suite_file in suite_files:
            print(f"Analyzing: {suite_file}")
            result = self.analyze_test_suite(suite_file)
            all_results.append(result)
            
            # Aggregate metrics for statistical analysis
            if "error" not in result:
                aggregate_metrics["test_counts"].append(result["basic_metrics"]["test_count"])
                aggregate_metrics["alcoa_scores"].append(result["alcoa_compliance"]["overall_score"])
                aggregate_metrics["specificity_scores"].append(result["quality_metrics"]["specificity_score"])
                aggregate_metrics["clarity_scores"].append(result["linguistic_metrics"]["clarity_score"])
        
        # Calculate summary statistics
        summary = {
            "total_suites_analyzed": len(suite_files),
            "successful_analyses": len([r for r in all_results if "error" not in r]),
            "aggregate_statistics": {}
        }
        
        for metric_name, values in aggregate_metrics.items():
            if values:
                summary["aggregate_statistics"][metric_name] = {
                    "mean": round(statistics.mean(values), 3),
                    "median": round(statistics.median(values), 3),
                    "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0,
                    "min": round(min(values), 3),
                    "max": round(max(values), 3)
                }
        
        return {
            "summary": summary,
            "individual_results": all_results,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main execution function"""
    print("=" * 60)
    print("Test Suite Analysis - Real Metrics Extraction")
    print("=" * 60)
    
    analyzer = TestSuiteAnalyzer()
    
    # Analyze all test suites
    results = analyzer.analyze_all_suites()
    
    # Save results
    output_file = f"output/cross_validation/test_suite_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAnalysis complete. Results saved to: {output_file}")
    
    # Print summary
    if "summary" in results:
        summary = results["summary"]
        print(f"\nSummary:")
        print(f"  Total suites analyzed: {summary['total_suites_analyzed']}")
        print(f"  Successful analyses: {summary['successful_analyses']}")
        
        if summary["aggregate_statistics"]:
            print("\nAggregate Statistics:")
            for metric, stats in summary["aggregate_statistics"].items():
                print(f"\n  {metric}:")
                for stat_name, value in stats.items():
                    print(f"    {stat_name}: {value}")
    
    return results


if __name__ == "__main__":
    main()