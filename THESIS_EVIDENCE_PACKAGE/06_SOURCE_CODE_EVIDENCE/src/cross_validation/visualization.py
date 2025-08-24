"""
Visualization Module for Cross-Validation Framework

This module provides comprehensive visualization capabilities for cross-validation
results including performance comparisons, coverage analysis, quality metrics,
and statistical analysis visualizations with GAMP-5 compliance.

Key Features:
- Performance comparison charts (time, cost, efficiency)
- Cross-validation box plots and distribution analysis
- Requirements coverage heatmaps and traceability visualizations
- Quality metrics dashboards with target compliance
- Statistical analysis plots (confidence intervals, effect sizes)
- Cost reduction waterfall diagrams
- Interactive dashboards with Plotly
- Static plots with Matplotlib/Seaborn
"""

import logging
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as sp
import seaborn as sns
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field

from .coverage_analyzer import CoverageReport
from .metrics_collector import CrossValidationMetrics
from .quality_metrics import QualityReport
from .results_aggregator import ComprehensiveReport
from .statistical_analyzer import StatisticalSummary

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


class VisualizationConfig(BaseModel):
    """Configuration for visualization generation."""
    style_theme: str = Field(default="plotly_white", description="Plotly theme")
    color_palette: list[str] = Field(
        default=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
        description="Color palette for plots"
    )
    figure_width: int = Field(default=1200, description="Default figure width in pixels")
    figure_height: int = Field(default=800, description="Default figure height in pixels")
    dpi: int = Field(default=300, description="DPI for static plots")
    export_formats: list[str] = Field(default=["html", "png"], description="Export formats")
    include_targets: bool = Field(default=True, description="Include target lines in plots")


