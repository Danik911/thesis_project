"""Tests for the MDA chat agent with mocked LLM.

Validates:
- ChatSession initialization
- Turn limit enforcement (MAX_TURNS)
- TTL enforcement (2 hours)
- _apply_edit with valid edits
- _apply_edit rollback on validation failure
- MDAEditAction validation
"""

import copy
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from main.src.lims.chat_agent import (
    MAX_TURNS,
    TTL_SECONDS,
    ChatSession,
    MDAEditAction,
    _sessions,
)
from main.src.lims.config import LIMSConfig


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear the in-memory session store between tests."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def valid_mda_dict(sample_mda_template) -> dict:
    """Valid MDA template as a dict."""
    return sample_mda_template.model_dump()


@pytest.fixture
def lims_config() -> LIMSConfig:
    """LIMSConfig with test values."""
    return LIMSConfig(
        llamaextract_api_key="test-key-for-llamaextract",
        openrouter_api_key="test-key-for-openrouter",
        openrouter_model="test/model",
    )


@pytest.fixture
def session(valid_mda_dict) -> ChatSession:
    """A fresh ChatSession for testing."""
    return ChatSession(
        job_id="test-job-001",
        mda_template=valid_mda_dict,
        chat_context={
            "pdf_filename": "test.pdf",
            "raw_extraction": {"sample": "extraction data"},
            "classification": {"test_type": "IDENTITY", "confidence": 0.95},
        },
    )


class TestChatSessionInit:
    def test_init_stores_job_id(self, session):
        assert session.job_id == "test-job-001"

    def test_init_stores_mda_template(self, session, valid_mda_dict):
        assert session.mda_template == valid_mda_dict

    def test_init_stores_chat_context(self, session):
        assert session.chat_context["pdf_filename"] == "test.pdf"

    def test_init_empty_messages(self, session):
        assert session.messages == []

    def test_init_empty_edits(self, session):
        assert session.edits == []

    def test_init_zero_turns(self, session):
        assert session.turn_count == 0

    def test_init_created_at_is_recent(self, session):
        assert time.time() - session.created_at < 5  # within 5 seconds


class TestTurnLimit:
    def test_turn_limit_raises_at_max(self, session):
        session.turn_count = MAX_TURNS
        with pytest.raises(ValueError, match="maximum turn limit"):
            session._check_turn_limit()

    def test_turn_limit_ok_below_max(self, session):
        session.turn_count = MAX_TURNS - 1
        # Should not raise
        session._check_turn_limit()

    def test_turn_limit_ok_at_zero(self, session):
        session.turn_count = 0
        session._check_turn_limit()

    def test_chat_enforces_turn_limit(self, session, lims_config):
        """chat() raises ValueError when turn limit is reached."""
        session.turn_count = MAX_TURNS
        with pytest.raises(ValueError, match="maximum turn limit"):
            session.chat("Hello", lims_config)


class TestTTL:
    def test_ttl_raises_when_expired(self, session):
        session.created_at = time.time() - TTL_SECONDS - 1
        with pytest.raises(TimeoutError, match="expired"):
            session._check_ttl()

    def test_ttl_ok_when_fresh(self, session):
        # Should not raise for a fresh session
        session._check_ttl()

    def test_ttl_ok_just_before_expiry(self, session):
        session.created_at = time.time() - TTL_SECONDS + 10
        # Should not raise (10 seconds before expiry)
        session._check_ttl()

    def test_chat_enforces_ttl(self, session, lims_config):
        """chat() raises TimeoutError when session TTL has expired."""
        session.created_at = time.time() - TTL_SECONDS - 1
        with pytest.raises(TimeoutError, match="expired"):
            session.chat("Hello", lims_config)


