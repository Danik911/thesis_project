"""
Main entry point for the GAMP-5 Pharmaceutical Test Generation System.

This module provides the primary interface for running the multi-agent system
with proper event logging and GAMP-5 compliance features.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Core workflow
from src.core.categorization_workflow import GAMPCategorizationWorkflow, run_categorization_workflow

# Event logging
from src.shared import (
    setup_event_logging,
    run_workflow_with_event_logging,
    get_config,
    Config
)

# Utilities
from src.shared.utils import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GAMP-5 Pharmaceutical Test Generation System"
    )
    
    parser.add_argument(
        "document",
        nargs="?",
        help="Path to the URS document to categorize"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-logging",
        action="store_true",
        help="Disable event logging"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files (default: logs)"
    )
    
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.60,
        help="Confidence threshold for categorization (default: 0.60)"
    )
    
    parser.add_argument(
        "--enable-document-processing",
        action="store_true",
        help="Enable LlamaParse document processing"
    )
    
    return parser.parse_args()


async def run_with_event_logging(document_path: Path, args):
    """Run the workflow with full event logging integration."""
    # Setup configuration
    config = get_config()
    config.logging.log_directory = args.log_dir
    # Don't override the log_level here - it's already set from config
    config.gamp5_compliance.audit_log_directory = f"{args.log_dir}/audit"
    
    # Create directories
    Path(config.logging.log_directory).mkdir(parents=True, exist_ok=True)
    Path(config.gamp5_compliance.audit_log_directory).mkdir(parents=True, exist_ok=True)
    
    # Setup event logging
    print("📊 Setting up event logging system...")
    event_handler = setup_event_logging(config)
    
    # Create workflow
    workflow = GAMPCategorizationWorkflow(
        timeout=300,
        verbose=args.verbose,
        enable_error_handling=True,
        confidence_threshold=args.confidence_threshold,
        enable_document_processing=args.enable_document_processing
    )
    
    # Load document
    if document_path.exists():
        print(f"📄 Loading document: {document_path}")
        if document_path.suffix in ['.md', '.txt', '.rst']:
            document_content = document_path.read_text()
        else:
            # For other file types, pass the path
            document_content = str(document_path)
    else:
        raise FileNotFoundError(f"Document not found: {document_path}")
    
    # Run workflow with event logging
    print(f"\n🚀 Running GAMP-5 categorization with event logging...")
    result, events = await run_workflow_with_event_logging(
        workflow,
        event_handler,
        urs_content=document_content,
        document_name=document_path.name
    )
    
    # Display results
    if result:
        summary = result.get("summary", {})
        print(f"\n✅ Categorization Complete!")
        print(f"  - Category: {summary.get('category', 'Unknown')}")
        print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
        print(f"  - Review Required: {summary.get('review_required', False)}")
        print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
        
        # Event statistics
        print(f"\n📊 Event Logging Summary:")
        print(f"  - Events Captured: {len(events)}")
        stats = event_handler.get_statistics()
        print(f"  - Events Processed: {stats['events_processed']}")
        print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")
        
        # Compliance statistics
        compliance_stats = event_handler.compliance_logger.get_audit_statistics()
        print(f"\n🔒 GAMP-5 Compliance:")
        print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
        print(f"  - Compliance Standards: {', '.join(compliance_stats['compliance_standards'])}")
        
        # Log file locations
        print(f"\n📁 Log Files:")
        print(f"  - Events: {config.logging.log_directory}/")
        print(f"  - Audit: {config.gamp5_compliance.audit_log_directory}/")
        
        return result
    else:
        print("\n❌ Workflow failed to produce results")
        return None


async def run_without_logging(document_path: Path, args):
    """Run the workflow without event logging (simpler mode)."""
    # Load document
    if document_path.exists():
        print(f"📄 Loading document: {document_path}")
        document_content = document_path.read_text()
    else:
        raise FileNotFoundError(f"Document not found: {document_path}")
    
    # Run workflow directly
    print(f"\n🚀 Running GAMP-5 categorization...")
    result = await run_categorization_workflow(
        urs_content=document_content,
        document_name=document_path.name,
        enable_error_handling=True,
        verbose=args.verbose,
        confidence_threshold=args.confidence_threshold,
        enable_document_processing=args.enable_document_processing
    )
    
    # Display results
    if result:
        summary = result.get("summary", {})
        print(f"\n✅ Categorization Complete!")
        print(f"  - Category: {summary.get('category', 'Unknown')}")
        print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
        print(f"  - Review Required: {summary.get('review_required', False)}")
        print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
        
        return result
    else:
        print("\n❌ Workflow failed to produce results")
        return None


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    print("🏥 GAMP-5 Pharmaceutical Test Generation System")
    print("=" * 60)
    
    # Determine document path
    if args.document:
        document_path = Path(args.document)
    else:
        # Use default test document
        document_path = Path(__file__).parent.parent / "simple_test_data.md"
        if not document_path.exists():
            print("❌ No document specified and default test document not found")
            print("Usage: python main.py <document_path>")
            return 1
    
    try:
        # Run with or without event logging
        if args.no_logging:
            result = await run_without_logging(document_path, args)
        else:
            result = await run_with_event_logging(document_path, args)
        
        # Return appropriate exit code
        if result:
            return 0
        else:
            return 1
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the async main function
    sys.exit(asyncio.run(main()))