#!/usr/bin/env python3
"""
Statistical Validation for Cross-Validation Folds

This module provides comprehensive statistical validation for k-fold cross-validation
splits in pharmaceutical URS datasets. Implements chi-square tests, KS tests, and
balance metrics with NO FALLBACK LOGIC - all tests fail explicitly with detailed
error messages.

GAMP-5 Compliance: All statistical tests follow pharmaceutical validation standards
with explicit error handling and detailed reporting for regulatory compliance.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of a statistical validation test."""
    test_name: str
    passed: bool
    p_value: float
    statistic: float
    threshold: float
    description: str
    details: dict[str, Any]


class CrossValidationValidator:
    """
    Statistical validator for cross-validation fold quality.
    
    This class performs comprehensive statistical tests to validate that
    k-fold splits maintain proper stratification and balance across GAMP
    categories and complexity distributions.
    """

    def __init__(self, cv_manager=None, config_path: str | None = None):
        """
        Initialize validator with CV manager or config path.
        
        Args:
            cv_manager: CrossValidationManager instance (optional)
            config_path: Path to CV configuration file (optional)
            
        Raises:
            ImportError: If required statistical libraries not available
            RuntimeError: If initialization fails
        """
        if not SCIPY_AVAILABLE:
            raise ImportError(
                "SciPy required for statistical validation. Install with: pip install scipy"
            )

        try:
            self.cv_manager = cv_manager

            # Load config if provided
            if config_path:
                config_path = Path(config_path)
                if not config_path.exists():
                    raise FileNotFoundError(f"Config file not found: {config_path}")

                with open(config_path, encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                # Use default config path
                default_config = Path(__file__).parent / "cv_config.json"
                if default_config.exists():
                    with open(default_config, encoding="utf-8") as f:
                        self.config = json.load(f)
                else:
                    self.config = None

            # Set validation thresholds
            if self.config:
                thresholds = self.config.get("validation_thresholds", {})
                self.chi_square_threshold = thresholds.get("chi_square_p_value_min", 0.05)
                self.ks_test_threshold = thresholds.get("ks_test_p_value_min", 0.05)
                self.category_deviation_max = thresholds.get("category_deviation_max", 0.2)
                self.complexity_deviation_max = thresholds.get("complexity_deviation_max", 0.15)
            else:
                # Default thresholds
                self.chi_square_threshold = 0.05
                self.ks_test_threshold = 0.05
                self.category_deviation_max = 0.2
                self.complexity_deviation_max = 0.15

        except Exception as e:
            raise RuntimeError(f"Failed to initialize CrossValidationValidator: {e!s}")

    def validate_category_distribution(self) -> ValidationResult:
        """
        Test category distribution across folds using chi-square test.
        
        Returns:
            ValidationResult with chi-square test results
            
        Raises:
            RuntimeError: If test cannot be performed or fails
        """
        if not self.cv_manager:
            raise RuntimeError("CV manager not provided")

        try:
            # Collect category counts per fold
            fold_categories = {}
            categories = ["Category 3", "Category 4", "Category 5", "Ambiguous"]

            for fold_num in range(1, 6):
                fold_data = self.cv_manager.get_fold(fold_num)
                test_docs = fold_data["test"]

                category_counts = dict.fromkeys(categories, 0)
                for doc in test_docs:
                    if doc.normalized_category in category_counts:
                        category_counts[doc.normalized_category] += 1

                fold_categories[f"fold_{fold_num}"] = category_counts

            # Create contingency table for chi-square test
            # Rows: categories, Columns: folds
            observed = []
            for category in categories:
                row = []
                for fold_num in range(1, 6):
                    count = fold_categories[f"fold_{fold_num}"][category]
                    row.append(count)
                observed.append(row)

            # Perform chi-square test
            chi2_stat, p_value = stats.chi2_contingency(observed)[:2]

            # Determine if test passed
            test_passed = p_value >= self.chi_square_threshold

            return ValidationResult(
                test_name="Category Distribution Chi-Square Test",
                passed=test_passed,
                p_value=p_value,
                statistic=chi2_stat,
                threshold=self.chi_square_threshold,
                description="Tests independence of GAMP categories across folds (H0: categories are independent of fold assignment)",
                details={
                    "observed_frequencies": {
                        f"{categories[i]}": observed[i] for i in range(len(categories))
                    },
                    "fold_categories": fold_categories,
                    "degrees_of_freedom": (len(categories) - 1) * (5 - 1),
                    "interpretation": "PASSED: Categories well-balanced across folds" if test_passed else "FAILED: Significant category imbalance detected"
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to validate category distribution: {e!s}")

    def validate_complexity_distribution(self) -> ValidationResult:
        """
        Test complexity score distribution across folds using Kolmogorov-Smirnov test.
        
        Returns:
            ValidationResult with KS test results
            
        Raises:
            RuntimeError: If test cannot be performed or fails
        """
        if not self.cv_manager:
            raise RuntimeError("CV manager not provided")

        try:
            # Collect complexity scores per fold
            fold_complexities = {}
            all_complexities = []

            for fold_num in range(1, 6):
                fold_data = self.cv_manager.get_fold(fold_num)
                test_docs = fold_data["test"]

                fold_scores = [doc.complexity_score for doc in test_docs]
                fold_complexities[f"fold_{fold_num}"] = fold_scores
                all_complexities.extend(fold_scores)

            # Perform KS tests comparing each fold to overall distribution
            ks_results = {}
            min_p_value = 1.0
            max_ks_stat = 0.0

            for fold_num in range(1, 6):
                fold_key = f"fold_{fold_num}"
                fold_scores = fold_complexities[fold_key]

                if len(fold_scores) == 0:
                    raise RuntimeError(f"No complexity scores found for {fold_key}")

                # KS test against overall distribution
                ks_stat, ks_p = stats.ks_2samp(fold_scores, all_complexities)

                ks_results[fold_key] = {
                    "ks_statistic": ks_stat,
                    "p_value": ks_p,
                    "sample_size": len(fold_scores),
                    "mean": sum(fold_scores) / len(fold_scores),
                    "std": self._calculate_std(fold_scores)
                }

                min_p_value = min(min_p_value, ks_p)
                max_ks_stat = max(max_ks_stat, ks_stat)

            # Overall test result based on minimum p-value
            test_passed = min_p_value >= self.ks_test_threshold

            return ValidationResult(
                test_name="Complexity Distribution KS Test",
                passed=test_passed,
                p_value=min_p_value,
                statistic=max_ks_stat,
                threshold=self.ks_test_threshold,
                description="Tests if complexity scores are similarly distributed across folds (H0: same distribution)",
                details={
                    "fold_results": ks_results,
                    "overall_complexity_stats": {
                        "mean": sum(all_complexities) / len(all_complexities),
                        "std": self._calculate_std(all_complexities),
                        "min": min(all_complexities),
                        "max": max(all_complexities),
                        "count": len(all_complexities)
                    },
                    "worst_fold": min(ks_results.keys(), key=lambda k: ks_results[k]["p_value"]),
                    "interpretation": "PASSED: Complexity well-distributed across folds" if test_passed else "FAILED: Significant complexity imbalance detected"
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to validate complexity distribution: {e!s}")

    def validate_fold_balance(self) -> ValidationResult:
        """
        Test overall fold balance using coefficient of variation.
        
        Returns:
            ValidationResult with balance metrics
            
        Raises:
            RuntimeError: If test cannot be performed or fails
        """
        if not self.cv_manager:
            raise RuntimeError("CV manager not provided")

        try:
            # Collect fold sizes and characteristics
            fold_sizes = []
            fold_requirements = []
            category_coefficients = {}

            # Get category distribution per fold
            categories = ["Category 3", "Category 4", "Category 5", "Ambiguous"]
            category_counts = {cat: [] for cat in categories}

            for fold_num in range(1, 6):
                fold_data = self.cv_manager.get_fold(fold_num)
                test_docs = fold_data["test"]

                fold_sizes.append(len(test_docs))
                fold_requirements.append(sum(doc.total_requirements for doc in test_docs))

                # Count categories
                fold_category_counts = dict.fromkeys(categories, 0)
                for doc in test_docs:
                    if doc.normalized_category in fold_category_counts:
                        fold_category_counts[doc.normalized_category] += 1

                for cat in categories:
                    category_counts[cat].append(fold_category_counts[cat])

            # Calculate coefficients of variation
            size_cv = self._coefficient_of_variation(fold_sizes)
            req_cv = self._coefficient_of_variation(fold_requirements)

            for cat in categories:
                counts = category_counts[cat]
                category_coefficients[cat] = self._coefficient_of_variation(counts)

            # Check against thresholds
            max_category_cv = max(category_coefficients.values())
            balance_passed = (size_cv <= self.category_deviation_max and
                            max_category_cv <= self.category_deviation_max)

            return ValidationResult(
                test_name="Fold Balance Analysis",
                passed=balance_passed,
                p_value=1.0 - max(size_cv, max_category_cv),  # Pseudo p-value
                statistic=max_category_cv,
                threshold=self.category_deviation_max,
                description="Tests overall balance of document counts and categories across folds",
                details={
                    "fold_sizes": fold_sizes,
                    "fold_requirements": fold_requirements,
                    "size_coefficient_of_variation": size_cv,
                    "requirements_coefficient_of_variation": req_cv,
                    "category_coefficients": category_coefficients,
                    "max_category_cv": max_category_cv,
                    "balance_metrics": {
                        "size_balance": "Good" if size_cv <= 0.1 else "Acceptable" if size_cv <= 0.2 else "Poor",
                        "category_balance": "Good" if max_category_cv <= 0.1 else "Acceptable" if max_category_cv <= 0.2 else "Poor"
                    },
                    "interpretation": "PASSED: Folds are well-balanced" if balance_passed else "FAILED: Significant fold imbalance detected"
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to validate fold balance: {e!s}")

    def validate_stratification_quality(self) -> ValidationResult:
        """
        Test the quality of stratification across multiple dimensions.
        
        Returns:
            ValidationResult with stratification quality metrics
            
        Raises:
            RuntimeError: If test cannot be performed or fails
        """
        if not self.cv_manager:
            raise RuntimeError("CV manager not provided")

        try:
            # Analyze stratification across GAMP categories and complexity levels
            stratification_metrics = {
                "gamp_category_balance": {},
                "complexity_level_balance": {},
                "domain_balance": {},
                "combined_balance": {}
            }

            # Collect data per fold
            fold_data_collection = {}
            for fold_num in range(1, 6):
                fold_data = self.cv_manager.get_fold(fold_num)
                test_docs = fold_data["test"]

                fold_data_collection[f"fold_{fold_num}"] = {
                    "gamp_categories": [doc.normalized_category for doc in test_docs],
                    "complexity_levels": [doc.complexity_level for doc in test_docs],
                    "domains": [doc.domain for doc in test_docs],
                    "complexity_scores": [doc.complexity_score for doc in test_docs]
                }

            # Calculate balance metrics for each stratification dimension
            dimensions = ["gamp_categories", "complexity_levels", "domains"]
            overall_balance_score = 0.0

            for dimension in dimensions:
                # Get unique values across all folds
                all_values = set()
                for fold_key, fold_info in fold_data_collection.items():
                    all_values.update(fold_info[dimension])

                # Calculate distribution for each value
                value_distributions = {}
                for value in all_values:
                    value_counts = []
                    for fold_key, fold_info in fold_data_collection.items():
                        count = fold_info[dimension].count(value)
                        value_counts.append(count)

                    if sum(value_counts) > 0:  # Only calculate if value appears
                        cv = self._coefficient_of_variation(value_counts)
                        value_distributions[value] = {
                            "counts_per_fold": value_counts,
                            "coefficient_of_variation": cv,
                            "total_count": sum(value_counts)
                        }

                # Calculate dimension balance score
                if value_distributions:
                    avg_cv = sum(dist["coefficient_of_variation"] for dist in value_distributions.values()) / len(value_distributions)
                    stratification_metrics[f"{dimension[:-1]}_balance"] = {
                        "value_distributions": value_distributions,
                        "average_coefficient_of_variation": avg_cv,
                        "balance_quality": "Excellent" if avg_cv <= 0.1 else "Good" if avg_cv <= 0.2 else "Acceptable" if avg_cv <= 0.3 else "Poor"
                    }
                    overall_balance_score += (1.0 - min(avg_cv, 1.0))

            # Normalize overall balance score
            overall_balance_score /= len(dimensions)

            # Test passes if overall balance is acceptable
            stratification_passed = overall_balance_score >= 0.7  # 70% balance threshold

            return ValidationResult(
                test_name="Stratification Quality Analysis",
                passed=stratification_passed,
                p_value=overall_balance_score,  # Use balance score as pseudo p-value
                statistic=1.0 - overall_balance_score,
                threshold=0.3,  # Max acceptable imbalance
                description="Tests quality of stratification across GAMP categories, complexity levels, and domains",
                details={
                    "stratification_metrics": stratification_metrics,
                    "overall_balance_score": overall_balance_score,
                    "fold_data_summary": {
                        fold_key: {
                            "test_count": len(fold_info["gamp_categories"]),
                            "unique_categories": len(set(fold_info["gamp_categories"])),
                            "complexity_range": f"{min(fold_info['complexity_scores']):.2f}-{max(fold_info['complexity_scores']):.2f}" if fold_info["complexity_scores"] else "N/A"
                        }
                        for fold_key, fold_info in fold_data_collection.items()
                    },
                    "interpretation": "PASSED: High-quality stratification achieved" if stratification_passed else "FAILED: Stratification quality below threshold"
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to validate stratification quality: {e!s}")

    def run_comprehensive_validation(self) -> dict[str, Any]:
        """
        Run all validation tests and generate comprehensive report.
        
        Returns:
            Dictionary containing all validation results and summary
            
        Raises:
            RuntimeError: If validation suite fails
        """
        try:
            validation_report = {
                "timestamp": datetime.now().isoformat(),
                "validation_suite": "Comprehensive Cross-Validation Fold Validation",
                "dataset_info": {
                    "total_documents": len(self.cv_manager.documents) if self.cv_manager else "Unknown",
                    "total_folds": 5
                },
                "test_results": {},
                "overall_summary": {
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "overall_passed": False
                },
                "recommendations": []
            }

            # Define validation tests
            validation_tests = [
                ("category_distribution", self.validate_category_distribution),
                ("complexity_distribution", self.validate_complexity_distribution),
                ("fold_balance", self.validate_fold_balance),
                ("stratification_quality", self.validate_stratification_quality)
            ]

            # Run each test
            for test_name, test_func in validation_tests:
                try:
                    result = test_func()
                    validation_report["test_results"][test_name] = {
                        "test_name": result.test_name,
                        "passed": result.passed,
                        "p_value": result.p_value,
                        "statistic": result.statistic,
                        "threshold": result.threshold,
                        "description": result.description,
                        "details": result.details
                    }

                    if result.passed:
                        validation_report["overall_summary"]["tests_passed"] += 1
                    else:
                        validation_report["overall_summary"]["tests_failed"] += 1
                        validation_report["recommendations"].append(f"Address {result.test_name} failure: {result.details.get('interpretation', 'See test details')}")

                except Exception as e:
                    validation_report["test_results"][test_name] = {
                        "test_name": test_name,
                        "passed": False,
                        "error": str(e),
                        "description": f"Test failed to execute: {e!s}"
                    }
                    validation_report["overall_summary"]["tests_failed"] += 1
                    validation_report["recommendations"].append(f"Fix {test_name} execution error: {e!s}")

            # Determine overall pass/fail
            total_tests = validation_report["overall_summary"]["tests_passed"] + validation_report["overall_summary"]["tests_failed"]
            validation_report["overall_summary"]["overall_passed"] = validation_report["overall_summary"]["tests_failed"] == 0
            validation_report["overall_summary"]["pass_rate"] = validation_report["overall_summary"]["tests_passed"] / total_tests if total_tests > 0 else 0

            # Add general recommendations
            if validation_report["overall_summary"]["overall_passed"]:
                validation_report["recommendations"].insert(0, "PASSED: Cross-validation folds pass all statistical validation tests")
                validation_report["recommendations"].append("Dataset is ready for thesis cross-validation experiments")
            else:
                validation_report["recommendations"].insert(0, "WARNING: Cross-validation folds failed one or more validation tests")
                validation_report["recommendations"].append("Consider regenerating folds with improved stratification")

            return validation_report

        except Exception as e:
            raise RuntimeError(f"Failed to run comprehensive validation: {e!s}")

    def generate_validation_report(self, output_path: str | None = None) -> str:
        """
        Generate and save a comprehensive validation report.
        
        Args:
            output_path: Path to save report (optional)
            
        Returns:
            Path to generated report file
            
        Raises:
            RuntimeError: If report generation fails
        """
        try:
            # Run comprehensive validation
            validation_results = self.run_comprehensive_validation()

            # Set output path
            if output_path is None:
                output_path = Path(__file__).parent / f"cv_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            output_path = Path(output_path)

            # Save report
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)

            return str(output_path)

        except Exception as e:
            raise RuntimeError(f"Failed to generate validation report: {e!s}")

    def _calculate_std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def _coefficient_of_variation(self, values: list[float]) -> float:
        """Calculate coefficient of variation (std/mean)."""
        if not values or len(values) <= 1:
            return 0.0

        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0

        std_val = self._calculate_std(values)
        return std_val / mean_val


def validate_cross_validation_folds(cv_manager, config_path: str | None = None) -> dict[str, Any]:
    """
    Factory function to validate cross-validation folds.
    
    Args:
        cv_manager: CrossValidationManager instance
        config_path: Optional path to configuration file
        
    Returns:
        Dictionary containing comprehensive validation results
        
    Raises:
        RuntimeError: If validation fails
    """
    try:
        validator = CrossValidationValidator(cv_manager, config_path)
        return validator.run_comprehensive_validation()

    except Exception as e:
        raise RuntimeError(f"Failed to validate cross-validation folds: {e!s}")


if __name__ == "__main__":
    """
    Example usage and validation execution.
    """
    try:
        # Import CV manager (assuming it's available)
        from cv_manager import load_cv_manager

        print("Loading cross-validation manager...")
        cv_manager = load_cv_manager()

        print("Running comprehensive fold validation...")
        validator = CrossValidationValidator(cv_manager)

        # Run comprehensive validation
        validation_results = validator.run_comprehensive_validation()

        # Print summary
        summary = validation_results["overall_summary"]
        print("\\nValidation Summary:")
        print(f"Tests passed: {summary['tests_passed']}")
        print(f"Tests failed: {summary['tests_failed']}")
        print(f"Overall result: {'PASSED' if summary['overall_passed'] else 'FAILED'}")
        print(f"Pass rate: {summary['pass_rate']:.1%}")

        # Print recommendations
        print("\\nRecommendations:")
        for rec in validation_results["recommendations"]:
            print(f"  - {rec}")

        # Generate detailed report
        report_path = validator.generate_validation_report()
        print(f"\\nDetailed report saved to: {report_path}")

    except ImportError as e:
        print(f"Import error (expected in isolated testing): {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
