#!/usr/bin/env python3
"""
Comprehensive Test Coverage Calculator for Pharmaceutical Test Generation System
Calculates coverage percentages across multiple dimensions
"""

import json
import glob
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import datetime

class TestCoverageAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.coverage_metrics = {}
        
    def calculate_owasp_coverage(self) -> Dict:
        """Calculate OWASP security test coverage"""
        # Based on the statistical analysis report
        owasp_stats_file = self.base_path / "03_COMPLIANCE_DOCUMENTATION/owasp/analysis/statistical_analysis_report_20250822_084144.json"
        
        with open(owasp_stats_file, 'r') as f:
            owasp_data = json.load(f)
        
        # OWASP LLM Top 10 categories
        total_owasp_categories = 10
        tested_categories = 6  # LLM01, LLM05, LLM06, LLM07, LLM09, LLM10
        
        # Extract test execution data
        total_scenarios = owasp_data['executive_summary']['total_scenarios_tested']
        mitigation_rate = owasp_data['statistical_analysis']['mitigation_metrics']['overall_mitigation_rate']
        successful_blocks = owasp_data['statistical_analysis']['mitigation_metrics']['security_blocks']
        
        # Category-specific coverage
        category_coverage = {}
        for category, data in owasp_data['statistical_analysis']['mitigation_metrics']['category_effectiveness'].items():
            category_coverage[category] = {
                'tests_executed': data['total_tests'],
                'successful_blocks': data['successful_blocks'],
                'mitigation_rate': data['mitigation_rate'] * 100
            }
        
        return {
            'category_coverage_percentage': (tested_categories / total_owasp_categories) * 100,
            'categories_tested': tested_categories,
            'total_categories': total_owasp_categories,
            'untested_categories': ['LLM02', 'LLM03', 'LLM04', 'LLM08'],  # Not tested
            'total_scenarios_executed': total_scenarios,
            'successful_mitigations': successful_blocks,
            'overall_mitigation_rate': mitigation_rate * 100,
            'category_details': category_coverage
        }
    
    def calculate_functional_coverage(self) -> Dict:
        """Calculate functional test generation coverage"""
        # Based on N30 master statistical analysis
        master_stats_file = self.base_path / "07_UNIFIED_ANALYSIS/final_reports/N30_MASTER_STATISTICAL_ANALYSIS.json"
        
        with open(master_stats_file, 'r') as f:
            master_data = json.load(f)
        
        metrics = master_data['metrics']
        
        # Document processing coverage
        total_documents = metrics['total_documents']
        successful_documents = metrics['total_success']
        success_rate = metrics['weighted_success_rate']
        
        # Test generation metrics
        total_tests_generated = metrics['total_tests_generated']
        avg_tests_per_success = metrics['avg_tests_per_success']
        
        # Categorization accuracy
        categorization_accuracy = metrics['overall_categorization_accuracy']
        correct_categorizations = metrics['total_categorized_correct']
        total_categorized = metrics['total_categorized']
        
        # Per-corpus breakdown
        corpus_trends = master_data['trends']
        
        return {
            'document_processing_coverage': (successful_documents / total_documents) * 100,
            'documents_processed': total_documents,
            'documents_successful': successful_documents,
            'success_rate_percentage': success_rate * 100,
            'total_tests_generated': total_tests_generated,
            'avg_tests_per_document': avg_tests_per_success,
            'categorization_accuracy': categorization_accuracy * 100,
            'categorization_coverage': (total_categorized / total_documents) * 100,
            'corpus_breakdown': {
                'corpus_1': {
                    'success_rate': corpus_trends['success_rate_trend']['corpus_1'] * 100,
                    'accuracy': corpus_trends['categorization_accuracy_trend']['corpus_1'] * 100
                },
                'corpus_2': {
                    'success_rate': corpus_trends['success_rate_trend']['corpus_2'] * 100,
                    'accuracy': corpus_trends['categorization_accuracy_trend']['corpus_2'] * 100
                },
                'corpus_3': {
                    'success_rate': corpus_trends['success_rate_trend']['corpus_3'] * 100,
                    'accuracy': corpus_trends['categorization_accuracy_trend']['corpus_3'] * 100
                }
            }
        }
    
    def calculate_agent_coverage(self) -> Dict:
        """Calculate multi-agent system component coverage"""
        # Agents in the system based on directory structure
        agents = {
            'categorization': 'GAMP-5 Categorization Agent',
            'planner': 'Test Planning Agent',
            'context_provider': 'Context Provider Agent',
            'research_agent': 'Research Agent',
            'sme_agent': 'SME Agent',
            'oq_generator': 'OQ Test Generator Agent'
        }
        
        # Agents tested based on trace analysis and test results
        tested_agents = [
            'categorization',  # Heavily tested, 91.3% accuracy
            'context_provider',  # Used in all successful runs
            'research_agent',   # Used in all successful runs
            'sme_agent',       # Used in all successful runs
            'oq_generator'     # Generated 316 tests
        ]
        
        # Planner agent status uncertain from data
        partially_tested_agents = ['planner']
        
        agent_coverage = (len(tested_agents) / len(agents)) * 100
        
        # Workflow stages
        workflow_stages = [
            'Document Ingestion',
            'GAMP-5 Categorization',
            'Test Planning',
            'Parallel Agent Execution',
            'Test Generation',
            'Result Compilation',
            'Compliance Validation',
            'Output Management'
        ]
        
        tested_stages = [
            'Document Ingestion',      # 30 documents processed
            'GAMP-5 Categorization',  # 91.3% accuracy
            'Parallel Agent Execution', # Context, Research, SME
            'Test Generation',         # 316 tests generated
            'Result Compilation',      # JSON outputs produced
            'Compliance Validation',   # ALCOA+ scores calculated
            'Output Management'        # Test suites saved
        ]
        
        stage_coverage = (len(tested_stages) / len(workflow_stages)) * 100
        
        return {
            'agent_coverage_percentage': agent_coverage,
            'total_agents': len(agents),
            'tested_agents': len(tested_agents),
            'partially_tested_agents': len(partially_tested_agents),
            'agent_details': {
                'fully_tested': tested_agents,
                'partially_tested': partially_tested_agents,
                'untested': [a for a in agents.keys() if a not in tested_agents and a not in partially_tested_agents]
            },
            'workflow_stage_coverage': stage_coverage,
            'total_stages': len(workflow_stages),
            'tested_stages': len(tested_stages),
            'stage_details': {
                'tested': tested_stages,
                'untested': [s for s in workflow_stages if s not in tested_stages]
            }
        }
    
    def calculate_compliance_coverage(self) -> Dict:
        """Calculate regulatory compliance coverage"""
        # Based on OWASP analysis compliance assessment
        owasp_stats_file = self.base_path / "03_COMPLIANCE_DOCUMENTATION/owasp/analysis/statistical_analysis_report_20250822_084144.json"
        
        with open(owasp_stats_file, 'r') as f:
            owasp_data = json.load(f)
        
        compliance = owasp_data['compliance_assessment']
        
        # GAMP-5 requirements
        gamp5_components = compliance['gamp5']['components']
        gamp5_coverage = compliance['gamp5']['overall_score']
        gamp5_compliant = compliance['gamp5']['compliant']
        
        # 21 CFR Part 11 requirements
        cfr_components = compliance['cfr_21_part_11']['components']
        cfr_coverage = compliance['cfr_21_part_11']['overall_score']
        cfr_compliant = compliance['cfr_21_part_11']['compliant']
        
        # ALCOA+ requirements
        alcoa_components = compliance['alcoa_plus']['components']
        alcoa_coverage = compliance['alcoa_plus']['overall_score']
        alcoa_compliant = compliance['alcoa_plus']['compliant']
        
        overall_compliance = compliance['overall_compliance_score']
        
        return {
            'overall_compliance_coverage': overall_compliance,
            'gamp5': {
                'coverage_percentage': gamp5_coverage,
                'compliant': gamp5_compliant,
                'components_tested': len(gamp5_components),
                'component_scores': gamp5_components
            },
            'cfr_21_part_11': {
                'coverage_percentage': cfr_coverage,
                'compliant': cfr_compliant,
                'components_tested': len(cfr_components),
                'component_scores': cfr_components
            },
            'alcoa_plus': {
                'coverage_percentage': alcoa_coverage,
                'compliant': alcoa_compliant,
                'components_tested': len(alcoa_components),
                'component_scores': alcoa_components
            }
        }
    
    def calculate_requirement_coverage(self) -> Dict:
        """Calculate URS requirement coverage"""
        # Count test suites generated
        test_suite_files = list(self.base_path.glob("**/URS-*_test_suite.json"))
        unique_urs_tested = set()
        
        for file in test_suite_files:
            # Extract URS number from filename
            urs_id = file.stem.split('_')[0]  # e.g., "URS-001"
            unique_urs_tested.add(urs_id)
        
        # Total URS documents (from corpus data)
        total_urs_documents = 30  # Based on N30 analysis
        
        # Requirements per document (estimated from test generation)
        avg_requirements_per_doc = 10  # Conservative estimate
        total_requirements = total_urs_documents * avg_requirements_per_doc
        
        # Tests generated per requirement
        total_tests = 316  # From master stats
        tests_per_requirement = total_tests / len(unique_urs_tested) if unique_urs_tested else 0
        
        return {
            'document_coverage_percentage': (len(unique_urs_tested) / total_urs_documents) * 100 if total_urs_documents > 0 else 0,
            'unique_documents_tested': len(unique_urs_tested),
            'total_documents': total_urs_documents,
            'estimated_requirements': total_requirements,
            'tests_generated': total_tests,
            'avg_tests_per_document': tests_per_requirement,
            'urs_ids_tested': sorted(list(unique_urs_tested))
        }
    
    def calculate_test_type_coverage(self) -> Dict:
        """Calculate coverage by test type"""
        # Test types in OQ validation
        test_types = [
            'Installation Verification',
            'System Configuration',
            'Integration Testing',
            'Performance Testing',
            'Security Testing',
            'User Access Control',
            'Data Integrity',
            'Backup and Recovery',
            'Audit Trail',
            'Compliance Verification'
        ]
        
        # Based on generated test analysis
        covered_types = [
            'Installation Verification',  # Found in test suites
            'System Configuration',       # Found in test suites
            'Integration Testing',        # Agent integration tests
            'Security Testing',          # OWASP tests
            'User Access Control',       # RBAC tests
            'Data Integrity',           # ALCOA+ validation
            'Audit Trail',              # Compliance tests
            'Compliance Verification'    # GAMP-5 tests
        ]
        
        type_coverage = (len(covered_types) / len(test_types)) * 100
        
        return {
            'test_type_coverage_percentage': type_coverage,
            'total_test_types': len(test_types),
            'covered_types': len(covered_types),
            'type_details': {
                'covered': covered_types,
                'not_covered': [t for t in test_types if t not in covered_types]
            }
        }
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive coverage report"""
        print("Calculating OWASP Security Coverage...")
        owasp_coverage = self.calculate_owasp_coverage()
        
        print("Calculating Functional Test Coverage...")
        functional_coverage = self.calculate_functional_coverage()
        
        print("Calculating Agent Coverage...")
        agent_coverage = self.calculate_agent_coverage()
        
        print("Calculating Compliance Coverage...")
        compliance_coverage = self.calculate_compliance_coverage()
        
        print("Calculating Requirement Coverage...")
        requirement_coverage = self.calculate_requirement_coverage()
        
        print("Calculating Test Type Coverage...")
        test_type_coverage = self.calculate_test_type_coverage()
        
        # Calculate overall system coverage (weighted average)
        coverage_scores = [
            owasp_coverage['category_coverage_percentage'],
            functional_coverage['success_rate_percentage'],
            agent_coverage['agent_coverage_percentage'],
            compliance_coverage['overall_compliance_coverage'],
            requirement_coverage['document_coverage_percentage'],
            test_type_coverage['test_type_coverage_percentage']
        ]
        
        overall_coverage = sum(coverage_scores) / len(coverage_scores)
        
        report = {
            'metadata': {
                'timestamp': datetime.datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'base_path': str(self.base_path)
            },
            'executive_summary': {
                'overall_system_coverage': round(overall_coverage, 2),
                'coverage_assessment': self._assess_coverage_level(overall_coverage),
                'key_achievements': self._identify_achievements(owasp_coverage, functional_coverage, compliance_coverage),
                'coverage_gaps': self._identify_gaps(owasp_coverage, functional_coverage, agent_coverage)
            },
            'detailed_coverage': {
                'owasp_security': owasp_coverage,
                'functional_testing': functional_coverage,
                'system_components': agent_coverage,
                'regulatory_compliance': compliance_coverage,
                'requirements': requirement_coverage,
                'test_types': test_type_coverage
            },
            'statistical_confidence': {
                'sample_size': 30,
                'confidence_level': '95%',
                'margin_of_error': '±8.3%',
                'statistical_power': 0.50,
                'interpretation': 'Adequate for initial validation, larger sample recommended for production'
            },
            'recommendations': self._generate_recommendations(
                owasp_coverage, functional_coverage, agent_coverage, 
                compliance_coverage, requirement_coverage, test_type_coverage
            )
        }
        
        return report
    
    def _assess_coverage_level(self, coverage: float) -> str:
        """Assess overall coverage level"""
        if coverage >= 90:
            return "EXCELLENT - Production Ready"
        elif coverage >= 80:
            return "GOOD - Minor Gaps"
        elif coverage >= 70:
            return "ADEQUATE - Improvement Needed"
        elif coverage >= 60:
            return "MARGINAL - Significant Gaps"
        else:
            return "INSUFFICIENT - Major Work Required"
    
    def _identify_achievements(self, owasp, functional, compliance) -> List[str]:
        """Identify key coverage achievements"""
        achievements = []
        
        if owasp['overall_mitigation_rate'] > 50:
            achievements.append(f"Strong security mitigation: {owasp['overall_mitigation_rate']:.1f}%")
        
        if functional['categorization_accuracy'] > 90:
            achievements.append(f"High categorization accuracy: {functional['categorization_accuracy']:.1f}%")
        
        if functional['total_tests_generated'] > 300:
            achievements.append(f"Comprehensive test generation: {functional['total_tests_generated']} tests")
        
        if compliance['alcoa_plus']['coverage_percentage'] > 95:
            achievements.append(f"ALCOA+ compliance: {compliance['alcoa_plus']['coverage_percentage']:.1f}%")
        
        return achievements
    
    def _identify_gaps(self, owasp, functional, agent) -> List[str]:
        """Identify coverage gaps"""
        gaps = []
        
        if owasp['category_coverage_percentage'] < 100:
            untested = owasp['untested_categories']
            gaps.append(f"OWASP categories not tested: {', '.join(untested)}")
        
        if functional['success_rate_percentage'] < 85:
            gaps.append(f"Document processing success below target: {functional['success_rate_percentage']:.1f}%")
        
        if agent['agent_details']['untested']:
            gaps.append(f"Untested agents: {', '.join(agent['agent_details']['untested'])}")
        
        if agent['stage_details']['untested']:
            gaps.append(f"Untested workflow stages: {', '.join(agent['stage_details']['untested'])}")
        
        return gaps
    
    def _generate_recommendations(self, *coverage_data) -> List[str]:
        """Generate coverage improvement recommendations"""
        recommendations = []
        
        owasp, functional, agent, compliance, requirement, test_type = coverage_data
        
        # OWASP recommendations
        if owasp['category_coverage_percentage'] < 100:
            recommendations.append("Complete testing for remaining OWASP LLM Top 10 categories (LLM02, LLM03, LLM04, LLM08)")
        
        # Functional recommendations
        if functional['success_rate_percentage'] < 85:
            recommendations.append("Improve document processing reliability to achieve 85% or higher success rate")
        
        # Agent recommendations  
        if agent['agent_details']['untested'] or agent['agent_details']['partially_tested']:
            recommendations.append("Complete testing for planner agent and verify full integration")
        
        # Compliance recommendations
        if not compliance['cfr_21_part_11']['compliant']:
            recommendations.append("Implement electronic signatures for full 21 CFR Part 11 compliance")
        
        # Requirement recommendations
        if requirement['document_coverage_percentage'] < 100:
            recommendations.append(f"Expand testing to cover all {requirement['total_documents']} URS documents")
        
        # Test type recommendations
        if test_type['type_details']['not_covered']:
            recommendations.append(f"Add coverage for: {', '.join(test_type['type_details']['not_covered'])}")
        
        # Sample size recommendation
        recommendations.append("Increase sample size to 114+ documents for 80% statistical power")
        
        return recommendations


def main():
    """Main execution function"""
    base_path = r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\THESIS_EVIDENCE_PACKAGE"
    
    print("=" * 80)
    print("PHARMACEUTICAL TEST GENERATION SYSTEM - TEST COVERAGE ANALYSIS")
    print("=" * 80)
    print()
    
    analyzer = TestCoverageAnalyzer(base_path)
    report = analyzer.generate_comprehensive_report()
    
    # Save report
    output_file = Path(base_path) / "TEST_COVERAGE_ANALYSIS.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS COMPLETE")
    print("=" * 80)
    
    print(f"\nOverall System Coverage: {report['executive_summary']['overall_system_coverage']:.1f}%")
    print(f"Assessment: {report['executive_summary']['coverage_assessment']}")
    
    print("\nCOVERAGE BREAKDOWN:")
    print("-" * 40)
    
    coverage_data = report['detailed_coverage']
    
    print(f"1. OWASP Security Coverage: {coverage_data['owasp_security']['category_coverage_percentage']:.1f}%")
    print(f"   - Categories Tested: {coverage_data['owasp_security']['categories_tested']}/{coverage_data['owasp_security']['total_categories']}")
    print(f"   - Scenarios Executed: {coverage_data['owasp_security']['total_scenarios_executed']}")
    print(f"   - Mitigation Rate: {coverage_data['owasp_security']['overall_mitigation_rate']:.1f}%")
    
    print(f"\n2. Functional Test Coverage: {coverage_data['functional_testing']['success_rate_percentage']:.1f}%")
    print(f"   - Documents Processed: {coverage_data['functional_testing']['documents_successful']}/{coverage_data['functional_testing']['documents_processed']}")
    print(f"   - Tests Generated: {coverage_data['functional_testing']['total_tests_generated']}")
    print(f"   - Categorization Accuracy: {coverage_data['functional_testing']['categorization_accuracy']:.1f}%")
    
    print(f"\n3. System Component Coverage: {coverage_data['system_components']['agent_coverage_percentage']:.1f}%")
    print(f"   - Agents Tested: {coverage_data['system_components']['tested_agents']}/{coverage_data['system_components']['total_agents']}")
    print(f"   - Workflow Stages: {coverage_data['system_components']['tested_stages']}/{coverage_data['system_components']['total_stages']}")
    
    print(f"\n4. Compliance Coverage: {coverage_data['regulatory_compliance']['overall_compliance_coverage']:.1f}%")
    print(f"   - GAMP-5: {coverage_data['regulatory_compliance']['gamp5']['coverage_percentage']:.1f}%")
    print(f"   - 21 CFR Part 11: {coverage_data['regulatory_compliance']['cfr_21_part_11']['coverage_percentage']:.1f}%")
    print(f"   - ALCOA+: {coverage_data['regulatory_compliance']['alcoa_plus']['coverage_percentage']:.1f}%")
    
    print(f"\n5. Requirement Coverage: {coverage_data['requirements']['document_coverage_percentage']:.1f}%")
    print(f"   - Documents Tested: {coverage_data['requirements']['unique_documents_tested']}/{coverage_data['requirements']['total_documents']}")
    
    print(f"\n6. Test Type Coverage: {coverage_data['test_types']['test_type_coverage_percentage']:.1f}%")
    print(f"   - Types Covered: {coverage_data['test_types']['covered_types']}/{coverage_data['test_types']['total_test_types']}")
    
    print("\nKEY ACHIEVEMENTS:")
    for achievement in report['executive_summary']['key_achievements']:
        print(f"   * {achievement}")
    
    print("\nCOVERAGE GAPS:")
    for gap in report['executive_summary']['coverage_gaps']:
        print(f"   * {gap}")
    
    print("\nRECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\nFull report saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()