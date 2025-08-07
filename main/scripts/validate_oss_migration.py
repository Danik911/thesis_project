#!/usr/bin/env python3
"""
OSS Migration Validation Script
Validates that the system is ready for or has completed OSS migration.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MigrationValidator:
    """Validates OSS migration readiness and completion."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "ready": False,
            "issues": []
        }
    
    def check_environment(self) -> bool:
        """Check environment variables."""
        print("\n[1/6] Checking Environment Variables...")
        
        checks = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY") is not None,
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY") is not None,
        }
        
        self.results["checks"]["environment"] = checks
        
        for key, present in checks.items():
            status = "[OK]" if present else "[MISSING]"
            print(f"  {status} {key}: {'Present' if present else 'Missing'}")
            if not present and key == "OPENROUTER_API_KEY":
                self.results["issues"].append(f"Missing required {key}")
        
        return checks["OPENROUTER_API_KEY"]
    
    def check_openrouter_llm(self) -> bool:
        """Check if OpenRouter LLM class exists."""
        print("\n[2/6] Checking OpenRouter LLM Implementation...")
        
        llm_path = self.project_root / "src" / "llms" / "openrouter_llm.py"
        exists = llm_path.exists()
        
        self.results["checks"]["openrouter_llm"] = exists
        
        if exists:
            print(f"  [OK] OpenRouter LLM class found at: {llm_path}")
            
            # Check for required methods
            with open(llm_path, 'r') as f:
                content = f.read()
                required_methods = ["complete", "chat", "parse_structured_response"]
                for method in required_methods:
                    if f"def {method}" in content:
                        print(f"    [OK] Method '{method}' implemented")
                    else:
                        print(f"    [FAIL] Method '{method}' missing")
        else:
            print(f"  [FAIL] OpenRouter LLM class not found")
            self.results["issues"].append("OpenRouter LLM class not implemented")
        
        return exists
    
    def check_categorization_agent(self) -> bool:
        """Check if categorization agent has been migrated."""
        print("\n[3/6] Checking Categorization Agent Migration...")
        
        agent_path = self.project_root / "src" / "agents" / "categorization" / "agent.py"
        
        if not agent_path.exists():
            print(f"  [FAIL] Categorization agent not found")
            return False
        
        with open(agent_path, 'r') as f:
            content = f.read()
        
        checks = {
            "parse_structured_response": "def parse_structured_response" in content,
            "direct_llm_calls": "llm.complete(" in content,
            "no_llmtextcompletion": "LLMTextCompletionProgram" not in content or "# Legacy" in content,
            "json_import": "import json" in content,
            "regex_import": "import re" in content
        }
        
        self.results["checks"]["categorization_agent"] = checks
        
        all_good = True
        for check, passed in checks.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {check.replace('_', ' ').title()}: {'Yes' if passed else 'No'}")
            if not passed:
                all_good = False
                self.results["issues"].append(f"Categorization agent: {check} failed")
        
        return all_good
    
    def check_human_consultation(self) -> bool:
        """Check human consultation system."""
        print("\n[4/6] Checking Human Consultation System...")
        
        consultation_path = self.project_root / "src" / "core" / "human_consultation.py"
        exists = consultation_path.exists()
        
        self.results["checks"]["human_consultation"] = exists
        
        if exists:
            print(f"  [OK] Human consultation system found")
            
            with open(consultation_path, 'r') as f:
                content = f.read()
                
            # Check for NO FALLBACK policy
            no_fallbacks = "NO fallback" in content or "no_fallback" in content.lower()
            if no_fallbacks:
                print(f"    [OK] NO FALLBACK policy enforced")
            else:
                print(f"    [WARN] Check NO FALLBACK policy")
        else:
            print(f"  [FAIL] Human consultation system not found")
            self.results["issues"].append("Human consultation system missing")
        
        return exists
    
    def check_test_coverage(self) -> bool:
        """Check if OSS migration tests exist."""
        print("\n[5/6] Checking Test Coverage...")
        
        test_dir = self.project_root / "tests" / "oss_migration"
        exists = test_dir.exists()
        
        if exists:
            test_files = list(test_dir.glob("test_*.py"))
            print(f"  [OK] OSS migration tests directory found")
            print(f"    Found {len(test_files)} test files")
            
            required_tests = [
                "test_categorization_oss.py",
                "test_direct_parsing.py",
                "test_openrouter_direct.py"
            ]
            
            for test in required_tests:
                test_path = test_dir / test
                if test_path.exists():
                    print(f"    [OK] {test}")
                else:
                    print(f"    [FAIL] {test} missing")
            
            self.results["checks"]["test_coverage"] = len(test_files) >= 3
            return len(test_files) >= 3
        else:
            print(f"  [FAIL] OSS migration tests not found")
            self.results["issues"].append("No OSS migration tests")
            self.results["checks"]["test_coverage"] = False
            return False
    
    def check_documentation(self) -> bool:
        """Check if migration documentation exists."""
        print("\n[6/6] Checking Documentation...")
        
        docs = {
            "Migration Guide": self.project_root / "docs" / "guides" / "OSS_MODEL_MIGRATION_GUIDE.md",
            "OSS Report": self.project_root / "docs" / "reports" / "oss_migration" / "OSS_MIGRATION_SUCCESS.md",
            "Test Report": self.project_root / "docs" / "reports" / "oss_migration" / "OSS_LLM_Testing_Report.md"
        }
        
        all_present = True
        for name, path in docs.items():
            if path.exists():
                print(f"  [OK] {name}: Found")
            else:
                print(f"  [FAIL] {name}: Missing")
                all_present = False
        
        self.results["checks"]["documentation"] = all_present
        return all_present
    
    def generate_report(self) -> None:
        """Generate final validation report."""
        print("\n" + "="*60)
        print("MIGRATION VALIDATION REPORT")
        print("="*60)
        
        # Calculate readiness
        critical_checks = [
            self.results["checks"].get("environment", {}).get("OPENROUTER_API_KEY", False),
            self.results["checks"].get("openrouter_llm", False),
            self.results["checks"].get("categorization_agent", {}).get("parse_structured_response", False),
            self.results["checks"].get("human_consultation", False)
        ]
        
        ready = all(critical_checks)
        self.results["ready"] = ready
        
        if ready:
            print("\n[READY] SYSTEM IS READY FOR OSS MIGRATION")
            print("\nYou can proceed with:")
            print("  1. Set LLM_PROVIDER=openrouter in environment")
            print("  2. Run integration tests")
            print("  3. Deploy with feature flags")
        else:
            print("\n[FAILED] SYSTEM NOT READY FOR MIGRATION")
            print("\nIssues to resolve:")
            for issue in self.results["issues"]:
                print(f"  - {issue}")
            print("\nRefer to: main/docs/guides/OSS_MODEL_MIGRATION_GUIDE.md")
        
        # Save report
        report_path = self.project_root / "migration_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
    
    def run(self) -> bool:
        """Run all validation checks."""
        print("="*60)
        print("OSS MIGRATION VALIDATION SCRIPT")
        print("="*60)
        
        # Run all checks
        self.check_environment()
        self.check_openrouter_llm()
        self.check_categorization_agent()
        self.check_human_consultation()
        self.check_test_coverage()
        self.check_documentation()
        
        # Generate report
        self.generate_report()
        
        return self.results["ready"]


def main():
    """Main entry point."""
    validator = MigrationValidator()
    ready = validator.run()
    
    # Return appropriate exit code
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()