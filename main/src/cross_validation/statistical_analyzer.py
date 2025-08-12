"""
Statistical Analysis for Cross-Validation Framework

This module provides comprehensive statistical analysis including significance testing,
confidence intervals, effect size calculations, and multiple comparison corrections
with full GAMP-5 compliance and pharmaceutical validation standards.

Key Features:
- Paired t-tests for fold comparisons
- Wilcoxon signed-rank test for non-parametric data
- 95% confidence intervals with bootstrap resampling
- Cohen's d effect size calculations
- Bonferroni and Holm-Bonferroni multiple comparison corrections
- Statistical power analysis
- Normality testing and assumptions validation
"""

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy import stats
from scipy.stats import bootstrap


class StatisticalTest(BaseModel):
    """Results of a single statistical test."""
    test_name: str = Field(description="Name of the statistical test")
    test_type: str = Field(description="Type of test (parametric, non-parametric)")
    statistic: float = Field(description="Test statistic value")
    p_value: float = Field(description="P-value of the test")
    degrees_of_freedom: int | None = Field(default=None, description="Degrees of freedom")
    effect_size: float | None = Field(default=None, description="Effect size (Cohen's d)")
    effect_size_interpretation: str | None = Field(default=None, description="Effect size interpretation")
    is_significant: bool = Field(description="Whether result is statistically significant (p<0.05)")
    corrected_p_value: float | None = Field(default=None, description="P-value after multiple comparison correction")
    is_significant_corrected: bool | None = Field(default=None, description="Significance after correction")
    sample_size: int = Field(description="Sample size used in test")
    power: float | None = Field(default=None, description="Statistical power of the test")


class ConfidenceInterval(BaseModel):
    """Confidence interval for a metric."""
    metric_name: str = Field(description="Name of the metric")
    point_estimate: float = Field(description="Point estimate (mean)")
    confidence_level: float = Field(description="Confidence level (e.g., 0.95)")
    lower_bound: float = Field(description="Lower bound of confidence interval")
    upper_bound: float = Field(description="Upper bound of confidence interval")
    margin_of_error: float = Field(description="Margin of error")
    method: str = Field(description="Method used (bootstrap, t-distribution, etc.)")
    sample_size: int = Field(description="Sample size")
    standard_error: float | None = Field(default=None, description="Standard error")


class AssumptionTest(BaseModel):
    """Results of statistical assumption testing."""
    assumption_name: str = Field(description="Name of the assumption being tested")
    test_name: str = Field(description="Name of the test used")
    statistic: float = Field(description="Test statistic")
    p_value: float = Field(description="P-value")
    assumption_met: bool = Field(description="Whether assumption is satisfied")
    interpretation: str = Field(description="Interpretation of the result")


class StatisticalSummary(BaseModel):
    """Comprehensive statistical analysis summary."""
    experiment_id: str = Field(description="Experiment identifier")
    analysis_type: str = Field(description="Type of analysis performed")
    sample_size: int = Field(description="Total sample size")

    # Descriptive statistics
    descriptive_stats: dict[str, dict[str, float]] = Field(description="Descriptive statistics by metric")

    # Statistical tests
    statistical_tests: list[StatisticalTest] = Field(description="All statistical tests performed")

    # Confidence intervals
    confidence_intervals: list[ConfidenceInterval] = Field(description="Confidence intervals for key metrics")

    # Assumption testing
    assumption_tests: list[AssumptionTest] = Field(description="Statistical assumption test results")

    # Multiple comparison corrections
    multiple_comparison_method: str | None = Field(default=None, description="Multiple comparison correction method")
    family_wise_error_rate: float | None = Field(default=None, description="Family-wise error rate")

    # Target validation
    meets_significance_targets: bool = Field(description="Whether significance targets are met")
    significant_improvements: list[str] = Field(description="Metrics showing significant improvement")

    # Recommendations
    recommendations: list[str] = Field(description="Statistical recommendations")
    limitations: list[str] = Field(description="Analysis limitations and caveats")

    analysis_timestamp: str = Field(description="When analysis was performed")


