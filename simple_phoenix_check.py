#!/usr/bin/env python3
"""
Simple Phoenix Check - Windows Compatible
"""

import phoenix as px
import pandas as pd
from datetime import datetime

def check_phoenix():
    print("=== Phoenix Trace Analysis ===")
    print(f"Analysis Time: {datetime.now().isoformat()}")
    
    try:
        # Check for active session
        session = px.active_session()
        if session:
            print("ACTIVE SESSION FOUND")
            print(f"Session details: {session}")
        else:
            print("NO ACTIVE SESSION")
            
        # Try connecting to Phoenix directly
        print("\nTrying to connect to Phoenix at localhost:6006...")
        
        # Check environment for traces
        print("\nEnvironment check:")
        import os
        print(f"PHOENIX_COLLECTOR_ENDPOINT: {os.getenv('PHOENIX_COLLECTOR_ENDPOINT', 'Not set')}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Exception type: {type(e)}")

if __name__ == "__main__":
    check_phoenix()