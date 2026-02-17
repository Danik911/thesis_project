# Task L4b — Chat Agent + Mandatory HITL + Router Endpoints

**Phase:** 4 (Workflow + HITL + Export) | **PRP Tasks Merged:** L4.3, L4.4, L4.6
**Dependencies:** Task L4a (MDA Generation Backend)
**Branch:** `prjoject_p_protatype`

---

## Objective

Build the chat agent with structured edit actions for MDA refinement, implement the mandatory HITL state machine (no auto-approval, no confidence thresholds), and add all remaining LIMS API endpoints.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/lims/chat_agent.py` | `ChatSession` with `MDAEditAction` structured tool, Pydantic re-validation, TTL/turn limits |
| `main/src/lims/job_store.py` | In-memory job store + state machine: EXTRACTING->GENERATING->PENDING_REVIEW->APPROVED->EXPORTED |
| `main/src/lims/prompts/chat_system_prompt.py` | Chat prompt template: PDF context + current MDA state + edit instructions |
| `main/src/lims/prompts/edit_contract_prompt.py` | Structured edit action JSON schema documentation |
| `main/tests/lims/test_job_store.py` | State machine tests: valid/invalid transitions, mandatory HITL enforcement |
| `main/tests/lims/test_chat_agent.py` | Chat agent unit tests (mock LLM, structured edit validation) |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/lims_router.py` | Add: `GET /status/{job_id}`, `POST /chat`, `POST /approve/{job_id}`, `GET /export/{job_id}`. Update `POST /extract` to return `job_id`. |

---

## Implementation Details

### 1. job_store.py — In-Memory State Machine

```python
"""In-memory LIMS job store with mandatory HITL state machine.

Job lifecycle: EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED

CRITICAL: No auto-approval, no confidence thresholds, no timeout bypass.
Human MUST explicitly call POST /lims/approve/{job_id} before XLSX export.
"""

import logging
import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LIMSJobStatus(str, Enum):
    EXTRACTING = "EXTRACTING"
    GENERATING = "GENERATING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"


class LIMSJob(BaseModel):
    job_id: str
    status: LIMSJobStatus
    created_at: datetime
    updated_at: datetime
    pdf_filename: str
    raw_extraction: Optional[dict] = None
    mda_template: Optional[dict] = None
    chat_history: list[dict] = []
    edit_log: list[dict] = []
    error: Optional[str] = None


# In-memory store (acceptable for PoC — data lost on restart)
_jobs: dict[str, LIMSJob] = {}

VALID_TRANSITIONS = {
    LIMSJobStatus.EXTRACTING: {LIMSJobStatus.GENERATING, LIMSJobStatus.FAILED},
    LIMSJobStatus.GENERATING: {LIMSJobStatus.PENDING_REVIEW, LIMSJobStatus.FAILED},
    LIMSJobStatus.PENDING_REVIEW: {LIMSJobStatus.APPROVED},  # MANDATORY HITL
    LIMSJobStatus.APPROVED: {LIMSJobStatus.EXPORTED},
    LIMSJobStatus.EXPORTED: set(),
    LIMSJobStatus.FAILED: set(),
}


def create_job(pdf_filename: str) -> str:
    """Create a new LIMS job in EXTRACTING state. Returns job_id."""
    job_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    _jobs[job_id] = LIMSJob(
        job_id=job_id,
        status=LIMSJobStatus.EXTRACTING,
        created_at=now,
        updated_at=now,
        pdf_filename=pdf_filename,
    )
    return job_id


def get_job(job_id: str) -> LIMSJob:
    """Get job by ID. Raises KeyError if not found."""
    if job_id not in _jobs:
        raise KeyError(f"Job '{job_id}' not found")
    return _jobs[job_id]


def update_status(job_id: str, new_status: LIMSJobStatus) -> None:
    """Transition job status. Raises ValueError for invalid transitions."""
    job = get_job(job_id)
    allowed = VALID_TRANSITIONS.get(job.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {job.status} -> {new_status}. "
            f"Allowed from {job.status}: {sorted(s.value for s in allowed)}"
        )
    old = job.status
    job.status = new_status
    job.updated_at = datetime.now(UTC)
    logger.info(f"Job {job_id}: {old} -> {new_status}")


def approve_job(job_id: str) -> None:
    """Explicit human approval — the ONLY path to APPROVED status."""
    update_status(job_id, LIMSJobStatus.APPROVED)
```

