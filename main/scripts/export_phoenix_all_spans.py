#!/usr/bin/env python3
"""
Export ALL spans from Phoenix including ChromaDB operations using query_spans.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Fix Windows Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import phoenix as px
from phoenix.trace.dsl import SpanQuery


def export_all_spans_complete():
    """Export all spans using query_spans method."""
    
    print("Phoenix Complete Span Export")
    print("=" * 50)
    
    # Create export directory
    export_dir = Path("docs/reports/monitoring/phoenix_exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to Phoenix
        print("\nConnecting to Phoenix...")
        client = px.Client()
        print("✅ Connected successfully")
        
        # Method 1: Use query_spans with no filter to get ALL spans
        print("\n1. Querying ALL spans (no filters)...")
        try:
            # Create an unfiltered query
            query = SpanQuery()
            all_spans_df = client.query_spans(query)
            
            if all_spans_df is not None and not all_spans_df.empty:
                print(f"✅ Found {len(all_spans_df)} spans using query_spans")
                
                # Save all spans
                all_spans_path = export_dir / f"phoenix_query_all_spans_{timestamp}.jsonl"
                all_spans_df.to_json(
                    all_spans_path,
                    orient='records',
                    lines=True,
                    date_format='iso'
                )
                print(f"   Saved to: {all_spans_path}")
                
                # Analyze span types
                if 'span_kind' in all_spans_df.columns:
                    print("\n   Span kinds found:")
                    for kind, count in all_spans_df['span_kind'].value_counts().items():
                        print(f"     - {kind}: {count}")
                
                # Look for ChromaDB operations
                if 'name' in all_spans_df.columns:
                    chromadb_spans = all_spans_df[
                        all_spans_df['name'].str.contains('chromadb', case=False, na=False)
                    ]
                    print(f"\n   ChromaDB spans: {len(chromadb_spans)}")
                    
                    # Also check for vector/collection operations
                    vector_spans = all_spans_df[
                        all_spans_df['name'].str.contains('vector|collection|embed', case=False, na=False, regex=True)
                    ]
                    print(f"   Vector/Collection spans: {len(vector_spans)}")
            else:
                print("⚠️ No spans returned from query_spans")
                
        except Exception as e:
            print(f"❌ Error with query_spans: {e}")
            print("   This might be due to Phoenix version compatibility")
        
        # Method 2: Try with time range (last 24 hours)
        print("\n2. Querying spans from last 24 hours...")
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            recent_spans = client.query_spans(
                start_time=start_time,
                end_time=end_time
            )
            
            if recent_spans is not None and not recent_spans.empty:
                print(f"✅ Found {len(recent_spans)} spans in last 24 hours")
                
                # Save recent spans
                recent_path = export_dir / f"phoenix_recent_spans_{timestamp}.jsonl"
                recent_spans.to_json(
                    recent_path,
                    orient='records',
                    lines=True,
                    date_format='iso'
                )
                print(f"   Saved to: {recent_path}")
            else:
                print("⚠️ No recent spans found")
                
        except Exception as e:
            print(f"❌ Error querying recent spans: {e}")
        
        # Method 3: Try direct DataFrame export (fallback)
        print("\n3. Using get_spans_dataframe (fallback method)...")
        try:
            fallback_spans = client.get_spans_dataframe()
            
            if fallback_spans is not None and not fallback_spans.empty:
                print(f"✅ Found {len(fallback_spans)} spans via get_spans_dataframe")
                
                # Check if this method returns different results
                if 'all_spans_df' in locals():
                    if len(fallback_spans) != len(all_spans_df):
                        print(f"   ⚠️ Different count than query_spans!")
                        print(f"   This suggests different filtering behavior")
                
        except Exception as e:
            print(f"❌ Error with get_spans_dataframe: {e}")
        
        # Method 4: Try to access raw OTLP data if available
        print("\n4. Checking for raw trace data access...")
        try:
            # Check if Phoenix stores data locally
            phoenix_dir = Path.home() / ".phoenix"
            if phoenix_dir.exists():
                print(f"✅ Found Phoenix data directory: {phoenix_dir}")
                
                # Look for SQLite database
                db_files = list(phoenix_dir.glob("**/*.db"))
                for db_file in db_files[:3]:  # Limit to first 3
                    print(f"   - Database: {db_file}")
                    
                # Look for trace files
                trace_files = list(phoenix_dir.glob("**/*.jsonl"))
                for trace_file in trace_files[:3]:  # Limit to first 3
                    print(f"   - Trace file: {trace_file}")
            else:
                print("⚠️ Phoenix data directory not found")
                
        except Exception as e:
            print(f"⚠️ Could not check for raw data: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("Export Summary:")
        print(f"Export directory: {export_dir.absolute()}")
        
        print("\nFiles created:")
        for file in sorted(export_dir.glob(f"*{timestamp}*")):
            size_mb = file.stat().st_size / 1024 / 1024
            print(f"  - {file.name} ({size_mb:.2f} MB)")
        
        print("\n💡 FINDINGS:")
        print("- If ChromaDB spans are visible in UI but not in exports,")
        print("  this is likely a Phoenix export limitation")
        print("- Consider using OpenTelemetry direct export as alternative")
        print("- Or access Phoenix's internal database directly")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    export_all_spans_complete()