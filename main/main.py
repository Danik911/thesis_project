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

# Initialize Phoenix observability before any other imports to ensure proper instrumentation
import os

if os.getenv("PHOENIX_ENABLE_TRACING", "true").lower() == "true":
    try:
        from src.monitoring.phoenix_config import setup_phoenix
        phoenix_manager = setup_phoenix()
        print("🔭 Phoenix observability initialized - LLM calls will be traced")
    except Exception as e:
        print(f"⚠️  Phoenix initialization failed: {e}")
        # Continue without Phoenix - don't fail the application

def setup_unicode_support():
    """
    Configure proper Unicode support for Windows console to prevent encoding crashes.
    
    This is critical for pharmaceutical systems that must handle Unicode characters
    in documentation and user interfaces without fallback masking.
    """
    try:
        import os

        # Set UTF-8 environment variable (Python 3.7+)
        os.environ.setdefault("PYTHONUTF8", "1")

        # Reconfigure stdout and stderr for UTF-8 on Windows
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="strict")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="strict")

        # Verify Unicode support
        test_unicode = "🧑‍⚕️ GAMP-5 Test: ✅ ❌ 📋 🔍 ⚡"

        # Test print capability - fail explicitly if Unicode not supported
        try:
            print(test_unicode)
            return True
        except UnicodeEncodeError as e:
            raise UnicodeEncodeError(
                e.encoding, e.object, e.start, e.end,
                f"Console does not support Unicode characters required for pharmaceutical UI. "
                f"Configure PYTHONUTF8=1 environment variable or use a UTF-8 capable terminal. "
                f"Error: {e.reason}"
            ) from e

    except Exception as e:
        # NO FALLBACKS - pharmaceutical systems must handle Unicode properly
        raise RuntimeError(
            f"Failed to configure Unicode support for pharmaceutical compliance system. "
            f"Unicode characters are required for regulatory interface. Error: {e}"
        ) from e

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Core workflows
from uuid import UUID

from src.core.categorization_workflow import (
    GAMPCategorizationWorkflow,
    run_categorization_workflow,
)
from src.core.events import HumanResponseEvent

# Human consultation system
from src.core.human_consultation import HumanConsultationManager
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