### 2. chat_agent.py — Structured Edit Actions

```python
"""Chat agent for MDA refinement with structured edit actions.

Uses OpenRouter (OpenAI-compatible) with function calling.
Every MDA modification must be a structured MDAEditAction validated by Pydantic.
Invalid edits are rejected — MDA state remains unchanged.

Docs:
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- OpenRouter: https://openrouter.ai/docs
"""

import json
import logging
import os
from datetime import datetime, UTC
from typing import Any, Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from .mda_schema import MDATemplate
from .prompts.chat_system_prompt import CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MAX_TURNS = 50
TTL_SECONDS = 7200  # 2 hours


class MDAEditAction(BaseModel):
    """Structured edit action — the ONLY way to modify MDA via chat."""
    sheet: Literal["analyses", "components", "calc_variables", "calculations"]
    action: Literal["add", "modify", "delete"]
    target: dict[str, str]  # e.g. {"analysis": "AND_ACS_DYE", "component_name": "X"}
    changes: dict[str, Any] = {}
    reason: str


class ChatSession:
    """Per-job chat session with memory guardrails (TTL + turn limit)."""

    def __init__(self, job_id: str, mda_template: dict, pdf_text: str = ""):
        self.job_id = job_id
        self.mda_state = mda_template.copy()
        self.pdf_text = pdf_text[:10000]  # Truncate for context window
        self.messages: list[dict] = []
        self.edit_log: list[dict] = []
        self.created_at = datetime.now(UTC)

    def chat(self, user_message: str) -> dict:
        """Process a chat message. Returns response + optional MDA updates."""
        # Enforce turn limit
        if len(self.messages) >= MAX_TURNS * 2:
            raise ValueError(f"Chat session limit ({MAX_TURNS} turns) reached.")

        # Enforce TTL
        elapsed = (datetime.now(UTC) - self.created_at).total_seconds()
        if elapsed > TTL_SECONDS:
            raise ValueError(f"Chat session expired (TTL: {TTL_SECONDS}s).")

        self.messages.append({"role": "user", "content": user_message})

        # Build system context with current MDA state
        system = CHAT_SYSTEM_PROMPT.format(
            mda_state=json.dumps(self.mda_state, indent=2)[:5000],
            pdf_context=self.pdf_text[:3000],
        )

        client = OpenAI(
            api_key=os.getenv("LIMS_OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model=os.getenv("LIMS_OPENROUTER_MODEL", "openai/gpt-5"),
            messages=[
                {"role": "system", "content": system},
                *self.messages,
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "modify_mda",
                    "description": "Apply a structured edit to the MDA template",
                    "parameters": MDAEditAction.model_json_schema(),
                }
            }],
            temperature=0.2,
        )

        assistant_msg = response.choices[0].message
        self.messages.append({
            "role": "assistant",
            "content": assistant_msg.content or "",
        })

        edits_applied = []

        # Process tool calls (structured edits)
        if assistant_msg.tool_calls:
            for tool_call in assistant_msg.tool_calls:
                if tool_call.function.name == "modify_mda":
                    try:
                        edit = MDAEditAction.model_validate_json(
                            tool_call.function.arguments
                        )
                        self._apply_edit(edit)
                        edits_applied.append(edit.model_dump())
                    except (ValidationError, ValueError) as e:
                        logger.warning(f"Edit rejected for job {self.job_id}: {e}")
                        edits_applied.append({"error": str(e)})

        return {
            "response": assistant_msg.content or "",
            "edits_applied": edits_applied,
            "updated_mda": self.mda_state if edits_applied else None,
        }

    def _apply_edit(self, edit: MDAEditAction) -> None:
        """Apply a structured edit, then re-validate entire MDA.

        If validation fails, the edit is rolled back and ValueError raised.
        """
        backup = json.loads(json.dumps(self.mda_state))

        try:
            sheet_data = self.mda_state.get(edit.sheet, [])

            if edit.action == "modify":
                for item in sheet_data:
                    if all(item.get(k) == v for k, v in edit.target.items()):
                        item.update(edit.changes)
                        break

            elif edit.action == "add":
                new_item = {**edit.target, **edit.changes}
                sheet_data.append(new_item)
                self.mda_state[edit.sheet] = sheet_data

            elif edit.action == "delete":
                self.mda_state[edit.sheet] = [
                    item for item in sheet_data
                    if not all(item.get(k) == v for k, v in edit.target.items())
                ]

            # Re-validate entire MDA — CRITICAL: ensures consistency
            mda = MDATemplate.model_validate(self.mda_state)
            self.mda_state = mda.model_dump()

            self.edit_log.append({
                "timestamp": datetime.now(UTC).isoformat(),
                **edit.model_dump(),
            })

        except Exception as e:
            # Rollback on any validation failure
            self.mda_state = backup
            raise ValueError(f"Edit rejected (MDA unchanged): {e}") from e


# Per-job session store (in-memory, lost on restart)
_sessions: dict[str, ChatSession] = {}
```

