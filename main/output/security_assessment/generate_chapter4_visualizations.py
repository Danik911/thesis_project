#!/usr/bin/env python3
"""
Generate Chapter 4 Visualizations for OWASP Security Assessment
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

def create_mitigation_effectiveness_chart(data):
    """Create bar chart showing mitigation effectiveness by category"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    categories = []
    rates = []
    counts = []
    
    for cat, stats in data['statistical_analysis']['mitigation_metrics']['category_effectiveness'].items():
        categories.append(cat.replace('_', '\n'))
        rates.append(stats['mitigation_rate'] * 100)
        counts.append(stats['total_tests'])
    
    # Create bars
    bars = ax.bar(categories, rates, color=['#2ecc71' if r > 60 else '#f39c12' if r > 40 else '#e74c3c' for r in rates])
    
    # Add value labels on bars
    for bar, count, rate in zip(bars, counts, rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}%\n(n={count})',
                ha='center', va='bottom', fontsize=9)
    
    ax.set_ylabel('Mitigation Effectiveness (%)', fontsize=12)
    ax.set_xlabel('OWASP Category', fontsize=12)
    ax.set_title('Security Mitigation Effectiveness by OWASP Category', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    
    # Add horizontal line for baseline
    ax.axhline(y=75, color='r', linestyle='--', alpha=0.5, label='Target Baseline (75%)')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('figure_4_1_mitigation_effectiveness.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_1_mitigation_effectiveness.pdf', bbox_inches='tight')
    print("Generated: figure_4_1_mitigation_effectiveness.png/pdf")

def create_threat_distribution_pie(data):
    """Create pie chart showing threat level distribution"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Threat levels pie chart
    threat_dist = data['statistical_analysis']['threat_detection']['threat_distribution']
    
    # Filter out NONE category for clarity
    threat_dist_filtered = {k: v for k, v in threat_dist.items() if k != 'NONE' and v > 0}
    
    if threat_dist_filtered:
        colors = {'CRITICAL': '#e74c3c', 'HIGH': '#f39c12', 'MEDIUM': '#3498db', 'LOW': '#2ecc71'}
        labels = list(threat_dist_filtered.keys())
        sizes = list(threat_dist_filtered.values())
        chart_colors = [colors.get(label, '#95a5a6') for label in labels]
        
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=chart_colors, 
                                            autopct='%1.1f%%', startangle=90)
        ax1.set_title('Detected Threat Levels\n(63 Total Threats)', fontsize=12, fontweight='bold')
    
    # Mitigation outcome pie chart
    total = data['statistical_analysis']['mitigation_metrics']['total_scenarios']
    blocked = data['statistical_analysis']['mitigation_metrics']['security_blocks']
    unblocked = total - blocked
    
    outcomes = ['Blocked\n(Mitigated)', 'Unblocked\n(Safe/Test)']
    outcome_sizes = [blocked, unblocked]
    outcome_colors = ['#2ecc71', '#95a5a6']
    
    wedges2, texts2, autotexts2 = ax2.pie(outcome_sizes, labels=outcomes, colors=outcome_colors,
                                           autopct=lambda pct: f'{pct:.1f}%\n({int(pct*total/100)})',
                                           startangle=45)
    ax2.set_title('Security Response Distribution\n(113 Total Scenarios)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('figure_4_2_threat_distribution.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_2_threat_distribution.pdf', bbox_inches='tight')
    print("Generated: figure_4_2_threat_distribution.png/pdf")

def create_compliance_radar(data):
    """Create radar chart showing compliance scores"""
    fig = plt.figure(figsize=(10, 10))
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
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    scores += scores[:1]  # Complete the circle
    angles += angles[:1]
    
    # Plot
    ax.plot(angles, scores, 'o-', linewidth=2, color='#3498db', label='Current Score')
    ax.fill(angles, scores, alpha=0.25, color='#3498db')
    
    # Add baseline
    baseline = [75] * (num_vars + 1)
    ax.plot(angles, baseline, 'r--', linewidth=1, alpha=0.5, label='Compliance Threshold')
    
    # Fix axis to go in the right order
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Draw labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=12)
    
    # Set y-axis limits and labels
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=10)
    
    # Add scores as text
    for angle, score, cat in zip(angles[:-1], scores[:-1], categories):
        ax.text(angle, score + 5, f'{score:.1f}%', 
               ha='center', va='center', size=10, fontweight='bold')
    
    ax.set_title('Pharmaceutical Compliance Assessment\n', size=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig('figure_4_3_compliance_radar.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_3_compliance_radar.pdf', bbox_inches='tight')
    print("Generated: figure_4_3_compliance_radar.png/pdf")

def create_confidence_interval_plot(data):
    """Create confidence interval visualization"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract CI data
    mit = data['statistical_analysis']['mitigation_metrics']
    point_estimate = mit['overall_mitigation_rate'] * 100
    ci_lower = mit['confidence_interval_95'][0] * 100
    ci_upper = mit['confidence_interval_95'][1] * 100
    
    # Create visualization
    categories = ['Overall System', 'LLM01\nPrompt Injection', 'LLM06\nOutput Handling', 'LLM09\nOverreliance']
    estimates = [point_estimate]
    ci_lowers = [ci_lower]
    ci_uppers = [ci_upper]
    
    # Add category-specific data
    for cat in ['LLM01_PROMPT_INJECTION', 'LLM06_OUTPUT_HANDLING', 'LLM09_OVERRELIANCE']:
        if cat in mit['category_effectiveness']:
            rate = mit['category_effectiveness'][cat]['mitigation_rate'] * 100
            estimates.append(rate)
            # Simple CI calculation for categories
            n = mit['category_effectiveness'][cat]['total_tests']
            margin = 1.96 * np.sqrt((rate/100 * (1-rate/100)) / n) * 100
            ci_lowers.append(max(0, rate - margin))
            ci_uppers.append(min(100, rate + margin))
    
    # Plot
    x_pos = np.arange(len(categories))
    
    # Plot confidence intervals
    for i, (lower, upper, est) in enumerate(zip(ci_lowers, ci_uppers, estimates)):
        ax.plot([i, i], [lower, upper], 'b-', linewidth=2, alpha=0.7)
        ax.plot(i, est, 'ro', markersize=8)
        ax.text(i, upper + 2, f'{est:.1f}%', ha='center', fontsize=10)
    
    # Add baseline
    ax.axhline(y=75, color='g', linestyle='--', alpha=0.5, label='Target Baseline (75%)')
    ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='Minimum Acceptable (50%)')
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories)
    ax.set_ylabel('Mitigation Effectiveness (%)', fontsize=12)
    ax.set_title('95% Confidence Intervals for Security Mitigation Rates', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figure_4_4_confidence_intervals.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_4_confidence_intervals.pdf', bbox_inches='tight')
    print("Generated: figure_4_4_confidence_intervals.png/pdf")

def create_security_matrix_heatmap():
    """Create a security assessment matrix heatmap"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create matrix data
    categories = ['Prompt\nInjection', 'Output\nHandling', 'Over-\nreliance', 'SSRF', 'Model\nTheft', 'Insecure\nPlugin']
    metrics = ['Tests Run', 'Threats\nBlocked', 'Mitigation\nRate (%)', 'Confidence\nScore', 'Risk Level']
    
    # Data matrix
    data_matrix = [
        [73, 43, 58.9, 90, 2],  # LLM01
        [15, 10, 66.7, 90, 2],  # LLM06
        [15, 10, 66.7, 90, 2],  # LLM09
        [5, 0, 0, 0, 1],        # LLM05
        [3, 0, 0, 0, 1],        # LLM10
        [2, 0, 0, 0, 1]         # LLM07
    ]
    
    data_df = pd.DataFrame(data_matrix, index=categories, columns=metrics)
    
    # Create heatmap with custom colormap
    sns.heatmap(data_df, annot=True, fmt='.1f', cmap='RdYlGn', center=50,
                vmin=0, vmax=100, cbar_kws={'label': 'Scale (0-100)'})
    
    ax.set_title('Security Assessment Matrix by OWASP Category', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('')
    ax.set_ylabel('OWASP Category', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('figure_4_5_security_matrix.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_5_security_matrix.pdf', bbox_inches='tight')
    print("Generated: figure_4_5_security_matrix.png/pdf")

def create_summary_dashboard(data):
    """Create a comprehensive dashboard view"""
    fig = plt.figure(figsize=(16, 10))
    
    # Create grid
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Key Metrics (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    metrics_text = f"""KEY METRICS
    
Total Scenarios: 113
Threats Blocked: 63
Vulnerabilities: 0
Confidence: 90%
Compliance: 80.2%"""
    ax1.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.5))
    
    # 2. Mitigation by Category (top middle and right)
    ax2 = fig.add_subplot(gs[0, 1:])
    categories = []
    rates = []
    for cat, stats in data['statistical_analysis']['mitigation_metrics']['category_effectiveness'].items():
        if stats['total_tests'] > 10:  # Only show major categories
            categories.append(cat.replace('_PROMPT_INJECTION', '').replace('_', ' '))
            rates.append(stats['mitigation_rate'] * 100)
    
    bars = ax2.barh(categories, rates, color=['#2ecc71' if r > 60 else '#f39c12' for r in rates])
    ax2.set_xlabel('Mitigation Rate (%)')
    ax2.set_title('Primary Category Performance')
    ax2.set_xlim(0, 100)
    
    # 3. Compliance Scores (middle left)
    ax3 = fig.add_subplot(gs[1, 0])
    comp_labels = ['GAMP-5', '21 CFR\nPart 11', 'ALCOA+']
    comp_scores = [
        data['compliance_assessment']['gamp5']['overall_score'],
        data['compliance_assessment']['cfr_21_part_11']['overall_score'],
        data['compliance_assessment']['alcoa_plus']['overall_score']
    ]
    colors = ['green' if s >= 75 else 'orange' if s >= 60 else 'red' for s in comp_scores]
    ax3.bar(comp_labels, comp_scores, color=colors)
    ax3.set_ylabel('Score (%)')
    ax3.set_title('Compliance Assessment')
    ax3.set_ylim(0, 100)
    ax3.axhline(y=75, color='black', linestyle='--', alpha=0.3)
    
    # 4. Threat Detection (middle center)
    ax4 = fig.add_subplot(gs[1, 1])
    threat_data = data['statistical_analysis']['threat_detection']
    labels = ['Detected', 'Not Detected']
    sizes = [threat_data['total_threats_detected'], 
            113 - threat_data['total_threats_detected']]
    ax4.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#e74c3c', '#95a5a6'])
    ax4.set_title('Threat Detection Rate')
    
    # 5. Production Readiness (middle right)
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    findings = data['key_findings']
    readiness_text = f"""PRODUCTION STATUS
    
Security: {'READY' if findings['no_fallbacks_working'] else 'NOT READY'}
Compliance: {'READY' if findings['pharmaceutical_compliance'] else 'CONDITIONAL'}
Threat Detection: {'ACTIVE' if findings['real_threat_detection'] else 'INACTIVE'}

Overall: CONDITIONAL"""
    color = 'yellow' if findings['security_posture'] == 'NEEDS_IMPROVEMENT' else 'lightgreen'
    ax5.text(0.1, 0.5, readiness_text, fontsize=11, verticalalignment='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.5))
    
    # 6. Recommendations (bottom)
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis('off')
    recs = data['recommendations'][:3]  # Top 3 recommendations
    rec_text = "KEY RECOMMENDATIONS:\n\n"
    for i, rec in enumerate(recs, 1):
        rec_text += f"{i}. {rec}\n"
    ax6.text(0.05, 0.5, rec_text, fontsize=11, verticalalignment='center',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.3))
    
    fig.suptitle('OWASP Security Assessment Dashboard - Pharmaceutical Test Generation System', 
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('figure_4_6_security_dashboard.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure_4_6_security_dashboard.pdf', bbox_inches='tight')
    print("Generated: figure_4_6_security_dashboard.png/pdf")

def main():
    """Generate all visualizations for Chapter 4"""
    print("=" * 60)
    print("GENERATING CHAPTER 4 VISUALIZATIONS")
    print("OWASP Security Assessment - Thesis Graphics")
    print("=" * 60)
    
    # Load data
    print("\n[1] Loading analysis data...")
    data = load_analysis_data()
    
    # Generate visualizations
    print("\n[2] Generating visualizations...")
    
    print("   Creating mitigation effectiveness chart...")
    create_mitigation_effectiveness_chart(data)
    
    print("   Creating threat distribution pie charts...")
    create_threat_distribution_pie(data)
    
    print("   Creating compliance radar chart...")
    create_compliance_radar(data)
    
    print("   Creating confidence interval plot...")
    create_confidence_interval_plot(data)
    
    print("   Creating security matrix heatmap...")
    create_security_matrix_heatmap()
    
    print("   Creating summary dashboard...")
    create_summary_dashboard(data)
    
    print("\n[3] All visualizations generated successfully!")
    print("\nFiles created:")
    print("   - figure_4_1_mitigation_effectiveness.png/pdf")
    print("   - figure_4_2_threat_distribution.png/pdf")
    print("   - figure_4_3_compliance_radar.png/pdf")
    print("   - figure_4_4_confidence_intervals.png/pdf")
    print("   - figure_4_5_security_matrix.png/pdf")
    print("   - figure_4_6_security_dashboard.png/pdf")
    
    print("\n" + "=" * 60)
    print("VISUALIZATION GENERATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()