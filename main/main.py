"""
Main entry point for the GAMP-5 Pharmaceutical Test Generation System.

This module provides the primary interface for running the multi-agent system
with proper event logging and GAMP-5 compliance features.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Core workflows
from src.core.categorization_workflow import (
    GAMPCategorizationWorkflow,
    run_categorization_workflow,
)
from src.core.unified_workflow import (
    UnifiedTestGenerationWorkflow,
    run_unified_test_generation_workflow,
)

# Event logging
from src.shared import (
    get_config,
    run_workflow_with_event_logging,
    setup_event_logging,
)
from src.shared.output_manager import (
    TruncatedStreamHandler,
    get_output_manager,
    safe_print,
    truncate_string,
)

# Utilities
from src.shared.utils import setup_logging


def setup_safe_output_management():
    """Setup safe output management to prevent Claude Code overflow."""

    # Get output manager and configure
    output_manager = get_output_manager()

    # Replace root logger handlers with truncated handlers
    root_logger = logging.getLogger()

    # Remove existing console handlers
    console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
    for handler in console_handlers:
        root_logger.removeHandler(handler)

    # Add truncated stream handler
    truncated_handler = TruncatedStreamHandler()
    truncated_handler.setLevel(logging.WARNING)  # Reduce verbosity
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    truncated_handler.setFormatter(formatter)
    root_logger.addHandler(truncated_handler)

    return output_manager


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GAMP-5 Pharmaceutical Test Generation System"
    )

    parser.add_argument(
        "document",
        nargs="?",
        help="Path to the URS document to process (categorization + test generation by default)"
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

    parser.add_argument(
        "--categorization-only",
        action="store_true",
        help="Run only GAMP-5 categorization (skip planning and agent coordination)"
    )

    parser.add_argument(
        "--disable-parallel-coordination",
        action="store_true",
        help="Disable parallel agent coordination in planning workflow"
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
    safe_print("📊 Setting up event logging system...")
    event_handler = setup_event_logging(config)

    # Determine workflow type
    if args.categorization_only:
        # Create categorization-only workflow
        workflow = GAMPCategorizationWorkflow(
            timeout=300,
            verbose=args.verbose,
            enable_error_handling=True,
            confidence_threshold=args.confidence_threshold,
            enable_document_processing=args.enable_document_processing
        )
        workflow_type = "categorization"
    else:
        # Create unified workflow
        workflow = UnifiedTestGenerationWorkflow(
            timeout=900,  # 15 minutes for complete workflow
            verbose=args.verbose,
            enable_error_handling=True,
            confidence_threshold=args.confidence_threshold,
            enable_document_processing=args.enable_document_processing,
            enable_parallel_coordination=not args.disable_parallel_coordination
        )
        workflow_type = "unified"

    # Load document
    if document_path.exists():
        safe_print(f"📄 Loading document: {document_path}")
        if document_path.suffix in [".md", ".txt", ".rst"]:
            document_content = document_path.read_text()
        else:
            # For other file types, pass the path
            document_content = str(document_path)
    else:
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Run workflow with event logging
    if workflow_type == "categorization":
        safe_print("\n🚀 Running GAMP-5 categorization with event logging...")
    else:
        safe_print("\n🚀 Running unified test generation workflow with event logging...")
    result, events = await run_workflow_with_event_logging(
        workflow,
        event_handler,
        urs_content=document_content,
        document_name=document_path.name
    )

    # Display results
    if result:
        if workflow_type == "categorization":
            summary = result.get("summary", {})
            safe_print("\n✅ Categorization Complete!")
            safe_print(f"  - Category: {summary.get('category', 'Unknown')}")
            safe_print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
            safe_print(f"  - Review Required: {summary.get('review_required', False)}")
            safe_print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
        else:
            # Display unified workflow results
            summary = result.get("summary", {})
            categorization = result.get("categorization", {})
            planning = result.get("planning", {})
            consultation = result.get("consultation", {})

            safe_print("\n✅ Unified Test Generation Complete!")
            safe_print(f"  - Status: {summary.get('status', 'Unknown')}")
            safe_print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")

            if categorization.get("category"):
                safe_print(f"  - GAMP Category: {categorization['category']}")
                safe_print(f"  - Confidence: {categorization.get('confidence', 0):.1%}")
                safe_print(f"  - Review Required: {categorization.get('review_required', False)}")

            if summary.get("estimated_test_count"):
                safe_print(f"  - Estimated Tests: {summary['estimated_test_count']}")
                safe_print(f"  - Timeline: {summary.get('timeline_estimate_days', 'N/A')} days")
                safe_print(f"  - Agents Coordinated: {summary.get('agents_coordinated', 0)}")
                safe_print(f"  - Agent Success Rate: {summary.get('coordination_success_rate', 0):.1%}")

            if consultation.get("required"):
                safe_print(f"  - Consultation Required: {consultation['event'].consultation_type}")
                safe_print(f"  - Urgency: {consultation['event'].urgency}")

        # Event statistics
        safe_print("\n📊 Event Logging Summary:")
        safe_print(f"  - Events Captured: {len(events)}")
        stats = event_handler.get_statistics()
        safe_print(f"  - Events Processed: {stats['events_processed']}")
        safe_print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")

        # Compliance statistics
        compliance_stats = event_handler.compliance_logger.get_audit_statistics()
        safe_print("\n🔒 GAMP-5 Compliance:")
        safe_print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
        safe_print(f"  - Compliance Standards: {', '.join(compliance_stats['compliance_standards'])}")

        # Log file locations
        safe_print("\n📁 Log Files:")
        safe_print(f"  - Events: {config.logging.log_directory}/")
        safe_print(f"  - Audit: {config.gamp5_compliance.audit_log_directory}/")

        # Output management statistics
        output_stats = get_output_manager().get_output_stats()
        safe_print("\n📈 Output Management:")
        safe_print(f"  - Console Output Used: {output_stats['total_output_size']} / {output_stats['max_console_output']} bytes")
        safe_print(f"  - Usage: {output_stats['usage_percentage']:.1f}%")
        if output_stats["truncated"]:
            safe_print("  - ⚠️  Output was truncated to prevent overflow")

        return result
    safe_print("\n❌ Workflow failed to produce results")
    return None


async def run_without_logging(document_path: Path, args):
    """Run the workflow without event logging (simpler mode)."""
    # Load document
    if document_path.exists():
        safe_print(f"📄 Loading document: {document_path}")
        if document_path.suffix in [".md", ".txt", ".rst"]:
            document_content = document_path.read_text()
        else:
            # For other file types, pass the path
            document_content = str(document_path)
    else:
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Determine workflow type and run
    if args.categorization_only:
        safe_print("\n🚀 Running GAMP-5 categorization...")
        result = await run_categorization_workflow(
            urs_content=document_content,
            document_name=document_path.name,
            enable_error_handling=True,
            verbose=args.verbose,
            confidence_threshold=args.confidence_threshold,
            enable_document_processing=args.enable_document_processing
        )
    else:
        safe_print("\n🚀 Running unified test generation workflow...")
        result = await run_unified_test_generation_workflow(
            urs_content=document_content,
            document_name=document_path.name,
            document_version="1.0",
            author="system",
            timeout=900,
            verbose=args.verbose,
            enable_error_handling=True,
            confidence_threshold=args.confidence_threshold,
            enable_document_processing=args.enable_document_processing,
            enable_parallel_coordination=not args.disable_parallel_coordination
        )

    # Display results
    if result:
        if args.categorization_only:
            summary = result.get("summary", {})
            safe_print("\n✅ Categorization Complete!")
            safe_print(f"  - Category: {summary.get('category', 'Unknown')}")
            safe_print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
            safe_print(f"  - Review Required: {summary.get('review_required', False)}")
            safe_print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
        else:
            # Display unified workflow results
            summary = result.get("summary", {})
            categorization = result.get("categorization", {})
            planning = result.get("planning", {})
            consultation = result.get("consultation", {})

            safe_print("\n✅ Unified Test Generation Complete!")
            safe_print(f"  - Status: {summary.get('status', 'Unknown')}")
            safe_print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")

            if categorization.get("category"):
                safe_print(f"  - GAMP Category: {categorization['category']}")
                safe_print(f"  - Confidence: {categorization.get('confidence', 0):.1%}")
                safe_print(f"  - Review Required: {categorization.get('review_required', False)}")

            if summary.get("estimated_test_count"):
                safe_print(f"  - Estimated Tests: {summary['estimated_test_count']}")
                safe_print(f"  - Timeline: {summary.get('timeline_estimate_days', 'N/A')} days")
                safe_print(f"  - Agents Coordinated: {summary.get('agents_coordinated', 0)}")
                safe_print(f"  - Agent Success Rate: {summary.get('coordination_success_rate', 0):.1%}")

            if consultation.get("required"):
                safe_print(f"  - Consultation Required: {consultation['event'].consultation_type}")
                safe_print(f"  - Urgency: {consultation['event'].urgency}")

        return result
    workflow_name = "Categorization" if args.categorization_only else "Unified workflow"
    safe_print(f"\n❌ {workflow_name} failed to produce results")
    return None


async def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup safe output management first
    output_manager = setup_safe_output_management()

    # Setup logging with reduced verbosity
    log_level = "WARNING" if not args.verbose else "INFO"  # Reduced default verbosity
    setup_logging(log_level)

    safe_print("🏥 GAMP-5 Pharmaceutical Test Generation System")
    if args.categorization_only:
        safe_print("📋 Running in Categorization-Only Mode")
    else:
        safe_print("🚀 Running Unified Test Generation Workflow")
    safe_print("=" * 60)

    # Determine document path
    if args.document:
        document_path = Path(args.document)
    else:
        # Use default test document
        document_path = Path(__file__).parent.parent / "simple_test_data.md"
        if not document_path.exists():
            safe_print("❌ No document specified and default test document not found")
            safe_print("Usage: python main.py <document_path>")
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
        return 1

    except FileNotFoundError as e:
        safe_print(f"\n❌ Error: {e}")
        return 1
    except KeyboardInterrupt:
        safe_print("\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        error_msg = truncate_string(str(e), 300)  # Truncate long error messages
        safe_print(f"\n❌ Unexpected error: {error_msg}")
        if args.verbose:
            import traceback
            # Limit traceback output
            tb_lines = traceback.format_exc().split("\n")
            if len(tb_lines) > 20:  # Limit traceback lines
                tb_output = "\n".join(tb_lines[:10] + ["... [TRACEBACK TRUNCATED] ..."] + tb_lines[-5:])
            else:
                tb_output = "\n".join(tb_lines)
            safe_print(truncate_string(tb_output, 2000))
        return 1
    finally:
        # Ensure Phoenix observability is properly shut down
        if not args.no_logging:
            try:
                from src.shared.event_logging import shutdown_event_logging
                shutdown_event_logging()
                safe_print("\n🔒 Phoenix observability shutdown complete")
            except Exception as shutdown_error:
                safe_print(f"\n⚠️  Warning: Error during Phoenix shutdown: {shutdown_error}")


if __name__ == "__main__":
    # Run the async main function
    sys.exit(asyncio.run(main()))
