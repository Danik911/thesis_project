#!/usr/bin/env python3
"""
Phoenix Trace Analysis Script
Analyzes traces captured during workflow execution
"""

import phoenix as px
import pandas as pd
from phoenix.trace import TraceDataset
import json
import sys
from datetime import datetime

def analyze_phoenix_traces():
    print("=== Phoenix Trace Analysis ===")
    print(f"Analysis Time: {datetime.now().isoformat()}")
    
    try:
        # Try to get active session
        session = px.active_session()
        if session:
            print(f"✅ Active Phoenix session found: {session}")
        else:
            print("❌ No active Phoenix session")
            return
            
        # Get traces
        traces = session.get_traces()
        print(f"📊 Found {len(traces)} traces")
        
        if not traces.empty:
            print("\n=== Trace Summary ===")
            print(f"Trace columns: {list(traces.columns)}")
            print(f"Date range: {traces.index.min()} to {traces.index.max()}")
            
            # Analyze trace types
            if 'name' in traces.columns:
                trace_types = traces['name'].value_counts()
                print(f"\n📈 Trace Types:")
                for trace_type, count in trace_types.items():
                    print(f"  - {trace_type}: {count}")
            
            # Look for LLM-related traces
            llm_traces = traces[traces['name'].str.contains('llm|openai|claude', case=False, na=False)]
            print(f"\n🤖 LLM Traces: {len(llm_traces)}")
            
            # Look for workflow traces
            workflow_traces = traces[traces['name'].str.contains('workflow|event|step', case=False, na=False)]
            print(f"🔄 Workflow Traces: {len(workflow_traces)}")
            
            # Look for error traces
            error_traces = traces[traces['status_code'] != 'OK'] if 'status_code' in traces.columns else pd.DataFrame()
            print(f"❌ Error Traces: {len(error_traces)}")
            
            # Show recent traces
            print(f"\n=== Recent Traces (Last 10) ===")
            recent = traces.tail(10)
            for idx, trace in recent.iterrows():
                status = trace.get('status_code', 'UNKNOWN')
                name = trace.get('name', 'unnamed')
                print(f"  {idx}: {name} - {status}")
                
        else:
            print("📋 No traces found in Phoenix session")
            
    except Exception as e:
        print(f"❌ Error analyzing Phoenix traces: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_phoenix_traces()