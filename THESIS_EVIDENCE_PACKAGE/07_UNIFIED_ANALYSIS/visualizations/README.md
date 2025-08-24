# Thesis Visualizations - Chapter 4

## Overview
This directory contains all visualizations for Chapter 4: Results and Analysis of the thesis on "Multi-Agent LLM System for Pharmaceutical Test Generation". The visualizations are based on the comprehensive n=30 cross-validation study.

## Directory Structure
```
visualizations/
├── figures/           # Static high-resolution figures for thesis
├── interactive/       # Interactive HTML visualizations for presentations
├── thesis_visualizations.py     # Script for static figures
└── interactive_visualizations.py # Script for interactive charts
```

## Static Figures (for Thesis Document)

All figures are provided in both **PNG** (for viewing) and **PDF** (for LaTeX inclusion) formats at 300 DPI resolution.

### Figure 4.1: Success Rates with Confidence Intervals
- **File**: `figures/fig_4_1_success_rates_ci.[png/pdf]`
- **Content**: Bar chart showing success rates for overall (76.7%) and each corpus with 95% confidence intervals
- **Key Finding**: Clear improvement trend from Corpus 1 (64.7%) to Corpus 3 (100%)
- **Target Line**: 85% target clearly marked

### Figure 4.2: Temporal Improvement Analysis
- **File**: `figures/fig_4_2_temporal_improvement.[png/pdf]`
- **Content**: Dual plot showing success rate and accuracy trends over time, plus processing time evolution
- **Key Finding**: Consistent improvement trajectory: 64.7% → 87.5% → 100%
- **Significance**: Demonstrates system learning and optimization

### Figure 4.3: Cost-Benefit Waterfall Analysis
- **File**: `figures/fig_4_3_cost_benefit_waterfall.[png/pdf]`
- **Content**: Waterfall chart breaking down cost savings from manual ($240) to AI system ($0.042)
- **Key Finding**: 91% cost reduction achieved
- **Components**: Labor savings, time reduction, error reduction vs. AI costs

### Figure 4.4: Compliance Assessment Dashboard
- **File**: `figures/fig_4_4_compliance_dashboard.[png/pdf]`
- **Content**: Multi-panel dashboard with gauge charts, bar charts, spider plot, and heatmap
- **Coverage**: GAMP-5 (91.3%), 21 CFR Part 11 (Pass), ALCOA+ (96.3%)
- **Key Finding**: Strong compliance foundation with specific gaps identified

### Figure 4.5: Performance Metrics Distribution
- **File**: `figures/fig_4_5_performance_distribution.[png/pdf]`
- **Content**: Four-panel analysis with violin plots, box plots, histogram, and swarm plot
- **Metrics**: Processing time, test count, confidence scores, token usage
- **Key Finding**: Consistent performance with acceptable variance

### Figure 4.6: GAMP-5 Categorization Confusion Matrix
- **File**: `figures/fig_4_6_confusion_matrix.[png/pdf]`
- **Content**: 4x4 confusion matrix for categorization accuracy
- **Overall Accuracy**: 91.3% (21/23 correct)
- **Errors**: 2 ambiguous documents misclassified

### Figure 4.7: Statistical Power Analysis
- **File**: `figures/fig_4_7_power_analysis.[png/pdf]`
- **Content**: Power curve and effect size comparison
- **Current Power**: 0.50 (below 0.80 target)
- **Required Sample**: n=114 for 80% power
- **Effect Size**: 0.329 (small)

### Figure 4.8: Cross-Corpus Comparison
- **File**: `figures/fig_4_8_corpus_comparison.[png/pdf]`
- **Content**: Six-panel comprehensive comparison across all corpuses
- **Metrics**: Success rates, processing time, costs, test generation, API usage, weighted contribution
- **Key Finding**: Each corpus contributes proportionally to overall results

## Interactive Visualizations (for Presentations)

HTML files that can be opened in any modern browser for interactive exploration.

