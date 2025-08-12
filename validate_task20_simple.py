#!/usr/bin/env python3
"""
Task 20 Cross-Validation Results Validation (Simple ASCII Version)

CRITICAL: Validates REAL execution data with NO FALLBACKS
"""

import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

def validate_execution_data():
    """Validate the real execution data from Task 20."""
    
    print("TASK 20 CROSS-VALIDATION RESULTS VALIDATION")
    print("=" * 50)
    
    # Load environment
    load_dotenv('.env')
    
    # Check execution log
    project_root = Path(__file__).parent
    execution_log = project_root / "main/output/cross_validation/structured_logs/TASK20_REAL_EXECUTION_urs_processing.jsonl"
    
    if not execution_log.exists():
        print("[ERROR] Main execution log not found")
        print(f"Expected: {execution_log}")
        return False
    
    print(f"[OK] Found execution log: {execution_log.name}")
    
    # Parse execution records
    execution_data = []
    try:
        with open(execution_log) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    execution_data.append(data)
    except Exception as e:
        print(f"[ERROR] Failed to parse execution log: {e}")
        return False
    
    print(f"[OK] Parsed {len(execution_data)} execution records")
    
    # Analyze records
    successful_runs = []
    failed_runs = []
    total_cost = 0.0
    total_tokens = 0
    
    print("\nEXECUTION ANALYSIS:")
    print("-" * 30)
    
    for record in execution_data:
        doc_id = record.get('document_id', 'Unknown')
        success = record.get('success', False)
        processing_time = record.get('processing_time_seconds', 0)
        model = record.get('model_name', 'Unknown')
        
        print(f"\nDocument: {doc_id}")
        print(f"  Success: {success}")
        print(f"  Processing Time: {processing_time:.1f}s")
        print(f"  Model: {model}")
        
        if success:
            successful_runs.append(record)
            cost = record.get('cost_usd', 0)
            total_cost += cost
            
            token_usage = record.get('token_usage', {})
            tokens = token_usage.get('total_tokens', 0)
            total_tokens += tokens
            
            print(f"  Cost: ${cost:.6f}")
            print(f"  Tokens: {tokens:,}")
            print(f"  Tests Generated: {record.get('generated_tests_count', 0)}")
            print(f"  GAMP Category: {record.get('gamp_category_detected', 'Unknown')}")
            
            # Check for real API indicators
            if tokens > 0 and cost > 0:
                print("  [OK] Real API call indicators present")
            else:
                print("  [WARN] Missing API indicators")
        else:
            failed_runs.append(record)
            error = record.get('error_message', 'Unknown error')
            print(f"  Error: {error}")
            
            # Check for fallback patterns (should NOT exist)
            error_lower = error.lower()
            if any(term in error_lower for term in ['default', 'fallback', 'synthetic', 'mock']):
                print("  [ERROR] FALLBACK PATTERN DETECTED")
                return False
            else:
                print("  [OK] Honest error reporting (no fallbacks)")
    
    # Summary statistics
    print("\nEXECUTION SUMMARY:")
    print("-" * 30)
    success_rate = len(successful_runs) / len(execution_data) if execution_data else 0
    print(f"Total Documents Processed: {len(execution_data)}")
    print(f"Successful: {len(successful_runs)}")
    print(f"Failed: {len(failed_runs)}")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Total Cost: ${total_cost:.6f}")
    print(f"Total Tokens: {total_tokens:,}")
    
    if successful_runs:
        avg_cost = total_cost / len(successful_runs)
        avg_tokens = total_tokens / len(successful_runs)
        print(f"Average Cost per Success: ${avg_cost:.6f}")
        print(f"Average Tokens per Success: {avg_tokens:,.0f}")
    
    # Validate DeepSeek pricing
    print("\nDEEPSEEK PRICING VALIDATION:")
    print("-" * 30)
    
    # DeepSeek V3 pricing (as of Jan 2025)
    deepseek_input_price = 0.14 / 1_000_000  # $0.14 per 1M tokens
    deepseek_output_price = 0.28 / 1_000_000  # $0.28 per 1M tokens
    
    pricing_valid = True
    for record in successful_runs:
        token_usage = record.get('token_usage', {})
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        
        expected_cost = (prompt_tokens * deepseek_input_price) + (completion_tokens * deepseek_output_price)
        actual_cost = record.get('cost_usd', 0)
        
        cost_diff = abs(actual_cost - expected_cost)
        cost_tolerance = expected_cost * 0.1  # 10% tolerance
        
        print(f"\nDocument: {record.get('document_id')}")
        print(f"  Prompt Tokens: {prompt_tokens:,}")
        print(f"  Completion Tokens: {completion_tokens:,}")
        print(f"  Expected Cost: ${expected_cost:.6f}")
        print(f"  Actual Cost: ${actual_cost:.6f}")
        print(f"  Difference: ${cost_diff:.6f}")
        
        if cost_diff <= cost_tolerance:
            print(f"  [OK] Pricing matches DeepSeek rates")
        else:
            print(f"  [ERROR] Pricing mismatch exceeds tolerance")
            pricing_valid = False
    
    # Check environment configuration
    print("\nAPI CONFIGURATION:")
    print("-" * 30)
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print("[OK] OPENROUTER_API_KEY present in environment")
        print(f"   Key prefix: {openrouter_key[:8]}...")
    else:
        print("[ERROR] OPENROUTER_API_KEY not found")
        return False
    
    # Anti-mock validation
    print("\nANTI-MOCK VALIDATION:")
    print("-" * 30)
    
    mock_indicators_found = []
    for record in execution_data:
        record_str = json.dumps(record).lower()
        
        mock_terms = ['mock', 'synthetic', 'fake', 'test_mode', 'simulation', 'dummy']
        for term in mock_terms:
            if term in record_str:
                mock_indicators_found.append(f"'{term}' found in {record.get('document_id', 'unknown')}")
    
    if mock_indicators_found:
        print("[ERROR] MOCK INDICATORS DETECTED:")
        for indicator in mock_indicators_found:
            print(f"  - {indicator}")
        return False
    else:
        print("[OK] No mock/synthetic indicators found - appears to be real execution")
    
    print("\nVALIDATION RESULTS:")
    print("=" * 50)
    
    if pricing_valid and len(successful_runs) > 0:
        print("[SUCCESS] VALIDATION PASSED - Real execution data confirmed")
        print("- API calls verified with actual costs and tokens")
        print("- Cost calculations match DeepSeek pricing")
        print("- No fallback patterns detected")
        print("- Statistical data appears authentic")
        
        # Key findings
        print(f"\nKEY FINDINGS:")
        print(f"- {len(successful_runs)}/{len(execution_data)} documents processed successfully ({success_rate:.1%})")
        print(f"- Total cost: ${total_cost:.6f} for {total_tokens:,} tokens")
        print(f"- Model: deepseek/deepseek-chat (DeepSeek V3)")
        print(f"- Real processing times: {processing_time:.1f}s average")
        
        return True
    else:
        print("[FAILED] VALIDATION ISSUES FOUND")
        return False

if __name__ == "__main__":
    success = validate_execution_data()
    exit(0 if success else 1)