class TestApplyEdit:
    """Test _apply_edit with valid and invalid edits."""

    def test_add_component(self, session):
        """Add a valid component via _apply_edit."""
        initial_count = len(session.mda_template["components"])

        edit = MDAEditAction(
            sheet="components",
            action="add",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "NEW_VISUAL_CHECK",
            },
            changes={
                "order_number": 3,
                "result_type": "L",
                "list_key": "YES_NO_2",
                "reportable": True,
            },
            reason="Adding visual check per reviewer request",
        )

        session._apply_edit(edit)

        assert len(session.mda_template["components"]) == initial_count + 1
        assert len(session.edits) == 1

    def test_modify_component(self, session):
        """Modify an existing component via _apply_edit."""
        edit = MDAEditAction(
            sheet="components",
            action="modify",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "ABSORBANCE_595",
            },
            changes={
                "reportable": False,
            },
            reason="Mark as non-reportable per reviewer request",
        )

        session._apply_edit(edit)

        # Find the modified component
        comp = None
        for c in session.mda_template["components"]:
            if c["component_name"] == "ABSORBANCE_595":
                comp = c
                break
        assert comp is not None
        assert comp["reportable"] is False

    def test_delete_component(self, session, valid_mda_dict):
        """Delete a component, but only if the resulting MDA is still valid.

        We need to add a non-K component first that we can safely delete
        without breaking cross-sheet integrity.
        """
        # First add a component we can delete safely
        add_edit = MDAEditAction(
            sheet="components",
            action="add",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "DELETABLE_COMP",
            },
            changes={
                "order_number": 99,
                "result_type": "T",
                "reportable": False,
            },
            reason="Adding temp component for deletion test",
        )
        session._apply_edit(add_edit)

        count_before = len(session.mda_template["components"])

        delete_edit = MDAEditAction(
            sheet="components",
            action="delete",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "DELETABLE_COMP",
            },
            changes={},
            reason="Removing test component",
        )
        session._apply_edit(delete_edit)

        assert len(session.mda_template["components"]) == count_before - 1

    def test_rollback_on_validation_failure(self, session):
        """Edit that breaks cross-sheet integrity is rolled back."""
        snapshot = copy.deepcopy(session.mda_template)

        # Try to add a K-type component without a matching calculation
        # This should fail MDATemplate validation and get rolled back
        edit = MDAEditAction(
            sheet="components",
            action="add",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "INVALID_K_NO_CALC",
            },
            changes={
                "order_number": 99,
                "result_type": "K",
                "auto_calc": True,
            },
            reason="This should fail validation (no matching Calculation)",
        )

        with pytest.raises(ValueError, match="introduces new validation errors"):
            session._apply_edit(edit)

        # MDA should be rolled back to snapshot
        assert session.mda_template == snapshot

    def test_modify_nonexistent_item_raises(self, session):
        """Modifying a non-existent item raises KeyError."""
        edit = MDAEditAction(
            sheet="components",
            action="modify",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "DOES_NOT_EXIST",
            },
            changes={"reportable": False},
            reason="Test nonexistent modification",
        )

        with pytest.raises(KeyError, match="Cannot find item"):
            session._apply_edit(edit)

    def test_incremental_fix_allowed_when_template_already_invalid(self, valid_mda_dict):
        """Edits should be allowed if they don't introduce new validation paths.

        This enables reviewers to repair invalid templates incrementally via chat.
        """
        invalid_mda = copy.deepcopy(valid_mda_dict)

        # Seed two known validation errors on different component minimum fields
        assert len(invalid_mda["components"]) >= 2
        idx_a = len(invalid_mda["components"]) - 2
        idx_b = len(invalid_mda["components"]) - 1
        invalid_mda["components"][idx_a]["minimum"] = "Pass"
        invalid_mda["components"][idx_b]["minimum"] = "Pass"

        session = ChatSession(
            job_id="test-incremental-fix",
            mda_template=invalid_mda,
            chat_context={},
        )

        # Fix only one of the two errors; template remains invalid overall.
        edit = MDAEditAction(
            sheet="components",
            action="modify",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": invalid_mda["components"][idx_a]["component_name"],
            },
            changes={"minimum": None},
            reason="Fix first minimum parse error",
        )

        session._apply_edit(edit)

        # Edit is accepted and persisted even though one error remains.
        assert len(session.edits) == 1
        assert session.mda_template["components"][idx_a]["minimum"] is None

    def test_chat_edit_normalizes_identity_alias(self, valid_mda_dict):
        """analysis_type alias values should be normalized before validation."""
        session = ChatSession(
            job_id="test-normalize-analysis-type",
            mda_template=copy.deepcopy(valid_mda_dict),
            chat_context={},
        )

        edit = MDAEditAction(
            sheet="analyses",
            action="modify",
            target={"name": session.mda_template["analyses"][0]["name"]},
            changes={"analysis_type": "IDENTITY"},
            reason="Use semantic label",
        )

        session._apply_edit(edit)
        assert session.mda_template["analyses"][0]["analysis_type"] == "ID"

    def test_delete_nonexistent_item_raises(self, session):
        """Deleting a non-existent item raises KeyError."""
        edit = MDAEditAction(
            sheet="components",
            action="delete",
            target={
                "analysis": "AND_ACS_DYE",
                "component_name": "DOES_NOT_EXIST",
            },
            changes={},
            reason="Test nonexistent deletion",
        )

        with pytest.raises(KeyError, match="Cannot find item"):
            session._apply_edit(edit)