### 3. Updated lims_router.py — All Endpoints

Add these endpoints to the existing router:

```python
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel


class ChatRequest(BaseModel):
    job_id: str
    message: str


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Get job status + current MDA state."""
    from main.src.lims.job_store import get_job
    try:
        job = get_job(job_id)
    except KeyError:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "mda_template": job.mda_template,
        "pdf_filename": job.pdf_filename,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


@router.post("/chat")
async def chat_with_mda(body: ChatRequest) -> dict:
    """Send chat message, receive response + optional MDA modifications.

    Only available when job status is PENDING_REVIEW.
    """
    from main.src.lims.chat_agent import ChatSession, _sessions
    from main.src.lims.job_store import get_job, LIMSJobStatus

    try:
        job = get_job(body.job_id)
    except KeyError:
        raise HTTPException(404, f"Job '{body.job_id}' not found")

    if job.status != LIMSJobStatus.PENDING_REVIEW:
        raise HTTPException(
            400,
            f"Chat only available in PENDING_REVIEW status (current: {job.status.value})",
        )

    # Create or retrieve chat session
    if body.job_id not in _sessions:
        _sessions[body.job_id] = ChatSession(
            job_id=body.job_id,
            mda_template=job.mda_template or {},
        )

    result = await asyncio.to_thread(_sessions[body.job_id].chat, body.message)

    # Update job MDA if edits were applied
    if result.get("updated_mda"):
        job.mda_template = result["updated_mda"]

    return result


@router.post("/approve/{job_id}")
async def approve_job_endpoint(job_id: str) -> dict:
    """Human approval — mandatory HITL gate. No bypass path exists."""
    from main.src.lims.job_store import approve_job, get_job

    try:
        approve_job(job_id)
        job = get_job(job_id)
    except KeyError:
        raise HTTPException(404, f"Job '{job_id}' not found")
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"job_id": job_id, "status": job.status.value}


@router.get("/export/{job_id}")
async def export_xlsx(job_id: str):
    """Download XLSX. Returns 403 if job not APPROVED.

    CRITICAL: This is the mandatory HITL enforcement point.
    No XLSX can be produced without explicit human approval.
    """
    from main.src.lims.job_store import get_job, update_status, LIMSJobStatus
    from main.src.lims.xlsx_exporter import export_mda_to_xlsx
    from main.src.lims.mda_schema import MDATemplate

    try:
        job = get_job(job_id)
    except KeyError:
        raise HTTPException(404, f"Job '{job_id}' not found")

    if job.status not in (LIMSJobStatus.APPROVED, LIMSJobStatus.EXPORTED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Export requires APPROVED status. Current: {job.status.value}. "
                f"Human must approve via POST /lims/approve/{job_id} first."
            ),
        )

    mda = MDATemplate.model_validate(job.mda_template)
    xlsx_bytes = export_mda_to_xlsx(mda)

    # Update status to EXPORTED
    if job.status == LIMSJobStatus.APPROVED:
        update_status(job_id, LIMSJobStatus.EXPORTED)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    stem = job.pdf_filename.replace(".pdf", "").replace(" ", "_")
    filename = f"MDA_{stem}_{timestamp}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

### 4. Update POST /lims/extract

The existing `POST /lims/extract` needs to:
1. Create a job via `job_store.create_job()`
2. Run extraction
3. Optionally trigger MDA generation
4. Return `{job_id, status, ...extraction_result}`

### 5. test_job_store.py — HITL Enforcement Tests

```python
"""Tests for job state machine — mandatory HITL enforcement."""

