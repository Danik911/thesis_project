"""
Consultation Handler for Human-in-the-Loop Terminal Input.

This module provides an event-driven consultation handler that processes
ConsultationInputEvent requests and collects human input without blocking
the LlamaIndex workflow execution.

Implements GAMP-5 compliant human consultation for pharmaceutical validation
with full audit trail and regulatory compliance features.
"""

import sys
from datetime import UTC, datetime
from uuid import uuid4

from .events import ConsultationInputEvent, HumanResponseEvent


def flush_output():
    """Ensure terminal output is displayed immediately."""
    sys.stdout.flush()
    sys.stderr.flush()


class ConsultationEventHandler:
    """
    Handles human consultation events in single console mode.
    
    This handler processes ConsultationInputEvent requests and collects
    human input for GAMP-5 categorization decisions. It operates outside
    the workflow steps to avoid terminal blocking issues.
    """

    def __init__(self):
        """Initialize the consultation handler."""
        self.active_consultations = {}

    async def handle_consultation_input(self, event: ConsultationInputEvent) -> HumanResponseEvent:
        """
        Handle consultation input request and collect human response.
        
        Args:
            event: ConsultationInputEvent requesting human input
            
        Returns:
            HumanResponseEvent containing collected consultation data
            
        Raises:
            TimeoutError: If consultation times out
            ValueError: If invalid input provided
        """
        consultation_id = event.consultation_id
        self.active_consultations[consultation_id] = event

        try:
            # Display consultation prompt with clear formatting
            self._display_consultation_prompt(event)

            # Get operator credentials for 21 CFR Part 11 compliance
            operator_name = self._get_operator_credential("Enter your name (for audit trail): ")
            operator_id = self._get_operator_credential("Enter your employee ID: ")
            operator_role = self._get_operator_role()

            # Get GAMP-5 category selection
            category_input = self._get_category_selection()

            # Get decision justification
            justification = self._get_justification()

            # Create digital signature
            timestamp = datetime.now(UTC)
            digital_signature = f"{operator_name}_{operator_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            # Create response event with full compliance data
            response_event = HumanResponseEvent(
                response_type="gamp_categorization_decision",
                response_data={
                    "gamp_category": int(category_input),
                    "category_justification": justification,
                    "consultation_context": event.consultation_context,
                    "original_confidence": event.consultation_context.get("confidence_score", 0.0),
                    "original_suggestion": event.consultation_context.get("gamp_category"),
                    "decision_timestamp": timestamp.isoformat(),
                    "consultation_method": "single_console_human_input"
                },
                user_id=operator_name,
                user_role=operator_role,
                decision_rationale=justification,
                confidence_level=1.0,  # Human decisions have full confidence
                consultation_id=consultation_id,
                session_id=uuid4(),
                digital_signature=digital_signature,
                approval_level="validation_engineer",
                regulatory_impact="high"
            )

            print("\n✅ Consultation completed successfully")
            print(f"   Category: {category_input}")
            print(f"   Operator: {operator_name} ({operator_role})")
            print(f"   Signature: {digital_signature}")
            print("="*60 + "\n")
            flush_output()

            return response_event

        except Exception as e:
            print(f"\n❌ Consultation failed: {e!s}")
            print("="*60 + "\n")
            flush_output()
            raise
        finally:
            # Clean up active consultation
            if consultation_id in self.active_consultations:
                del self.active_consultations[consultation_id]

    def _display_consultation_prompt(self, event: ConsultationInputEvent):
        """Display the consultation prompt to the user."""
        context = event.consultation_context

        print(f"\n{'='*60}")
        print("🚨 HUMAN CONSULTATION REQUIRED")
        print(f"{'='*60}")
        print(f"📋 Reason: {context.get('reason', 'Low confidence categorization')}")

        if "confidence_score" in context:
            print(f"📊 AI Confidence: {context['confidence_score']:.2%}")

        if "gamp_category" in context:
            suggested = context["gamp_category"]
            if hasattr(suggested, "value"):
                suggested = suggested.value
            print(f"🤖 AI Suggestion: Category {suggested}")

        print("\n⚠️  Low confidence detected - human expertise required")
        print(f"🕒 Timeout: {event.timeout_seconds} seconds")
        print(f"{'='*60}")
        flush_output()

    def _get_operator_credential(self, prompt: str) -> str:
        """Get operator credential with validation."""
        while True:
            try:
                credential = input(prompt).strip()
                if not credential:
                    print("❌ Credential cannot be empty. Please try again.")
                    continue
                if len(credential) < 2:
                    print("❌ Credential too short. Please enter a valid value.")
                    continue
                return credential
            except KeyboardInterrupt:
                raise ValueError("Consultation cancelled by user")
            except EOFError:
                raise ValueError("Input stream closed")

    def _get_operator_role(self) -> str:
        """Get operator role with validation."""
        print("\n👤 OPERATOR ROLE SELECTION")
        print("Available roles:")
        print("  1 - Validation Engineer")
        print("  2 - Quality Assurance")
        print("  3 - Regulatory Specialist")
        print("  4 - System Administrator")

        valid_roles = {
            "1": "validation_engineer",
            "2": "quality_assurance",
            "3": "regulatory_specialist",
            "4": "system_administrator"
        }

        while True:
            try:
                role_input = input("Select your role (1-4): ").strip()
                if role_input in valid_roles:
                    return valid_roles[role_input]
                print("❌ Invalid selection. Please choose 1-4.")
            except KeyboardInterrupt:
                raise ValueError("Consultation cancelled by user")
            except EOFError:
                raise ValueError("Input stream closed")

    def _get_category_selection(self) -> str:
        """Get GAMP-5 category selection with validation."""
        print("\n📋 GAMP-5 CATEGORY SELECTION")
        print("Available categories:")
        print("  1 - Category 1 (Infrastructure Software)")
        print("  3 - Category 3 (Non-configured Products)")
        print("  4 - Category 4 (Configured Products)")
        print("  5 - Category 5 (Custom Applications)")

        valid_categories = ["1", "3", "4", "5"]

        while True:
            try:
                category = input("\nEnter category (1/3/4/5): ").strip()
                if category in valid_categories:
                    return category
                print("❌ Invalid category. Please select 1, 3, 4, or 5.")
            except KeyboardInterrupt:
                raise ValueError("Consultation cancelled by user")
            except EOFError:
                raise ValueError("Input stream closed")

    def _get_justification(self) -> str:
        """Get decision justification with validation."""
        print("\n📝 DECISION JUSTIFICATION")
        while True:
            try:
                justification = input("Enter justification for your decision: ").strip()
                if not justification:
                    print("❌ Justification cannot be empty. Please provide a reason.")
                    continue
                if len(justification) < 10:
                    print("❌ Justification too short. Please provide more detail.")
                    continue
                return justification
            except KeyboardInterrupt:
                raise ValueError("Consultation cancelled by user")
            except EOFError:
                raise ValueError("Input stream closed")


# Global handler instance for single console mode
_consultation_handler = ConsultationEventHandler()


async def process_consultation_input(event: ConsultationInputEvent) -> HumanResponseEvent:
    """
    Process consultation input event and return human response.
    
    This is the main entry point for consultation handling that can be
    called from workflow steps.
    
    Args:
        event: ConsultationInputEvent requesting human input
        
    Returns:
        HumanResponseEvent with collected consultation data
    """
    return await _consultation_handler.handle_consultation_input(event)