class StatisticalAnalyzer:
    """
    Statistical analyzer for cross-validation experiments.

    This class provides comprehensive statistical analysis with proper assumption
    testing, effect size calculations, and multiple comparison corrections following
    pharmaceutical validation standards and GAMP-5 compliance.
    """

    # Effect size interpretation thresholds (Cohen's d)
    EFFECT_SIZE_THRESHOLDS = {
        0.2: "small",
        0.5: "medium",
        0.8: "large",
        1.2: "very_large"
    }

    def __init__(self,
                 alpha: float = 0.05,
                 confidence_level: float = 0.95,
                 output_directory: str | Path | None = None):
        """
        Initialize the StatisticalAnalyzer.

        Args:
            alpha: Significance level (default 0.05)
            confidence_level: Confidence level for intervals (default 0.95)
            output_directory: Directory to store analysis reports
        """
        self.alpha = alpha
        self.confidence_level = confidence_level
        self.logger = logging.getLogger(__name__)
        self.output_directory = Path(output_directory) if output_directory else Path.cwd() / "statistical_reports"
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Suppress scipy warnings for cleaner output
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="scipy")

        self.logger.info(f"StatisticalAnalyzer initialized with α={alpha}, CI={confidence_level}")

    def paired_t_test(self,
                     group1: list[float],
                     group2: list[float],
                     test_name: str = "paired_t_test",
                     alternative: str = "two-sided") -> StatisticalTest:
        """
        Perform paired t-test between two related samples.

        Args:
            group1: First group of measurements
            group2: Second group of measurements (paired)
            test_name: Name for the test
            alternative: Alternative hypothesis ('two-sided', 'less', 'greater')

        Returns:
            Statistical test results

        Raises:
            ValueError: If groups have different lengths or insufficient data
        """
        if len(group1) != len(group2):
            msg = f"Groups must have equal length: {len(group1)} vs {len(group2)}"
            raise ValueError(msg)

        if len(group1) < 3:
            msg = f"Insufficient data for paired t-test: n={len(group1)}"
            raise ValueError(msg)

        # Convert to numpy arrays
        arr1 = np.array(group1)
        arr2 = np.array(group2)

        # Calculate differences
        differences = arr1 - arr2

        # Perform paired t-test
        try:
            t_statistic, p_value = stats.ttest_rel(arr1, arr2, alternative=alternative)

            # Calculate effect size (Cohen's d for paired samples)
            effect_size = np.mean(differences) / np.std(differences, ddof=1) if np.std(differences, ddof=1) > 0 else 0.0

            # Calculate statistical power (approximate)
            power = self._calculate_power_paired_t(effect_size, len(group1), self.alpha)

            return StatisticalTest(
                test_name=test_name,
                test_type="parametric",
                statistic=float(t_statistic),
                p_value=float(p_value),
                degrees_of_freedom=len(group1) - 1,
                effect_size=float(effect_size),
                effect_size_interpretation=self._interpret_effect_size(abs(effect_size)),
                is_significant=float(p_value) < self.alpha,
                sample_size=len(group1),
                power=float(power)
            )

        except Exception as e:
            self.logger.exception(f"Paired t-test failed: {e!s}")
            msg = f"Paired t-test calculation failed: {e!s}"
            raise ValueError(msg) from e

    def wilcoxon_signed_rank_test(self,
                                 group1: list[float],
                                 group2: list[float],
                                 test_name: str = "wilcoxon_signed_rank") -> StatisticalTest:
        """
        Perform Wilcoxon signed-rank test (non-parametric paired test).

        Args:
            group1: First group of measurements
            group2: Second group of measurements (paired)
            test_name: Name for the test

        Returns:
            Statistical test results
        """
        if len(group1) != len(group2):
            msg = f"Groups must have equal length: {len(group1)} vs {len(group2)}"
            raise ValueError(msg)

        if len(group1) < 6:  # Minimum for Wilcoxon
            msg = f"Insufficient data for Wilcoxon test: n={len(group1)}"
            raise ValueError(msg)

        try:
            # Perform Wilcoxon signed-rank test
            statistic, p_value = stats.wilcoxon(group1, group2, alternative="two-sided")

            # Calculate effect size (r = Z / sqrt(N))
            n = len(group1)
            z_score = stats.norm.ppf(1 - p_value / 2)  # Convert p to z
            effect_size = abs(z_score) / np.sqrt(n)

            return StatisticalTest(
                test_name=test_name,
                test_type="non_parametric",
                statistic=float(statistic),
                p_value=float(p_value),
                effect_size=float(effect_size),
                effect_size_interpretation=self._interpret_effect_size_wilcoxon(effect_size),
                is_significant=float(p_value) < self.alpha,
                sample_size=n
            )

        except Exception as e:
            self.logger.exception(f"Wilcoxon test failed: {e!s}")
            msg = f"Wilcoxon test calculation failed: {e!s}"
            raise ValueError(msg) from e

    def calculate_confidence_interval(self,
                                    data: list[float],
                                    metric_name: str = "value",
                                    method: str = "bootstrap") -> ConfidenceInterval:
        """
        Calculate confidence interval for a metric.

        Args:
            data: Sample data
            metric_name: Name of the metric (default: "value")
            method: Method to use ('bootstrap', 't_distribution', 'normal')

        Returns:
            Confidence interval results
        """
        if not data or len(data) < 2:
            msg = "Insufficient data for confidence interval calculation"
            raise ValueError(msg)

        data_array = np.array(data)
        point_estimate = float(np.mean(data_array))
        len(data_array)

        if method == "bootstrap":
            return self._bootstrap_confidence_interval(data_array, metric_name, point_estimate)
        if method == "t_distribution":
            return self._t_confidence_interval(data_array, metric_name, point_estimate)
        if method == "normal":
            return self._normal_confidence_interval(data_array, metric_name, point_estimate)
        msg = f"Unknown confidence interval method: {method}"
        raise ValueError(msg)

    def _bootstrap_confidence_interval(self,
                                     data: np.ndarray,
                                     metric_name: str,
                                     point_estimate: float) -> ConfidenceInterval:
        """Calculate bootstrap confidence interval."""
        try:
            # Define the statistic function
            def statistic_func(x, axis):
                return np.mean(x, axis=axis)

            # Perform bootstrap resampling
            rng = np.random.RandomState(42)  # For reproducibility
            res = bootstrap((data,), statistic_func, n_resamples=10000,
                          confidence_level=self.confidence_level, random_state=rng)

            lower_bound = float(res.confidence_interval.low)
            upper_bound = float(res.confidence_interval.high)
            margin_of_error = max(abs(upper_bound - point_estimate), abs(point_estimate - lower_bound))

            return ConfidenceInterval(
                metric_name=metric_name,
                point_estimate=point_estimate,
                confidence_level=self.confidence_level,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                margin_of_error=margin_of_error,
                method="bootstrap",
                sample_size=len(data)
            )

        except Exception as e:
            self.logger.warning(f"Bootstrap CI failed, falling back to t-distribution: {e!s}")
            return self._t_confidence_interval(data, metric_name, point_estimate)

    def _t_confidence_interval(self,
                              data: np.ndarray,
                              metric_name: str,
                              point_estimate: float) -> ConfidenceInterval:
        """Calculate t-distribution based confidence interval."""
        n = len(data)
        std_error = float(np.std(data, ddof=1) / np.sqrt(n))

        # t-critical value
        alpha = 1 - self.confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df=n-1)

        margin_of_error = float(t_critical * std_error)
        lower_bound = point_estimate - margin_of_error
        upper_bound = point_estimate + margin_of_error

        return ConfidenceInterval(
            metric_name=metric_name,
            point_estimate=point_estimate,
            confidence_level=self.confidence_level,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            margin_of_error=margin_of_error,
            method="t_distribution",
            sample_size=n,
            standard_error=std_error
        )

    def _normal_confidence_interval(self,
                                  data: np.ndarray,
                                  metric_name: str,
                                  point_estimate: float) -> ConfidenceInterval:
        """Calculate normal distribution based confidence interval."""
        n = len(data)
        std_error = float(np.std(data, ddof=1) / np.sqrt(n))

        # z-critical value
        alpha = 1 - self.confidence_level
        z_critical = stats.norm.ppf(1 - alpha/2)

        margin_of_error = float(z_critical * std_error)
        lower_bound = point_estimate - margin_of_error
        upper_bound = point_estimate + margin_of_error

        return ConfidenceInterval(
            metric_name=metric_name,
            point_estimate=point_estimate,
            confidence_level=self.confidence_level,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            margin_of_error=margin_of_error,
            method="normal",
            sample_size=n,
            standard_error=std_error
        )

    def test_normality(self, data: list[float], test_name: str = "shapiro_wilk") -> AssumptionTest:
        """
        Test for normality assumption.

        Args:
            data: Sample data
            test_name: Name of normality test ('shapiro_wilk', 'jarque_bera', 'anderson')

        Returns:
            Assumption test results
        """
        data_array = np.array(data)

        if len(data_array) < 3:
            msg = "Insufficient data for normality testing"
            raise ValueError(msg)

        try:
            statistic = 0.0
            p_value = 0.0

            if test_name == "shapiro_wilk":
                if len(data_array) > 5000:
                    test_name = "jarque_bera"
                    statistic, p_value = stats.jarque_bera(data_array)
                else:
                    statistic, p_value = stats.shapiro(data_array)
            elif test_name == "jarque_bera":
                statistic, p_value = stats.jarque_bera(data_array)

            assumption_met = p_value > self.alpha  # Fail to reject null (normality)

            interpretation = (
                f"Data appears to be normally distributed (p={p_value:.4f})" if assumption_met
                else f"Data significantly deviates from normality (p={p_value:.4f})"
            )

            return AssumptionTest(
                assumption_name="normality",
                test_name=test_name,
                statistic=float(statistic),
                p_value=float(p_value),
                assumption_met=assumption_met,
                interpretation=interpretation
            )

        except Exception as e:
            self.logger.exception(f"Normality test failed: {e!s}")
            msg = f"Normality test calculation failed: {e!s}"
            raise ValueError(msg) from e

    def apply_multiple_comparison_correction(self,
                                           p_values: list[float],
                                           method: str = "holm_bonferroni") -> tuple[list[float], float]:
        """
        Apply multiple comparison correction to p-values.

        Args:
            p_values: List of uncorrected p-values
            method: Correction method ('bonferroni', 'holm_bonferroni', 'fdr_bh')

        Returns:
            Tuple of (corrected_p_values, family_wise_error_rate)
        """
        if not p_values:
            return [], 0.0

        p_array = np.array(p_values)

        try:
            if method == "bonferroni":
                corrected_p = p_array * len(p_array)
                corrected_p = np.minimum(corrected_p, 1.0)  # Cap at 1.0
                family_wise_error_rate = self.alpha

            elif method == "holm_bonferroni":
                # Holm-Bonferroni sequential method
                sorted_indices = np.argsort(p_array)
                sorted_p = p_array[sorted_indices]
                n = len(p_array)

                corrected_p = np.zeros_like(p_array)
                for i, idx in enumerate(sorted_indices):
                    correction_factor = n - i
                    corrected_p[idx] = min(1.0, sorted_p[i] * correction_factor)

                # Ensure monotonicity
                sorted_corrected = corrected_p[sorted_indices]
                for i in range(1, len(sorted_corrected)):
                    sorted_corrected[i] = max(sorted_corrected[i], sorted_corrected[i-1])
                corrected_p[sorted_indices] = sorted_corrected

                family_wise_error_rate = self.alpha

            elif method == "fdr_bh":
                # Benjamini-Hochberg FDR control
                sorted_indices = np.argsort(p_array)
                sorted_p = p_array[sorted_indices]
                n = len(p_array)

                corrected_p = np.zeros_like(p_array)
                for i, idx in enumerate(sorted_indices):
                    correction_factor = n / (i + 1)
                    corrected_p[idx] = min(1.0, sorted_p[i] * correction_factor)

                family_wise_error_rate = self.alpha * np.sum(1.0 / np.arange(1, n+1))  # Harmonic number

            else:
                msg = f"Unknown correction method: {method}"
                raise ValueError(msg)

            return corrected_p.tolist(), float(family_wise_error_rate)

        except Exception as e:
            self.logger.exception(f"Multiple comparison correction failed: {e!s}")
            msg = f"Multiple comparison correction failed: {e!s}"
            raise ValueError(msg) from e

    def comprehensive_analysis(self,
                              fold_results: dict[str, list[float]],
                              baseline_results: dict[str, float] | None = None,
                              experiment_id: str = "analysis") -> StatisticalSummary:
        """
        Perform comprehensive statistical analysis of cross-validation results.

        Args:
            fold_results: Dictionary with metric names as keys and fold results as values
            baseline_results: Optional baseline values for comparison
            experiment_id: Experiment identifier

        Returns:
            Comprehensive statistical summary
        """
        if not fold_results:
            msg = "No fold results provided for analysis"
            raise ValueError(msg)

        # Validate data
        fold_lengths = [len(values) for values in fold_results.values()]
        if not all(length == fold_lengths[0] for length in fold_lengths):
            msg = "All metrics must have the same number of fold results"
            raise ValueError(msg)

        sample_size = fold_lengths[0]
        if sample_size < 3:
            msg = f"Insufficient sample size for analysis: {sample_size}"
            raise ValueError(msg)

        # Calculate descriptive statistics
        descriptive_stats = {}
        for metric, values in fold_results.items():
            values_array = np.array(values)
            descriptive_stats[metric] = {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array, ddof=1)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "median": float(np.median(values_array)),
                "q25": float(np.percentile(values_array, 25)),
                "q75": float(np.percentile(values_array, 75)),
                "coefficient_of_variation": float(np.std(values_array, ddof=1) / np.mean(values_array)) if np.mean(values_array) > 0 else 0.0
            }

        # Perform statistical tests
        statistical_tests = []
        assumption_tests = []
        confidence_intervals = []

        for metric, values in fold_results.items():
            # Test normality assumption
            try:
                normality_test = self.test_normality(values, f"{metric}_normality")
                assumption_tests.append(normality_test)
            except Exception as e:
                self.logger.warning(f"Normality test failed for {metric}: {e!s}")

            # Calculate confidence interval
            try:
                ci = self.calculate_confidence_interval(values, metric, method="bootstrap")
                confidence_intervals.append(ci)
            except Exception as e:
                self.logger.warning(f"Confidence interval calculation failed for {metric}: {e!s}")

            # Compare against baseline if provided
            if baseline_results and metric in baseline_results:
                baseline_value = baseline_results[metric]

                # One-sample t-test against baseline
                try:
                    t_stat, p_val = stats.ttest_1samp(values, baseline_value)
                    effect_size = (np.mean(values) - baseline_value) / np.std(values, ddof=1)

                    test_result = StatisticalTest(
                        test_name=f"{metric}_vs_baseline",
                        test_type="parametric",
                        statistic=float(t_stat),
                        p_value=float(p_val),
                        degrees_of_freedom=len(values) - 1,
                        effect_size=float(effect_size),
                        effect_size_interpretation=self._interpret_effect_size(abs(effect_size)),
                        is_significant=float(p_val) < self.alpha,
                        sample_size=len(values)
                    )
                    statistical_tests.append(test_result)

                except Exception as e:
                    self.logger.warning(f"Baseline comparison failed for {metric}: {e!s}")

        # Apply multiple comparison correction if multiple tests
        if len(statistical_tests) > 1:
            p_values = [test.p_value for test in statistical_tests]
            try:
                corrected_p_values, fwer = self.apply_multiple_comparison_correction(p_values, "holm_bonferroni")

                for i, test in enumerate(statistical_tests):
                    test.corrected_p_value = corrected_p_values[i]
                    test.is_significant_corrected = corrected_p_values[i] < self.alpha

                multiple_comparison_method = "holm_bonferroni"
                family_wise_error_rate = fwer

            except Exception as e:
                self.logger.warning(f"Multiple comparison correction failed: {e!s}")
                multiple_comparison_method = None
                family_wise_error_rate = None
        else:
            multiple_comparison_method = None
            family_wise_error_rate = None

        # Determine target compliance
        significant_tests = [test for test in statistical_tests if test.is_significant]
        meets_significance_targets = len(significant_tests) > 0
        significant_improvements = [test.test_name for test in significant_tests
                                  if test.effect_size and test.effect_size > 0]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            descriptive_stats, statistical_tests, assumption_tests, confidence_intervals
        )

        # Identify limitations
        limitations = self._identify_limitations(sample_size, assumption_tests, statistical_tests)

        summary = StatisticalSummary(
            experiment_id=experiment_id,
            analysis_type="cross_validation_comprehensive",
            sample_size=sample_size,
            descriptive_stats=descriptive_stats,
            statistical_tests=statistical_tests,
            confidence_intervals=confidence_intervals,
            assumption_tests=assumption_tests,
            multiple_comparison_method=multiple_comparison_method,
            family_wise_error_rate=family_wise_error_rate,
            meets_significance_targets=meets_significance_targets,
            significant_improvements=significant_improvements,
            recommendations=recommendations,
            limitations=limitations,
            analysis_timestamp=pd.Timestamp.now().isoformat()
        )

        self.logger.info(f"Comprehensive analysis completed for {experiment_id}: "
                        f"{len(statistical_tests)} tests, {len(significant_tests)} significant")

        return summary

    def _interpret_effect_size(self, effect_size: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_effect = abs(effect_size)
        for threshold, interpretation in sorted(self.EFFECT_SIZE_THRESHOLDS.items()):
            if abs_effect < threshold:
                return interpretation
        return "very_large"

    def _interpret_effect_size_wilcoxon(self, effect_size: float) -> str:
        """Interpret effect size for Wilcoxon test (r statistic)."""
        abs_effect = abs(effect_size)
        if abs_effect < 0.1:
            return "negligible"
        if abs_effect < 0.3:
            return "small"
        if abs_effect < 0.5:
            return "medium"
        return "large"

    def _calculate_power_paired_t(self, effect_size: float, n: int, alpha: float) -> float:
        """Calculate statistical power for paired t-test (approximate)."""
        try:
            from scipy.stats import t as t_dist

            # Critical t-value
            df = n - 1
            t_critical = t_dist.ppf(1 - alpha/2, df)

            # Non-centrality parameter
            ncp = effect_size * np.sqrt(n)

            # Power calculation (approximation)
            power = 1 - t_dist.cdf(t_critical, df, loc=ncp) + t_dist.cdf(-t_critical, df, loc=ncp)

            return min(1.0, max(0.0, power))

        except Exception:
            return 0.0  # Return 0 if calculation fails

    def _generate_recommendations(self,
                                descriptive_stats: dict[str, dict[str, float]],
                                statistical_tests: list[StatisticalTest],
                                assumption_tests: list[AssumptionTest],
                                confidence_intervals: list[ConfidenceInterval]) -> list[str]:
        """Generate statistical recommendations."""
        recommendations = []

        # Sample size recommendations
        sample_sizes = [test.sample_size for test in statistical_tests if test.sample_size]
        if sample_sizes and min(sample_sizes) < 5:
            recommendations.append("Consider increasing sample size (number of folds) for more robust statistical inference")

        # Effect size recommendations
        large_effects = [test for test in statistical_tests
                        if test.effect_size and abs(test.effect_size) > 0.8]
        if large_effects:
            recommendations.append(f"Large effect sizes detected for {len(large_effects)} metrics - results may be practically significant")

        # Normality violations
        normality_violations = [test for test in assumption_tests
                              if test.assumption_name == "normality" and not test.assumption_met]
        if normality_violations:
            recommendations.append("Consider using non-parametric tests due to normality violations")

        # Multiple testing
        if len(statistical_tests) > 3:
            recommendations.append("Multiple comparison correction applied - interpret individual p-values cautiously")

        # Confidence interval width
        wide_cis = [ci for ci in confidence_intervals
                   if ci.margin_of_error > 0.1 * abs(ci.point_estimate)]
        if wide_cis:
            recommendations.append("Some confidence intervals are wide - consider increasing sample size for more precise estimates")

        return recommendations

    def _identify_limitations(self,
                            sample_size: int,
                            assumption_tests: list[AssumptionTest],
                            statistical_tests: list[StatisticalTest]) -> list[str]:
        """Identify analysis limitations."""
        limitations = []

        if sample_size < 10:
            limitations.append(f"Small sample size (n={sample_size}) limits statistical power and generalizability")

        normality_violations = [test for test in assumption_tests
                              if test.assumption_name == "normality" and not test.assumption_met]
        if normality_violations:
            limitations.append("Parametric test assumptions violated - results may not be optimal")

        low_power_tests = [test for test in statistical_tests
                          if test.power and test.power < 0.8]
        if low_power_tests:
            limitations.append(f"Low statistical power for {len(low_power_tests)} tests - may miss true effects")

        if len(statistical_tests) > 10:
            limitations.append("Many simultaneous tests increase risk of Type I error despite correction")

        return limitations

    def save_statistical_summary(self, summary: StatisticalSummary) -> Path:
        """
        Save statistical summary to JSON file.

        Args:
            summary: Statistical summary to save

        Returns:
            Path to saved summary
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistical_summary_{summary.experiment_id}_{timestamp}.json"
        output_path = self.output_directory / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, indent=2, default=str)

        self.logger.info(f"Statistical summary saved to: {output_path}")
        return output_path
