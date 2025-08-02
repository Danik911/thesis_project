#!/usr/bin/env python
"""
Master Phoenix Observability Fix Script

This script orchestrates all Phoenix fixes in the correct order:
1. Environment and dependency fixes
2. GraphQL API repairs
3. Comprehensive diagnostic testing
4. End-to-end validation

This is the single entry point to fix all Phoenix observability issues.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterPhoenixFixer:
    """Master Phoenix observability fix orchestrator."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "fix_session_id": f"phoenix_fix_{int(time.time())}",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "phases": {},
            "overall_success": False,
            "recommendations": []
        }
        
        # Available fix scripts
        self.fix_scripts = {
            "environment": "fix_phoenix_environment.py",
            "graphql": "fix_phoenix_graphql.py",
            "diagnostic": "main/debug_phoenix_comprehensive.py",
            "end_to_end": "test_phoenix_end_to_end.py"
        }
    
    def run_script(self, script_name, description):
        """Run a fix script and capture results."""
        logger.info(f"🔧 {description}")
        logger.info("=" * 60)
        
        script_path = self.project_root / self.fix_scripts[script_name]
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        try:
            # Run the script
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Capture results
            phase_result = {
                "script": str(script_path),
                "description": description,
                "duration_seconds": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            self.results["phases"][script_name] = phase_result
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully ({duration:.1f}s)")
                
                # Print key output lines
                if result.stdout:
                    output_lines = result.stdout.strip().split('\\n')
                    key_lines = [line for line in output_lines 
                               if any(marker in line for marker in ['✅', '❌', '🎉', '⚠️', 'SUCCESS', 'FAIL'])]
                    
                    if key_lines:
                        logger.info("   Key results:")
                        for line in key_lines[-5:]:  # Last 5 key lines
                            logger.info(f"   {line}")
                
                return True
            else:
                logger.error(f"❌ {description} failed (return code: {result.returncode})")
                
                # Print error details
                if result.stderr:
                    error_lines = result.stderr.strip().split('\\n')
                    logger.error("   Errors:")
                    for line in error_lines[-3:]:  # Last 3 error lines
                        logger.error(f"   {line}")
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} timed out after 5 minutes")
            self.results["phases"][script_name] = {
                "script": str(script_path),
                "description": description,
                "success": False,
                "error": "Timeout after 5 minutes"
            }
            return False
            
        except Exception as e:
            logger.error(f"❌ {description} failed with exception: {e}")
            self.results["phases"][script_name] = {
                "script": str(script_path),
                "description": description,
                "success": False,
                "error": str(e)
            }
            return False
    
    def check_prerequisite_files(self):
        """Check that all required fix scripts exist."""
        logger.info("🔍 Checking prerequisite files...")
        
        missing_files = []
        for script_name, script_path in self.fix_scripts.items():
            full_path = self.project_root / script_path
            if not full_path.exists():
                missing_files.append(full_path)
                logger.error(f"   ❌ Missing: {full_path}")
            else:
                logger.info(f"   ✅ Found: {full_path}")
        
        if missing_files:
            logger.error(f"❌ {len(missing_files)} required files missing")
            return False
        else:
            logger.info("✅ All prerequisite files present")
            return True
    
    def run_all_fixes(self):
        """Run all Phoenix fixes in correct order."""
        logger.info("🚀 Master Phoenix Observability Fix")
        logger.info("=" * 80)
        logger.info(f"Fix Session ID: {self.results['fix_session_id']}")
        logger.info(f"Project Root: {self.project_root}")
        logger.info("=" * 80)
        
        # Check prerequisites
        if not self.check_prerequisite_files():
            logger.error("❌ Prerequisites not met - cannot continue")
            return self.results
        
        # Define fix phases in order
        fix_phases = [
            ("environment", "Phase 1: Environment and Dependency Fixes"),
            ("diagnostic", "Phase 2: Comprehensive Diagnostic Analysis"),
            ("graphql", "Phase 3: GraphQL API Repair"),
            ("end_to_end", "Phase 4: End-to-End Validation Test")
        ]
        
        successful_phases = 0
        critical_failure = False
        
        for phase_name, phase_description in fix_phases:
            logger.info(f"\\n{'='*20} {phase_description} {'='*20}")
            
            try:
                if self.run_script(phase_name, phase_description):
                    successful_phases += 1
                    logger.info(f"✅ {phase_description} - SUCCESS")
                    
                    # Short pause between phases
                    if phase_name != fix_phases[-1][0]:  # Not the last phase
                        logger.info("⏳ Pausing between phases...")
                        time.sleep(3)
                        
                else:
                    logger.error(f"❌ {phase_description} - FAILED")
                    
                    # Determine if this is a critical failure
                    if phase_name in ["environment", "end_to_end"]:
                        critical_failure = True
                        logger.error("🚨 CRITICAL FAILURE - this phase is required for Phoenix to work")
                    else:
                        logger.warning("⚠️ Non-critical failure - continuing with remaining phases")
                        
            except Exception as e:
                logger.error(f"❌ {phase_description} failed with exception: {e}")
                if phase_name in ["environment", "end_to_end"]:
                    critical_failure = True
        
        # Final assessment
        self.results["successful_phases"] = successful_phases
        self.results["total_phases"] = len(fix_phases)
        self.results["critical_failure"] = critical_failure
        
        # Determine overall success
        # Phoenix is functional if environment is fixed and end-to-end test passes
        environment_success = self.results["phases"].get("environment", {}).get("success", False)
        e2e_success = self.results["phases"].get("end_to_end", {}).get("success", False)
        
        self.results["overall_success"] = environment_success and e2e_success and not critical_failure
        
        # Generate recommendations
        self._generate_recommendations()
        
        logger.info("=" * 80)
        logger.info(f"🏁 Master Phoenix Fix Complete: {successful_phases}/{len(fix_phases)} phases successful")
        
        if self.results["overall_success"]:
            logger.info("🎉 PHOENIX OBSERVABILITY IS NOW FULLY FUNCTIONAL!")
        else:
            logger.error("❌ Phoenix observability issues remain")
        
        return self.results
    
    def _generate_recommendations(self):
        """Generate recommendations based on fix results."""
        recommendations = []
        
        # Check each phase
        for phase_name, phase_data in self.results["phases"].items():
            if not phase_data.get("success", False):
                if phase_name == "environment":
                    recommendations.append("🚨 CRITICAL: Environment fixes failed")
                    recommendations.append("   • Manually install missing packages")
                    recommendations.append("   • Check Python version compatibility")
                    recommendations.append("   • Verify UV package manager is working")
                    
                elif phase_name == "graphql":
                    recommendations.append("⚠️ GraphQL API issues detected")
                    recommendations.append("   • Restart Phoenix server manually")
                    recommendations.append("   • Check Phoenix version compatibility")
                    recommendations.append("   • Consider Phoenix version downgrade")
                    
                elif phase_name == "diagnostic":
                    recommendations.append("⚠️ Diagnostic analysis incomplete")
                    recommendations.append("   • Review diagnostic logs for specific issues")
                    recommendations.append("   • Check Phoenix server health manually")
                    
                elif phase_name == "end_to_end":
                    recommendations.append("🚨 CRITICAL: End-to-end test failed")
                    recommendations.append("   • Phoenix may not be receiving traces")
                    recommendations.append("   • GraphQL API may still be broken")
                    recommendations.append("   • Manual investigation required")
        
        # Success recommendations
        if self.results["overall_success"]:
            recommendations.append("✅ Phoenix observability is fully functional")
            recommendations.append("   • All traces will be captured and visible")
            recommendations.append("   • Enhanced pharmaceutical features are working")
            recommendations.append("   • Compliance dashboards can be generated")
            recommendations.append("   • Ready for production workflow use")
        
        # General recommendations
        recommendations.extend([
            "",
            "📋 Next Steps:",
            "   • Test with actual workflow: python main/main.py",
            "   • Monitor Phoenix UI: http://localhost:6006",
            "   • Check compliance dashboard generation",
            "   • Verify audit trail completeness"
        ])
        
        self.results["recommendations"] = recommendations
    
    def save_results(self, filename=None):
        """Save complete fix results."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"master_phoenix_fix_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 Complete fix results saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print comprehensive summary."""
        print("\\n" + "=" * 80)
        print("📋 MASTER PHOENIX FIX SUMMARY")
        print("=" * 80)
        
        print(f"🆔 Fix Session: {self.results['fix_session_id']}")
        print(f"📅 Date/Time: {self.results['datetime']}")
        print(f"✅ Successful Phases: {self.results.get('successful_phases', 0)}/{self.results.get('total_phases', 0)}")
        
        print("\\n🔧 Phase Results:")
        for phase_name, phase_data in self.results["phases"].items():
            status = "✅ SUCCESS" if phase_data.get("success", False) else "❌ FAILED"
            duration = phase_data.get("duration_seconds", 0)
            print(f"   {status}: {phase_data.get('description', phase_name)} ({duration:.1f}s)")
        
        if self.results["overall_success"]:
            print("\\n🎉 OVERALL STATUS: PHOENIX OBSERVABILITY FULLY FUNCTIONAL!")
            print("   • All traces will be captured and retrievable")
            print("   • GraphQL API is working correctly")
            print("   • Enhanced pharmaceutical features enabled")
            print("   • Ready for production workflow use")
        else:
            print("\\n❌ OVERALL STATUS: CRITICAL ISSUES REMAIN")
            print("   • Phoenix observability not fully functional")
            print("   • Manual intervention required")
        
        if self.results["recommendations"]:
            print("\\n💡 Recommendations:")
            for rec in self.results["recommendations"]:
                if rec.strip():  # Skip empty lines
                    print(f"   {rec}")
        
        print("\\n🧪 Testing Commands:")
        print("   • Basic test: python main/examples/test_phoenix_basic.py")
        print("   • Full diagnostic: python main/debug_phoenix_comprehensive.py")
        print("   • End-to-end test: python test_phoenix_end_to_end.py")
        print("   • Production workflow: python main/main.py [document_path]")
        
        print("\\n🌐 Phoenix URLs:")
        print("   • UI Dashboard: http://localhost:6006")
        print("   • GraphQL API: http://localhost:6006/graphql")
        print("   • OTLP Endpoint: http://localhost:6006/v1/traces")

def main():
    """Run master Phoenix fix."""
    fixer = MasterPhoenixFixer()
    results = fixer.run_all_fixes()
    
    # Save complete results
    filename = fixer.save_results()
    
    # Print comprehensive summary
    fixer.print_summary()
    
    print(f"\\n📁 Complete results saved to: {filename}")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n🎉 Phoenix observability is ready for use!")
    else:
        print("\\n⚠️ Manual intervention required - see recommendations above")
    
    sys.exit(0 if success else 1)