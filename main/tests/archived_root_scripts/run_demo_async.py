#!/usr/bin/env python3
"""
Demo runner with proper async execution
"""
import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

async def run_demo():
    # Import after env is loaded
    from main import run_with_event_logging, parse_arguments
    from pathlib import Path
    
    # Setup args
    class Args:
        def __init__(self):
            self.verbose = True
            self.categorization_only = False
            self.disable_parallel_coordination = False
            self.confidence_threshold = 0.60
            self.enable_document_processing = False
            self.no_logging = False
            self.log_dir = "logs"
            self.consult = False
            self.list_consultations = False
            self.respond_to = None
    
    args = Args()
    document_path = Path(r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\urs_corpus\category_3\URS-001.md")
    
    print(f"Running demonstration with {document_path.name}")
    await run_with_event_logging(document_path, args)
    print("Demo completed!")

if __name__ == "__main__":
    asyncio.run(run_demo())