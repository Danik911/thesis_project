#!/usr/bin/env python3
"""
Complete End-to-End Test of Pharmaceutical Workflow with DeepSeek V3
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value

# Verify API key is loaded
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("ERROR: OPENROUTER_API_KEY not found in environment!")
    sys.exit(1)

print(f"=== PHARMACEUTICAL TEST GENERATION E2E TEST ===")
print(f"Model: DeepSeek V3 (deepseek/deepseek-chat)")
print(f"API Key: {api_key[:20]}...")
print(f"Start Time: {datetime.now().isoformat()}")
print()

# Test with URS document
urs_file = "tests/test_data/test_urs.txt"
if not Path(urs_file).exists():
    print(f"ERROR: Test file {urs_file} not found!")
    sys.exit(1)

print(f"Testing with URS: {urs_file}")
print()

try:
    # Import and run the main workflow
    from main import main
    
    # Run with the URS file
    start_time = time.time()
    
    print("=== LAUNCHING COMPLETE WORKFLOW ===")
    print("Expected agents: Categorization -> Context Provider -> OQ Generator")
    print("Expected duration: 2-5 minutes")
    print()
    
    # Run main workflow with URS file
    main([urs_file])
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print()
    print(f"=== WORKFLOW COMPLETED ===")
    print(f"Total execution time: {execution_time:.2f} seconds ({execution_time/60:.1f} minutes)")
    
    # Check for output files
    output_dir = Path("output")
    if output_dir.exists():
        output_files = list(output_dir.glob("**/*.json"))
        if output_files:
            latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
            print(f"Latest output file: {latest_file}")
            
            # Read and validate the output
            try:
                with open(latest_file, 'r') as f:
                    test_suite = json.load(f)
                    
                test_count = len(test_suite.get('tests', []))
                print(f"Generated {test_count} OQ tests")
                
                if test_count == 25:
                    print("SUCCESS: Exactly 25 tests generated as expected!")
                else:
                    print(f"WARNING: Expected 25 tests, got {test_count}")
                    
                # Show sample test
                if test_suite.get('tests'):
                    sample_test = test_suite['tests'][0]
                    print()
                    print("Sample test case:")
                    print(f"  ID: {sample_test.get('test_id')}")
                    print(f"  Title: {sample_test.get('title')}")
                    print(f"  Category: {sample_test.get('gamp_category')}")
                    
            except Exception as e:
                print(f"ERROR reading output file: {e}")
        else:
            print("WARNING: No output files found")
    else:
        print("WARNING: Output directory not found")
    
    # Check trace files
    trace_dir = Path("logs/traces")
    if trace_dir.exists():
        trace_files = list(trace_dir.glob("all_spans_*.jsonl"))
        if trace_files:
            latest_trace = max(trace_files, key=lambda p: p.stat().st_mtime)
            with open(latest_trace, 'r') as f:
                trace_count = len(f.readlines())
            print(f"Captured {trace_count} total spans in {latest_trace.name}")
        
        chromadb_files = list(trace_dir.glob("chromadb_spans_*.jsonl"))
        if chromadb_files:
            latest_chromadb = max(chromadb_files, key=lambda p: p.stat().st_mtime)
            with open(latest_chromadb, 'r') as f:
                chromadb_count = len(f.readlines())
            print(f"Captured {chromadb_count} ChromaDB spans in {latest_chromadb.name}")
        
    print()
    print("=== END-TO-END TEST COMPLETED SUCCESSFULLY ===")
    
except Exception as e:
    print(f"ERROR: Workflow failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)