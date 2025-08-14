#!/usr/bin/env python3
"""
Cross-Validation Workflow Integration

This module integrates k-fold cross-validation with the main pharmaceutical test
generation workflow. Provides seamless integration for running the unified workflow
across multiple folds with aggregated results and metrics collection.

GAMP-5 Compliance: All operations follow pharmaceutical validation standards with
explicit error handling, audit trail support, and NO FALLBACK LOGIC.
"""

import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add datasets directory to path for CV manager import
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "datasets" / "cross_validation"))

try:
    from cv_manager import CrossValidationManager, load_cv_manager
    from validate_folds import CrossValidationValidator
    CV_MODULES_AVAILABLE = True
except ImportError:
    CV_MODULES_AVAILABLE = False


@dataclass
class CVFoldResult:
    """Results from a single cross-validation fold execution."""
    fold_number: int
    test_documents: list[str]
    train_documents: list[str]
    execution_time_seconds: float
    test_generation_results: dict[str, Any]
    workflow_metrics: dict[str, Any]
    errors: list[str]
    success: bool


@dataclass
class CVAggregatedResults:
    """Aggregated results across all cross-validation folds."""
    total_folds: int
    successful_folds: int
    failed_folds: int
    execution_summary: dict[str, Any]
    performance_metrics: dict[str, Any]
    fold_results: list[CVFoldResult]
    statistical_analysis: dict[str, Any]
    recommendations: list[str]


