#!/usr/bin/env python3
"""
Statistical Power Analyzer for n=30 Sample Size
Performs power analysis, sample size adequacy tests, and effect size calculations
"""

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestPower, NormalIndPower
from typing import Dict, List, Tuple, Optional
import math


class StatisticalPowerAnalyzer:
    def __init__(self, n: int = 30, alpha: float = 0.05):
        """
        Initialize power analyzer with sample size and significance level
        
        Args:
            n: Sample size (default 30)
            alpha: Significance level (default 0.05)
        """
        self.n = n
        self.alpha = alpha
        self.power_analysis = TTestPower()
        self.normal_power = NormalIndPower()
        
    def calculate_power(self) -> Dict:
        """Calculate comprehensive power analysis for the sample"""
        power_results = {
            "sample_size": self.n,
            "significance_level": self.alpha,
            "power_by_effect_size": self.calculate_power_by_effect_size(),
            "minimum_detectable_effect": self.calculate_minimum_detectable_effect(),
            "sample_size_adequacy": self.assess_sample_size_adequacy(),
            "type_ii_error_analysis": self.analyze_type_ii_error(),
            "post_hoc_power": self.calculate_post_hoc_power(),
            "comparative_analysis": self.compare_to_standards()
        }
        return power_results
    
    def calculate_power_by_effect_size(self) -> Dict:
        """Calculate statistical power for different effect sizes"""
        effect_sizes = {
            "small": 0.2,
            "medium": 0.5,
            "large": 0.8,
            "very_large": 1.2
        }
        
        power_values = {}
        for label, effect_size in effect_sizes.items():
            # One-sample t-test power
            power_one_sample = self.power_analysis.solve_power(
                effect_size=effect_size,
                nobs=self.n,
                alpha=self.alpha,
                alternative='two-sided'
            )
            
            # Two-sample t-test power (assuming equal groups)
            power_two_sample = self.power_analysis.solve_power(
                effect_size=effect_size,
                nobs=self.n/2,  # Per group
                alpha=self.alpha,
                alternative='two-sided'
            )
            
            power_values[label] = {
                "effect_size": effect_size,
                "one_sample_power": power_one_sample,
                "two_sample_power": power_two_sample,
                "interpretation": self.interpret_power(power_one_sample)
            }
        
        return power_values
    
    def interpret_power(self, power: float) -> str:
        """Interpret power value"""
        if power >= 0.95:
            return "Excellent (>95%)"
        elif power >= 0.80:
            return "Good (80-95%)"
        elif power >= 0.70:
            return "Acceptable (70-80%)"
        elif power >= 0.50:
            return "Marginal (50-70%)"
        else:
            return "Poor (<50%)"
    
    def calculate_minimum_detectable_effect(self) -> Dict:
        """Calculate minimum detectable effect size for target power levels"""
        target_powers = [0.70, 0.80, 0.90, 0.95]
        mde_results = {}
        
        for target_power in target_powers:
            # Calculate MDE for one-sample test
            mde_one_sample = self.power_analysis.solve_power(
                power=target_power,
                nobs=self.n,
                alpha=self.alpha,
                alternative='two-sided'
            )
            
            # Calculate MDE for two-sample test
            mde_two_sample = self.power_analysis.solve_power(
                power=target_power,
                nobs=self.n/2,
                alpha=self.alpha,
                alternative='two-sided'
            )
            
            mde_results[f"power_{int(target_power*100)}"] = {
                "target_power": target_power,
                "mde_one_sample": mde_one_sample,
                "mde_two_sample": mde_two_sample,
                "interpretation": self.interpret_effect_size(mde_one_sample)
            }
        
        return mde_results
    
    def interpret_effect_size(self, effect_size: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_effect = abs(effect_size)
        if abs_effect < 0.2:
            return "Negligible"
        elif abs_effect < 0.5:
            return "Small"
        elif abs_effect < 0.8:
            return "Medium"
        else:
            return "Large"
    
    def assess_sample_size_adequacy(self) -> Dict:
        """Assess whether sample size is adequate for various analyses"""
        assessments = {}
        
        # For regression (rule of thumb: 10-20 observations per predictor)
        max_predictors_conservative = self.n / 20
        max_predictors_liberal = self.n / 10
        
        assessments["regression"] = {
            "max_predictors_conservative": int(max_predictors_conservative),
            "max_predictors_liberal": int(max_predictors_liberal),
            "adequate_for_basic": self.n >= 30,
            "interpretation": "Adequate for basic analyses" if self.n >= 30 else "Marginal"
        }
        
        # For ANOVA (minimum 20 per group for 3 groups)
        assessments["anova"] = {
            "max_groups_equal": int(self.n / 10),  # Assuming min 10 per group
            "adequate_for_3_groups": self.n >= 30,
            "interpretation": "Adequate for 3-group ANOVA" if self.n >= 30 else "Limited"
        }
        
        # For factor analysis (various rules)
        assessments["factor_analysis"] = {
            "subjects_to_variables_ratio": "3:1 minimum met" if self.n >= 30 else "Below minimum",
            "absolute_minimum": self.n >= 50,
            "interpretation": "Marginal for EFA" if self.n >= 30 else "Insufficient"
        }
        
        # Central Limit Theorem
        assessments["clt_assumption"] = {
            "meets_clt": self.n >= 30,
            "interpretation": "Sample size meets CLT assumption" if self.n >= 30 else "Below CLT threshold"
        }
        
        # For pharmaceutical validation (custom criteria)
        assessments["pharmaceutical_validation"] = {
            "meets_minimum": self.n >= 30,
            "meets_preferred": self.n >= 50,
            "regulatory_acceptability": "Acceptable for proof-of-concept" if self.n >= 30 else "May require justification"
        }
        
        return assessments
    
    def analyze_type_ii_error(self) -> Dict:
        """Analyze Type II error (false negative) rates"""
        # Type II error = 1 - power
        effect_sizes = [0.2, 0.5, 0.8, 1.0]
        type_ii_errors = {}
        
        for effect_size in effect_sizes:
            power = self.power_analysis.solve_power(
                effect_size=effect_size,
                nobs=self.n,
                alpha=self.alpha,
                alternative='two-sided'
            )
            
            type_ii_error = 1 - power
            
            type_ii_errors[f"effect_{effect_size}"] = {
                "effect_size": effect_size,
                "power": power,
                "type_ii_error": type_ii_error,
                "type_ii_error_percentage": type_ii_error * 100,
                "interpretation": self.interpret_type_ii_error(type_ii_error)
            }
        
        return type_ii_errors
    
    def interpret_type_ii_error(self, beta: float) -> str:
        """Interpret Type II error rate"""
        if beta <= 0.05:
            return "Excellent (<5%)"
        elif beta <= 0.20:
            return "Acceptable (5-20%)"
        elif beta <= 0.50:
            return "High (20-50%)"
        else:
            return "Very High (>50%)"
    
    def calculate_post_hoc_power(self) -> Dict:
        """Calculate post-hoc power based on observed results"""
        # Based on actual results from corpus analysis
        observed_success_rate = 29 / 30  # 96.7%
        baseline_rate = 0.5  # Random baseline
        
        # Calculate observed effect size
        observed_mean = observed_success_rate
        baseline_mean = baseline_rate
        
        # Estimate pooled standard deviation
        p = (observed_mean + baseline_mean) / 2
        pooled_sd = np.sqrt(p * (1 - p))
        
        # Cohen's d
        observed_effect_size = (observed_mean - baseline_mean) / pooled_sd if pooled_sd > 0 else 0
        
        # Calculate post-hoc power
        if observed_effect_size > 0:
            post_hoc_power = self.power_analysis.solve_power(
                effect_size=observed_effect_size,
                nobs=self.n,
                alpha=self.alpha,
                alternative='two-sided'
            )
        else:
            post_hoc_power = 0
        
        return {
            "observed_effect_size": observed_effect_size,
            "post_hoc_power": post_hoc_power,
            "interpretation": f"Actual study power: {self.interpret_power(post_hoc_power)}",
            "observed_success_rate": observed_success_rate,
            "baseline_comparison": baseline_rate,
            "effect_size_interpretation": self.interpret_effect_size(observed_effect_size)
        }
    
    def compare_to_standards(self) -> Dict:
        """Compare power analysis to standard requirements"""
        # Calculate power for medium effect size (standard benchmark)
        standard_power = self.power_analysis.solve_power(
            effect_size=0.5,
            nobs=self.n,
            alpha=self.alpha,
            alternative='two-sided'
        )
        
        comparisons = {
            "cohen_standard": {
                "requirement": 0.80,
                "achieved": standard_power,
                "meets_standard": standard_power >= 0.80,
                "gap": max(0, 0.80 - standard_power)
            },
            "pharmaceutical_standard": {
                "requirement": 0.90,
                "achieved": standard_power,
                "meets_standard": standard_power >= 0.90,
                "gap": max(0, 0.90 - standard_power)
            },
            "sample_size_for_80_power": self.calculate_required_sample_size(0.80),
            "sample_size_for_90_power": self.calculate_required_sample_size(0.90),
            "sample_size_for_95_power": self.calculate_required_sample_size(0.95)
        }
        
        return comparisons
    
    def calculate_required_sample_size(self, target_power: float, effect_size: float = 0.5) -> Dict:
        """Calculate required sample size for target power"""
        required_n = self.power_analysis.solve_power(
            effect_size=effect_size,
            power=target_power,
            alpha=self.alpha,
            alternative='two-sided'
        )
        
        return {
            "target_power": target_power,
            "effect_size": effect_size,
            "required_n": math.ceil(required_n),
            "current_n": self.n,
            "additional_needed": max(0, math.ceil(required_n) - self.n),
            "adequacy": "Adequate" if self.n >= required_n else f"Need {math.ceil(required_n) - self.n} more"
        }
    
    def generate_power_curve_data(self) -> Dict:
        """Generate data for power curve visualization"""
        effect_sizes = np.linspace(0, 2, 50)
        sample_sizes = [10, 20, 30, 50, 100]
        
        curves = {}
        for n in sample_sizes:
            powers = []
            for effect_size in effect_sizes:
                power = self.power_analysis.solve_power(
                    effect_size=effect_size,
                    nobs=n,
                    alpha=self.alpha,
                    alternative='two-sided'
                )
                powers.append(power)
            
            curves[f"n_{n}"] = {
                "sample_size": n,
                "effect_sizes": effect_sizes.tolist(),
                "power_values": powers
            }
        
        return curves
    
    def sensitivity_analysis(self) -> Dict:
        """Perform sensitivity analysis on power calculations"""
        base_power = self.power_analysis.solve_power(
            effect_size=0.5,
            nobs=self.n,
            alpha=self.alpha,
            alternative='two-sided'
        )
        
        sensitivity = {
            "base_case": {
                "n": self.n,
                "alpha": self.alpha,
                "effect_size": 0.5,
                "power": base_power
            },
            "vary_alpha": {},
            "vary_n": {},
            "vary_effect_size": {}
        }
        
        # Vary alpha
        for alpha in [0.01, 0.05, 0.10]:
            power = self.power_analysis.solve_power(
                effect_size=0.5,
                nobs=self.n,
                alpha=alpha,
                alternative='two-sided'
            )
            sensitivity["vary_alpha"][f"alpha_{alpha}"] = power
        
        # Vary n
        for n_mult in [0.5, 0.75, 1.0, 1.25, 1.5]:
            n_test = int(self.n * n_mult)
            if n_test > 0:
                power = self.power_analysis.solve_power(
                    effect_size=0.5,
                    nobs=n_test,
                    alpha=self.alpha,
                    alternative='two-sided'
                )
                sensitivity["vary_n"][f"n_{n_test}"] = power
        
        # Vary effect size
        for es in [0.2, 0.3, 0.5, 0.8, 1.0]:
            power = self.power_analysis.solve_power(
                effect_size=es,
                nobs=self.n,
                alpha=self.alpha,
                alternative='two-sided'
            )
            sensitivity["vary_effect_size"][f"es_{es}"] = power
        
        return sensitivity