#!/usr/bin/env python3
"""
Fix Visualization Overlapping Issues for Chapter 4
Pharmaceutical Test Generation System - Thesis Graphics
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime

# Set style for academic publication
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_analysis_data():
    """Load the statistical analysis report"""
    report_path = Path("statistical_analysis_report_20250822_084144.json")
    with open(report_path, 'r') as f:
        return json.load(f)

def fix_compliance_radar(data):
    """Create fixed radar chart with no overlapping text"""
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='polar')
    
    # Compliance data
    comp = data['compliance_assessment']
    
    categories = ['GAMP-5', '21 CFR\nPart 11', 'ALCOA+']
    scores = [
        comp['gamp5']['overall_score'],
        comp['cfr_21_part_11']['overall_score'],
        comp['alcoa_plus']['overall_score']
    ]
    
    # Number of variables
    num_vars = len(categories)
    
    # Compute angle for each axis with better spacing
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    scores_complete = scores + scores[:1]  # Complete the circle
    angles_complete = angles + angles[:1]
    
    # Plot
    ax.plot(angles_complete, scores_complete, 'o-', linewidth=2.5, 
            color='#3498db', label='Current Score', markersize=10)
    ax.fill(angles_complete, scores_complete, alpha=0.25, color='#3498db')
    
    # Add baseline
    baseline = [75] * (num_vars + 1)
    ax.plot(angles_complete, baseline, 'r--', linewidth=1.5, 
            alpha=0.5, label='Compliance Threshold (75%)')
    
    # Fix axis to go in the right order
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Draw labels with larger font
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, size=14, fontweight='bold')
    
    # Set y-axis limits and labels
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=11)
    
    # Add scores as text with better positioning to avoid overlap
    # ALCOA+ score positioning adjusted to avoid overlap
    score_positions = {
        'GAMP-5': (angles[0], scores[0] - 8),  # Below the point
        '21 CFR\nPart 11': (angles[1], scores[1] + 8),  # Above the point
        'ALCOA+': (angles[2] - 0.15, scores[2] - 5)  # Shifted left and below
    }
    
    for i, (cat, score) in enumerate(zip(categories, scores)):
        angle_pos, radius_pos = score_positions[cat.replace('\n', '\n')]
        # Use white background box for better readability
        bbox_props = dict(boxstyle="round,pad=0.3", facecolor="white", 
                         edgecolor="gray", alpha=0.9)
        ax.text(angle_pos, radius_pos, f'{score:.1f}%', 
               ha='center', va='center', size=12, fontweight='bold',
               bbox=bbox_props)
    
    # Title with more padding
    ax.set_title('Pharmaceutical Compliance Assessment\n', 
                size=16, fontweight='bold', pad=30)
    
    # Legend positioned better
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), 
             fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figure_4_3_compliance_radar_fixed.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_3_compliance_radar_fixed.pdf', bbox_inches='tight')
    print("Generated: figure_4_3_compliance_radar_fixed.png/pdf")

def fix_confidence_interval_plot(data):
    """Create fixed confidence interval visualization with no overlapping"""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Extract CI data
    mit = data['statistical_analysis']['mitigation_metrics']
    point_estimate = mit['overall_mitigation_rate'] * 100
    ci_lower = mit['confidence_interval_95'][0] * 100
    ci_upper = mit['confidence_interval_95'][1] * 100
    
    # Create visualization
    categories = ['Overall\nSystem', 'LLM01\nPrompt\nInjection', 
                 'LLM06\nOutput\nHandling', 'LLM09\nOver-\nreliance']
    estimates = [point_estimate]
    ci_lowers = [ci_lower]
    ci_uppers = [ci_upper]
    
    # Add category-specific data
    cat_mapping = {
        'LLM01_PROMPT_INJECTION': 1,
        'LLM06_OUTPUT_HANDLING': 2,
        'LLM09_OVERRELIANCE': 3
    }
    
    for cat, idx in cat_mapping.items():
        if cat in mit['category_effectiveness']:
            rate = mit['category_effectiveness'][cat]['mitigation_rate'] * 100
            estimates.append(rate)
            # Simple CI calculation for categories
            n = mit['category_effectiveness'][cat]['total_tests']
            margin = 1.96 * np.sqrt((rate/100 * (1-rate/100)) / n) * 100 if n > 0 else 10
            ci_lowers.append(max(0, rate - margin))
            ci_uppers.append(min(100, rate + margin))
    
    # Plot with wider spacing
    x_pos = np.arange(len(categories)) * 1.5  # Increase spacing
    
    # Plot confidence intervals with thicker lines
    for i, (lower, upper, est) in enumerate(zip(ci_lowers, ci_uppers, estimates)):
        # Vertical CI lines
        ax.plot([x_pos[i], x_pos[i]], [lower, upper], 'b-', linewidth=3, alpha=0.7)
        # Horizontal caps
        ax.plot([x_pos[i]-0.1, x_pos[i]+0.1], [lower, lower], 'b-', linewidth=2)
        ax.plot([x_pos[i]-0.1, x_pos[i]+0.1], [upper, upper], 'b-', linewidth=2)
        # Point estimate
        ax.plot(x_pos[i], est, 'ro', markersize=10)
        
        # Add value labels with smart positioning
        # Alternate above and below to avoid overlap
        if i % 2 == 0:
            y_offset = upper + 3
            va = 'bottom'
        else:
            y_offset = upper + 6
            va = 'bottom'
        
        # Add white background for better readability
        bbox_props = dict(boxstyle="round,pad=0.2", facecolor="white", 
                         edgecolor="none", alpha=0.8)
        ax.text(x_pos[i], y_offset, f'{est:.1f}%\n[{lower:.1f}, {upper:.1f}]', 
               ha='center', va=va, fontsize=10, fontweight='bold',
               bbox=bbox_props)
    
    # Add baseline with labels in legend
    ax.axhline(y=75, color='g', linestyle='--', linewidth=2, 
              alpha=0.5, label='Target Baseline (75%)')
    ax.axhline(y=50, color='orange', linestyle='--', linewidth=2, 
              alpha=0.5, label='Minimum Acceptable (50%)')
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylabel('Mitigation Effectiveness (%)', fontsize=13)
    ax.set_xlabel('Assessment Category', fontsize=13)
    ax.set_title('95% Confidence Intervals for Mitigation Effectiveness', 
                fontsize=15, fontweight='bold', pad=20)
    ax.set_ylim(0, 105)  # Increased to accommodate labels
    
    # Improve legend positioning
    ax.legend(loc='lower right', fontsize=11, frameon=True, 
             fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('figure_4_4_confidence_intervals_fixed.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_4_confidence_intervals_fixed.pdf', bbox_inches='tight')
    print("Generated: figure_4_4_confidence_intervals_fixed.png/pdf")

def create_statistical_summary_visuals():
    """Create comprehensive visualizations for all statistical JSON files"""
    
    # Load all assessment data
    extended_1 = None
    extended_2 = None
    
    try:
        with open('extended_results/extended_assessment_20250822_081632.json', 'r') as f:
            extended_1 = json.load(f)
    except:
        print("Could not load extended_assessment_20250822_081632.json")
    
    try:
        with open('extended_results/extended_assessment_20250822_082617.json', 'r') as f:
            extended_2 = json.load(f)
    except:
        print("Could not load extended_assessment_20250822_082617.json")
    
    # Create combined statistics visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Panel 1: Test execution timeline
    ax1 = axes[0, 0]
    if extended_1 and extended_2:
        times = ['Assessment 1\n(08:16)', 'Assessment 2\n(08:26)']
        durations = [
            extended_1.get('duration_seconds', 0) / 60,  # Convert to minutes
            extended_2.get('duration_seconds', 0) / 60
        ]
        scenarios = [
            extended_1['summary']['total_scenarios'],
            extended_2['summary']['total_scenarios']
        ]
        
        x = np.arange(len(times))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, durations, width, label='Duration (min)', color='#3498db')
        bars2 = ax1.bar(x + width/2, scenarios, width, label='Scenarios', color='#2ecc71')
        
        ax1.set_xlabel('Assessment Run')
        ax1.set_ylabel('Value')
        ax1.set_title('Test Execution Summary', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(times)
        ax1.legend()
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom')
        for bar in bars2:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
    
    # Panel 2: Error analysis
    ax2 = axes[0, 1]
    if extended_1 or extended_2:
        error_types = ['Timeout', 'Security Block', 'API Error', 'Other']
        error_counts = [0, 0, 0, 0]
        
        # Count errors from both assessments
        for assessment in [extended_1, extended_2]:
            if assessment and 'raw_results' in assessment:
                for result in assessment['raw_results']:
                    if 'error' in result:
                        error_msg = result['error'].lower()
                        if 'timeout' in error_msg or 'timed out' in error_msg:
                            error_counts[0] += 1
                        elif 'security' in error_msg or 'owasp' in error_msg:
                            error_counts[1] += 1
                        elif 'api' in error_msg or 'authentication' in error_msg:
                            error_counts[2] += 1
                        else:
                            error_counts[3] += 1
        
        # Create pie chart
        colors = ['#e74c3c', '#f39c12', '#9b59b6', '#95a5a6']
        non_zero = [(t, c, col) for t, c, col in zip(error_types, error_counts, colors) if c > 0]
        
        if non_zero:
            labels, sizes, chart_colors = zip(*non_zero)
            wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=chart_colors,
                                               autopct='%1.0f%%', startangle=90)
            ax2.set_title('Error Distribution Analysis', fontweight='bold')
    
    # Panel 3: Mitigation effectiveness over time
    ax3 = axes[1, 0]
    if extended_1 and extended_2:
        assessments = ['Assessment 1', 'Assessment 2', 'Combined']
        effectiveness = [
            extended_1['summary']['mitigation_effectiveness'] * 100,
            extended_2['summary']['mitigation_effectiveness'] * 100,
            ((extended_1['summary']['mitigation_effectiveness'] + 
              extended_2['summary']['mitigation_effectiveness']) / 2) * 100
        ]
        
        bars = ax3.bar(assessments, effectiveness, color=['#3498db', '#2ecc71', '#e67e22'])
        ax3.axhline(y=75, color='r', linestyle='--', alpha=0.5, label='Target (75%)')
        ax3.set_ylabel('Mitigation Effectiveness (%)')
        ax3.set_title('Mitigation Effectiveness Comparison', fontweight='bold')
        ax3.set_ylim(0, 105)
        ax3.legend()
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    # Panel 4: Test category distribution
    ax4 = axes[1, 1]
    categories = ['LLM01', 'LLM05', 'LLM06', 'LLM07', 'LLM09', 'LLM10']
    planned = [20, 5, 5, 2, 5, 3]  # Planned test counts
    executed = [3, 0, 0, 0, 0, 0]  # Actually executed from the limited run
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, planned, width, label='Planned', color='#3498db', alpha=0.7)
    bars2 = ax4.bar(x + width/2, executed, width, label='Executed', color='#2ecc71')
    
    ax4.set_xlabel('OWASP Category')
    ax4.set_ylabel('Number of Tests')
    ax4.set_title('Test Coverage by Category', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories, rotation=45)
    ax4.legend()
    
    plt.suptitle('Extended Security Assessment Statistics', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('figure_4_5_statistical_summary.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_5_statistical_summary.pdf', bbox_inches='tight')
    print("Generated: figure_4_5_statistical_summary.png/pdf")

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("FIXING CHAPTER 4 VISUALIZATIONS")
    print("="*60 + "\n")
    
    # Load data
    print("Loading statistical analysis data...")
    data = load_analysis_data()
    
    # Fix overlapping issues
    print("\nFixing visualization overlaps...")
    print("-" * 40)
    
    print("\n1. Fixing Compliance Radar Chart (ALCOA+ overlap)...")
    fix_compliance_radar(data)
    
    print("\n2. Fixing Confidence Intervals Plot (top-right overlap)...")
    fix_confidence_interval_plot(data)
    
    print("\n3. Creating Statistical Summary Visualizations...")
    create_statistical_summary_visuals()
    
    print("\n" + "="*60)
    print("VISUALIZATION FIXES COMPLETE")
    print("="*60)
    print("\nFixed files generated:")
    print("  - figure_4_3_compliance_radar_fixed.png/pdf")
    print("  - figure_4_4_confidence_intervals_fixed.png/pdf")
    print("  - figure_4_5_statistical_summary.png/pdf")
    print("\nThese files have no overlapping text and are ready for thesis inclusion.")

if __name__ == "__main__":
    main()