class VisualizationSuite:
    """
    Comprehensive visualization suite for cross-validation analysis.

    This class generates interactive and static visualizations for all aspects
    of cross-validation analysis following pharmaceutical validation standards
    and GAMP-5 compliance requirements.
    """

    def __init__(self,
                 output_directory: str | Path | None = None,
                 config: VisualizationConfig | None = None):
        """
        Initialize the VisualizationSuite.

        Args:
            output_directory: Directory to store generated visualizations
            config: Visualization configuration
        """
        self.logger = logging.getLogger(__name__)
        self.output_directory = Path(output_directory) if output_directory else Path.cwd() / "visualizations"
        self.output_directory.mkdir(parents=True, exist_ok=True)

        self.config = config or VisualizationConfig()

        # Set up matplotlib and seaborn styling
        plt.style.use("default")
        sns.set_palette(self.config.color_palette)

        # Create subdirectories
        (self.output_directory / "interactive").mkdir(exist_ok=True)
        (self.output_directory / "static").mkdir(exist_ok=True)

        self.logger.info(f"VisualizationSuite initialized with output directory: {self.output_directory}")

    def create_performance_dashboard(self,
                                   performance_metrics: CrossValidationMetrics,
                                   experiment_id: str) -> Path:
        """
        Create comprehensive performance analysis dashboard.

        Args:
            performance_metrics: Performance metrics from cross-validation
            experiment_id: Experiment identifier

        Returns:
            Path to generated dashboard file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Processing Time Distribution",
                "Cost Analysis by Fold",
                "Success Rate by Fold",
                "Token Usage Overview"
            ],
            specs=[
                [{"type": "box"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "pie"}]
            ]
        )

        # Processing time distribution
        if performance_metrics.fold_results:
            processing_times = [fold.avg_processing_time for fold in performance_metrics.fold_results
                              if fold.avg_processing_time]
            fold_ids = [fold.fold_id for fold in performance_metrics.fold_results
                       if fold.avg_processing_time]

            if processing_times:
                fig.add_trace(
                    go.Box(y=processing_times, x=fold_ids, name="Processing Time (s)"),
                    row=1, col=1
                )

        # Cost analysis by fold
        if performance_metrics.fold_results:
            fold_costs = [fold.total_cost_usd for fold in performance_metrics.fold_results]
            fold_names = [fold.fold_id for fold in performance_metrics.fold_results]

            fig.add_trace(
                go.Bar(x=fold_names, y=fold_costs, name="Cost (USD)",
                       marker_color=self.config.color_palette[1]),
                row=1, col=2
            )

        # Success rate by fold
        if performance_metrics.fold_results:
            success_rates = [fold.success_rate for fold in performance_metrics.fold_results]
            fold_names = [fold.fold_id for fold in performance_metrics.fold_results]

            colors = ["green" if rate >= 90 else "orange" if rate >= 75 else "red"
                     for rate in success_rates]

            fig.add_trace(
                go.Bar(x=fold_names, y=success_rates, name="Success Rate (%)",
                       marker_color=colors),
                row=2, col=1
            )

            # Add target line
            if self.config.include_targets:
                fig.add_hline(y=90, line_dash="dash", line_color="red",
                            annotation_text="Target: 90%", row=2, col=1)

        # Token usage pie chart
        if performance_metrics.total_tokens > 0:
            # Approximate token distribution (this would need actual data from metrics)
            token_data = {
                "Prompt Tokens": performance_metrics.total_tokens * 0.3,  # Estimated
                "Completion Tokens": performance_metrics.total_tokens * 0.7  # Estimated
            }

            fig.add_trace(
                go.Pie(labels=list(token_data.keys()), values=list(token_data.values()),
                       name="Token Usage"),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            title_text=f"Performance Dashboard - {experiment_id}",
            showlegend=True,
            height=self.config.figure_height,
            width=self.config.figure_width,
            template=self.config.style_theme
        )

        # Add target lines where applicable
        if self.config.include_targets:
            fig.add_annotation(
                text="Performance targets shown as dashed lines",
                showarrow=False,
                x=0, y=1.02,
                xref="paper", yref="paper",
                font={"size": 10, "color": "gray"}
            )

        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_dashboard_{experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Performance dashboard saved to: {output_path}")
        return output_path

    def create_coverage_heatmap(self,
                               coverage_reports: list[CoverageReport],
                               experiment_id: str) -> Path:
        """
        Create requirements coverage heatmap visualization.

        Args:
            coverage_reports: Coverage analysis reports
            experiment_id: Experiment identifier

        Returns:
            Path to generated heatmap file
        """
        if not coverage_reports:
            msg = "No coverage reports provided for visualization"
            raise ValueError(msg)

        # Prepare data for heatmap
        documents = [report.document_id for report in coverage_reports]
        categories = set()
        for report in coverage_reports:
            categories.update(report.coverage_by_category.keys())

        categories = sorted(categories)

        # Create coverage matrix
        coverage_matrix = []
        for category in categories:
            category_row = []
            for report in coverage_reports:
                coverage = report.coverage_by_category.get(category, 0)
                category_row.append(coverage)
            coverage_matrix.append(category_row)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=coverage_matrix,
            x=documents,
            y=categories,
            colorscale="RdYlGn",
            zmid=90,  # Center colorscale at 90% target
            zmin=0,
            zmax=100,
            text=[[f"{val:.1f}%" for val in row] for row in coverage_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoveringmode="closest",
            hovertemplate="<b>%{y}</b><br>"
                         "Document: %{x}<br>"
                         "Coverage: %{z:.1f}%<br>"
                         "<extra></extra>"
        ))

        # Add target line at 90%
        if self.config.include_targets:
            # Add rectangles for target zones
            target_zones = []
            for i, category in enumerate(categories):
                for j, _document in enumerate(documents):
                    coverage_val = coverage_matrix[i][j]
                    if coverage_val >= 90:
                        target_zones.append({
                            "type": "rect",
                            "x0": j-0.4, "y0": i-0.4,
                            "x1": j+0.4, "y1": i+0.4,
                            "line": {"color": "darkgreen", "width": 3},
                            "fillcolor": "rgba(0,0,0,0)"
                        })

        fig.update_layout(
            title=f"Requirements Coverage Heatmap - {experiment_id}",
            xaxis_title="URS Documents",
            yaxis_title="Requirement Categories",
            width=max(self.config.figure_width, len(documents) * 80),
            height=max(self.config.figure_height, len(categories) * 60),
            template=self.config.style_theme
        )

        # Add colorbar title
        fig.update_coloraxes(colorbar_title_text="Coverage Percentage")

        # Save heatmap
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coverage_heatmap_{experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Coverage heatmap saved to: {output_path}")
        return output_path

    def create_quality_metrics_dashboard(self,
                                       quality_reports: list[QualityReport],
                                       experiment_id: str) -> Path:
        """
        Create quality metrics dashboard with target compliance.

        Args:
            quality_reports: Quality assessment reports
            experiment_id: Experiment identifier

        Returns:
            Path to generated dashboard file
        """
        if not quality_reports:
            msg = "No quality reports provided for visualization"
            raise ValueError(msg)

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Accuracy Distribution Across Folds",
                "False Positive vs False Negative Rates",
                "F1 Score Trends",
                "Target Compliance Summary"
            ],
            specs=[
                [{"type": "violin"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "pie"}]
            ]
        )

        # Accuracy distribution
        accuracies = [report.overall_accuracy for report in quality_reports]
        fold_ids = [report.fold_id or f"Fold_{i+1}" for i, report in enumerate(quality_reports)]

        fig.add_trace(
            go.Violin(y=accuracies, x=fold_ids, name="Accuracy Distribution",
                     box_visible=True, meanline_visible=True),
            row=1, col=1
        )

        # Add accuracy target line
        if self.config.include_targets:
            fig.add_hline(y=0.85, line_dash="dash", line_color="red",
                         annotation_text="Target: 85%", row=1, col=1)

        # FP vs FN scatter plot
        fp_rates = [report.false_positive_rate for report in quality_reports]
        fn_rates = [report.false_negative_rate for report in quality_reports]

        colors = ["green" if (fp < 0.05 and fn < 0.05) else "red"
                 for fp, fn in zip(fp_rates, fn_rates, strict=False)]

        fig.add_trace(
            go.Scatter(x=fp_rates, y=fn_rates, mode="markers+text",
                      text=fold_ids, textposition="top center",
                      marker={"size": 10, "color": colors},
                      name="FP vs FN Rates"),
            row=1, col=2
        )

        # Add target zones
        if self.config.include_targets:
            fig.add_vline(x=0.05, line_dash="dash", line_color="red", row=1, col=2)
            fig.add_hline(y=0.05, line_dash="dash", line_color="red", row=1, col=2)

            # Add target zone rectangle
            fig.add_shape(
                type="rect", x0=0, y0=0, x1=0.05, y1=0.05,
                fillcolor="green", opacity=0.2, line_width=0,
                row=1, col=2
            )

        # F1 Score trends
        f1_scores = [report.confusion_matrix.f1_score for report in quality_reports]

        fig.add_trace(
            go.Bar(x=fold_ids, y=f1_scores, name="F1 Score",
                   marker_color=self.config.color_palette[2]),
            row=2, col=1
        )

        # Target compliance pie chart
        fp_compliant = sum(1 for report in quality_reports if report.meets_fp_target)
        fn_compliant = sum(1 for report in quality_reports if report.meets_fn_target)
        both_compliant = sum(1 for report in quality_reports if report.meets_quality_targets)

        compliance_data = {
            "Both Targets Met": both_compliant,
            "FP Target Only": fp_compliant - both_compliant,
            "FN Target Only": fn_compliant - both_compliant,
            "Neither Target Met": len(quality_reports) - fp_compliant - fn_compliant + both_compliant
        }

        fig.add_trace(
            go.Pie(labels=list(compliance_data.keys()), values=list(compliance_data.values()),
                   name="Target Compliance",
                   marker_colors=["green", "yellow", "orange", "red"]),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title_text=f"Quality Metrics Dashboard - {experiment_id}",
            showlegend=True,
            height=self.config.figure_height,
            width=self.config.figure_width,
            template=self.config.style_theme
        )

        # Update axes labels
        fig.update_xaxes(title_text="False Positive Rate", row=1, col=2)
        fig.update_yaxes(title_text="False Negative Rate", row=1, col=2)

        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_dashboard_{experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Quality metrics dashboard saved to: {output_path}")
        return output_path

    def create_statistical_analysis_plots(self,
                                         statistical_summary: StatisticalSummary,
                                         experiment_id: str) -> Path:
        """
        Create statistical analysis visualization plots.

        Args:
            statistical_summary: Statistical analysis summary
            experiment_id: Experiment identifier

        Returns:
            Path to generated plots file
        """
        # Create subplots for statistical analysis
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Confidence Intervals",
                "Effect Sizes",
                "P-Value Distribution",
                "Statistical Power Analysis"
            ]
        )

        # Confidence intervals plot
        if statistical_summary.confidence_intervals:
            metrics = [ci.metric_name for ci in statistical_summary.confidence_intervals]
            point_estimates = [ci.point_estimate for ci in statistical_summary.confidence_intervals]
            lower_bounds = [ci.lower_bound for ci in statistical_summary.confidence_intervals]
            upper_bounds = [ci.upper_bound for ci in statistical_summary.confidence_intervals]

            # Create error bars
            error_y = {
                "type": "data",
                "symmetric": False,
                "array": [ub - pe for ub, pe in zip(upper_bounds, point_estimates, strict=False)],
                "arrayminus": [pe - lb for pe, lb in zip(point_estimates, lower_bounds, strict=False)]
            }

            fig.add_trace(
                go.Scatter(x=metrics, y=point_estimates, error_y=error_y,
                          mode="markers", marker_size=10, name="95% Confidence Intervals"),
                row=1, col=1
            )

        # Effect sizes plot
        if statistical_summary.statistical_tests:
            test_names = [test.test_name for test in statistical_summary.statistical_tests
                         if test.effect_size is not None]
            effect_sizes = [test.effect_size for test in statistical_summary.statistical_tests
                           if test.effect_size is not None]

            if effect_sizes:
                colors = ["green" if abs(es) >= 0.8 else "yellow" if abs(es) >= 0.5 else "red"
                         for es in effect_sizes]

                fig.add_trace(
                    go.Bar(x=test_names, y=effect_sizes, name="Effect Size (Cohen's d)",
                           marker_color=colors),
                    row=1, col=2
                )

                # Add effect size interpretation lines
                if self.config.include_targets:
                    fig.add_hline(y=0.2, line_dash="dot", line_color="gray",
                                 annotation_text="Small", row=1, col=2)
                    fig.add_hline(y=0.5, line_dash="dot", line_color="orange",
                                 annotation_text="Medium", row=1, col=2)
                    fig.add_hline(y=0.8, line_dash="dot", line_color="green",
                                 annotation_text="Large", row=1, col=2)

        # P-value distribution
        if statistical_summary.statistical_tests:
            p_values = [test.p_value for test in statistical_summary.statistical_tests]

            fig.add_trace(
                go.Histogram(x=p_values, nbinsx=20, name="P-Value Distribution",
                           marker_color=self.config.color_palette[3]),
                row=2, col=1
            )

            # Add significance threshold
            if self.config.include_targets:
                fig.add_vline(x=0.05, line_dash="dash", line_color="red",
                             annotation_text="α = 0.05", row=2, col=1)

        # Statistical power analysis (if available)
        if statistical_summary.statistical_tests:
            test_names_power = [test.test_name for test in statistical_summary.statistical_tests
                               if test.power is not None]
            powers = [test.power for test in statistical_summary.statistical_tests
                     if test.power is not None]

            if powers:
                colors_power = ["green" if p >= 0.8 else "yellow" if p >= 0.6 else "red"
                               for p in powers]

                fig.add_trace(
                    go.Bar(x=test_names_power, y=powers, name="Statistical Power",
                           marker_color=colors_power),
                    row=2, col=2
                )

                # Add power threshold
                if self.config.include_targets:
                    fig.add_hline(y=0.8, line_dash="dash", line_color="green",
                                 annotation_text="Target: 80%", row=2, col=2)

        # Update layout
        fig.update_layout(
            title_text=f"Statistical Analysis - {experiment_id}",
            showlegend=True,
            height=self.config.figure_height,
            width=self.config.figure_width,
            template=self.config.style_theme
        )

        # Save plots
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistical_analysis_{experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Statistical analysis plots saved to: {output_path}")
        return output_path

    def create_cost_reduction_waterfall(self,
                                      performance_metrics: CrossValidationMetrics,
                                      baseline_cost: float,
                                      experiment_id: str) -> Path:
        """
        Create cost reduction waterfall diagram.

        Args:
            performance_metrics: Performance metrics
            baseline_cost: Baseline cost for comparison
            experiment_id: Experiment identifier

        Returns:
            Path to generated waterfall chart
        """
        # Calculate cost components
        actual_cost = performance_metrics.total_cost_usd
        cost_reduction = baseline_cost - actual_cost
        percentage_reduction = (cost_reduction / baseline_cost * 100) if baseline_cost > 0 else 0

        # Prepare waterfall data
        categories = ["Baseline Cost", "LLM Processing", "Infrastructure", "Net Cost", "Savings"]
        values = [
            baseline_cost,
            -actual_cost * 0.8,  # Estimated LLM portion
            -actual_cost * 0.2,  # Estimated infrastructure portion
            actual_cost,
            cost_reduction
        ]

        # Create waterfall chart
        fig = go.Figure(go.Waterfall(
            name="Cost Analysis",
            orientation="v",
            measure=["absolute", "relative", "relative", "total", "total"],
            x=categories,
            textposition="outside",
            text=[f"${val:.2f}" for val in values],
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}},
            totals={"marker": {"color": "blue"}}
        ))

        fig.update_layout(
            title=f"Cost Reduction Analysis - {experiment_id}<br>"
                  f"<sub>Total Reduction: ${cost_reduction:.2f} ({percentage_reduction:.1f}%)</sub>",
            yaxis_title="Cost (USD)",
            width=self.config.figure_width,
            height=self.config.figure_height,
            template=self.config.style_theme
        )

        # Save waterfall chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_waterfall_{experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Cost waterfall chart saved to: {output_path}")
        return output_path

    def create_cross_validation_boxplots(self,
                                        performance_metrics: CrossValidationMetrics,
                                        quality_reports: list[QualityReport],
                                        experiment_id: str) -> Path:
        """
        Create cross-validation box plots showing distribution across folds.

        Args:
            performance_metrics: Performance metrics
            quality_reports: Quality reports
            experiment_id: Experiment identifier

        Returns:
            Path to generated box plots
        """
        # Use matplotlib for static box plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Cross-Validation Analysis - {experiment_id}", fontsize=16)

        # Processing time distribution
        if performance_metrics.fold_results:
            processing_times = [fold.avg_processing_time for fold in performance_metrics.fold_results
                              if fold.avg_processing_time]
            if processing_times:
                axes[0, 0].boxplot(processing_times)
                axes[0, 0].set_title("Processing Time Distribution")
                axes[0, 0].set_ylabel("Time (seconds)")

                # Add target line if applicable
                if self.config.include_targets:
                    target_time = 1800  # 30 minutes as example target
                    axes[0, 0].axhline(y=target_time, color="red", linestyle="--",
                                      label=f"Target: {target_time}s")
                    axes[0, 0].legend()

        # Success rate distribution
        if performance_metrics.fold_results:
            success_rates = [fold.success_rate for fold in performance_metrics.fold_results]
            axes[0, 1].boxplot(success_rates)
            axes[0, 1].set_title("Success Rate Distribution")
            axes[0, 1].set_ylabel("Success Rate (%)")

            if self.config.include_targets:
                axes[0, 1].axhline(y=90, color="red", linestyle="--", label="Target: 90%")
                axes[0, 1].legend()

        # Accuracy distribution
        if quality_reports:
            accuracies = [report.overall_accuracy * 100 for report in quality_reports]  # Convert to percentage
            axes[1, 0].boxplot(accuracies)
            axes[1, 0].set_title("Accuracy Distribution")
            axes[1, 0].set_ylabel("Accuracy (%)")

            if self.config.include_targets:
                axes[1, 0].axhline(y=85, color="red", linestyle="--", label="Target: 85%")
                axes[1, 0].legend()

        # Cost distribution
        if performance_metrics.fold_results:
            costs = [fold.total_cost_usd for fold in performance_metrics.fold_results]
            axes[1, 1].boxplot(costs)
            axes[1, 1].set_title("Cost Distribution")
            axes[1, 1].set_ylabel("Cost (USD)")

        plt.tight_layout()

        # Save static plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_boxplots_{experiment_id}_{timestamp}.png"
        output_path = self.output_directory / "static" / filename

        plt.savefig(str(output_path), dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        self.logger.info(f"Cross-validation box plots saved to: {output_path}")
        return output_path

    def create_comprehensive_dashboard(self,
                                     comprehensive_report: ComprehensiveReport) -> Path:
        """
        Create a comprehensive dashboard combining all visualizations.

        Args:
            comprehensive_report: Comprehensive analysis report

        Returns:
            Path to generated comprehensive dashboard
        """
        # Create multi-tab dashboard
        fig = sp.make_subplots(
            rows=3, cols=3,
            subplot_titles=[
                "Executive Summary", "Performance Overview", "Quality Metrics",
                "Coverage Analysis", "Statistical Significance", "Target Compliance",
                "Cost Analysis", "Fold Consistency", "GAMP Compliance"
            ],
            specs=[[{"type": "table"}, {"type": "bar"}, {"type": "scatter"}],
                   [{"type": "heatmap"}, {"type": "bar"}, {"type": "pie"}],
                   [{"type": "waterfall"}, {"type": "box"}, {"type": "indicator"}]]
        )

        # Executive Summary Table
        executive_data = comprehensive_report.executive_summary
        summary_table = go.Table(
            header={"values": ["Metric", "Value", "Target", "Status"]},
            cells={"values": [
                ["Documents Tested", "Success Rate", "Time Reduction", "Coverage", "Compliance"],
                [f"{executive_data.total_documents_tested}",
                 f"{executive_data.overall_success_rate:.1f}%",
                 f"{executive_data.time_reduction_achieved:.1f}%",
                 f"{executive_data.average_coverage:.1f}%",
                 f"{executive_data.compliance_percentage:.1f}%"],
                ["N/A", ">90%", ">70%", ">90%", ">80%"],
                ["✓",
                 "✓" if executive_data.overall_success_rate >= 90 else "✗",
                 "✓" if executive_data.time_reduction_achieved >= 70 else "✗",
                 "✓" if executive_data.average_coverage >= 90 else "✗",
                 "✓" if executive_data.compliance_percentage >= 80 else "✗"]
            ]}
        )
        fig.add_trace(summary_table, row=1, col=1)

        # Add other visualizations (simplified versions)
        # This would include data from the comprehensive report

        # Update layout
        fig.update_layout(
            title_text=f"Comprehensive Analysis Dashboard - {comprehensive_report.experiment_id}",
            height=1200,
            width=1800,
            template=self.config.style_theme,
            showlegend=False
        )

        # Save comprehensive dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_dashboard_{comprehensive_report.experiment_id}_{timestamp}.html"
        output_path = self.output_directory / "interactive" / filename

        fig.write_html(str(output_path))

        self.logger.info(f"Comprehensive dashboard saved to: {output_path}")
        return output_path

    def generate_all_visualizations(self,
                                  performance_metrics: CrossValidationMetrics,
                                  coverage_reports: list[CoverageReport],
                                  quality_reports: list[QualityReport],
                                  statistical_summary: StatisticalSummary,
                                  comprehensive_report: ComprehensiveReport,
                                  baseline_cost: float = 2000.0) -> list[Path]:
        """
        Generate all visualizations for the cross-validation analysis.

        Args:
            performance_metrics: Performance metrics
            coverage_reports: Coverage reports
            quality_reports: Quality reports
            statistical_summary: Statistical summary
            comprehensive_report: Comprehensive report
            baseline_cost: Baseline cost for comparison

        Returns:
            List of paths to generated visualization files
        """
        generated_files = []
        experiment_id = comprehensive_report.experiment_id

        try:
            # Performance dashboard
            perf_dashboard = self.create_performance_dashboard(performance_metrics, experiment_id)
            generated_files.append(perf_dashboard)

            # Coverage heatmap
            if coverage_reports:
                coverage_heatmap = self.create_coverage_heatmap(coverage_reports, experiment_id)
                generated_files.append(coverage_heatmap)

            # Quality metrics dashboard
            if quality_reports:
                quality_dashboard = self.create_quality_metrics_dashboard(quality_reports, experiment_id)
                generated_files.append(quality_dashboard)

            # Statistical analysis plots
            stats_plots = self.create_statistical_analysis_plots(statistical_summary, experiment_id)
            generated_files.append(stats_plots)

            # Cost reduction waterfall
            cost_waterfall = self.create_cost_reduction_waterfall(performance_metrics, baseline_cost, experiment_id)
            generated_files.append(cost_waterfall)

            # Cross-validation box plots
            cv_boxplots = self.create_cross_validation_boxplots(performance_metrics, quality_reports, experiment_id)
            generated_files.append(cv_boxplots)

            # Comprehensive dashboard
            comp_dashboard = self.create_comprehensive_dashboard(comprehensive_report)
            generated_files.append(comp_dashboard)

            self.logger.info(f"Generated {len(generated_files)} visualization files")

        except Exception as e:
            self.logger.exception(f"Error generating visualizations: {e!s}")
            raise

        return generated_files

    def create_visualization_index(self, generated_files: list[Path], experiment_id: str) -> Path:
        """
        Create an HTML index page linking to all generated visualizations.

        Args:
            generated_files: List of paths to visualization files
            experiment_id: Experiment identifier

        Returns:
            Path to generated index file
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cross-Validation Analysis - {experiment_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .visualization-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .viz-card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}
                .viz-card h3 {{ margin-top: 0; color: #0066cc; }}
                .viz-link {{ display: inline-block; background: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
                .viz-link:hover {{ background: #0052a3; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>Cross-Validation Analysis Results</h1>
            <p><strong>Experiment ID:</strong> {experiment_id}</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="visualization-grid">
        """

        # Add cards for each visualization
        viz_descriptions = {
            "performance_dashboard": "Performance metrics overview including timing, cost, and success rates",
            "coverage_heatmap": "Requirements coverage analysis across documents and categories",
            "quality_dashboard": "Quality metrics with accuracy, precision, and recall analysis",
            "statistical_analysis": "Statistical significance testing and confidence intervals",
            "cost_waterfall": "Cost reduction analysis and ROI calculations",
            "cv_boxplots": "Cross-validation distribution analysis",
            "comprehensive_dashboard": "Combined dashboard with all key metrics"
        }

        for file_path in generated_files:
            filename = file_path.name
            # Extract visualization type from filename
            viz_type = None
            for key in viz_descriptions:
                if key in filename:
                    viz_type = key
                    break

            description = viz_descriptions.get(viz_type, "Visualization analysis")

            html_content += f"""
                <div class="viz-card">
                    <h3>{filename.replace('_', ' ').title().replace('.html', '').replace('.png', '')}</h3>
                    <p>{description}</p>
                    <a href="{file_path.name}" class="viz-link">View Visualization</a>
                </div>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        # Save index file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        index_filename = f"visualization_index_{experiment_id}_{timestamp}.html"
        index_path = self.output_directory / index_filename

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"Visualization index created: {index_path}")
        return index_path
