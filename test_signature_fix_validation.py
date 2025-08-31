#!/usr/bin/env python3
"""
Test script to validate the signature fix for human consultation.

This script tests that when human consultation occurs, the categorization signature
shows the human operator instead of "system".
"""

import sys
import os
from pathlib import Path

# Add the main directory to Python path
main_dir = Path(__file__).parent / "main"
sys.path.insert(0, str(main_dir))

import asyncio
import json
from datetime import datetime

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.core.types import URSIngestionEvent
from src.config.system_config import get_config

async def test_signature_fix():
    """Test the signature fix with a simple workflow run."""
    
    print("🔧 Testing Signature Fix for Human Consultation")
    print("=" * 60)
    
    # Create test URS content that should trigger low confidence (consultation)
    test_urs_content = """
    URS-TEST-SIGNATURE-FIX
    
    This is a test document for validating signature capture.
    The system should categorize this, potentially trigger consultation,
    and create a signature with the correct signer information.
    
    Software: Legacy system migration to cloud platform
    Purpose: Validate signature capture workflow
    """
    
    # Initialize workflow
    workflow = UnifiedTestGenerationWorkflow(timeout=600, verbose=True)
    
    # Create ingestion event
    ingestion_event = URSIngestionEvent(
        urs_content=test_urs_content,
        session_id="signature_fix_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    
    print(f"📄 Test Document: URS-TEST-SIGNATURE-FIX")
    print(f"🔍 Session ID: {ingestion_event.session_id}")
    print()
    
    try:
        print("🚀 Starting workflow...")
        result = await workflow.run(ingestion_event)
        
        print("✅ Workflow completed successfully!")
        print(f"📊 Result type: {type(result).__name__}")
        
        # Check the signature manifest for the new signature
        print("\n📋 Checking signature manifest...")
        
        signature_manifest_path = main_dir / "compliance" / "signatures" / "signature_manifest.json"
        if signature_manifest_path.exists():
            with open(signature_manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Find the most recent categorization signature
            cat_signatures = [
                sig for sig in manifest["signatures"] 
                if sig["record_id"].startswith("cat_")
            ]
            
            if cat_signatures:
                latest_sig = sorted(cat_signatures, key=lambda x: x["signature_timestamp"])[-1]
                
                print(f"🔍 Latest categorization signature:")
                print(f"   📝 Record ID: {latest_sig['record_id']}")
                print(f"   👤 Signer: {latest_sig['signer_name']}")
                print(f"   🆔 Signer ID: {latest_sig['signer_id']}")
                print(f"   ⏰ Timestamp: {latest_sig['signature_timestamp']}")
                
                # Check if human consultation occurred
                if latest_sig['signer_id'] == 'system':
                    print("⚠️  SIGNATURE STILL SHOWS SYSTEM")
                    print("   This means either:")
                    print("   1. No human consultation was triggered (expected for high confidence)")
                    print("   2. The signature fix didn't work (bug)")
                else:
                    print("🎉 SIGNATURE SHOWS HUMAN OPERATOR!")
                    print(f"   Human signer captured: {latest_sig['signer_name']}")
                    
            else:
                print("❌ No categorization signatures found in manifest")
        else:
            print("❌ Signature manifest not found")
            
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 60)
    print("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(test_signature_fix())