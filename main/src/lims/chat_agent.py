"""MDA refinement chat agent with structured edit actions.

Provides a conversational interface for human reviewers to refine
MDA templates via OpenRouter function calling. Each edit is validated
against the MDATemplate Pydantic schema with automatic rollback on
failure.

GAMP-5 Category 5: Custom pharmaceutical software component.
No fallback logic -- all errors propagate with full diagnostics.
"""

from __future__ import annotations

import copy
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Literal

from langfuse import observe
from openai import OpenAI
from pydantic import BaseModel, ValidationError, field_validator

from .config import LIMSConfig
from .mda_schema import MDATemplate
from .prompts.chat_system_prompt import CHAT_SYSTEM_PROMPT
from .prompts.edit_contract_prompt import EDIT_CONTRACT_PROMPT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TURNS = 50
TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# MDAEditAction model
# ---------------------------------------------------------------------------


class MDAEditAction(BaseModel):
    """Structured edit action for MDA template modification.

    Each edit targets a specific sheet, identifies the item to modify,
    and specifies the changes. Every edit includes a reason for ALCOA+
    audit trail compliance.
    """

    sheet: Literal["analyses", "components", "calc_variables", "calculations"]
    action: Literal["add", "modify", "delete"]
    target: dict[str, str]
    changes: dict[str, Any] = {}
    reason: str

    @field_validator("target")
    @classmethod
    def validate_target_not_empty(cls, v: dict[str, str]) -> dict[str, str]:
        if not v:
            raise ValueError(
                "target must not be empty -- it identifies which item to modify. "
                "Example: {'analysis': 'AND_ACS_DYE', 'component_name': 'ABSORBANCE_595'}"
            )
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "reason must not be empty -- audit trail requires justification "
                "for every MDA modification (ALCOA+ compliance)"
            )
        return v


# ---------------------------------------------------------------------------
# OpenAI function tool definition for modify_mda
# ---------------------------------------------------------------------------

_MODIFY_MDA_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "modify_mda",
        "description": (
            "Apply a structured edit to the MDA template. "
            "Use this tool for ALL modifications -- never describe changes "
            "without calling this function.\n\n" + EDIT_CONTRACT_PROMPT
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sheet": {
                    "type": "string",
                    "enum": ["analyses", "components", "calc_variables", "calculations"],
                    "description": "Target MDA sheet to modify.",
                },
                "action": {
                    "type": "string",
                    "enum": ["add", "modify", "delete"],
                    "description": "Edit operation type.",
                },
                "target": {
                    "type": "object",
                    "description": "Identifies the item to modify/delete or new item keys for add.",
                    "additionalProperties": {"type": "string"},
                },
                "changes": {
                    "type": "object",
                    "description": "Fields to set (add/modify) or empty (delete).",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this edit is needed (ALCOA+ audit trail).",
                },
            },
            "required": ["sheet", "action", "target", "reason"],
        },
    },
}


# ---------------------------------------------------------------------------
# ChatSession
# ---------------------------------------------------------------------------


