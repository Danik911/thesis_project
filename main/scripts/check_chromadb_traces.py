#!/usr/bin/env python3
"""
Check if ChromaDB traces are being captured in Phoenix.
"""

import sys
from pathlib import Path
import time

# Fix Windows Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import phoenix as px
import pandas as pd


def check_chromadb_traces():
    """Check for ChromaDB traces in Phoenix."""
    
    print("Checking for ChromaDB traces in Phoenix")
    print("=" * 50)
    
    try:
        # Connect to Phoenix
        client = px.Client()
        print("✅ Connected to Phoenix")
        
        # Method 1: Get all spans without filter (avoid timeout)
        print("\n1. Getting all recent spans...")
        all_spans = client.get_spans_dataframe()
        
        if all_spans is not None and not all_spans.empty:
            print(f"✅ Found {len(all_spans)} total spans")
            
            # Check for ChromaDB in span names
            print("\n2. Searching for ChromaDB spans...")
            chromadb_spans = all_spans[
                all_spans['name'].str.contains('chromadb', case=False, na=False)
            ]
            
            if not chromadb_spans.empty:
                print(f"✅ Found {len(chromadb_spans)} ChromaDB spans!")
                print("\nChromaDB operation types:")
                for name in chromadb_spans['name'].unique():
                    count = len(chromadb_spans[chromadb_spans['name'] == name])
                    print(f"  - {name}: {count} spans")
                    
                # Show sample attributes
                print("\nSample ChromaDB span attributes:")
                sample_span = chromadb_spans.iloc[0]
                for col in chromadb_spans.columns:
                    if col.startswith('attributes.') and pd.notna(sample_span[col]):
                        print(f"  - {col}: {sample_span[col]}")
                        
            else:
                print("❌ No ChromaDB spans found")
                
                # Check for other vector/retrieval operations
                print("\n3. Checking for vector/retrieval operations...")
                vector_keywords = ['vector', 'retriev', 'embed', 'collection', 'query', 'search']
                
                for keyword in vector_keywords:
                    keyword_spans = all_spans[
                        all_spans['name'].str.contains(keyword, case=False, na=False)
                    ]
                    if not keyword_spans.empty:
                        print(f"  - Found {len(keyword_spans)} spans containing '{keyword}'")
                        for name in keyword_spans['name'].unique()[:5]:
                            print(f"    • {name}")
                
                # Show all unique span names (limited)
                print("\n4. All span types found (first 20):")
                unique_names = all_spans['name'].unique()
                for i, name in enumerate(unique_names[:20]):
                    print(f"  - {name}")
                if len(unique_names) > 20:
                    print(f"  ... and {len(unique_names) - 20} more")
                    
        else:
            print("❌ No spans found in Phoenix")
            
        # Check span kinds
        if 'span_kind' in all_spans.columns:
            print("\n5. Span kinds distribution:")
            kind_counts = all_spans['span_kind'].value_counts()
            for kind, count in kind_counts.items():
                print(f"  - {kind}: {count}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_chromadb_traces()