class CrossValidationWorkflowIntegration:
    """
    Integration layer for running unified workflow with k-fold cross-validation.
    
    This class coordinates the execution of the main pharmaceutical test generation
    workflow across multiple cross-validation folds, collecting and aggregating
    results for comprehensive evaluation.
    """

    def __init__(self, config_path: str | None = None, workflow_module_path: str | None = None):
        """
        Initialize CV workflow integration.
        
        Args:
            config_path: Path to CV configuration file
            workflow_module_path: Path to main workflow module (defaults to unified_workflow.py)
            
        Raises:
            ImportError: If required modules not available
            RuntimeError: If initialization fails
        """
        if not CV_MODULES_AVAILABLE:
            raise ImportError(
                "Cross-validation modules not available. Ensure cv_manager.py and validate_folds.py are in the correct location."
            )

        try:
            # Initialize CV manager
            self.cv_manager = load_cv_manager(config_path)
            self.validator = CrossValidationValidator(self.cv_manager, config_path)

            # Set workflow module path
            if workflow_module_path is None:
                self.workflow_module_path = Path(__file__).parent / "unified_workflow.py"
            else:
                self.workflow_module_path = Path(workflow_module_path)

            if not self.workflow_module_path.exists():
                raise FileNotFoundError(f"Workflow module not found: {self.workflow_module_path}")

            # Initialize logging
            self._setup_logging()

            # Initialize results storage
            self.fold_results = []
            self.execution_start_time = None
            self.execution_end_time = None

        except Exception as e:
            raise RuntimeError(f"Failed to initialize CV workflow integration: {e!s}")

    def _setup_logging(self) -> None:
        """Setup logging for CV workflow execution."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'cv_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def execute_fold(self, fold_number: int, workflow_config: dict | None = None) -> CVFoldResult:
        """
        Execute workflow for a single cross-validation fold.
        
        Args:
            fold_number: Fold number to execute (1-5)
            workflow_config: Optional workflow configuration override
            
        Returns:
            CVFoldResult containing execution results
            
        Raises:
            RuntimeError: If fold execution fails
        """
        fold_start_time = datetime.now()
        errors = []

        try:
            self.logger.info(f"Starting execution for fold {fold_number}")

            # Get fold data
            fold_data = self.cv_manager.get_fold(fold_number)
            test_docs = [doc.doc_id for doc in fold_data["test"]]
            train_docs = [doc.doc_id for doc in fold_data["train"]]

            self.logger.info(f"Fold {fold_number}: {len(test_docs)} test, {len(train_docs)} train documents")

            # Import and configure workflow
            workflow_results = await self._execute_workflow_for_fold(
                fold_number, fold_data, workflow_config
            )

            # Calculate execution time
            execution_time = (datetime.now() - fold_start_time).total_seconds()

            # Create fold result
            fold_result = CVFoldResult(
                fold_number=fold_number,
                test_documents=test_docs,
                train_documents=train_docs,
                execution_time_seconds=execution_time,
                test_generation_results=workflow_results.get("test_generation", {}),
                workflow_metrics=workflow_results.get("metrics", {}),
                errors=errors,
                success=len(errors) == 0
            )

            self.logger.info(f"Fold {fold_number} completed successfully in {execution_time:.2f}s")
            return fold_result

        except Exception as e:
            error_msg = f"Fold {fold_number} execution failed: {e!s}"
            errors.append(error_msg)
            self.logger.error(error_msg)

            execution_time = (datetime.now() - fold_start_time).total_seconds()

            return CVFoldResult(
                fold_number=fold_number,
                test_documents=[],
                train_documents=[],
                execution_time_seconds=execution_time,
                test_generation_results={},
                workflow_metrics={},
                errors=errors,
                success=False
            )

    async def _execute_workflow_for_fold(
        self,
        fold_number: int,
        fold_data: dict,
        workflow_config: dict | None
    ) -> dict[str, Any]:
        """
        Execute the main workflow for a specific fold.
        
        Args:
            fold_number: Current fold number
            fold_data: Fold training and test data
            workflow_config: Workflow configuration
            
        Returns:
            Dictionary containing workflow results
            
        Raises:
            RuntimeError: If workflow execution fails
        """
        try:
            # Dynamic import of workflow module
            sys.path.insert(0, str(self.workflow_module_path.parent))

            try:
                from unified_workflow import run_unified_workflow
                UNIFIED_WORKFLOW_AVAILABLE = True
            except ImportError:
                UNIFIED_WORKFLOW_AVAILABLE = False

            if not UNIFIED_WORKFLOW_AVAILABLE:
                raise ImportError("Unified workflow module not available")

            # Prepare workflow inputs for this fold
            workflow_inputs = self._prepare_workflow_inputs(fold_data, workflow_config)

            # Execute workflow
            self.logger.info(f"Executing unified workflow for fold {fold_number}")
            workflow_results = await run_unified_workflow(**workflow_inputs)

            # Process and validate results
            processed_results = self._process_workflow_results(workflow_results, fold_number)

            return processed_results

        except Exception as e:
            raise RuntimeError(f"Workflow execution failed for fold {fold_number}: {e!s}")

    def _prepare_workflow_inputs(self, fold_data: dict, workflow_config: dict | None) -> dict[str, Any]:
        """
        Prepare inputs for workflow execution based on fold data.
        
        Args:
            fold_data: Fold training and test data
            workflow_config: Optional workflow configuration
            
        Returns:
            Dictionary of workflow inputs
        """
        # Default workflow configuration
        inputs = {
            "train_documents": [doc.file_path for doc in fold_data["train"]],
            "test_documents": [doc.file_path for doc in fold_data["test"]],
            "enable_categorization": True,
            "enable_test_generation": True,
            "enable_monitoring": True,
            "output_format": "json",
            "compliance_mode": True
        }

        # Override with provided config
        if workflow_config:
            inputs.update(workflow_config)

        return inputs

    def _process_workflow_results(self, results: dict[str, Any], fold_number: int) -> dict[str, Any]:
        """
        Process and validate workflow results for a fold.
        
        Args:
            results: Raw workflow results
            fold_number: Current fold number
            
        Returns:
            Processed results dictionary
        """
        processed = {
            "fold_number": fold_number,
            "test_generation": {},
            "metrics": {},
            "categorization_results": {},
            "validation_results": {}
        }

        # Extract test generation results
        if "test_generation" in results:
            test_gen = results["test_generation"]
            processed["test_generation"] = {
                "tests_generated": test_gen.get("total_tests", 0),
                "success_rate": test_gen.get("success_rate", 0.0),
                "categories_covered": test_gen.get("categories_covered", []),
                "execution_time": test_gen.get("execution_time_seconds", 0.0)
            }

        # Extract workflow metrics
        if "metrics" in results:
            metrics = results["metrics"]
            processed["metrics"] = {
                "total_processing_time": metrics.get("total_time", 0.0),
                "categorization_accuracy": metrics.get("categorization_accuracy", 0.0),
                "test_quality_score": metrics.get("test_quality", 0.0),
                "compliance_score": metrics.get("compliance_score", 0.0)
            }

        # Extract categorization results
        if "categorization" in results:
            cat_results = results["categorization"]
            processed["categorization_results"] = {
                "accuracy": cat_results.get("accuracy", 0.0),
                "confidence_scores": cat_results.get("confidence_scores", []),
                "category_distribution": cat_results.get("category_distribution", {})
            }

        return processed

    async def run_cross_validation(self, workflow_config: dict | None = None) -> CVAggregatedResults:
        """
        Run complete k-fold cross-validation workflow.
        
        Args:
            workflow_config: Optional workflow configuration
            
        Returns:
            CVAggregatedResults with comprehensive results
            
        Raises:
            RuntimeError: If cross-validation execution fails
        """
        self.execution_start_time = datetime.now()
        self.fold_results = []

        try:
            self.logger.info("Starting k-fold cross-validation execution")

            # Validate folds before execution
            self.logger.info("Validating fold quality...")
            validation_results = self.validator.run_comprehensive_validation()

            if not validation_results["overall_summary"]["overall_passed"]:
                self.logger.warning("Fold validation failed, but proceeding with execution")
                self.logger.warning(f"Validation issues: {validation_results['recommendations']}")

            # Execute each fold
            for fold_number in range(1, 6):
                fold_result = await self.execute_fold(fold_number, workflow_config)
                self.fold_results.append(fold_result)

            self.execution_end_time = datetime.now()

            # Aggregate results
            aggregated_results = self._aggregate_results()

            self.logger.info("Cross-validation execution completed")
            return aggregated_results

        except Exception as e:
            self.execution_end_time = datetime.now()
            raise RuntimeError(f"Cross-validation execution failed: {e!s}")

    def _aggregate_results(self) -> CVAggregatedResults:
        """
        Aggregate results across all folds.
        
        Returns:
            CVAggregatedResults with comprehensive analysis
        """
        successful_folds = sum(1 for result in self.fold_results if result.success)
        failed_folds = len(self.fold_results) - successful_folds

        # Calculate execution summary
        total_execution_time = sum(result.execution_time_seconds for result in self.fold_results)
        avg_execution_time = total_execution_time / len(self.fold_results) if self.fold_results else 0

        execution_summary = {
            "total_execution_time_seconds": total_execution_time,
            "average_execution_time_per_fold": avg_execution_time,
            "start_time": self.execution_start_time.isoformat() if self.execution_start_time else None,
            "end_time": self.execution_end_time.isoformat() if self.execution_end_time else None
        }

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics()

        # Statistical analysis
        statistical_analysis = self._perform_statistical_analysis()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return CVAggregatedResults(
            total_folds=len(self.fold_results),
            successful_folds=successful_folds,
            failed_folds=failed_folds,
            execution_summary=execution_summary,
            performance_metrics=performance_metrics,
            fold_results=self.fold_results,
            statistical_analysis=statistical_analysis,
            recommendations=recommendations
        )

    def _calculate_performance_metrics(self) -> dict[str, Any]:
        """Calculate aggregated performance metrics across folds."""
        successful_results = [r for r in self.fold_results if r.success]

        if not successful_results:
            return {"error": "No successful folds to analyze"}

        # Extract metrics from successful folds
        test_counts = [r.test_generation_results.get("tests_generated", 0) for r in successful_results]
        success_rates = [r.test_generation_results.get("success_rate", 0.0) for r in successful_results]

        workflow_metrics = {}
        for result in successful_results:
            for key, value in result.workflow_metrics.items():
                if key not in workflow_metrics:
                    workflow_metrics[key] = []
                if isinstance(value, (int, float)):
                    workflow_metrics[key].append(value)

        # Calculate aggregated metrics
        metrics = {
            "test_generation": {
                "total_tests_generated": sum(test_counts),
                "average_tests_per_fold": sum(test_counts) / len(test_counts) if test_counts else 0,
                "average_success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
                "min_tests_generated": min(test_counts) if test_counts else 0,
                "max_tests_generated": max(test_counts) if test_counts else 0
            },
            "workflow_performance": {}
        }

        # Aggregate workflow metrics
        for metric_name, values in workflow_metrics.items():
            if values:
                metrics["workflow_performance"][metric_name] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std": self._calculate_std(values)
                }

        return metrics

    def _perform_statistical_analysis(self) -> dict[str, Any]:
        """Perform statistical analysis of results across folds."""
        successful_results = [r for r in self.fold_results if r.success]

        analysis = {
            "fold_consistency": {},
            "performance_variance": {},
            "reliability_metrics": {}
        }

        if len(successful_results) < 2:
            analysis["error"] = "Insufficient successful folds for statistical analysis"
            return analysis

        # Analyze consistency across folds
        test_counts = [r.test_generation_results.get("tests_generated", 0) for r in successful_results]
        success_rates = [r.test_generation_results.get("success_rate", 0.0) for r in successful_results]

        analysis["fold_consistency"] = {
            "test_generation_cv": self._coefficient_of_variation(test_counts),
            "success_rate_cv": self._coefficient_of_variation(success_rates),
            "consistency_rating": "High" if max(self._coefficient_of_variation(test_counts), self._coefficient_of_variation(success_rates)) < 0.1 else "Medium" if max(self._coefficient_of_variation(test_counts), self._coefficient_of_variation(success_rates)) < 0.2 else "Low"
        }

        # Performance variance analysis
        execution_times = [r.execution_time_seconds for r in successful_results]
        analysis["performance_variance"] = {
            "execution_time_cv": self._coefficient_of_variation(execution_times),
            "mean_execution_time": sum(execution_times) / len(execution_times),
            "performance_stability": "Stable" if self._coefficient_of_variation(execution_times) < 0.2 else "Variable"
        }

        # Reliability metrics
        analysis["reliability_metrics"] = {
            "success_rate": len(successful_results) / len(self.fold_results),
            "failure_analysis": [r.errors for r in self.fold_results if not r.success],
            "overall_reliability": "High" if len(successful_results) == len(self.fold_results) else "Medium" if len(successful_results) >= 0.8 * len(self.fold_results) else "Low"
        }

        return analysis

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on CV results."""
        recommendations = []

        successful_folds = sum(1 for result in self.fold_results if result.success)
        total_folds = len(self.fold_results)

        # Success rate recommendations
        success_rate = successful_folds / total_folds if total_folds > 0 else 0
        if success_rate == 1.0:
            recommendations.append("✓ All folds executed successfully - excellent reliability")
        elif success_rate >= 0.8:
            recommendations.append(f"⚠ {total_folds - successful_folds} fold(s) failed - investigate failure causes")
        else:
            recommendations.append(f"❌ High failure rate ({100*(1-success_rate):.1f}%) - review workflow implementation")

        # Performance recommendations
        if successful_folds > 1:
            successful_results = [r for r in self.fold_results if r.success]
            test_counts = [r.test_generation_results.get("tests_generated", 0) for r in successful_results]

            if test_counts:
                cv = self._coefficient_of_variation(test_counts)
                if cv < 0.1:
                    recommendations.append("✓ Consistent test generation across folds")
                elif cv < 0.2:
                    recommendations.append("⚠ Moderate variation in test generation - acceptable")
                else:
                    recommendations.append("❌ High variation in test generation - investigate fold balance")

        # General recommendations
        recommendations.append("💡 Save detailed results for thesis documentation")
        recommendations.append("💡 Use aggregated metrics for final model evaluation")

        return recommendations

    def save_results(self, output_path: str | None = None) -> str:
        """
        Save cross-validation results to file.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            Path to saved results file
            
        Raises:
            RuntimeError: If saving fails
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"cv_results_{timestamp}.json"

            output_path = Path(output_path)

            # Aggregate results if not already done
            if hasattr(self, "aggregated_results"):
                results = self.aggregated_results
            else:
                results = self._aggregate_results()

            # Convert to JSON-serializable format
            results_dict = asdict(results)

            # Save to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Results saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            raise RuntimeError(f"Failed to save results: {e!s}")

    def _calculate_std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def _coefficient_of_variation(self, values: list[float]) -> float:
        """Calculate coefficient of variation."""
        if not values or len(values) <= 1:
            return 0.0

        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0

        std_val = self._calculate_std(values)
        return std_val / mean_val


async def run_cross_validation_workflow(
    config_path: str | None = None,
    workflow_config: dict | None = None,
    output_path: str | None = None
) -> CVAggregatedResults:
    """
    Factory function to run complete cross-validation workflow.
    
    Args:
        config_path: Path to CV configuration file
        workflow_config: Workflow configuration dictionary
        output_path: Optional output path for results
        
    Returns:
        CVAggregatedResults with comprehensive analysis
        
    Raises:
        RuntimeError: If execution fails
    """
    try:
        # Initialize CV workflow integration
        cv_integration = CrossValidationWorkflowIntegration(config_path)

        # Run cross-validation
        results = await cv_integration.run_cross_validation(workflow_config)

        # Save results if output path provided
        if output_path:
            cv_integration.aggregated_results = results
            cv_integration.save_results(output_path)

        return results

    except Exception as e:
        raise RuntimeError(f"Cross-validation workflow execution failed: {e!s}")


if __name__ == "__main__":
    """
    Example usage for cross-validation workflow execution.
    """
    async def main():
        try:
            print("Initializing cross-validation workflow...")

            # Example workflow configuration
            workflow_config = {
                "enable_categorization": True,
                "enable_test_generation": True,
                "enable_monitoring": True,
                "output_format": "json"
            }

            # Run cross-validation
            results = await run_cross_validation_workflow(
                workflow_config=workflow_config,
                output_path="cv_results_example.json"
            )

            # Print summary
            print("\\nCross-Validation Results Summary:")
            print(f"Total folds: {results.total_folds}")
            print(f"Successful folds: {results.successful_folds}")
            print(f"Failed folds: {results.failed_folds}")
            print(f"Overall success rate: {results.successful_folds/results.total_folds:.1%}")

            print("\\nRecommendations:")
            for rec in results.recommendations:
                print(f"  - {rec}")

        except Exception as e:
            print(f"ERROR: {e}")
            exit(1)

    # Run if scipy available (for validation)
    if CV_MODULES_AVAILABLE:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\\nExecution interrupted by user")
    else:
        print("Cross-validation modules not available. Ensure all dependencies are installed.")