class ChatSession:
    """Conversational MDA refinement session for a single job.

    Maintains chat history, enforces turn limits and TTL, and applies
    structured edits to the MDA template with validation and rollback.

    Args:
        job_id: The LIMS job ID this session belongs to.
        mda_template: The current MDA template as a dict (from model_dump).
        pdf_text: Optional original PDF extraction text for context.
    """

    def __init__(
        self,
        job_id: str,
        mda_template: dict[str, Any],
        chat_context: dict[str, Any] | None = None,
    ) -> None:
        self.job_id = job_id
        self.mda_template = mda_template
        self.chat_context = chat_context or {}
        self.messages: list[dict[str, Any]] = []
        self.edits: list[MDAEditAction] = []
        self.turn_count: int = 0
        self.created_at: float = time.time()

        logger.info(
            "ChatSession created for job %s (max_turns=%d, ttl=%ds)",
            job_id,
            MAX_TURNS,
            TTL_SECONDS,
        )

    def _check_ttl(self) -> None:
        """Raise if the session has exceeded its TTL.

        Raises:
            TimeoutError: If session has been alive longer than TTL_SECONDS.
        """
        elapsed = time.time() - self.created_at
        if elapsed > TTL_SECONDS:
            raise TimeoutError(
                f"Chat session for job '{self.job_id}' has expired. "
                f"Elapsed: {elapsed:.0f}s, TTL: {TTL_SECONDS}s. "
                f"Create a new session to continue editing."
            )

    def _check_turn_limit(self) -> None:
        """Raise if the turn limit has been reached.

        Raises:
            ValueError: If turn_count >= MAX_TURNS.
        """
        if self.turn_count >= MAX_TURNS:
            raise ValueError(
                f"Chat session for job '{self.job_id}' has reached the "
                f"maximum turn limit ({MAX_TURNS}). "
                f"Approve the template or create a new session."
            )

    def _build_workflow_context(self) -> dict[str, Any]:
        """Build compact workflow context for grounding and traceability."""
        raw_extraction = self.chat_context.get("raw_extraction")
        provenance = self.chat_context.get("provenance") or {}
        classification = self.chat_context.get("classification") or {}
        conflicts = self.chat_context.get("conflicts") or []
        stage_details = self.chat_context.get("stage_details") or []
        extraction_trace = self.chat_context.get("extraction_trace") or {}

        provenance_fields = provenance.get("fields", {}) if isinstance(provenance, dict) else {}

        top_provenance: list[dict[str, Any]] = []
        for path, entry in list(provenance_fields.items())[:40]:
            if not isinstance(entry, dict):
                continue
            top_provenance.append({
                "path": path,
                "source": entry.get("source"),
                "confidence": entry.get("confidence"),
                "source_detail": entry.get("source_detail"),
            })

        conflict_sample = []
        for item in conflicts[:20]:
            if isinstance(item, dict):
                conflict_sample.append({
                    "field_path": item.get("field_path"),
                    "template_value": item.get("template_value"),
                    "extracted_value": item.get("extracted_value"),
                })

        stage_sample = []
        for stage in stage_details[:10]:
            if isinstance(stage, dict):
                stage_sample.append({
                    "stage": stage.get("stage"),
                    "summary": stage.get("summary"),
                })

        raw_sample = ""
        if raw_extraction:
            raw_sample = json.dumps(raw_extraction, default=str)[:30000]

        return {
            "pdf_filename": self.chat_context.get("pdf_filename"),
            "classification": classification,
            "extraction_trace": extraction_trace,
            "stage_details": stage_sample,
            "conflicts": conflict_sample,
            "provenance_summary": {
                "total_fields": len(provenance_fields),
                "sample": top_provenance,
            },
            "raw_extraction_sample": raw_sample,
        }

    def _extract_evidence_refs(
        self,
        max_refs: int = 20,
    ) -> list[dict[str, Any]]:
        """Return a compact evidence reference list for parameter source attribution."""
        provenance = self.chat_context.get("provenance") or {}
        provenance_fields = provenance.get("fields", {}) if isinstance(provenance, dict) else {}
        refs: list[dict[str, Any]] = []

        for path, entry in list(provenance_fields.items())[:max_refs]:
            if not isinstance(entry, dict):
                continue
            refs.append({
                "path": path,
                "source": entry.get("source"),
                "confidence": entry.get("confidence"),
                "source_detail": entry.get("source_detail", ""),
            })
        return refs

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current MDA state and full workflow context."""
        mda_json = json.dumps(self.mda_template, indent=2, default=str)
        workflow_context = json.dumps(self._build_workflow_context(), indent=2, default=str)
        evidence_refs = json.dumps(self._extract_evidence_refs(), indent=2, default=str)
        return CHAT_SYSTEM_PROMPT.format(
            mda_state=mda_json,
            workflow_context=workflow_context,
            evidence_refs=evidence_refs,
        )

    def _apply_edit(self, edit: MDAEditAction) -> None:
        """Apply a structured edit to the MDA template with rollback on failure.

        Takes a snapshot of the current template before applying the edit.
        For invalid-in-progress templates, incremental edits are allowed as
        long as they do not introduce NEW validation error locations.
        If the edit introduces new error locations, the snapshot is restored
        and a ValueError is raised.

        Args:
            edit: The edit action to apply.

        Raises:
            ValueError: If the edit results in an invalid MDA template.
            KeyError: If the target item cannot be found for modify/delete.
        """
        # Snapshot for rollback
        snapshot = copy.deepcopy(self.mda_template)
        baseline_errors = self._validation_error_paths(self.mda_template)

        try:
            sheet_data: list[dict[str, Any]] = self.mda_template.get(edit.sheet, [])

            if edit.action == "add":
                new_item = {**edit.target, **edit.changes}
                sheet_data.append(new_item)
                logger.info(
                    "Job %s: adding item to '%s': %s",
                    self.job_id,
                    edit.sheet,
                    edit.target,
                )

            elif edit.action == "modify":
                item = self._find_item(sheet_data, edit.target)
                if item is None:
                    raise KeyError(
                        f"Cannot find item matching {edit.target} in sheet "
                        f"'{edit.sheet}' for modification. "
                        f"Available items: {len(sheet_data)}"
                    )
                item.update(edit.changes)
                logger.info(
                    "Job %s: modifying item in '%s': target=%s, changes=%s",
                    self.job_id,
                    edit.sheet,
                    edit.target,
                    list(edit.changes.keys()),
                )

            elif edit.action == "delete":
                item = self._find_item(sheet_data, edit.target)
                if item is None:
                    raise KeyError(
                        f"Cannot find item matching {edit.target} in sheet "
                        f"'{edit.sheet}' for deletion. "
                        f"Available items: {len(sheet_data)}"
                    )
                sheet_data.remove(item)
                logger.info(
                    "Job %s: deleting item from '%s': %s",
                    self.job_id,
                    edit.sheet,
                    edit.target,
                )

            # Conservative normalization before validation:
            # - analysis_type aliases (e.g., IDENTITY -> ID)
            # - qualitative tokens in numeric bounds for L/T/D components
            from .data_normalizer import (
                _normalize_analysis_type,
                sanitize_component_numeric_bounds,
            )

            analyses = self.mda_template.get("analyses", [])
            if isinstance(analyses, list):
                for analysis in analyses:
                    if not isinstance(analysis, dict):
                        continue
                    analysis["analysis_type"] = _normalize_analysis_type(
                        analysis.get("analysis_type"),
                        analysis.get("name"),
                    )

            components = self.mda_template.get("components", [])
            if isinstance(components, list):
                sanitize_component_numeric_bounds(components)

            # Re-validate entire MDA after edit.
            # Allow incremental repair: the model may still be invalid, but
            # must not introduce NEW error locations compared to baseline.
            post_errors = self._validation_error_paths(self.mda_template)
            new_errors = sorted(post_errors - baseline_errors)
            if new_errors:
                raise ValueError(
                    "Edit introduces new validation errors: "
                    f"{', '.join(new_errors[:10])}"
                    + (" ..." if len(new_errors) > 10 else "")
                )

            # Log successful edit
            self.edits.append(edit)
            logger.info(
                "Job %s: edit applied (sheet=%s, action=%s, reason=%s, baseline_errors=%d, post_errors=%d)",
                self.job_id,
                edit.sheet,
                edit.action,
                edit.reason,
                len(baseline_errors),
                len(post_errors),
            )

        except Exception:
            # Rollback on any failure
            self.mda_template.clear()
            self.mda_template.update(snapshot)
            logger.warning(
                "Job %s: edit rolled back due to validation failure (sheet=%s, action=%s)",
                self.job_id,
                edit.sheet,
                edit.action,
            )
            raise

    @staticmethod
    def _validation_error_paths(mda_template: dict[str, Any]) -> set[str]:
        """Return validation error paths for the current MDA template.

        Returns an empty set when validation passes.
        """
        try:
            MDATemplate.model_validate(mda_template)
            return set()
        except ValidationError as e:
            paths: set[str] = set()
            for err in e.errors():
                loc = err.get("loc", ())
                if isinstance(loc, tuple):
                    paths.add(".".join(str(part) for part in loc))
                elif isinstance(loc, list):
                    paths.add(".".join(str(part) for part in loc))
                else:
                    paths.add(str(loc))
            return paths

    @staticmethod
    def _find_item(
        items: list[dict[str, Any]],
        target: dict[str, str],
    ) -> dict[str, Any] | None:
        """Find an item in a sheet's list matching all target key-value pairs.

        Args:
            items: List of item dicts from the sheet.
            target: Key-value pairs that must all match.

        Returns:
            The matching item dict, or None if not found.
        """
        for item in items:
            if all(str(item.get(k)) == str(v) for k, v in target.items()):
                return item
        return None

    @observe(name="lims-chat")
    def chat(self, user_message: str, config: LIMSConfig) -> dict[str, Any]:
        """Process a user message and return the LLM response with any edits.

        Args:
            user_message: The reviewer's message.
            config: LIMS configuration with OpenRouter API key and model.

        Returns:
            dict with keys:
                - response: str -- the LLM's text response
                - edits_applied: list[dict] -- edits that were successfully applied
                - edits_rejected: list[dict] -- edits that failed validation
                - mda_template: dict -- current MDA state after any edits
                - turn_count: int -- current turn number

        Raises:
            TimeoutError: If session TTL has expired.
            ValueError: If turn limit reached or API key missing.
        """
        self._check_ttl()
        self._check_turn_limit()

        if not config.openrouter_api_key:
            raise ValueError(
                "LIMS_OPENROUTER_API_KEY is not set. "
                "Add it to .env.local to enable MDA chat."
            )

        if not user_message or not user_message.strip():
            raise ValueError("user_message must not be empty")

        self.turn_count += 1

        # Build message list with fresh system prompt (reflects current MDA state)
        system_prompt = self._build_system_prompt()
        messages_for_llm: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation history
        messages_for_llm.extend(self.messages)

        # Add the new user message
        messages_for_llm.append({"role": "user", "content": user_message})
        self.messages.append({"role": "user", "content": user_message})

        # Call LLM via OpenRouter
        client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        logger.info(
            "Job %s: sending chat message (turn %d/%d, model=%s)",
            self.job_id,
            self.turn_count,
            MAX_TURNS,
            config.openrouter_model,
        )

        response = client.chat.completions.create(
            model=config.openrouter_model,
            messages=messages_for_llm,
            tools=[_MODIFY_MDA_TOOL],
            tool_choice="auto",
            temperature=0.1,
        )

        assistant_message = response.choices[0].message

        # Process tool calls (edits)
        edits_applied: list[dict[str, Any]] = []
        edits_rejected: list[dict[str, Any]] = []

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                if tool_call.function.name == "modify_mda":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        edit_action = MDAEditAction(**args)
                        self._apply_edit(edit_action)
                        edits_applied.append(edit_action.model_dump())
                    except (json.JSONDecodeError, Exception) as e:
                        error_info = {
                            "raw_args": tool_call.function.arguments,
                            "error": f"{type(e).__name__}: {e}",
                        }
                        edits_rejected.append(error_info)
                        logger.warning(
                            "Job %s: edit rejected: %s",
                            self.job_id,
                            error_info["error"],
                        )

        # Extract text response
        response_text = assistant_message.content or ""

        # Store assistant message in history
        self.messages.append({
            "role": "assistant",
            "content": response_text,
            "edits_applied": edits_applied,
            "edits_rejected": edits_rejected,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(
            "Job %s: chat response received (edits_applied=%d, edits_rejected=%d)",
            self.job_id,
            len(edits_applied),
            len(edits_rejected),
        )

        return {
            "response": response_text,
            "edits_applied": edits_applied,
            "edits_rejected": edits_rejected,
            "mda_template": self.mda_template,
            "turn_count": self.turn_count,
            "evidence_refs": self._extract_evidence_refs(),
        }


# ---------------------------------------------------------------------------
# Per-job session store (in-memory)
# ---------------------------------------------------------------------------

_sessions: dict[str, ChatSession] = {}


def get_or_create_session(
    job_id: str,
    mda_template: dict[str, Any],
    chat_context: dict[str, Any] | None = None,
) -> ChatSession:
    """Get an existing chat session or create a new one.

    Args:
        job_id: The LIMS job ID.
        mda_template: Current MDA template dict.
        chat_context: Full pipeline context for grounded chat responses.

    Returns:
        The ChatSession for this job.
    """
    if job_id not in _sessions:
        _sessions[job_id] = ChatSession(
            job_id=job_id,
            mda_template=mda_template,
            chat_context=chat_context,
        )
        logger.info("Created new chat session for job %s", job_id)
    else:
        # Keep session context and MDA synchronized with latest job state
        session = _sessions[job_id]
        session.chat_context = chat_context or {}
        session.mda_template = mda_template
    return _sessions[job_id]


def get_session(job_id: str) -> ChatSession | None:
    """Get an existing chat session if one exists.

    Args:
        job_id: The LIMS job ID.

    Returns:
        The ChatSession or None if no session exists.
    """
    return _sessions.get(job_id)
