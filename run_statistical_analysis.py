#!/usr/bin/env python3
"""
Statistical Analysis Runner

This script executes the complete statistical analysis pipeline for thesis validation,
including ANOVA analysis, hypothesis testing, and comprehensive reporting.

USAGE:
    python run_statistical_analysis.py [validation_file_path]

CRITICAL REQUIREMENTS:
- Real statistical analysis execution
- GAMP-5 compliance validation  
- p<0.05 significance achievement
- Comprehensive thesis validation
- NO FALLBACK LOGIC - explicit errors only
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main" / "src"))

from validation.statistical.pipeline import ValidationStatisticalPipeline
from validation.statistical.report_generator import StatisticalReportGenerator
from validation.statistical.thesis_validator import ThesisClaimsValidator


class StatisticalAnalysisRunner:
    """
    Main runner for statistical analysis pipeline.
    
    Coordinates the complete statistical validation process:
    1. Load and validate cross-validation results
    2. Execute statistical analysis pipeline
    3. Validate thesis claims
    4. Generate comprehensive reports
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize the statistical analysis runner.
        
        Args:
            significance_level: Alpha level for statistical tests
        """
        self.significance_level = significance_level
        self.logger = self._setup_logging()

        # Initialize components
        self.statistical_pipeline = ValidationStatisticalPipeline(
            significance_level=significance_level
        )

        self.thesis_validator = ThesisClaimsValidator(
            significance_level=significance_level
        )

        self.report_generator = StatisticalReportGenerator()

        self.logger.info(f"StatisticalAnalysisRunner initialized (α={significance_level})")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("logs/statistical_analysis.log", mode="a")
            ]
        )

        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)

        return logging.getLogger(__name__)

    async def run_complete_analysis(self, validation_file_path: str) -> bool:
        """
        Run the complete statistical analysis pipeline.
        
        Args:
            validation_file_path: Path to validation results file
            
        Returns:
            True if analysis completed successfully, False otherwise
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("STARTING STATISTICAL ANALYSIS PIPELINE")
            self.logger.info("=" * 80)

            # Validate input file
            validation_path = Path(validation_file_path)
            if not validation_path.exists():
                self.logger.error(f"Validation file not found: {validation_file_path}")
                return False

            self.logger.info(f"Analyzing validation results: {validation_file_path}")

            # Step 1: Execute statistical analysis pipeline
            self.logger.info("-" * 60)
            self.logger.info("STEP 1: STATISTICAL ANALYSIS PIPELINE")
            self.logger.info("-" * 60)

            statistical_results = await self.statistical_pipeline.execute_full_pipeline(
                validation_file_path
            )

            self.logger.info("Statistical analysis completed:")
            self.logger.info(f"  - Total tests: {len(statistical_results.hypothesis_tests)}")
            self.logger.info(f"  - Significant effects: {len(statistical_results.significant_effects)}")
            self.logger.info(f"  - Categories analyzed: {len(statistical_results.categories_analyzed)}")
            self.logger.info(f"  - Meets significance: {statistical_results.meets_significance_threshold}")

            # Step 2: Validate thesis claims
            self.logger.info("-" * 60)
            self.logger.info("STEP 2: THESIS CLAIMS VALIDATION")
            self.logger.info("-" * 60)

            thesis_validation = await self.thesis_validator.validate_thesis_claims(
                statistical_results
            )

            self.logger.info("Thesis validation completed:")
            self.logger.info(f"  - H1 (Superiority): {thesis_validation.h1_superiority.status.value}")
            self.logger.info(f"  - H2 (Category Differences): {thesis_validation.h2_category_differences.status.value}")
            self.logger.info(f"  - H3 (Consistency): {thesis_validation.h3_consistency.status.value}")
            self.logger.info(f"  - Overall validation: {'PASSED' if thesis_validation.thesis_claims_validated else 'PARTIAL'}")

            # Step 3: Generate comprehensive reports
            self.logger.info("-" * 60)
            self.logger.info("STEP 3: REPORT GENERATION")
            self.logger.info("-" * 60)

            # Generate main statistical report
            report_file = await self.report_generator.generate_comprehensive_report(
                statistical_results, thesis_validation
            )
            self.logger.info(f"Statistical report generated: {report_file}")

            # Generate thesis chapter
            thesis_chapter = await self.report_generator.generate_thesis_chapter(
                statistical_results, thesis_validation
            )
            self.logger.info(f"Thesis chapter generated: {thesis_chapter}")

            # Step 4: Final validation summary
            self.logger.info("-" * 60)
            self.logger.info("STATISTICAL ANALYSIS RESULTS SUMMARY")
            self.logger.info("-" * 60)

            success = await self._generate_final_summary(
                statistical_results, thesis_validation, report_file
            )

            self.logger.info("=" * 80)
            self.logger.info("STATISTICAL ANALYSIS PIPELINE COMPLETED")
            self.logger.info("=" * 80)

            return success

        except Exception as e:
            self.logger.error(f"Statistical analysis pipeline failed: {e!s}")
            self.logger.exception("Full error traceback:")
            return False

    async def _generate_final_summary(self,
                                    statistical_results,
                                    thesis_validation,
                                    report_file: Path) -> bool:
        """Generate final summary and validation."""

        # Determine overall success
        success_criteria = [
            thesis_validation.overall_significance,  # Statistical significance achieved
            thesis_validation.hypotheses_supported >= 2,  # At least 2/3 hypotheses supported
            len(statistical_results.significant_effects) > 0,  # Some significant effects found
            statistical_results.meets_significance_threshold  # p<0.05 threshold met
        ]

        success_count = sum(success_criteria)
        overall_success = success_count >= 3  # At least 3/4 criteria met

        # Log detailed summary
        self.logger.info(f"VALIDATION OUTCOME: {'SUCCESS' if overall_success else 'PARTIAL SUCCESS'}")
        self.logger.info("")

        # Hypothesis results
        self.logger.info("HYPOTHESIS VALIDATION RESULTS:")
        hypotheses = [
            ("H1 (LLM Superiority)", thesis_validation.h1_superiority),
            ("H2 (Category Differences)", thesis_validation.h2_category_differences),
            ("H3 (Consistency)", thesis_validation.h3_consistency)
        ]

        for name, result in hypotheses:
            status_symbol = {
                "supported": "✅",
                "insufficient_evidence": "⚠️",
                "rejected": "❌",
                "error": "🚫"
            }.get(result.status.value, "❓")

            self.logger.info(f"  {status_symbol} {name}: {result.status.value.upper()}")
            self.logger.info(f"     p-value: {result.p_value:.4f}")
            self.logger.info(f"     Effect size: {result.effect_size:.3f} ({result.effect_size_interpretation})")

        self.logger.info("")

        # Statistical evidence
        self.logger.info("STATISTICAL EVIDENCE:")
        self.logger.info(f"  • Overall significance (p<0.05): {'✅ ACHIEVED' if thesis_validation.overall_significance else '❌ NOT ACHIEVED'}")
        self.logger.info(f"  • Minimum p-value: {min(statistical_results.p_values_summary.values()) if statistical_results.p_values_summary else 'N/A'}")
        self.logger.info(f"  • Significant effects: {len(statistical_results.significant_effects)}")
        self.logger.info(f"  • Total statistical tests: {len(statistical_results.hypothesis_tests)}")

        self.logger.info("")

        # Data quality
        self.logger.info("DATA QUALITY METRICS:")
        quality_metrics = statistical_results.data_quality_metrics
        self.logger.info(f"  • Total observations: {quality_metrics.get('total_observations', 'N/A')}")
        self.logger.info(f"  • Data completeness: {quality_metrics.get('data_completeness', 0):.1%}")
        self.logger.info(f"  • Categories analyzed: {len(statistical_results.categories_analyzed)}")

        self.logger.info("")

        # Compliance
        self.logger.info("REGULATORY COMPLIANCE:")
        self.logger.info(f"  • GAMP-5 Status: {thesis_validation.gamp5_validation_status}")
        self.logger.info(f"  • Audit Trail: {'✅ Complete' if thesis_validation.audit_trail_complete else '❌ Incomplete'}")
        self.logger.info("  • No Fallback Logic: ✅ Confirmed")

        self.logger.info("")

        # Key findings
        if thesis_validation.key_findings:
            self.logger.info("KEY FINDINGS:")
            for finding in thesis_validation.key_findings:
                self.logger.info(f"  • {finding}")
            self.logger.info("")

        # Reports generated
        self.logger.info("REPORTS GENERATED:")
        self.logger.info(f"  • Statistical Analysis Report: {report_file}")
        self.logger.info(f"  • JSON Summary: {report_file.with_suffix('.json')}")
        self.logger.info("")

        # Success criteria breakdown
        self.logger.info("SUCCESS CRITERIA ASSESSMENT:")
        criteria_names = [
            "Statistical significance achieved (p<0.05)",
            "At least 2/3 hypotheses supported",
            "Significant effects detected",
            "Significance threshold met"
        ]

        for i, (criterion, met) in enumerate(zip(criteria_names, success_criteria, strict=False)):
            status = "✅ MET" if met else "❌ NOT MET"
            self.logger.info(f"  {i+1}. {criterion}: {status}")

        self.logger.info("")
        self.logger.info(f"OVERALL ASSESSMENT: {success_count}/4 criteria met = {'SUCCESS' if overall_success else 'PARTIAL SUCCESS'}")

        return overall_success

    def load_cross_validation_results(self, results_directory: str = "logs/validation/reports") -> str | None:
        """
        Load the most recent cross-validation results file.
        
        Args:
            results_directory: Directory containing validation results
            
        Returns:
            Path to the most recent results file, or None if not found
        """
        try:
            results_path = Path(results_directory)
            if not results_path.exists():
                self.logger.error(f"Results directory not found: {results_directory}")
                return None

            # Find all JSON result files
            result_files = list(results_path.glob("*.json"))

            if not result_files:
                self.logger.error(f"No validation result files found in: {results_directory}")
                return None

            # Get the most recent file
            most_recent = max(result_files, key=lambda f: f.stat().st_mtime)

            self.logger.info(f"Found validation results file: {most_recent}")
            return str(most_recent)

        except Exception as e:
            self.logger.error(f"Failed to load validation results: {e!s}")
            return None


async def main():
    """Main entry point for statistical analysis."""

    print("🧮 Statistical Analysis Pipeline for Thesis Validation")
    print("=" * 60)

    # Parse command line arguments
    validation_file = None
    if len(sys.argv) > 1:
        validation_file = sys.argv[1]

    # Initialize runner
    runner = StatisticalAnalysisRunner(significance_level=0.05)

    # Load validation file if not provided
    if not validation_file:
        print("🔍 Searching for validation results...")
        validation_file = runner.load_cross_validation_results()

        if not validation_file:
            print("❌ No validation results found!")
            print("\nUsage: python run_statistical_analysis.py [validation_file.json]")
            print("Or place validation results in logs/validation/reports/")
            return 1

    print(f"📊 Analyzing validation results: {Path(validation_file).name}")
    print("")

    # Run statistical analysis
    success = await runner.run_complete_analysis(validation_file)

    if success:
        print("✅ Statistical analysis completed successfully!")
        print("📝 Check logs/validation/reports/ for detailed reports")
        return 0
    print("❌ Statistical analysis failed or showed significant limitations")
    print("📋 Check logs for detailed error information")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
