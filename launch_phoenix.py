#!/usr/bin/env python3
"""Launch Phoenix server for observability monitoring."""

import os
import sys
import phoenix as px
from phoenix.server.main import serve
import logging

# Set encoding to handle Unicode characters
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Launch Phoenix server."""
    try:
        logger.info("Starting Phoenix server...")
        
        # Set Phoenix configuration
        host = "localhost"
        port = 6006
        
        logger.info(f"Launching Phoenix at http://{host}:{port}")
        
        # Launch Phoenix server
        session = px.launch_app(
            host=host,
            port=port,
            primary_dataset=None,
            reference_dataset=None,
            trace=None,
            corpus=None,
        )
        
        print(f"✓ Phoenix server running at: {session.url}")
        print(f"✓ OpenTelemetry endpoint: http://{host}:{port}/v1/traces")
        print(f"✓ Project: test_generation_thesis")
        print("✓ Server is ready to accept traces")
        
        # Keep the server running
        print("\nPress Ctrl+C to stop the server")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down Phoenix server...")
            
    except Exception as e:
        logger.error(f"Failed to start Phoenix server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()