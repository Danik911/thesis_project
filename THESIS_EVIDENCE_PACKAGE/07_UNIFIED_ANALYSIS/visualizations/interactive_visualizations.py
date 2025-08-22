#!/usr/bin/env python3
"""
Interactive Visualizations for Thesis Presentation
Using Plotly for dynamic, interactive charts
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path

class InteractiveVisualizer:
    def __init__(self):
        """Initialize with thesis data"""
        self.base_dir = Path(__file__).parent
        self.interactive_dir = self.base_dir / "interactive"
        self.interactive_dir.mkdir(exist_ok=True)
        
        # Load actual data
        self.load_data()
        
        # Academic color scheme
        self.colors = px.colors.qualitative.Safe
        
    def load_data(self):
        """Load analysis data"""
        # Real data from analysis
        self.success_data = pd.DataFrame({
            'Corpus': ['Overall', 'Corpus 1', 'Corpus 2', 'Corpus 3'],
            'n': [30, 17, 8, 5],
            'Success_Rate': [76.7, 64.7, 87.5, 100],
            'CI_Lower': [59.1, 41.2, 62.5, 47.8],
            'CI_Upper': [88.2, 84.5, 100, 100],
            'Accuracy': [91.3, 81.8, 100, 100]
        })
        
        self.timeline_data = pd.DataFrame({
            'Date': ['Aug 11-14', 'Aug 21 (AM)', 'Aug 21 (PM)'],
            'Corpus': ['Corpus 1', 'Corpus 2', 'Corpus 3'],
            'Success_Rate': [64.7, 87.5, 100],
            'Processing_Time': [8.2, 5.4, 7.6],
            'Cost_per_Doc': [0.045, 0.019, 0.070],
            'Tests_Generated': [102, 120, 95]
        })
        
    def create_all_interactive(self):
        """Generate all interactive visualizations"""
        print("Generating interactive visualizations...")
        
        # 1. Interactive Success Rate Dashboard
        self.create_success_dashboard()
        
        # 2. Temporal Improvement Animation
        self.create_temporal_animation()
        
        # 3. 3D Performance Space
        self.create_3d_performance()
        
        # 4. Sankey Diagram for Workflow
        self.create_sankey_workflow()
        
        # 5. Interactive Compliance Radar
        self.create_compliance_radar()
        
        # 6. Hierarchical Sunburst
        self.create_sunburst_analysis()
        
        print(f"Interactive visualizations saved to: {self.interactive_dir}")
    
    def create_success_dashboard(self):
        """Interactive success rate dashboard with drill-down"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Success Rates with Confidence Intervals',
                          'Categorization Accuracy',
                          'Document Distribution',
                          'Performance Metrics'),
            specs=[[{'type': 'bar'}, {'type': 'scatter'}],
                  [{'type': 'pie'}, {'type': 'indicator'}]]
        )
        
        # Success rates with error bars
        fig.add_trace(
            go.Bar(
                x=self.success_data['Corpus'],
                y=self.success_data['Success_Rate'],
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=self.success_data['CI_Upper'] - self.success_data['Success_Rate'],
                    arrayminus=self.success_data['Success_Rate'] - self.success_data['CI_Lower']
                ),
                marker_color=['#2E4057', '#C73E1D', '#F18F01', '#54C6EB'],
                text=self.success_data['Success_Rate'].round(1),
                textposition='outside',
                name='Success Rate',
                hovertemplate='<b>%{x}</b><br>' +
                            'Success Rate: %{y:.1f}%<br>' +
                            '95% CI: [%{error_y.arrayminus:.1f}, %{error_y.array:.1f}]<br>' +
                            '<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Target line
        fig.add_hline(y=85, line_dash="dash", line_color="red",
                     annotation_text="Target: 85%", row=1, col=1)
        
        # Accuracy comparison
        fig.add_trace(
            go.Scatter(
                x=self.success_data['Corpus'][1:],
                y=self.success_data['Accuracy'][1:],
                mode='lines+markers',
                marker=dict(size=15, color='#048A81'),
                line=dict(width=3, color='#048A81'),
                name='Categorization Accuracy',
                hovertemplate='<b>%{x}</b><br>Accuracy: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Document distribution pie
        fig.add_trace(
            go.Pie(
                labels=['Corpus 1 (56.7%)', 'Corpus 2 (26.7%)', 'Corpus 3 (16.7%)'],
                values=[17, 8, 5],
                hole=0.4,
                marker=dict(colors=['#C73E1D', '#F18F01', '#54C6EB']),
                textinfo='value+percent',
                hovertemplate='<b>%{label}</b><br>Documents: %{value}<br>%{percent}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Key metric indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=76.7,
                title={'text': "Overall Success Rate"},
                delta={'reference': 85, 'relative': True},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#2E4057"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Interactive Success Rate Dashboard",
            showlegend=False,
            height=800,
            hovermode='closest'
        )
        
        # Save
        fig.write_html(self.interactive_dir / "dashboard_success_rates.html")
        fig.write_json(self.interactive_dir / "dashboard_success_rates.json")
    
    def create_temporal_animation(self):
        """Animated temporal improvement visualization"""
        # Prepare data for animation
        animation_data = []
        for i in range(len(self.timeline_data)):
            for j in range(i+1):
                row = self.timeline_data.iloc[j].copy()
                row['Frame'] = f"Stage {i+1}"
                animation_data.append(row)
        
        df_animation = pd.DataFrame(animation_data)
        
        # Create animated scatter plot
        fig = px.scatter(
            df_animation,
            x='Processing_Time',
            y='Success_Rate',
            size='Tests_Generated',
            color='Corpus',
            animation_frame='Frame',
            range_x=[0, 10],
            range_y=[50, 105],
            size_max=50,
            title="Temporal Evolution of System Performance",
            labels={
                'Processing_Time': 'Average Processing Time (minutes)',
                'Success_Rate': 'Success Rate (%)',
                'Tests_Generated': 'Tests Generated'
            }
        )
        
        # Add trend line annotation
        fig.add_annotation(
            x=7, y=95,
            text="Improvement Trajectory →",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#2E4057",
            ax=50,
            ay=-30
        )
        
        # Update traces
        fig.update_traces(
            marker=dict(line=dict(width=2, color='DarkSlateGrey')),
            selector=dict(mode='markers')
        )
        
        # Save
        fig.write_html(self.interactive_dir / "temporal_animation.html")
    
    def create_3d_performance(self):
        """3D visualization of performance space"""
        # Generate data points
        np.random.seed(42)
        
        # Create 3D scatter plot
        fig = go.Figure(data=[
            go.Scatter3d(
                x=[64.7, 87.5, 100],  # Success Rate
                y=[8.2, 5.4, 7.6],    # Processing Time
                z=[0.045, 0.019, 0.070],  # Cost
                mode='markers+text',
                marker=dict(
                    size=[17, 8, 5],  # Proportional to sample size
                    color=['#C73E1D', '#F18F01', '#54C6EB'],
                    opacity=0.8,
                    line=dict(width=2, color='black')
                ),
                text=['Corpus 1', 'Corpus 2', 'Corpus 3'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>' +
                            'Success: %{x:.1f}%<br>' +
                            'Time: %{y:.1f} min<br>' +
                            'Cost: $%{z:.3f}<br>' +
                            '<extra></extra>'
            )
        ])
        
        # Add ideal point
        fig.add_trace(
            go.Scatter3d(
                x=[100],
                y=[3],
                z=[0.01],
                mode='markers',
                marker=dict(
                    size=10,
                    color='green',
                    symbol='diamond',
                    line=dict(width=2, color='darkgreen')
                ),
                text=['Ideal Target'],
                name='Target',
                hovertemplate='<b>Ideal Target</b><br>' +
                            'Success: 100%<br>' +
                            'Time: 3 min<br>' +
                            'Cost: $0.01<br>' +
                            '<extra></extra>'
            )
        )
        
        # Update layout
        fig.update_layout(
            title="3D Performance Space Analysis",
            scene=dict(
                xaxis_title='Success Rate (%)',
                yaxis_title='Processing Time (min)',
                zaxis_title='Cost per Document ($)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=700
        )
        
        # Save
        fig.write_html(self.interactive_dir / "3d_performance_space.html")
    
    def create_sankey_workflow(self):
        """Sankey diagram showing document processing workflow"""
        # Define nodes
        labels = [
            # Source nodes (0-2)
            "30 Documents", "17 Corpus 1", "8 Corpus 2", "5 Corpus 3",
            # Processing nodes (4-7)
            "Categorization", "Context Analysis", "Test Generation", "Validation",
            # Outcome nodes (8-11)
            "23 Successful", "6 Failed", "1 Human Review", "316 Tests Generated"
        ]
        
        # Define links
        source = [0, 0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 7, 7]
        target = [1, 2, 3, 4, 4, 4, 5, 8, 6, 7, 8, 9, 10]
        value = [17, 8, 5, 17, 8, 5, 23, 7, 23, 23, 23, 6, 1]
        
        # Colors for links
        link_colors = ['rgba(46,64,87,0.4)'] * len(source)
        link_colors[11] = 'rgba(199,62,29,0.4)'  # Failed - red
        link_colors[12] = 'rgba(241,143,1,0.4)'  # Human review - orange
        
        # Create Sankey
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=['#2E4057', '#C73E1D', '#F18F01', '#54C6EB',
                      '#048A81', '#048A81', '#048A81', '#048A81',
                      '#54C6EB', '#C73E1D', '#F18F01', '#2E4057']
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=link_colors
            )
        )])
        
        fig.update_layout(
            title="Document Processing Workflow - Sankey Diagram",
            height=600,
            font=dict(size=12)
        )
        
        # Save
        fig.write_html(self.interactive_dir / "sankey_workflow.html")
    
    def create_compliance_radar(self):
        """Interactive radar chart for compliance metrics"""
        # ALCOA+ dimensions
        categories = ['Attributable', 'Legible', 'Contemporaneous', 
                     'Original', 'Accurate', 'Complete', 'Consistent', 
                     'Enduring', 'Available']
        
        fig = go.Figure()
        
        # Current performance
        fig.add_trace(go.Scatterpolar(
            r=[100, 100, 100, 100, 91.3, 76.7, 100, 100, 100],
            theta=categories,
            fill='toself',
            name='Current Performance',
            fillcolor='rgba(46,64,87,0.3)',
            line=dict(color='#2E4057', width=2)
        ))
        
        # Target performance
        fig.add_trace(go.Scatterpolar(
            r=[95, 95, 95, 95, 95, 95, 95, 95, 95],
            theta=categories,
            fill='toself',
            name='Target',
            fillcolor='rgba(255,0,0,0.1)',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Industry benchmark
        fig.add_trace(go.Scatterpolar(
            r=[85, 90, 85, 90, 80, 75, 85, 90, 88],
            theta=categories,
            fill='toself',
            name='Industry Benchmark',
            fillcolor='rgba(0,255,0,0.1)',
            line=dict(color='green', width=1, dash='dot')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="ALCOA+ Compliance - Interactive Radar Chart",
            height=600
        )
        
        # Save
        fig.write_html(self.interactive_dir / "compliance_radar.html")
    
    def create_sunburst_analysis(self):
        """Hierarchical sunburst chart for comprehensive analysis"""
        # Prepare hierarchical data
        data = dict(
            labels=[
                "System Performance", 
                # Level 1
                "Success Metrics", "Cost Efficiency", "Compliance", "Quality",
                # Level 2 - Success
                "Overall 76.7%", "Corpus 1", "Corpus 2", "Corpus 3",
                # Level 2 - Cost
                "91% Reduction", "API Usage", "Time Savings",
                # Level 2 - Compliance
                "GAMP-5", "21 CFR", "ALCOA+",
                # Level 2 - Quality
                "Accuracy 91.3%", "316 Tests", "Human Review"
            ],
            parents=[
                "",
                # Level 1
                "System Performance", "System Performance", "System Performance", "System Performance",
                # Level 2 - Success
                "Success Metrics", "Success Metrics", "Success Metrics", "Success Metrics",
                # Level 2 - Cost
                "Cost Efficiency", "Cost Efficiency", "Cost Efficiency",
                # Level 2 - Compliance
                "Compliance", "Compliance", "Compliance",
                # Level 2 - Quality
                "Quality", "Quality", "Quality"
            ],
            values=[
                0,
                # Level 1
                0, 0, 0, 0,
                # Level 2
                30, 17, 8, 5,  # Success
                91, 5, 4,      # Cost
                91.3, 100, 96.3,  # Compliance
                91.3, 316, 1   # Quality
            ]
        )
        
        fig = go.Figure(go.Sunburst(
            labels=data['labels'],
            parents=data['parents'],
            values=data['values'],
            branchvalues="total",
            marker=dict(
                colors=['#2E4057', '#048A81', '#F18F01', '#54C6EB', '#8B8B8B',
                       '#C73E1D', '#C73E1D', '#F18F01', '#54C6EB',
                       '#048A81', '#048A81', '#048A81',
                       '#2E4057', '#2E4057', '#2E4057',
                       '#54C6EB', '#54C6EB', '#F18F01'],
                line=dict(color="white", width=2)
            ),
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>%{percentParent}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Hierarchical System Performance Analysis",
            height=700
        )
        
        # Save
        fig.write_html(self.interactive_dir / "sunburst_analysis.html")


if __name__ == "__main__":
    visualizer = InteractiveVisualizer()
    visualizer.create_all_interactive()
    print("\nInteractive visualizations generated successfully!")
    print(f"Location: {visualizer.interactive_dir}")
    print("\nGenerated Interactive Visualizations:")
    print("- Success Rate Dashboard (dashboard_success_rates.html)")
    print("- Temporal Animation (temporal_animation.html)")
    print("- 3D Performance Space (3d_performance_space.html)")
    print("- Workflow Sankey Diagram (sankey_workflow.html)")
    print("- Compliance Radar Chart (compliance_radar.html)")
    print("- Hierarchical Sunburst (sunburst_analysis.html)")
    print("\nOpen HTML files in browser for interactive experience!")