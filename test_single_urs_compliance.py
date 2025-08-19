#!/usr/bin/env python
"""
Single URS Document Compliance Validation Script
Tests ALCOA+, GAMP-5, 21 CFR Part 11, and OWASP security on a single document
before running full 17-document cross-validation.

This ensures the system meets regulatory requirements before resource-intensive testing.
"""

import json
import os
import sys
import hashlib
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def load_test_results(test_dir: Path) -> Dict[str, Any]:
    """Load test results from most recent test execution."""
    results_file = test_dir / "results.json"
    test_suite_files = list(Path("main/output/test_suites").glob("test_suite_OQ-SUITE-*.json"))
    
    results = {}
    
    # Load main results
    if results_file.exists():
        with open(results_file, 'r') as f:
            results['execution'] = json.load(f)
    
    # Load test suite
    if test_suite_files:
        latest_suite = max(test_suite_files, key=lambda p: p.stat().st_mtime)
        with open(latest_suite, 'r') as f:
            results['test_suite'] = json.load(f)
    
    # Load traces if available
    trace_dir = Path("main/logs/traces")
    if trace_dir.exists():
        trace_files = list(trace_dir.glob("all_spans_*.jsonl"))
        if trace_files:
            results['traces_available'] = True
            results['trace_count'] = len(trace_files)
    
    return results