def setup_unicode_support():
    """
    Configure proper Unicode support for Windows console.
    
    This function addresses critical Unicode encoding issues by configuring
    Python's standard streams to use UTF-8 encoding, preventing UnicodeEncodeError
    crashes when printing Unicode characters (like emojis) on Windows systems.
    
    NO FALLBACKS: This function ensures proper Unicode support or fails explicitly
    with diagnostic information, in compliance with pharmaceutical system requirements.
    """
    import os
    import sys

    try:
        # Method 1: Configure UTF-8 mode via environment (most comprehensive)
        if not os.environ.get("PYTHONUTF8"):
            os.environ["PYTHONUTF8"] = "1"

        # Method 2: Reconfigure standard streams for UTF-8 (Python 3.7+)
        if hasattr(sys.stdout, "reconfigure"):
            # Check current encoding
            current_encoding = getattr(sys.stdout, "encoding", "unknown")
            if current_encoding.lower() not in ["utf-8", "utf8"]:
                sys.stdout.reconfigure(encoding="utf-8", errors="strict")
                sys.stderr.reconfigure(encoding="utf-8", errors="strict")
                # Note: stdin reconfiguration can cause issues, so we skip it

        # Verify configuration with actual test characters
        test_unicode = "🧑‍⚕️✅📋"  # Test characters that were causing crashes
        try:
            # Test if we can actually print unicode to stdout
            print(test_unicode)  # Direct test without safe_print to avoid recursion
            # If we get here, Unicode is working
        except UnicodeEncodeError as e:
            error_msg = (
                f"CRITICAL: Unicode configuration failed verification.\n"
                f"Test characters: {test_unicode!r}\n"
                f"Current stdout encoding: {getattr(sys.stdout, 'encoding', 'unknown')}\n"
                f"Error: {e}\n"
                f"Platform: {sys.platform}\n"
                f"SOLUTION: Ensure Windows Terminal or configure system for UTF-8 support"
            )
            safe_print(error_msg)
            raise RuntimeError("Unicode configuration verification failed - system cannot handle required characters") from e

    except Exception as e:
        error_msg = (
            f"CRITICAL: Unable to configure Unicode support.\n"
            f"Error: {e}\n"
            f"Platform: {sys.platform}\n"
            f"This will cause crashes when consultation workflow runs.\n"
            f"SOLUTION: Use Windows Terminal or configure PYTHONUTF8=1 environment variable"
        )
        safe_print(error_msg)
        raise RuntimeError("Unicode configuration failed - pharmaceutical system requires Unicode support") from e


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

    # Human consultation commands
    parser.add_argument(
        "--consult",
        action="store_true",
        help="Enter human consultation interface mode"
    )

    parser.add_argument(
        "--list-consultations",
        action="store_true",
        help="List active consultations"
    )

    parser.add_argument(
        "--respond-to",
        type=str,
        help="Respond to consultation by ID"
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
            # Read with explicit UTF-8 encoding to handle Unicode characters
            document_content = document_path.read_text(encoding="utf-8")
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
        document_name=document_path.name,
        document_version="1.0",
        author="system"
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

                # Show accurate agent execution information
                agents_executed = summary.get("agents_coordinated", 0)
                if agents_executed > 0:
                    success_rate = summary.get("coordination_success_rate", 0)
                    safe_print(f"  - Agents Executed: {agents_executed}")
                    safe_print(f"  - Agent Success Rate: {success_rate:.1%}")
                else:
                    safe_print("  - Active Agents: 2 (Categorization + Planner)")
                    safe_print("  - Parallel Agents: Not integrated (coordination requests generated only)")

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
            # Read with explicit UTF-8 encoding to handle Unicode characters
            document_content = document_path.read_text(encoding="utf-8")
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

                # Show accurate agent execution information
                agents_executed = summary.get("agents_coordinated", 0)
                if agents_executed > 0:
                    success_rate = summary.get("coordination_success_rate", 0)
                    safe_print(f"  - Agents Executed: {agents_executed}")
                    safe_print(f"  - Agent Success Rate: {success_rate:.1%}")
                else:
                    safe_print("  - Active Agents: 2 (Categorization + Planner)")
                    safe_print("  - Parallel Agents: Not integrated (coordination requests generated only)")

            if consultation.get("required"):
                safe_print(f"  - Consultation Required: {consultation['event'].consultation_type}")
                safe_print(f"  - Urgency: {consultation['event'].urgency}")

        return result
    workflow_name = "Categorization" if args.categorization_only else "Unified workflow"
    safe_print(f"\n❌ {workflow_name} failed to produce results")
    return None


async def run_consultation_interface():
    """Run the human consultation interface."""
    import sys

    # Check if running in interactive terminal
    if not sys.stdin.isatty():
        safe_print("❌ Consultation interface requires an interactive terminal")
        safe_print("💡 Run this command in an interactive shell, not through scripts or timeouts")
        return

    safe_print("🧑‍⚕️ Human Consultation Interface")
    safe_print("=" * 40)

    config = get_config()
    manager = HumanConsultationManager(config)

    while True:
        safe_print("\nAvailable commands:")
        safe_print("1. List active consultations")
        safe_print("2. View consultation details")
        safe_print("3. Respond to consultation")
        safe_print("4. Exit")

        try:
            choice = input("\nEnter choice (1-4): ").strip()

            if choice == "1":
                await list_active_consultations(manager)
            elif choice == "2":
                await view_consultation_details(manager)
            elif choice == "3":
                await respond_to_consultation(manager)
            elif choice == "4":
                safe_print("👋 Exiting consultation interface")
                break
            else:
                safe_print("❌ Invalid choice. Please enter 1-4.")

        except KeyboardInterrupt:
            safe_print("\n👋 Exiting consultation interface")
            break
        except EOFError:
            safe_print("\n👋 No more input available - exiting consultation interface")
            break
        except Exception as e:
            safe_print(f"❌ Unexpected error: {e}")
            break

async def list_active_consultations(manager: HumanConsultationManager):
    """List active consultations."""
    if not manager.active_sessions:
        safe_print("📋 No active consultations")
        return

    safe_print(f"📋 Active Consultations ({len(manager.active_sessions)}):")
    for session_id, session in manager.active_sessions.items():
        info = session.get_session_info()
        safe_print(f"  📄 {session_id}")
        safe_print(f"     Type: {info['consultation_type']}")
        safe_print(f"     Urgency: {info['urgency']}")
        safe_print(f"     Status: {info['status']}")
        safe_print(f"     Duration: {info['duration_seconds']:.1f}s")

async def view_consultation_details(manager: HumanConsultationManager):
    """View details of a specific consultation."""
    if not manager.active_sessions:
        safe_print("📋 No active consultations")
        return

    try:
        session_id = input("Enter consultation session ID: ").strip()
    except (EOFError, KeyboardInterrupt):
        safe_print("\n👋 Cancelled")
        return

    try:
        session_uuid = UUID(session_id)
        if session_uuid in manager.active_sessions:
            session = manager.active_sessions[session_uuid]
            info = session.get_session_info()

            safe_print("\n📄 Consultation Details:")
            safe_print(f"   Session ID: {info['session_id']}")
            safe_print(f"   Consultation ID: {info['consultation_id']}")
            safe_print(f"   Type: {info['consultation_type']}")
            safe_print(f"   Urgency: {info['urgency']}")
            safe_print(f"   Status: {info['status']}")
            safe_print(f"   Created: {info['created_at']}")
            safe_print(f"   Duration: {info['duration_seconds']:.1f}s")
            safe_print(f"   Timeout: {info['timeout_seconds']}s")
            safe_print(f"   Participants: {info['participants']}")
            safe_print(f"   Responses: {info['total_responses']}")

            # Show consultation context
            consultation_event = session.consultation_event
            safe_print("\n📝 Context:")
            for key, value in consultation_event.context.items():
                safe_print(f"   {key}: {value}")

        else:
            safe_print("❌ Consultation not found")

    except ValueError:
        safe_print("❌ Invalid session ID format")

async def respond_to_consultation(manager: HumanConsultationManager):
    """Respond to a consultation."""
    if not manager.active_sessions:
        safe_print("📋 No active consultations")
        return

    try:
        session_id = input("Enter consultation session ID: ").strip()
    except (EOFError, KeyboardInterrupt):
        safe_print("\n👋 Cancelled")
        return

    try:
        session_uuid = UUID(session_id)
        if session_uuid not in manager.active_sessions:
            safe_print("❌ Consultation not found")
            return

        session = manager.active_sessions[session_uuid]
        consultation_event = session.consultation_event

        safe_print(f"\n📄 Responding to: {consultation_event.consultation_type}")
        safe_print(f"Context: {consultation_event.context}")

        # Collect response data
        try:
            user_id = input("Enter your user ID: ").strip() or "cli_user"
            user_role = input("Enter your role (validation_engineer/quality_assurance/regulatory_specialist): ").strip() or "validation_engineer"
            decision_rationale = input("Enter decision rationale: ").strip()

            if not decision_rationale:
                safe_print("❌ Decision rationale is required")
                return

            confidence_input = input("Enter confidence level (0.0-1.0): ").strip() or "0.8"
            confidence_level = float(confidence_input)

            if not 0.0 <= confidence_level <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")

        except (EOFError, KeyboardInterrupt):
            safe_print("\n👋 Cancelled")
            return
        except ValueError as e:
            safe_print(f"❌ Invalid confidence level: {e}")
            return

        response_data = {}
        if "categorization" in consultation_event.consultation_type.lower():
            try:
                gamp_category = int(input("Enter GAMP category (1, 3, 4, 5): ").strip() or "5")
                if gamp_category not in [1, 3, 4, 5]:
                    raise ValueError("Invalid GAMP category")
                response_data["gamp_category"] = gamp_category
                response_data["risk_assessment"] = {"risk_level": input("Enter risk level (LOW/MEDIUM/HIGH): ").strip().upper() or "HIGH"}
            except ValueError as e:
                safe_print(f"❌ Invalid GAMP category: {e}")
                return

        # Create response event
        response_event = HumanResponseEvent(
            response_type="decision",
            response_data=response_data,
            user_id=user_id,
            user_role=user_role,
            decision_rationale=decision_rationale,
            confidence_level=confidence_level,
            consultation_id=consultation_event.consultation_id,
            session_id=session_uuid,
            approval_level="user"
        )

        # Add response to session
        await session.add_response(response_event)

        safe_print("✅ Response recorded successfully!")

    except ValueError:
        safe_print("❌ Invalid session ID format")
    except Exception as e:
        safe_print(f"❌ Error recording response: {e}")

async def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup Unicode support FIRST to prevent encoding crashes
    setup_unicode_support()

    # Setup safe output management after Unicode is configured
    output_manager = setup_safe_output_management()

    # Setup logging with reduced verbosity
    log_level = "WARNING" if not args.verbose else "INFO"  # Reduced default verbosity
    setup_logging(log_level)

    # Handle consultation interface commands
    if args.consult:
        await run_consultation_interface()
        return None
    if args.list_consultations:
        config = get_config()
        manager = HumanConsultationManager(config)
        await list_active_consultations(manager)
        return None
    if args.respond_to:
        config = get_config()
        manager = HumanConsultationManager(config)
        # Mock session for response (in real implementation, this would load from persistent storage)
        safe_print(f"📝 Response functionality would respond to consultation: {args.respond_to}")
        safe_print("⚠️  Note: This requires active consultation sessions which are currently in-memory only")
        return None

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
            safe_print("Usage: uv run python main.py <document_path>")
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
                # Add a small delay to ensure all spans are exported before shutdown
                import time
                safe_print("⏳ Waiting for span export completion...")
                time.sleep(2)

                from src.shared.event_logging import shutdown_event_logging
                shutdown_event_logging()
                safe_print("\n🔒 Phoenix observability shutdown complete")
            except Exception as shutdown_error:
                safe_print(f"\n⚠️  Warning: Error during Phoenix shutdown: {shutdown_error}")


if __name__ == "__main__":
    # Run the async main function
    sys.exit(asyncio.run(main()))
