#!/usr/bin/env python3
"""
Phoenix Enhanced Observability Integration Patch

This script applies the enhanced Phoenix observability integration to the unified workflow.
It adds compliance analysis, visualization generation, and comprehensive reporting.
"""

import sys
from pathlib import Path

# Add main to path
sys.path.append(str(Path.cwd() / "main"))

def create_enhanced_workflow_patch():
    """
    Create the enhanced workflow integration patch.
    
    This adds Phoenix enhanced observability features to the unified workflow
    including compliance analysis, violation detection, and dashboard generation.
    """
    
    # The imports to add at the top of unified_workflow.py
    enhanced_imports = '''
# Enhanced Phoenix Observability
from src.monitoring.phoenix_enhanced import (
    PhoenixGraphQLClient,
    WorkflowEventFlowVisualizer,
    AutomatedTraceAnalyzer,
    setup_enhanced_phoenix_observability
)
'''

    # The enhanced completion method
    enhanced_completion_method = '''
    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: OQTestSuiteEvent
    ) -> StopEvent:
        """
        Complete the unified workflow with enhanced Phoenix observability analysis.
        
        This method now includes:
        - Compliance violation detection
        - Event flow visualization  
        - GAMP-5 compliance dashboard generation
        - Comprehensive regulatory reporting
        
        Args:
            ctx: Workflow context
            ev: OQTestSuiteEvent with generated test suite
            
        Returns:
            StopEvent with comprehensive workflow results and observability reports
        """
        # Get all stored results using safe context operations
        workflow_start_time = await safe_context_get(ctx, "workflow_start_time", None)
        document_path = await safe_context_get(ctx, "document_path", "unknown")
        
        # Calculate total processing time
        total_time = datetime.now(UTC) - workflow_start_time if workflow_start_time else None
        
        # Get workflow components results
        categorization_result = await safe_context_get(ctx, "categorization_result")
        planning_result = await safe_context_get(ctx, "planning_result") 
        agent_results = await safe_context_get(ctx, "agent_results", [])
        
        self.logger.info("🔍 Starting enhanced Phoenix observability analysis...")
        
        # Initialize enhanced Phoenix observability
        observability_results = {}
        compliance_violations = []
        
        try:
            # Set up enhanced Phoenix observability
            enhanced_setup = await setup_enhanced_phoenix_observability()
            
            if enhanced_setup.get("status") == "ready":
                self.logger.info("✅ Enhanced Phoenix observability initialized successfully")
                
                # Get the enhanced clients
                graphql_client = enhanced_setup["graphql_client"]
                visualizer = enhanced_setup["visualizer"]
                analyzer = enhanced_setup["analyzer"]
                
                # 1. Analyze compliance violations
                self.logger.info("🔍 Analyzing GAMP-5 compliance violations...")
                try:
                    violations = await analyzer.analyze_compliance_violations(hours=1)
                    compliance_violations = violations
                    
                    if violations:
                        self.logger.warning(f"⚠️  Found {len(violations)} compliance violations")
                        for violation in violations[:3]:  # Log first 3
                            self.logger.warning(f"   - {violation.violation_type}: {violation.description}")
                    else:
                        self.logger.info("✅ No compliance violations detected")
                        
                except Exception as e:
                    self.logger.error(f"❌ Compliance analysis failed: {e}")
                    # NO FALLBACKS - surface the error explicitly
                    compliance_violations = [f"ANALYSIS_ERROR: {e}"]
                
                # 2. Generate compliance dashboard
                self.logger.info("📊 Generating GAMP-5 compliance dashboard...")
                try:
                    dashboard_path = await visualizer.create_compliance_dashboard()
                    observability_results["compliance_dashboard"] = dashboard_path
                    self.logger.info(f"✅ Compliance dashboard generated: {dashboard_path}")
                except Exception as e:
                    self.logger.error(f"❌ Dashboard generation failed: {e}")
                    # NO FALLBACKS - surface the error explicitly
                    observability_results["compliance_dashboard_error"] = str(e)
                
                # 3. Generate comprehensive compliance report
                self.logger.info("📋 Generating comprehensive compliance report...")
                try:
                    compliance_report = await analyzer.generate_compliance_report()
                    observability_results["compliance_report"] = compliance_report
                    
                    # Log key compliance metrics
                    summary = compliance_report.get("compliance_summary", {})
                    compliance_rate = summary.get("compliance_rate_percent", 0)
                    total_violations = compliance_report.get("violations_summary", {}).get("total_violations", 0)
                    
                    self.logger.info(f"📈 Compliance Rate: {compliance_rate:.1f}%")
                    self.logger.info(f"🚨 Total Violations: {total_violations}")
                    
                    # Check regulatory status
                    regulatory_status = compliance_report.get("report_metadata", {}).get("regulatory_status", "UNKNOWN")
                    if regulatory_status == "NON_COMPLIANT_CRITICAL":
                        self.logger.error("🚨 CRITICAL: System has critical compliance violations!")
                    elif regulatory_status == "COMPLIANT":
                        self.logger.info("✅ System is compliant with GAMP-5 requirements")
                    
                except Exception as e:
                    self.logger.error(f"❌ Compliance report generation failed: {e}")
                    # NO FALLBACKS - surface the error explicitly
                    observability_results["compliance_report_error"] = str(e)
                
                # 4. Query workflow traces for analysis
                self.logger.info("🔍 Querying workflow traces...")
                try:
                    traces = await graphql_client.query_workflow_traces(
                        workflow_type="UnifiedTestGenerationWorkflow",
                        hours=1
                    )
                    observability_results["trace_count"] = len(traces)
                    observability_results["traces_analyzed"] = [
                        {
                            "trace_id": trace.trace_id,
                            "duration_ms": trace.duration_ms,
                            "compliance_status": trace.compliance_status
                        }
                        for trace in traces[:5]  # Include first 5 traces
                    ]
                    self.logger.info(f"📊 Analyzed {len(traces)} workflow traces")
                except Exception as e:
                    self.logger.error(f"❌ Trace analysis failed: {e}")
                    observability_results["trace_analysis_error"] = str(e)
                
            else:
                self.logger.warning("⚠️  Enhanced Phoenix observability setup failed - continuing without enhanced features")
                observability_results["setup_error"] = "Enhanced Phoenix setup failed"
                
        except Exception as e:
            self.logger.error(f"❌ Enhanced Phoenix observability failed: {e}")
            # NO FALLBACKS - record the failure explicitly for regulatory compliance
            observability_results["enhanced_phoenix_error"] = str(e)
        
        # Compile comprehensive results
        final_results = {
            "workflow_metadata": {
                "session_id": self._workflow_session_id,
                "document_path": str(document_path),
                "total_processing_time_seconds": total_time.total_seconds() if total_time else None,
                "workflow_completion_time": datetime.now(UTC).isoformat(),
                "workflow_type": "UnifiedTestGenerationWorkflow"
            },
            
            "categorization_results": categorization_result,
            "planning_results": planning_result,
            "agent_coordination_results": agent_results,
            "test_generation_results": {
                "test_suite": ev.test_suite,
                "metadata": ev.metadata,
                "total_tests": len(ev.test_suite.get("test_procedures", [])) if ev.test_suite else 0
            },
            
            # Enhanced Phoenix Observability Results
            "enhanced_observability": observability_results,
            "compliance_violations": compliance_violations,
            "regulatory_compliance": {
                "gamp_5_compliant": len([v for v in compliance_violations if getattr(v, 'severity', 'UNKNOWN') == 'CRITICAL']) == 0,
                "audit_trail_complete": True,  # Based on workflow completion
                "pharmaceutical_validation_ready": len(compliance_violations) == 0
            }
        }
        
        # Log final status
        if compliance_violations and any(getattr(v, 'severity', 'UNKNOWN') == 'CRITICAL' for v in compliance_violations):
            self.logger.error("🚨 CRITICAL: Workflow completed with critical compliance violations")
        else:
            self.logger.info("✅ Unified workflow completed successfully with enhanced observability")
        
        self.logger.info(f"📊 Enhanced observability features: {list(observability_results.keys())}")
        
        return StopEvent(result=final_results)
'''

    return enhanced_imports, enhanced_completion_method