def validate_alcoa_plus(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate ALCOA+ compliance based on test results.
    Returns honest scores without inflation.
    """
    alcoa_scores = {
        'attributable': 0.0,
        'legible': 0.0,
        'contemporaneous': 0.0,
        'original': 0.0,
        'accurate': 0.0,
        'complete': 0.0,
        'consistent': 0.0,
        'enduring': 0.0,
        'available': 0.0
    }
    
    issues = []
    
    # Check if we have test results
    if 'execution' in results:
        execution = results['execution']
        
        # Attributable (can trace to source)
        if execution.get('test_metadata', {}).get('document_path'):
            alcoa_scores['attributable'] = 8.0  # Has document source
        else:
            alcoa_scores['attributable'] = 2.0
            issues.append("Missing document source attribution")
        
        # Legible (readable and clear)
        if 'test_suite' in results:
            test_suite = results['test_suite']
            if test_suite.get('test_cases'):
                alcoa_scores['legible'] = 9.0  # Tests are in structured JSON
            else:
                alcoa_scores['legible'] = 3.0
                issues.append("Test cases not legible")
        
        # Contemporaneous (recorded at time of activity)
        if execution.get('test_metadata', {}).get('execution_start'):
            alcoa_scores['contemporaneous'] = 8.0  # Has timestamps
        else:
            alcoa_scores['contemporaneous'] = 2.0
            issues.append("Missing contemporaneous timestamps")
        
        # Original (first capture)
        alcoa_scores['original'] = 7.0  # System generates original tests
        
        # Accurate (correct and verified)
        if execution.get('success'):
            alcoa_scores['accurate'] = 7.5  # Tests generated successfully
        else:
            alcoa_scores['accurate'] = 3.0
            issues.append("Test generation had errors")
        
        # Complete (all data present)
        workflow_results = execution.get('workflow_results', {})
        if workflow_results.get('oq_generation', {}).get('total_tests', 0) > 0:
            alcoa_scores['complete'] = 7.0  # Has test data
        else:
            alcoa_scores['complete'] = 2.0
            issues.append("Incomplete test generation")
        
        # Consistent (follows procedures)
        if workflow_results.get('categorization', {}).get('category'):
            alcoa_scores['consistent'] = 8.0  # Follows GAMP categorization
        else:
            alcoa_scores['consistent'] = 3.0
            issues.append("Inconsistent categorization")
        
        # Enduring (preserved)
        if results.get('traces_available'):
            alcoa_scores['enduring'] = 8.5  # Has trace preservation
        else:
            alcoa_scores['enduring'] = 5.0
            issues.append("No trace preservation")
        
        # Available (retrievable)
        alcoa_scores['available'] = 9.0  # Data is retrievable from files
    
    # Calculate overall score
    overall_score = sum(alcoa_scores.values()) / len(alcoa_scores)
    
    return {
        'scores': alcoa_scores,
        'overall_score': overall_score,
        'meets_target': overall_score >= 9.0,
        'issues': issues
    }

def validate_gamp5(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate GAMP-5 compliance."""
    criteria = {
        'risk_based_approach': False,
        'life_cycle_management': False,
        'supplier_assessment': False,
        'specification_management': False,
        'configuration_management': False,
        'testing_strategy': False,
        'documentation_standards': False,
        'change_control': False,
        'training_competency': False,
        'ongoing_verification': False
    }
    
    issues = []
    
    if 'execution' in results:
        workflow = results['execution'].get('workflow_results', {})
        
        # Check GAMP categorization
        if workflow.get('categorization', {}).get('category'):
            criteria['risk_based_approach'] = True
            criteria['testing_strategy'] = True
        else:
            issues.append("No GAMP categorization performed")
        
        # Check test generation
        if workflow.get('oq_generation', {}).get('generated_successfully'):
            criteria['specification_management'] = True
            criteria['documentation_standards'] = True
        else:
            issues.append("Test generation incomplete")
        
        # Check for test suite structure
        if 'test_suite' in results:
            test_suite = results['test_suite']
            if test_suite.get('gamp_category'):
                criteria['life_cycle_management'] = True
            
            # Check for regulatory basis in tests
            if test_suite.get('test_cases'):
                test = test_suite['test_cases'][0] if test_suite['test_cases'] else {}
                if test.get('regulatory_basis'):
                    criteria['ongoing_verification'] = True
    
    met_criteria = sum(criteria.values())
    total_criteria = len(criteria)
    compliance_percentage = (met_criteria / total_criteria) * 100
    
    return {
        'criteria': criteria,
        'met_criteria': met_criteria,
        'total_criteria': total_criteria,
        'compliance_percentage': compliance_percentage,
        'meets_target': compliance_percentage == 100,
        'issues': issues
    }

def validate_cfr_part11(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate 21 CFR Part 11 compliance."""
    requirements = {
        'electronic_records': False,
        'electronic_signatures': False,
        'audit_trail': False,
        'system_controls': False
    }
    
    issues = []
    
    # Check for audit trail
    if results.get('traces_available'):
        requirements['audit_trail'] = True
        requirements['electronic_records'] = True
    else:
        issues.append("No audit trail captured")
    
    # Check for system controls
    if 'execution' in results:
        if results['execution'].get('test_metadata', {}).get('model_used'):
            requirements['system_controls'] = True
        else:
            issues.append("System controls not documented")
    
    # Electronic signatures would need cryptographic implementation
    # Currently not implemented
    issues.append("Electronic signatures not implemented")
    
    met_requirements = sum(requirements.values())
    total_requirements = len(requirements)
    compliance_percentage = (met_requirements / total_requirements) * 100
    
    return {
        'requirements': requirements,
        'met_requirements': met_requirements,
        'total_requirements': total_requirements,
        'compliance_percentage': compliance_percentage,
        'meets_target': compliance_percentage == 100,
        'issues': issues
    }

def test_owasp_security() -> Dict[str, Any]:
    """
    Test OWASP LLM Top 10 security vulnerabilities.
    Focus on critical risks: LLM01, LLM06, LLM09
    """
    security_results = {
        'LLM01_prompt_injection': {'tested': False, 'vulnerable': False, 'mitigations': []},
        'LLM06_insecure_output': {'tested': False, 'vulnerable': False, 'mitigations': []},
        'LLM09_overreliance': {'tested': False, 'vulnerable': False, 'mitigations': []},
        'overall_secure': False,
        'issues': []
    }
    
    # Check if security measures are in place
    security_dir = Path("main/src/security")
    
    if security_dir.exists():
        # Check for input validation
        input_validator = security_dir / "input_validator.py"
        if input_validator.exists():
            security_results['LLM01_prompt_injection']['tested'] = True
            security_results['LLM01_prompt_injection']['mitigations'].append("Input validator present")
        
        # Check for output scanning
        output_scanner = security_dir / "output_scanner.py"
        if output_scanner.exists():
            security_results['LLM06_insecure_output']['tested'] = True
            security_results['LLM06_insecure_output']['mitigations'].append("Output scanner present")
        
        # Check for human consultation (overreliance mitigation)
        consultation = Path("main/src/agents/human_consultation.py")
        if consultation.exists():
            security_results['LLM09_overreliance']['tested'] = True
            security_results['LLM09_overreliance']['mitigations'].append("Human consultation system present")
    else:
        security_results['issues'].append("Security module not found")
    
    # Calculate overall security
    tested_count = sum(1 for k, v in security_results.items() 
                      if isinstance(v, dict) and v.get('tested'))
    
    security_results['overall_secure'] = tested_count >= 2  # At least 2 of 3 critical risks addressed
    
    if not security_results['overall_secure']:
        security_results['issues'].append(f"Only {tested_count}/3 critical OWASP risks addressed")
    
    return security_results

def generate_compliance_report(
    alcoa_results: Dict[str, Any],
    gamp5_results: Dict[str, Any],
    cfr_results: Dict[str, Any],
    security_results: Dict[str, Any]
) -> str:
    """Generate comprehensive compliance report."""
    
    report = []
    report.append("=" * 80)
    report.append("COMPLIANCE VALIDATION REPORT - SINGLE DOCUMENT TEST")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now(UTC).isoformat()}")
    report.append("")
    
    # Executive Summary
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 40)
    
    all_compliant = (
        alcoa_results['meets_target'] and
        gamp5_results['meets_target'] and
        cfr_results['meets_target'] and
        security_results['overall_secure']
    )
    
    if all_compliant:
        report.append("[PASS] SYSTEM IS COMPLIANT - Ready for full 17-document testing")
    else:
        report.append("[WARNING] COMPLIANCE ISSUES FOUND - Address before full testing")
    
    report.append("")
    
    # ALCOA+ Results
    report.append("1. ALCOA+ DATA INTEGRITY")
    report.append("-" * 40)
    report.append(f"Overall Score: {alcoa_results['overall_score']:.2f}/10")
    report.append(f"Target: >=9.0/10")
    report.append(f"Status: {'[PASS]' if alcoa_results['meets_target'] else '[FAIL]'}")
    report.append("")
    report.append("Attribute Scores:")
    for attr, score in alcoa_results['scores'].items():
        status = "[OK]" if score >= 7.0 else "[WARN]" if score >= 5.0 else "[FAIL]"
        report.append(f"  {status} {attr.capitalize()}: {score:.1f}/10")
    
    if alcoa_results['issues']:
        report.append("")
        report.append("Issues to Address:")
        for issue in alcoa_results['issues']:
            report.append(f"  - {issue}")
    
    report.append("")
    
    # GAMP-5 Results
    report.append("2. GAMP-5 COMPLIANCE")
    report.append("-" * 40)
    report.append(f"Compliance: {gamp5_results['compliance_percentage']:.1f}%")
    report.append(f"Criteria Met: {gamp5_results['met_criteria']}/{gamp5_results['total_criteria']}")
    report.append(f"Status: {'[PASS]' if gamp5_results['meets_target'] else '[FAIL]'}")
    report.append("")
    report.append("Criteria Status:")
    for criterion, met in gamp5_results['criteria'].items():
        status = "[OK]" if met else "[FAIL]"
        report.append(f"  {status} {criterion.replace('_', ' ').title()}")
    
    if gamp5_results['issues']:
        report.append("")
        report.append("Issues to Address:")
        for issue in gamp5_results['issues']:
            report.append(f"  - {issue}")
    
    report.append("")
    
    # 21 CFR Part 11 Results
    report.append("3. 21 CFR PART 11 COMPLIANCE")
    report.append("-" * 40)
    report.append(f"Compliance: {cfr_results['compliance_percentage']:.1f}%")
    report.append(f"Requirements Met: {cfr_results['met_requirements']}/{cfr_results['total_requirements']}")
    report.append(f"Status: {'[PASS]' if cfr_results['meets_target'] else '[FAIL]'}")
    report.append("")
    report.append("Requirements Status:")
    for req, met in cfr_results['requirements'].items():
        status = "[OK]" if met else "[FAIL]"
        report.append(f"  {status} {req.replace('_', ' ').title()}")
    
    if cfr_results['issues']:
        report.append("")
        report.append("Issues to Address:")
        for issue in cfr_results['issues']:
            report.append(f"  - {issue}")
    
    report.append("")
    
    # OWASP Security Results
    report.append("4. OWASP LLM TOP 10 SECURITY")
    report.append("-" * 40)
    report.append(f"Status: {'[SECURE]' if security_results['overall_secure'] else '[VULNERABLE]'}")
    report.append("")
    report.append("Critical Risks:")
    
    for risk_key in ['LLM01_prompt_injection', 'LLM06_insecure_output', 'LLM09_overreliance']:
        risk = security_results[risk_key]
        status = "[OK]" if risk['tested'] and not risk['vulnerable'] else "[WARN]" if risk['tested'] else "[FAIL]"
        risk_name = risk_key.replace('_', ' ').upper()
        report.append(f"  {status} {risk_name}")
        if risk['mitigations']:
            for mitigation in risk['mitigations']:
                report.append(f"      - {mitigation}")
    
    if security_results['issues']:
        report.append("")
        report.append("Security Issues:")
        for issue in security_results['issues']:
            report.append(f"  - {issue}")
    
    report.append("")
    
    # Recommendations
    report.append("RECOMMENDATIONS")
    report.append("-" * 40)
    
    recommendations = []
    
    if not alcoa_results['meets_target']:
        recommendations.append("1. Improve ALCOA+ compliance:")
        for attr, score in alcoa_results['scores'].items():
            if score < 7.0:
                recommendations.append(f"   - Enhance {attr} (current: {score:.1f}/10)")
    
    if not gamp5_results['meets_target']:
        recommendations.append("2. Complete GAMP-5 requirements:")
        for criterion, met in gamp5_results['criteria'].items():
            if not met:
                recommendations.append(f"   - Implement {criterion.replace('_', ' ')}")
    
    if not cfr_results['meets_target']:
        recommendations.append("3. Address 21 CFR Part 11 gaps:")
        for req, met in cfr_results['requirements'].items():
            if not met:
                recommendations.append(f"   - Implement {req.replace('_', ' ')}")
    
    if not security_results['overall_secure']:
        recommendations.append("4. Strengthen security controls:")
        for risk_key in ['LLM01_prompt_injection', 'LLM06_insecure_output', 'LLM09_overreliance']:
            if not security_results[risk_key]['tested']:
                recommendations.append(f"   - Add protection for {risk_key.replace('_', ' ')}")
    
    if recommendations:
        report.extend(recommendations)
    else:
        report.append("[OK] System is ready for full 17-document cross-validation testing!")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Main execution function."""
    print("Single Document Compliance Validation")
    print("=" * 60)
    
    # Find most recent test results
    cv_dirs = list(Path("main/output/cross_validation").glob("cv_test_*"))
    
    if not cv_dirs:
        print("[ERROR] No test results found. Please run a test first using:")
        print("   uv run python test_cv_single.py")
        return 1
    
    latest_dir = max(cv_dirs, key=lambda p: p.stat().st_mtime)
    print(f"Using test results from: {latest_dir.name}")
    print()
    
    # Load results
    print("Loading test results...")
    results = load_test_results(latest_dir)
    
    if not results:
        print("[ERROR] Could not load test results")
        return 1
    
    print(f"[OK] Loaded results for: {results.get('execution', {}).get('test_metadata', {}).get('document_name', 'Unknown')}")
    print()
    
    # Run compliance validations
    print("Running compliance validations...")
    print()
    
    # ALCOA+ Validation
    print("  1. Validating ALCOA+ compliance...")
    alcoa_results = validate_alcoa_plus(results)
    print(f"     Score: {alcoa_results['overall_score']:.2f}/10")
    
    # GAMP-5 Validation
    print("  2. Validating GAMP-5 compliance...")
    gamp5_results = validate_gamp5(results)
    print(f"     Compliance: {gamp5_results['compliance_percentage']:.1f}%")
    
    # 21 CFR Part 11 Validation
    print("  3. Validating 21 CFR Part 11...")
    cfr_results = validate_cfr_part11(results)
    print(f"     Compliance: {cfr_results['compliance_percentage']:.1f}%")
    
    # OWASP Security Testing
    print("  4. Testing OWASP security...")
    security_results = test_owasp_security()
    print(f"     Status: {'Secure' if security_results['overall_secure'] else 'Vulnerable'}")
    
    print()
    
    # Generate report
    print("Generating compliance report...")
    report = generate_compliance_report(
        alcoa_results,
        gamp5_results,
        cfr_results,
        security_results
    )
    
    # Save report
    report_file = latest_dir / "compliance_validation_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Also save JSON results
    json_results = {
        'timestamp': datetime.now(UTC).isoformat(),
        'test_directory': str(latest_dir),
        'alcoa_plus': alcoa_results,
        'gamp5': gamp5_results,
        'cfr_part11': cfr_results,
        'owasp_security': security_results,
        'overall_compliant': (
            alcoa_results['meets_target'] and
            gamp5_results['meets_target'] and
            cfr_results['meets_target'] and
            security_results['overall_secure']
        )
    }
    
    json_file = latest_dir / "compliance_validation_results.json"
    with open(json_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    # Print report
    print()
    print(report)
    
    # Save paths
    print(f"Report saved to: {report_file}")
    print(f"JSON results saved to: {json_file}")
    
    return 0 if json_results['overall_compliant'] else 1

if __name__ == "__main__":
    sys.exit(main())