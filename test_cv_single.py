#!/usr/bin/env python
"""
Test script for cv-validation-tester subagent
Tests a single URS document to validate the cross-validation workflow
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

def test_single_document():
    """Test cross-validation with a single URS document"""
    
    # Setup paths
    project_root = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project")
    main_dir = project_root / "main"
    test_doc = "../datasets/urs_corpus/category_3/URS-001.md"
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = main_dir / "output" / "cross_validation" / f"cv_test_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📊 Cross-Validation Single Document Test")
    print(f"=" * 50)
    print(f"Document: {test_doc}")
    print(f"Output: {output_dir}")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Change to main directory
    os.chdir(main_dir)
    
    # Set environment for validation mode
    env = os.environ.copy()
    env["VALIDATION_MODE"] = "true"
    
    # Load API keys from .env file
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    if key in ['OPENAI_API_KEY', 'OPENROUTER_API_KEY']:
                        env[key] = value
                        print(f"✅ Loaded {key[:20]}...")
    
    # Verify Phoenix is running
    print("\n🐳 Checking Phoenix Docker container...")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            check=False
        )
        if "phoenix" in result.stdout:
            print("✅ Phoenix container is running")
        else:
            print("⚠️ Phoenix container not found - starting it...")
            subprocess.run(
                ["docker", "run", "-d", "-p", "6006:6006", 
                 "--name", "phoenix-server", "arizephoenix/phoenix:latest"],
                check=False
            )
    except Exception as e:
        print(f"⚠️ Could not check Docker: {e}")
    
    # Run the test
    print(f"\n🚀 Executing test for {test_doc}...")
    print("Expected duration: 4-7 minutes")
    print()
    
    # Prepare command
    cmd = [
        "uv", "run", "python", "main.py",
        test_doc,
        "--verbose"
    ]
    
    # Create metadata file
    metadata = {
        "doc_id": "URS-001",
        "path": test_doc,
        "expected_category": 3,
        "start_time": datetime.now().isoformat(),
        "test_type": "single_document_validation"
    }
    
    metadata_file = output_dir / "URS-001_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Execute the test
    console_output = output_dir / "URS-001_console.txt"
    
    try:
        print("Starting execution...")
        with open(console_output, 'w') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            # Stream output
            for line in process.stdout:
                print(line.rstrip())
                log_file.write(line)
            
            process.wait()
            return_code = process.returncode
            
        # Update metadata with completion
        metadata["end_time"] = datetime.now().isoformat()
        metadata["return_code"] = return_code
        metadata["success"] = return_code == 0
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        if return_code == 0:
            print("\n✅ Test completed successfully!")
            
            # Look for generated test suite
            test_suites = list(Path("output/test_suites").glob("test_suite_OQ-SUITE-*.json"))
            if test_suites:
                latest_suite = max(test_suites, key=lambda p: p.stat().st_mtime)
                print(f"📄 Test suite generated: {latest_suite.name}")
                
                # Copy to CV output directory
                import shutil
                shutil.copy(latest_suite, output_dir / "test_suite.json")
        else:
            print(f"\n❌ Test failed with return code: {return_code}")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        metadata["error"] = str(e)
        metadata["success"] = False
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    # Generate simple results file
    results = {
        "timestamp": timestamp,
        "total_documents": 1,
        "results": [metadata],
        "summary": {
            "total_processed": 1,
            "successful": 1 if metadata.get("success") else 0,
            "failed": 0 if metadata.get("success") else 1,
            "success_rate": 1.0 if metadata.get("success") else 0.0
        }
    }
    
    results_file = output_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to: {output_dir}")
    print(f"  - Console log: URS-001_console.txt")
    print(f"  - Metadata: URS-001_metadata.json")
    print(f"  - Results summary: results.json")
    
    return metadata.get("success", False)

if __name__ == "__main__":
    success = test_single_document()
    sys.exit(0 if success else 1)