class TestMDAEditActionValidation:
    def test_valid_edit_action(self):
        edit = MDAEditAction(
            sheet="components",
            action="add",
            target={"analysis": "AND_TEST", "component_name": "NEW"},
            changes={"order_number": 1},
            reason="Adding new component",
        )
        assert edit.sheet == "components"
        assert edit.action == "add"

    def test_empty_target_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            MDAEditAction(
                sheet="components",
                action="add",
                target={},
                changes={},
                reason="Test",
            )

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            MDAEditAction(
                sheet="components",
                action="add",
                target={"analysis": "AND_TEST"},
                changes={},
                reason="",
            )

    def test_whitespace_reason_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            MDAEditAction(
                sheet="components",
                action="add",
                target={"analysis": "AND_TEST"},
                changes={},
                reason="   ",
            )

    def test_invalid_sheet_raises(self):
        with pytest.raises(ValidationError):
            MDAEditAction(
                sheet="invalid_sheet",  # type: ignore[arg-type]
                action="add",
                target={"name": "test"},
                changes={},
                reason="Test",
            )

    def test_invalid_action_raises(self):
        with pytest.raises(ValidationError):
            MDAEditAction(
                sheet="components",
                action="invalid_action",  # type: ignore[arg-type]
                target={"name": "test"},
                changes={},
                reason="Test",
            )