### 1. Success Rate Dashboard
- **File**: `interactive/dashboard_success_rates.html`
- **Features**: 
  - Hover for detailed statistics
  - Drill-down capability
  - Gauge showing overall performance vs. target
  - Interactive pie chart for distribution

### 2. Temporal Animation
- **File**: `interactive/temporal_animation.html`
- **Features**:
  - Animated progression through corpuses
  - Play/pause controls
  - Shows evolution of metrics over time

### 3. 3D Performance Space
- **File**: `interactive/3d_performance_space.html`
- **Features**:
  - Rotatable 3D scatter plot
  - Success rate vs. time vs. cost
  - Zoom and pan capabilities
  - Ideal target point marked

### 4. Workflow Sankey Diagram
- **File**: `interactive/sankey_workflow.html`
- **Features**:
  - Document flow visualization
  - Shows processing stages
  - Highlights failures and human review
  - Interactive node selection

### 5. Compliance Radar Chart
- **File**: `interactive/compliance_radar.html`
- **Features**:
  - ALCOA+ dimensions
  - Current vs. target vs. benchmark
  - Interactive legend
  - Hover for exact values

### 6. Hierarchical Sunburst
- **File**: `interactive/sunburst_analysis.html`
- **Features**:
  - Drill-down into categories
  - Proportional sizing
  - Complete system overview
  - Click to zoom sections

## Usage Instructions

### For Thesis Document (LaTeX)

```latex
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/fig_4_1_success_rates_ci.pdf}
    \caption{Success rates with 95\% confidence intervals across all corpuses (n=30)}
    \label{fig:success_rates}
\end{figure}
```

### For Presentations

1. Open any HTML file in a web browser
2. Use mouse to interact (hover, click, drag)
3. Most charts support:
   - Zoom (scroll wheel)
   - Pan (click and drag)
   - Export (camera icon in toolbar)

### For Publications

Use PDF versions for vector graphics quality:
- No pixelation at any zoom level
- Smaller file sizes
- Professional appearance
- CMYK color support

## Regenerating Visualizations

To regenerate with updated data:

```bash
# Static figures
python thesis_visualizations.py

# Interactive charts
python interactive_visualizations.py
```

## Color Scheme

The visualizations use a **colorblind-friendly** academic palette:
- Primary: `#2E4057` (Dark Blue)
- Secondary: `#048A81` (Teal)
- Success: `#54C6EB` (Light Blue)
- Warning: `#F18F01` (Orange)
- Danger: `#C73E1D` (Red)
- Neutral: `#8B8B8B` (Gray)

## Best Practices Applied

1. **Clarity**: Simple, uncluttered designs
2. **Accessibility**: Colorblind-friendly palette
3. **Consistency**: Uniform style across all figures
4. **Context**: Clear titles, labels, and legends
5. **Academic Standards**: Times New Roman font, 300 DPI
6. **Data Integrity**: Actual results, no smoothing

## Key Insights Visualized

1. **Temporal Improvement**: 64.7% → 87.5% → 100% success progression
2. **Cost Efficiency**: 91% reduction vs. manual process
3. **Statistical Reality**: 76.7% success with [59.1%, 88.2%] CI
4. **Compliance Strength**: 91.3% GAMP-5, 96.3% ALCOA+
5. **Power Limitation**: 0.50 power indicates need for larger sample

## Citation

If using these visualizations, please cite:
```
[Your Name]. (2025). Multi-Agent LLM System for Pharmaceutical Test Generation. 
Chapter 4: Results and Analysis. [Thesis]. [University Name].
```

## Technical Requirements

- **Python**: 3.8+
- **Libraries**: matplotlib, seaborn, plotly, pandas, numpy
- **Browser**: Chrome, Firefox, Edge (for interactive)
- **LaTeX**: pdflatex with graphicx package

---
*Generated: August 21, 2025*
*Data Source: n=30 cross-validation study*
*Contact: [Your Email]*