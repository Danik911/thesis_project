#!/usr/bin/env python3
"""
Export ALL Phoenix traces including system traces (ChromaDB, etc.) not just LLM conversations.
The OpenAI Fine-Tuning JSONL export only includes ChatCompletion traces.
This script exports comprehensive trace data for full observability analysis.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import os

# Fix Windows Unicode issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import phoenix as px
except ImportError:
    print("ERROR: Phoenix not installed. Run: uv pip install arize-phoenix")
    sys.exit(1)


def export_all_traces():
    """Export all Phoenix traces using multiple methods to ensure completeness."""
    
    print("Phoenix Comprehensive Trace Export Utility")
    print("=" * 50)
    
    # Create export directory
    export_dir = Path("docs/reports/monitoring/phoenix_exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to Phoenix
        print("\nConnecting to Phoenix...")
        client = px.Client()
        print("✅ Connected to Phoenix successfully")
        
        # Method 1: Export all spans as DataFrame
        print("\n1. Exporting all spans as DataFrame...")
        try:
            all_spans_df = client.get_spans_dataframe()
            
            if all_spans_df is not None and not all_spans_df.empty:
                # Save as JSONL (one span per line)
                spans_jsonl_path = export_dir / f"phoenix_all_spans_{timestamp}.jsonl"
                all_spans_df.to_json(
                    spans_jsonl_path, 
                    orient='records', 
                    lines=True,
                    date_format='iso'
                )
                print(f"   ✅ Exported {len(all_spans_df)} spans to {spans_jsonl_path}")
                
                # Also save as CSV for easy viewing
                spans_csv_path = export_dir / f"phoenix_all_spans_{timestamp}.csv"
                all_spans_df.to_csv(spans_csv_path, index=False)
                print(f"   ✅ Also saved as CSV: {spans_csv_path}")
                
                # Show span types found
                if 'span_kind' in all_spans_df.columns:
                    span_types = all_spans_df['span_kind'].value_counts()
                    print("\n   Span types found:")
                    for span_type, count in span_types.items():
                        print(f"     - {span_type}: {count}")
                
                # Check for ChromaDB spans
                chromadb_count = 0
                if 'name' in all_spans_df.columns:
                    chromadb_spans = all_spans_df[
                        all_spans_df['name'].str.contains('chromadb', case=False, na=False)
                    ]
                    chromadb_count = len(chromadb_spans)
                    print(f"\n   ChromaDB spans found: {chromadb_count}")
                    
                    if chromadb_count > 0:
                        # Save ChromaDB spans separately
                        chromadb_path = export_dir / f"phoenix_chromadb_spans_{timestamp}.jsonl"
                        chromadb_spans.to_json(
                            chromadb_path,
                            orient='records',
                            lines=True,
                            date_format='iso'
                        )
                        print(f"   ✅ ChromaDB spans saved to: {chromadb_path}")
                
            else:
                print("   ⚠️ No spans found in Phoenix")
                
        except Exception as e:
            print(f"   ❌ Error exporting spans: {e}")
        
        # Method 2: Export trace dataset
        print("\n2. Exporting complete trace dataset...")
        try:
            trace_dataset = client.get_trace_dataset()
            
            if trace_dataset:
                # Save trace dataset
                trace_path = export_dir / f"phoenix_trace_dataset_{timestamp}.jsonl"
                trace_dataset.save(str(trace_path))
                print(f"   ✅ Trace dataset saved to: {trace_path}")
                
                # Try to get dataset info
                try:
                    # Load and analyze the saved file
                    with open(trace_path, 'r') as f:
                        trace_count = sum(1 for _ in f)
                    print(f"   ✅ Total traces in dataset: {trace_count}")
                except:
                    pass
            else:
                print("   ⚠️ No trace dataset available")
                
        except Exception as e:
            print(f"   ❌ Error exporting trace dataset: {e}")
        
        # Method 3: Query specific span types
        print("\n3. Querying specific span types...")
        
        span_queries = {
            "LLM spans": "span_kind == 'LLM'",
            "ChromaDB spans": "attributes['vendor'] == 'chromadb'",
            "Retriever spans": "span_kind == 'RETRIEVER'",
            "Chain spans": "span_kind == 'CHAIN'",
            "Tool spans": "span_kind == 'TOOL'",
            "Agent spans": "span_kind == 'AGENT'",
        }
        
        for span_type, query in span_queries.items():
            try:
                print(f"\n   Querying {span_type}...")
                spans = client.get_spans_dataframe(query)
                
                if spans is not None and not spans.empty:
                    filename = span_type.lower().replace(' ', '_')
                    span_path = export_dir / f"phoenix_{filename}_{timestamp}.jsonl"
                    spans.to_json(
                        span_path,
                        orient='records',
                        lines=True,
                        date_format='iso'
                    )
                    print(f"   ✅ Found {len(spans)} {span_type} → {span_path}")
                else:
                    print(f"   ⚠️ No {span_type} found")
                    
            except Exception as e:
                print(f"   ❌ Error querying {span_type}: {e}")
        
        # Method 4: Export with attributes
        print("\n4. Checking for spans with specific attributes...")
        
        attribute_queries = {
            "Spans with ChromaDB collection": "attributes['collection'] IS NOT NULL",
            "Spans with document count": "attributes['document_count'] IS NOT NULL",
            "Spans with retrieval score": "attributes['score'] IS NOT NULL",
            "Spans with embeddings": "attributes['embedding'] IS NOT NULL",
        }
        
        for attr_type, query in attribute_queries.items():
            try:
                spans = client.get_spans_dataframe(query)
                if spans is not None and not spans.empty:
                    print(f"   ✅ {attr_type}: {len(spans)} spans")
            except:
                pass
        
        # Summary
        print("\n" + "=" * 50)
        print("Export Summary:")
        print(f"Export directory: {export_dir.absolute()}")
        print("\nFiles created:")
        for file in sorted(export_dir.glob(f"*{timestamp}*")):
            size_mb = file.stat().st_size / 1024 / 1024
            print(f"  - {file.name} ({size_mb:.2f} MB)")
        
        print("\n✅ Export complete!")
        print("\nNOTE: The OpenAI Fine-Tuning JSONL format only exports LLM conversations.")
        print("This script exports ALL trace types for comprehensive analysis.")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Check if Phoenix is running
    print("Make sure Phoenix is running at http://localhost:6006")
    print("If not, run: python start_phoenix.py\n")
    
    success = export_all_traces()
    sys.exit(0 if success else 1)