class TestChatWithMockedLLM:
    """Test chat() with mocked OpenAI client."""

    def _make_mock_response(
        self,
        content: str = "Here is my response.",
        tool_calls: list | None = None,
    ) -> MagicMock:
        """Create a mock OpenAI chat completion response."""
        message = MagicMock()
        message.content = content
        message.tool_calls = tool_calls

        choice = MagicMock()
        choice.message = message

        response = MagicMock()
        response.choices = [choice]
        return response

    @patch("main.src.lims.chat_agent.OpenAI")
    def test_chat_returns_response(self, mock_openai_cls, session, lims_config):
        """Test basic chat with a text-only response (no tool calls)."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = self._make_mock_response(
            content="The MDA looks good. No changes needed."
        )

        result = session.chat("How does the MDA look?", lims_config)

        assert result["response"] == "The MDA looks good. No changes needed."
        assert result["edits_applied"] == []
        assert result["edits_rejected"] == []
        assert result["turn_count"] == 1

    @patch("main.src.lims.chat_agent.OpenAI")
    def test_chat_increments_turn_count(self, mock_openai_cls, session, lims_config):
        """Each chat() call increments the turn counter."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = self._make_mock_response()

        session.chat("Message 1", lims_config)
        assert session.turn_count == 1

        session.chat("Message 2", lims_config)
        assert session.turn_count == 2

    @patch("main.src.lims.chat_agent.OpenAI")
    def test_chat_stores_messages(self, mock_openai_cls, session, lims_config):
        """Chat history is maintained."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = self._make_mock_response(
            content="Response text"
        )

        session.chat("Hello", lims_config)

        assert len(session.messages) == 2  # user + assistant
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[1]["content"] == "Response text"

    @patch("main.src.lims.chat_agent.OpenAI")
    def test_chat_with_valid_tool_call(self, mock_openai_cls, session, lims_config):
        """Test chat with a tool call that adds a valid component."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Create a mock tool call
        tool_call = MagicMock()
        tool_call.function.name = "modify_mda"
        tool_call.function.arguments = json.dumps({
            "sheet": "components",
            "action": "add",
            "target": {
                "analysis": "AND_ACS_DYE",
                "component_name": "VISUAL_CHECK",
            },
            "changes": {
                "order_number": 3,
                "result_type": "L",
                "list_key": "YES_NO_2",
                "reportable": True,
            },
            "reason": "Adding visual check component",
        })

        mock_client.chat.completions.create.return_value = self._make_mock_response(
            content="I have added the visual check component.",
            tool_calls=[tool_call],
        )

        result = session.chat("Add a visual check", lims_config)

        assert len(result["edits_applied"]) == 1
        assert result["edits_applied"][0]["sheet"] == "components"
        assert result["edits_applied"][0]["action"] == "add"
        assert result["edits_rejected"] == []

    @patch("main.src.lims.chat_agent.OpenAI")
    def test_chat_with_invalid_tool_call(self, mock_openai_cls, session, lims_config):
        """Test chat with a tool call that would break validation."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Create a tool call that adds K-type without matching calculation
        tool_call = MagicMock()
        tool_call.function.name = "modify_mda"
        tool_call.function.arguments = json.dumps({
            "sheet": "components",
            "action": "add",
            "target": {
                "analysis": "AND_ACS_DYE",
                "component_name": "BROKEN_K",
            },
            "changes": {
                "order_number": 99,
                "result_type": "K",
                "auto_calc": True,
            },
            "reason": "This will fail validation",
        })

        mock_client.chat.completions.create.return_value = self._make_mock_response(
            content="Attempting to add...",
            tool_calls=[tool_call],
        )

        result = session.chat("Add broken component", lims_config)

        assert result["edits_applied"] == []
        assert len(result["edits_rejected"]) == 1
        assert "error" in result["edits_rejected"][0]

    def test_chat_rejects_empty_message(self, session, lims_config):
        with pytest.raises(ValueError, match="must not be empty"):
            session.chat("", lims_config)

    def test_chat_rejects_missing_api_key(self, session):
        config = LIMSConfig(
            llamaextract_api_key="test-key",
            openrouter_api_key="",
        )
        with pytest.raises(ValueError, match="LIMS_OPENROUTER_API_KEY"):
            session.chat("Hello", config)


class TestBuildSystemPrompt:
    def test_system_prompt_contains_mda_state(self, session):
        prompt = session._build_system_prompt()
        # Should contain the MDA template JSON
        assert "AND_ACS_DYE" in prompt

    def test_system_prompt_contains_workflow_context(self, session):
        prompt = session._build_system_prompt()
        # Should contain classification info from chat_context
        assert "IDENTITY" in prompt

    def test_system_prompt_without_context(self, valid_mda_dict):
        session = ChatSession(
            job_id="test-no-context",
            mda_template=valid_mda_dict,
        )
        prompt = session._build_system_prompt()
        # Should still generate a valid prompt with empty context
        assert "AND_ACS_DYE" in prompt