import pytest
from main.src.lims.job_store import (
    create_job, get_job, update_status, approve_job,
    LIMSJobStatus, _jobs,
)


@pytest.fixture(autouse=True)
def clear_jobs():
    """Clear job store between tests."""
    _jobs.clear()
    yield
    _jobs.clear()


class TestJobStateTransitions:
    def test_valid_forward_transitions(self):
        job_id = create_job("test.pdf")
        assert get_job(job_id).status == LIMSJobStatus.EXTRACTING

        update_status(job_id, LIMSJobStatus.GENERATING)
        assert get_job(job_id).status == LIMSJobStatus.GENERATING

        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        assert get_job(job_id).status == LIMSJobStatus.PENDING_REVIEW

    def test_cannot_skip_to_approved(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        with pytest.raises(ValueError, match="Invalid transition"):
            update_status(job_id, LIMSJobStatus.APPROVED)

    def test_cannot_skip_to_exported(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError, match="Invalid transition"):
            update_status(job_id, LIMSJobStatus.EXPORTED)


class TestMandatoryHITL:
    def test_approve_is_only_path(self):
        """The ONLY way to APPROVED is via approve_job()."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        approve_job(job_id)
        assert get_job(job_id).status == LIMSJobStatus.APPROVED

    def test_no_auto_approval(self):
        """No path bypasses human approval."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        # Stays in PENDING_REVIEW indefinitely — no timeout, no auto-progression
        assert get_job(job_id).status == LIMSJobStatus.PENDING_REVIEW

    def test_export_requires_approved(self):
        """Export from PENDING_REVIEW should fail."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError):
            update_status(job_id, LIMSJobStatus.EXPORTED)
```

---

## Testing Strategy

```bash
# 1. Run unit tests
uv run pytest main/tests/lims/test_job_store.py -v
uv run pytest main/tests/lims/test_chat_agent.py -v

# 2. Run all LIMS tests
uv run pytest main/tests/lims/ -v

# 3. Manual API flow test
curl -X POST http://localhost:8080/lims/extract -F "file=@demo_data/AND_ACS_DYE-LAB-2499.pdf"
# Returns: {"job_id": "...", "status": "PENDING_REVIEW", ...}

curl http://localhost:8080/lims/status/{job_id}
# Returns: {"status": "PENDING_REVIEW", "mda_template": {...}}

curl -X POST http://localhost:8080/lims/chat \
  -H "Content-Type: application/json" \
  -d '{"job_id": "...", "message": "Why is DYE_VOLUME result_type K?"}'

curl http://localhost:8080/lims/export/{job_id}
# Returns: 403 (not approved yet)

curl -X POST http://localhost:8080/lims/approve/{job_id}
# Returns: {"status": "APPROVED"}

curl -O http://localhost:8080/lims/export/{job_id}
# Downloads XLSX
```

---

## Gate Criteria (Pass/Fail)

- [ ] Job state machine: PENDING_REVIEW cannot transition to EXPORTED directly
- [ ] `GET /lims/export/{job_id}` returns 403 when status is PENDING_REVIEW
- [ ] `POST /lims/approve/{job_id}` is the ONLY way to reach APPROVED
- [ ] Chat modifies MDA via structured edits, invalid edits rejected with error
- [ ] Chat maintains history across messages within a session
- [ ] TTL (2h) and turn limit (50) enforced
- [ ] `uv run pytest main/tests/lims/ -v` passes

---

## Sources

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) — tools, tool_calls
- [OpenRouter API](https://openrouter.ai/docs) — OpenAI-compatible, function calling support
- [Pydantic model_json_schema](https://docs.pydantic.dev/latest/concepts/json_schema/) — generating JSON schema
- [FastAPI Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) — Response, streaming, binary
