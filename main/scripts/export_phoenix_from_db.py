#!/usr/bin/env python3
"""
Export Phoenix traces directly from the SQLite database to get ALL spans including ChromaDB.
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Fix Windows Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def explore_phoenix_database():
    """Explore Phoenix SQLite database structure and export all traces."""
    
    print("Phoenix Database Direct Export")
    print("=" * 50)
    
    # Find Phoenix database
    phoenix_db = Path.home() / ".phoenix" / "phoenix.db"
    
    if not phoenix_db.exists():
        print(f"❌ Phoenix database not found at: {phoenix_db}")
        return
    
    print(f"✅ Found Phoenix database: {phoenix_db}")
    print(f"   Size: {phoenix_db.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Create export directory
    export_dir = Path("docs/reports/monitoring/phoenix_exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to database
        conn = sqlite3.connect(phoenix_db)
        cursor = conn.cursor()
        
        # 1. List all tables
        print("\n1. Database tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} rows")
        
        # 2. Explore spans table structure
        print("\n2. Exploring spans table...")
        cursor.execute("PRAGMA table_info(spans);")
        columns = cursor.fetchall()
        
        print("   Columns:")
        for col in columns[:10]:  # Show first 10 columns
            print(f"     - {col[1]} ({col[2]})")
        if len(columns) > 10:
            print(f"     ... and {len(columns) - 10} more columns")
        
        # 3. Sample spans to understand structure
        print("\n3. Sample span data...")
        cursor.execute("""
            SELECT 
                span_id,
                name,
                span_kind,
                parent_id,
                start_time,
                attributes
            FROM spans 
            LIMIT 5
        """)
        
        sample_spans = cursor.fetchall()
        for span in sample_spans:
            print(f"\n   Span: {span[0]}")
            print(f"   Name: {span[1]}")
            print(f"   Kind: {span[2]}")
            if span[5]:  # attributes
                try:
                    attrs = json.loads(span[5]) if isinstance(span[5], str) else span[5]
                    print(f"   Attributes: {list(attrs.keys())[:5]}...")
                except:
                    print(f"   Attributes: {str(span[5])[:100]}...")
        
        # 4. Look for ChromaDB spans
        print("\n4. Searching for ChromaDB spans...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spans 
            WHERE LOWER(name) LIKE '%chromadb%'
               OR LOWER(name) LIKE '%vector%'
               OR LOWER(name) LIKE '%collection%'
               OR LOWER(name) LIKE '%embed%'
        """)
        
        chromadb_count = cursor.fetchone()[0]
        print(f"   Found {chromadb_count} potential ChromaDB/vector spans")
        
        if chromadb_count > 0:
            # Get sample ChromaDB spans
            cursor.execute("""
                SELECT span_id, name, span_kind, attributes
                FROM spans 
                WHERE LOWER(name) LIKE '%chromadb%'
                   OR LOWER(name) LIKE '%vector%'
                   OR LOWER(name) LIKE '%collection%'
                LIMIT 5
            """)
            
            chromadb_spans = cursor.fetchall()
            print("\n   Sample ChromaDB/vector spans:")
            for span in chromadb_spans:
                print(f"     - {span[1]} ({span[2]})")
        
        # 5. Export ALL spans
        print("\n5. Exporting ALL spans from database...")
        
        # Get all spans with full data
        query = """
            SELECT 
                span_id,
                trace_id,
                parent_id,
                name,
                span_kind,
                start_time,
                end_time,
                attributes,
                events,
                status_code,
                status_message,
                cumulative_error_count,
                cumulative_llm_token_count_prompt,
                cumulative_llm_token_count_completion
            FROM spans
            ORDER BY start_time DESC
        """
        
        # Export to DataFrame
        df = pd.read_sql_query(query, conn)
        print(f"   Loaded {len(df)} spans from database")
        
        # Parse JSON fields
        for json_col in ['attributes', 'events']:
            if json_col in df.columns:
                df[json_col] = df[json_col].apply(
                    lambda x: json.loads(x) if x and isinstance(x, str) else x
                )
        
        # Save to file
        export_path = export_dir / f"phoenix_db_all_spans_{timestamp}.jsonl"
        df.to_json(
            export_path,
            orient='records',
            lines=True,
            date_format='iso',
            default_handler=str
        )
        print(f"   ✅ Exported to: {export_path}")
        
        # Also save ChromaDB spans separately if found
        if chromadb_count > 0:
            chromadb_df = df[
                df['name'].str.contains('chromadb|vector|collection|embed', case=False, na=False, regex=True)
            ]
            
            if not chromadb_df.empty:
                chromadb_path = export_dir / f"phoenix_db_chromadb_spans_{timestamp}.jsonl"
                chromadb_df.to_json(
                    chromadb_path,
                    orient='records',
                    lines=True,
                    date_format='iso',
                    default_handler=str
                )
                print(f"   ✅ ChromaDB spans exported to: {chromadb_path}")
        
        # 6. Analyze span types
        print("\n6. Span type analysis:")
        span_kinds = df['span_kind'].value_counts()
        for kind, count in span_kinds.items():
            print(f"   - {kind}: {count}")
        
        # Check for different span names
        print("\n7. Unique span names (first 20):")
        unique_names = df['name'].unique()
        for i, name in enumerate(unique_names[:20]):
            print(f"   - {name}")
        if len(unique_names) > 20:
            print(f"   ... and {len(unique_names) - 20} more")
        
        # Close connection
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Direct database export complete!")
        print(f"Total spans exported: {len(df)}")
        
    except Exception as e:
        print(f"\n❌ Error accessing database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    explore_phoenix_database()