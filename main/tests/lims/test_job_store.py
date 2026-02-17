"""Tests for the LIMS job store state machine and mandatory HITL enforcement.

Validates that the job state machine correctly enforces:
- Valid forward transitions through the pipeline
- PENDING_REVIEW cannot skip to EXPORTED
- approve_job() is the ONLY path to APPROVED
- No auto-approval (jobs stay in PENDING_REVIEW indefinitely)
- FAILED is a terminal state
"""

import pytest

from main.src.lims.job_store import (
    LIMSJob,
    LIMSJobStatus,
    VALID_TRANSITIONS,
    _jobs,
    approve_job,
    create_job,
    get_job,
    update_status,
)


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the in-memory job store before each test."""
    _jobs.clear()
    yield
    _jobs.clear()


class TestCreateJob:
    def test_create_job_returns_id(self):
        job_id = create_job("test.pdf")
        assert isinstance(job_id, str)
        assert len(job_id) == 32  # UUID4 hex

    def test_create_job_initial_status(self):
        job_id = create_job("test.pdf")
        job = get_job(job_id)
        assert job.status == LIMSJobStatus.EXTRACTING

    def test_create_job_stores_filename(self):
        job_id = create_job("my_document.pdf")
        job = get_job(job_id)
        assert job.pdf_filename == "my_document.pdf"

    def test_create_job_timestamps_set(self):
        job_id = create_job("test.pdf")
        job = get_job(job_id)
        assert job.created_at is not None
        assert job.updated_at is not None

    def test_create_job_empty_filename_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            create_job("")

    def test_create_job_whitespace_filename_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            create_job("   ")


class TestGetJob:
    def test_get_existing_job(self):
        job_id = create_job("test.pdf")
        job = get_job(job_id)
        assert isinstance(job, LIMSJob)
        assert job.job_id == job_id

    def test_get_nonexistent_job_raises(self):
        with pytest.raises(KeyError, match="not found"):
            get_job("nonexistent_id")


class TestValidForwardTransitions:
    """Test the happy path: EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED."""

    def test_extracting_to_generating(self):
        job_id = create_job("test.pdf")
        job = update_status(job_id, LIMSJobStatus.GENERATING)
        assert job.status == LIMSJobStatus.GENERATING

    def test_generating_to_pending_review(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        job = update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        assert job.status == LIMSJobStatus.PENDING_REVIEW

    def test_pending_review_to_approved_via_approve_job(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        job = approve_job(job_id)
        assert job.status == LIMSJobStatus.APPROVED

    def test_approved_to_exported(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        approve_job(job_id)
        job = update_status(job_id, LIMSJobStatus.EXPORTED)
        assert job.status == LIMSJobStatus.EXPORTED

    def test_full_lifecycle(self):
        """Complete lifecycle: EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED."""
        job_id = create_job("lifecycle_test.pdf")

        job = get_job(job_id)
        assert job.status == LIMSJobStatus.EXTRACTING

        update_status(job_id, LIMSJobStatus.GENERATING)
        assert get_job(job_id).status == LIMSJobStatus.GENERATING

        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        assert get_job(job_id).status == LIMSJobStatus.PENDING_REVIEW

        approve_job(job_id)
        assert get_job(job_id).status == LIMSJobStatus.APPROVED

        update_status(job_id, LIMSJobStatus.EXPORTED)
        assert get_job(job_id).status == LIMSJobStatus.EXPORTED


class TestFailedTransitions:
    """Test FAILED transitions from valid source states."""

    def test_extracting_to_failed(self):
        job_id = create_job("test.pdf")
        job = update_status(job_id, LIMSJobStatus.FAILED)
        assert job.status == LIMSJobStatus.FAILED

    def test_generating_to_failed(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        job = update_status(job_id, LIMSJobStatus.FAILED)
        assert job.status == LIMSJobStatus.FAILED


class TestMandatoryHITL:
    """Test that human-in-the-loop approval is strictly enforced."""

    def test_cannot_skip_to_approved_from_generating(self):
        """GENERATING -> APPROVED is NOT allowed -- must go through PENDING_REVIEW."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        with pytest.raises(ValueError, match="approve_job"):
            update_status(job_id, LIMSJobStatus.APPROVED)

    def test_cannot_skip_to_exported_from_pending_review(self):
        """PENDING_REVIEW -> EXPORTED is NOT allowed -- must go through APPROVED."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError, match="Invalid state transition"):
            update_status(job_id, LIMSJobStatus.EXPORTED)

    def test_cannot_skip_to_approved_from_extracting(self):
        """EXTRACTING -> APPROVED is NOT allowed."""
        job_id = create_job("test.pdf")
        with pytest.raises(ValueError, match="approve_job"):
            update_status(job_id, LIMSJobStatus.APPROVED)

    def test_update_status_blocks_approved(self):
        """update_status() NEVER allows APPROVED -- must use approve_job()."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError, match="approve_job"):
            update_status(job_id, LIMSJobStatus.APPROVED)

    def test_approve_job_is_only_path_to_approved(self):
        """approve_job() is the ONLY way to reach APPROVED status."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)

        # update_status rejects APPROVED
        with pytest.raises(ValueError, match="approve_job"):
            update_status(job_id, LIMSJobStatus.APPROVED)

        # approve_job succeeds
        job = approve_job(job_id)
        assert job.status == LIMSJobStatus.APPROVED

    def test_no_auto_approval(self):
        """Jobs in PENDING_REVIEW stay there indefinitely without human action."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)

        # Job stays in PENDING_REVIEW -- no automatic transition
        job = get_job(job_id)
        assert job.status == LIMSJobStatus.PENDING_REVIEW

    def test_approve_job_requires_pending_review(self):
        """approve_job() only works from PENDING_REVIEW."""
        job_id = create_job("test.pdf")
        # Job is in EXTRACTING -- cannot approve
        with pytest.raises(ValueError, match="PENDING_REVIEW"):
            approve_job(job_id)

    def test_approve_job_rejects_generating(self):
        """Cannot approve a job in GENERATING state."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        with pytest.raises(ValueError, match="PENDING_REVIEW"):
            approve_job(job_id)


class TestTerminalStates:
    """Test that terminal states (FAILED, EXPORTED) allow no transitions."""

    def test_failed_is_terminal(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.FAILED)

        # Cannot transition out of FAILED
        for target_status in LIMSJobStatus:
            if target_status == LIMSJobStatus.APPROVED:
                with pytest.raises(ValueError, match="approve_job"):
                    update_status(job_id, target_status)
            elif target_status != LIMSJobStatus.FAILED:
                with pytest.raises(ValueError, match="Invalid state transition"):
                    update_status(job_id, target_status)

    def test_exported_is_terminal(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        approve_job(job_id)
        update_status(job_id, LIMSJobStatus.EXPORTED)

        # Cannot transition out of EXPORTED
        for target_status in LIMSJobStatus:
            if target_status == LIMSJobStatus.APPROVED:
                with pytest.raises(ValueError, match="approve_job"):
                    update_status(job_id, target_status)
            elif target_status != LIMSJobStatus.EXPORTED:
                with pytest.raises(ValueError, match="Invalid state transition"):
                    update_status(job_id, target_status)

    def test_cannot_approve_failed_job(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.FAILED)
        with pytest.raises(ValueError, match="PENDING_REVIEW"):
            approve_job(job_id)


class TestInvalidTransitions:
    """Test various invalid transition combinations."""

    def test_cannot_go_backward_generating_to_extracting(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        with pytest.raises(ValueError, match="Invalid state transition"):
            update_status(job_id, LIMSJobStatus.EXTRACTING)

    def test_cannot_go_backward_pending_review_to_generating(self):
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError, match="Invalid state transition"):
            update_status(job_id, LIMSJobStatus.GENERATING)

    def test_cannot_fail_from_pending_review(self):
        """PENDING_REVIEW can only go to APPROVED (via approve_job)."""
        job_id = create_job("test.pdf")
        update_status(job_id, LIMSJobStatus.GENERATING)
        update_status(job_id, LIMSJobStatus.PENDING_REVIEW)
        with pytest.raises(ValueError, match="Invalid state transition"):
            update_status(job_id, LIMSJobStatus.FAILED)


class TestValidTransitionsDict:
    """Verify the VALID_TRANSITIONS mapping is complete and correct."""

    def test_all_statuses_have_entries(self):
        for status in LIMSJobStatus:
            assert status in VALID_TRANSITIONS, (
                f"Status {status.value} missing from VALID_TRANSITIONS"
            )

    def test_terminal_states_have_empty_transitions(self):
        assert VALID_TRANSITIONS[LIMSJobStatus.EXPORTED] == set()
        assert VALID_TRANSITIONS[LIMSJobStatus.FAILED] == set()

    def test_pending_review_only_allows_approved(self):
        assert VALID_TRANSITIONS[LIMSJobStatus.PENDING_REVIEW] == {
            LIMSJobStatus.APPROVED
        }
