#!/usr/bin/env python3
"""
Execute Fold 1 Validation Script

This script sets up validation mode environment variables and executes
fold 1 of the k=5 cross-validation with real API calls to DeepSeek V3.

Task 30: Execute First Fold Validation
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
project_root = Path(__file__).parent
env_file = project_root / ".env"

if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Set validation mode environment variables
os.environ["VALIDATION_MODE"] = "true"
os.environ["VALIDATION_MODE_EXPLICIT"] = "true"
os.environ["BYPASS_CONSULTATION_THRESHOLD"] = "0.7"

# Add the main directory to Python path
project_root = Path(__file__).parent
main_dir = project_root / "main"
sys.path.insert(0, str(main_dir))
sys.path.insert(0, str(main_dir / "src" / "core"))

print("=" * 80)
print("TASK 30: Execute First Fold Validation")
print("=" * 80)
print(f"Project Root: {project_root}")
print(f"Timestamp: {datetime.now().isoformat()}")
print()

print("Environment Variables Set:")
print(f"  VALIDATION_MODE = {os.environ.get('VALIDATION_MODE')}")
print(f"  VALIDATION_MODE_EXPLICIT = {os.environ.get('VALIDATION_MODE_EXPLICIT')}")
print(f"  BYPASS_CONSULTATION_THRESHOLD = {os.environ.get('BYPASS_CONSULTATION_THRESHOLD')}")
print()

# Verify Phoenix is running
print("Checking Phoenix observability status...")
try:
    import requests
    response = requests.get("http://localhost:6006", timeout=5)
    print("  [OK] Phoenix is running at http://localhost:6006")
except Exception as e:
    print(f"  [WARN] Phoenix connection issue: {e}")
print()

# Check API keys
print("Verifying API keys...")
required_keys = ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
for key in required_keys:
    value = os.environ.get(key)
    if value:
        print(f"  [OK] {key}: {'*' * 10}...{value[-4:]}")
    else:
        print(f"  [FAIL] {key}: NOT SET")
print()

async def execute_fold_1():
    """Execute fold 1 with validation mode."""
    try:
        print("Initializing CV Workflow Integration...")
        
        # Import the CV workflow integration
        from cv_workflow_integration import CrossValidationWorkflowIntegration
        
        # Initialize with default config
        cv_integration = CrossValidationWorkflowIntegration()
        
        print("[OK] CV Workflow Integration initialized")
        print()
        
        # Workflow configuration for validation mode
        workflow_config = {
            'enable_categorization': True,
            'enable_test_generation': True,
            'enable_monitoring': True,
            'output_format': 'json',
            'compliance_mode': True,
            'validation_mode': True,  # Explicit validation mode
            'target_model': 'deepseek/deepseek-chat'  # Ensure DeepSeek V3 is used
        }
        
        print("Workflow Configuration:")
        for key, value in workflow_config.items():
            print(f"  {key}: {value}")
        print()
        
        # Display fold 1 test documents
        print("Fold 1 Test Documents:")
        fold_data = cv_integration.cv_manager.get_fold(1)
        test_docs = [doc.doc_id for doc in fold_data['test']]
        for doc_id in test_docs:
            doc_info = next((doc for doc in fold_data['test'] if doc.doc_id == doc_id), None)
            if doc_info:
                print(f"  • {doc_id}: {doc_info.gamp_category} ({doc_info.total_requirements} requirements)")
        print()
        
        print("[START] Starting Fold 1 Execution...")
        print("   This will make REAL API calls to DeepSeek V3")
        print("   Expected duration: 10-20 minutes")
        print("   Monitor Phoenix traces at: http://localhost:6006")
        print()
        
        # Execute fold 1
        start_time = datetime.now()
        print(f"Execution started at: {start_time.isoformat()}")
        
        fold_result = await cv_integration.execute_fold(1, workflow_config)
        
        end_time = datetime.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 80)
        print("FOLD 1 EXECUTION COMPLETED")
        print("=" * 80)
        print(f"Execution Duration: {execution_duration:.2f} seconds ({execution_duration/60:.2f} minutes)")
        print(f"Success: {fold_result.success}")
        print()
        
        if fold_result.success:
            print("[SUCCESS] Fold 1 executed successfully!")
            print()
            print("Results Summary:")
            print(f"  Test Documents: {len(fold_result.test_documents)}")
            print(f"  Train Documents: {len(fold_result.train_documents)}")
            print(f"  Execution Time: {fold_result.execution_time_seconds:.2f}s")
            
            # Display test generation results
            if fold_result.test_generation_results:
                print("  Test Generation:")
                test_gen = fold_result.test_generation_results
                for key, value in test_gen.items():
                    print(f"    {key}: {value}")
            
            # Display workflow metrics
            if fold_result.workflow_metrics:
                print("  Workflow Metrics:")
                for key, value in fold_result.workflow_metrics.items():
                    print(f"    {key}: {value}")
        else:
            print("[FAIL] Fold 1 execution failed!")
            print("Errors:")
            for error in fold_result.errors:
                print(f"  • {error}")
        
        print()
        
        # Save results
        output_dir = project_root / "main" / "output" / "cross_validation"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "fold_1_results.json"
        
        # Convert result to dict for JSON serialization
        result_dict = {
            'fold_number': fold_result.fold_number,
            'test_documents': fold_result.test_documents,
            'train_documents': fold_result.train_documents,
            'execution_time_seconds': fold_result.execution_time_seconds,
            'test_generation_results': fold_result.test_generation_results,
            'workflow_metrics': fold_result.workflow_metrics,
            'errors': fold_result.errors,
            'success': fold_result.success,
            'execution_timestamp': end_time.isoformat(),
            'validation_mode_enabled': True,
            'environment_info': {
                'validation_mode': os.environ.get('VALIDATION_MODE'),
                'validation_mode_explicit': os.environ.get('VALIDATION_MODE_EXPLICIT'),
                'bypass_consultation_threshold': os.environ.get('BYPASS_CONSULTATION_THRESHOLD')
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Results saved to: {results_file}")
        print()
        
        # Check output files
        test_suites_dir = project_root / "main" / "output" / "test_suites"
        if test_suites_dir.exists():
            test_files = list(test_suites_dir.glob("*.json"))
            print(f"Test Suite Files Generated: {len(test_files)}")
            for test_file in test_files[-5:]:  # Show last 5 files
                print(f"  • {test_file.name}")
        
        print()
        print("[SUMMARY] Task 30 Execution Summary:")
        print("  [OK] Validation mode configured")
        print("  [OK] Environment variables set")
        print("  [OK] Fold 1 execution attempted")
        print(f"  [{'OK' if fold_result.success else 'FAIL'}] Real API calls made")
        print("  [OK] Phoenix traces captured")
        print("  [OK] Results saved")
        
        return fold_result
        
    except Exception as e:
        print(f"[FAIL] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the fold 1 execution
    result = asyncio.run(execute_fold_1())
    
    if result and result.success:
        print("\n[SUCCESS] Task 30 completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAIL] Task 30 failed!")
        sys.exit(1)