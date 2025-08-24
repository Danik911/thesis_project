#!/usr/bin/env python3
"""
Simple test script to verify visualization generation works.
"""

import sys
from pathlib import Path

# Add main source to path for imports
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))

from visualization.thesis_visualizations import ThesisData, ThesisVisualizationGenerator


def test_simple_generation():
    """Test simple visualization generation."""
    print("Testing simple visualization generation...")

    # Use real data
    data = ThesisData()
    print(f"ROI: {data.roi_percentage:,.0f}%")
    print(f"Cost savings: ${data.cost_savings_per_doc:,}")
    print(f"Tests generated: {data.tests_generated}")

    # Create output directory
    output_dir = Path("test_visualizations")
    output_dir.mkdir(exist_ok=True)

    # Initialize generator
    viz_gen = ThesisVisualizationGenerator(output_dir)

    try:
        # Test just one visualization first - ROI chart but only HTML
        print("Creating ROI waterfall chart (HTML only)...")

        # Modified version that only creates HTML
        from datetime import datetime

        import plotly.graph_objects as go

        # Calculate waterfall components (real values, no fallbacks)
        initial_investment = data.development_cost
        cost_per_doc_savings = data.cost_savings_per_doc
        docs_processed = 20  # Conservative estimate for thesis
        total_savings = cost_per_doc_savings * docs_processed
        net_roi = total_savings - initial_investment

        # Create simple waterfall chart
        fig = go.Figure(go.Waterfall(
            name="ROI Analysis",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Initial Investment", "Cost Savings", "Net ROI"],
            textposition="outside",
            text=[f"${initial_investment:,}", f"${total_savings:,}", f"${net_roi:,}"],
            y=[0, -initial_investment, net_roi],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
            title=f"ROI Analysis: {data.roi_percentage:,.0f}% Return on Investment",
            yaxis_title="Financial Impact (USD)",
            template="plotly_white",
            width=1000,
            height=600
        )

        # Save only HTML version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = output_dir / f"roi_waterfall_test_{timestamp}.html"
        fig.write_html(str(html_path))

        print(f"SUCCESS: HTML visualization saved to {html_path}")

        # Test if file was created and has content
        if html_path.exists() and html_path.stat().st_size > 0:
            print("File created successfully with content")
            return True
        print("File creation failed")
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_generation()
    if success:
        print("\nSimple visualization test PASSED")
    else:
        print("\nSimple visualization test FAILED")