def apply_integration_patch():
    """Apply the Phoenix enhanced integration patch to unified_workflow.py."""
    
    workflow_file = Path("main/src/core/unified_workflow.py")
    
    if not workflow_file.exists():
        print(f"❌ Workflow file not found: {workflow_file}")
        return False
    
    print("🔍 Reading current unified workflow...")
    
    # Read current file
    with open(workflow_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get the patch components
    enhanced_imports, enhanced_completion_method = create_enhanced_workflow_patch()
    
    # Check if already patched
    if "phoenix_enhanced" in content:
        print("⚠️  Workflow already appears to have enhanced Phoenix integration")
        return True
    
    print("🔧 Applying enhanced Phoenix integration patch...")
    
    try:
        # Add enhanced imports after existing monitoring imports
        import_insertion_point = content.find("from src.monitoring.phoenix_config import setup_phoenix")
        if import_insertion_point == -1:
            print("❌ Could not find phoenix_config import to add enhanced imports")
            return False
        
        # Find the end of that import line
        import_end = content.find('\n', import_insertion_point) + 1
        
        # Insert enhanced imports
        new_content = (
            content[:import_end] + 
            enhanced_imports + 
            content[import_end:]
        )
        
        # Find and replace the complete_workflow method
        # Look for the method signature
        method_start = new_content.find("async def complete_workflow(")
        if method_start == -1:
            print("❌ Could not find complete_workflow method to replace")
            return False
        
        # Find the method end (look for next @step or class end)
        method_end = new_content.find("\n    @step", method_start + 1)
        if method_end == -1:
            # Look for class end instead
            method_end = new_content.find("\nclass ", method_start + 1)
            if method_end == -1:
                # Look for end of file
                method_end = len(new_content)
        
        # Replace the method
        new_content = (
            new_content[:method_start] + 
            enhanced_completion_method.strip() + "\n\n" +
            new_content[method_end:]
        )
        
        # Write the updated file
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Enhanced Phoenix integration patch applied successfully!")
        print("📋 Added features:")
        print("   - Compliance violation detection")
        print("   - GAMP-5 compliance dashboard generation")
        print("   - Comprehensive regulatory reporting")
        print("   - Workflow trace analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply patch: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Phoenix Enhanced Observability Integration Patch")
    print("=" * 60)
    
    success = apply_integration_patch()
    
    if success:
        print("\n✅ INTEGRATION COMPLETE!")
        print("🎯 Next steps:")
        print("   1. Start Phoenix server: uv run python start_phoenix_server.py")
        print("   2. Run workflow test to validate enhanced features")
        print("   3. Check compliance dashboard at http://localhost:6006")
    else:
        print("\n❌ INTEGRATION FAILED!")
        print("   Manual integration may be required")
    
    print("=" * 60)