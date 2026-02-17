# Task L5 — Backend E2E Testing: Local + Docker + Thesis Preservation

**Phase:** 5 (Full Pipeline Testing) | **PRP Tasks Merged:** L5.1, L5.2, L5.3
**Dependencies:** Task L4b (Chat Agent + HITL + Router)
**Branch:** `prjoject_p_protatype`

---

## Objective

Verify the full LIMS pipeline works end-to-end in both local and Docker environments, and confirm thesis system functionality is completely preserved with no cross-contamination.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/tests/lims/test_e2e_pipeline.py` | Full pipeline test: extract -> generate -> chat -> approve -> export (integration marker) |
| `main/tests/lims/test_thesis_preservation.py` | Verify no LIMS imports in thesis code paths, thesis tests pass |
| `scripts/test_lims_e2e.sh` | Shell script for manual curl-based E2E testing (works for both local and Docker) |

---

## Implementation Details

### 1. test_e2e_pipeline.py — Full Pipeline Test

```python
"""End-to-end pipeline test for LIMS.

Requires LIMS_LLAMAEXTRACT_API_KEY and LIMS_OPENROUTER_API_KEY.
Marked as integration test — skipped if API keys not set.
"""

import pytest
from fastapi.testclient import TestClient

from main.api.app import app

client = TestClient(app)


@pytest.mark.integration
class TestLIMSPipelineE2E:
    """Full pipeline: extract -> status -> chat -> approve -> export."""

    def test_full_pipeline(self):
        import os

        if not os.getenv("LIMS_LLAMAEXTRACT_API_KEY"):
            pytest.skip("LIMS_LLAMAEXTRACT_API_KEY not set")
        if not os.getenv("LIMS_OPENROUTER_API_KEY"):
            pytest.skip("LIMS_OPENROUTER_API_KEY not set")

        # Step 1: Extract PDF
        with open("demo_data/AND_ACS_DYE-LAB-2499.pdf", "rb") as f:
            resp = client.post(
                "/lims/extract",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        job_id = data["job_id"]
        assert job_id

        # Step 2: Check status (should be PENDING_REVIEW)
        resp = client.get(f"/lims/status/{job_id}")
        assert resp.status_code == 200
        status_data = resp.json()
        assert status_data["status"] == "PENDING_REVIEW"
        assert status_data["mda_template"] is not None

        # Step 3: Chat — ask a question
        resp = client.post(
            "/lims/chat",
            json={
                "job_id": job_id,
                "message": "Summarize the analyses in this MDA.",
            },
        )
        assert resp.status_code == 200
        chat_data = resp.json()
        assert "response" in chat_data
        assert len(chat_data["response"]) > 0

        # Step 4: Attempt export BEFORE approval -> 403
        resp = client.get(f"/lims/export/{job_id}")
        assert resp.status_code == 403
        assert "APPROVED" in resp.json()["detail"]

        # Step 5: Approve (mandatory HITL gate)
        resp = client.post(f"/lims/approve/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"

        # Step 6: Export AFTER approval -> 200 + XLSX
        resp = client.get(f"/lims/export/{job_id}")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")
        assert len(resp.content) > 100  # XLSX has content


@pytest.mark.integration
class TestExportWithoutApprovalBlocked:
    """Verify no path exists to export without approval."""

    def test_fresh_job_cannot_export(self):
        import os

        if not os.getenv("LIMS_LLAMAEXTRACT_API_KEY"):
            pytest.skip("LIMS_LLAMAEXTRACT_API_KEY not set")

        with open("demo_data/AND_ACS_AQ126-LAB-2349.pdf", "rb") as f:
            resp = client.post(
                "/lims/extract",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        job_id = resp.json()["job_id"]

        # Try to export immediately — must fail
        resp = client.get(f"/lims/export/{job_id}")
        assert resp.status_code == 403
```

### 2. test_thesis_preservation.py — Cross-Contamination Check

```python
"""Verify LIMS code does not contaminate thesis code paths.

These tests ensure the additive-only migration strategy is maintained:
no LIMS imports in thesis core modules, thesis tests still pass.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestNoLIMSImportsInThesis:
    """Ensure no LIMS imports leak into thesis code."""

    def test_no_lims_imports_in_core(self):
        """No 'from main.src.lims' in thesis core modules."""
        core_dir = Path("main/src/core")
        if not core_dir.exists():
            pytest.skip("main/src/core/ not found")

        result = subprocess.run(
            [sys.executable, "-c",
             "import pathlib; "
             "files = list(pathlib.Path('main/src/core').rglob('*.py')); "
             "matches = [(f, l) for f in files for i, l in enumerate(f.read_text().splitlines()) "
             "if 'from main.src.lims' in l or 'import main.src.lims' in l]; "
             "print('\\n'.join(f'{f}:{l}' for f, l in matches))"],
            capture_output=True, text=True,
        )
        assert result.stdout.strip() == "", (
            f"LIMS imports found in thesis core code:\n{result.stdout}"
        )

    def test_no_lims_imports_in_agents(self):
        """No LIMS imports in thesis agents."""
        agents_dir = Path("main/src/agents")
        if not agents_dir.exists():
            pytest.skip("main/src/agents/ not found")

        result = subprocess.run(
            [sys.executable, "-c",
             "import pathlib; "
             "files = list(pathlib.Path('main/src/agents').rglob('*.py')); "
             "matches = [(f, l) for f in files for i, l in enumerate(f.read_text().splitlines()) "
             "if 'from main.src.lims' in l or 'import main.src.lims' in l]; "
             "print('\\n'.join(f'{f}:{l}' for f, l in matches))"],
            capture_output=True, text=True,
        )
        assert result.stdout.strip() == "", (
            f"LIMS imports found in thesis agents code:\n{result.stdout}"
        )

    def test_thesis_docker_compose_untouched(self):
        """docker-compose.dev.yml must not reference LIMS files."""
        compose_path = Path("docker-compose.dev.yml")
        content = compose_path.read_text()
        assert "lims" not in content.lower(), (
            "docker-compose.dev.yml contains LIMS references — thesis stack contaminated"
        )
```

### 3. scripts/test_lims_e2e.sh — Manual Curl Testing

```bash
#!/bin/bash
# =============================================================================
# LIMS End-to-End Test Script
# Usage:
#   ./scripts/test_lims_e2e.sh                           # Default: localhost:8080
#   ./scripts/test_lims_e2e.sh http://localhost:8080      # Custom base URL
#   ./scripts/test_lims_e2e.sh http://localhost:8080 demo_data/other.pdf
# =============================================================================
set -e

BASE_URL="${1:-http://localhost:8080}"
PDF_FILE="${2:-demo_data/AND_ACS_DYE-LAB-2499.pdf}"

echo "========================================"
echo "  LIMS E2E Test against $BASE_URL"
echo "========================================"
echo ""

# Step 1: Health check
echo "Step 0: Health check..."
curl -sf "$BASE_URL/health" > /dev/null
echo "  OK"

# Step 1: Extract
echo ""
echo "Step 1: Extract PDF ($PDF_FILE)..."
EXTRACT_RESULT=$(curl -s -X POST "$BASE_URL/lims/extract" -F "file=@$PDF_FILE")
JOB_ID=$(echo "$EXTRACT_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
STATUS=$(echo "$EXTRACT_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'unknown'))")
echo "  Job ID: $JOB_ID"
echo "  Status: $STATUS"

# Step 2: Check status
echo ""
echo "Step 2: Check status..."
STATUS_RESULT=$(curl -s "$BASE_URL/lims/status/$JOB_ID")
echo "$STATUS_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Status: {d[\"status\"]}')"

# Step 3: Chat
echo ""
echo "Step 3: Chat (ask question)..."
CHAT_RESULT=$(curl -s -X POST "$BASE_URL/lims/chat" \
  -H "Content-Type: application/json" \
  -d "{\"job_id\": \"$JOB_ID\", \"message\": \"Summarize the extracted analyses.\"}")
echo "$CHAT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Response: {d[\"response\"][:200]}...')"

# Step 4: Export before approval (expect 403)
echo ""
echo "Step 4: Export before approval (expect 403)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/lims/export/$JOB_ID")
echo "  HTTP $HTTP_CODE (expected 403)"
if [ "$HTTP_CODE" != "403" ]; then
  echo "  FAIL: Expected 403, got $HTTP_CODE"
  exit 1
fi

# Step 5: Approve
echo ""
echo "Step 5: Approve (mandatory HITL)..."
APPROVE_RESULT=$(curl -s -X POST "$BASE_URL/lims/approve/$JOB_ID")
echo "$APPROVE_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Status: {d[\"status\"]}')"

# Step 6: Export after approval
echo ""
echo "Step 6: Export XLSX..."
curl -s -o "mda_output.xlsx" "$BASE_URL/lims/export/$JOB_ID"
SIZE=$(wc -c < mda_output.xlsx)
echo "  Downloaded: mda_output.xlsx ($SIZE bytes)"
if [ "$SIZE" -lt 100 ]; then
  echo "  FAIL: XLSX too small ($SIZE bytes)"
  exit 1
fi

echo ""
echo "========================================"
echo "  ALL STEPS PASSED"
echo "========================================"
```

---

## Testing Strategy

```bash
# 1. Run preservation tests (no API keys needed)
uv run pytest main/tests/lims/test_thesis_preservation.py -v

# 2. Run E2E tests (requires API keys)
uv run pytest main/tests/lims/test_e2e_pipeline.py -v -m integration

# 3. Run ALL tests (thesis + LIMS)
uv run pytest main/tests/ -v

# 4. Manual local E2E
uv run uvicorn main.api.app:app --port 8080
bash scripts/test_lims_e2e.sh

# 5. Docker E2E
wsl -e bash -c "docker compose -f docker-compose.lims.yml up -d"
bash scripts/test_lims_e2e.sh
wsl -e bash -c "docker compose -f docker-compose.lims.yml down"

# 6. Thesis preservation (Docker)
wsl -e bash -c "docker compose -f docker-compose.dev.yml up -d"
curl http://localhost:8080/health
wsl -e bash -c "docker compose -f docker-compose.dev.yml down"
```

---

## Gate Criteria (Pass/Fail)

- [ ] Local: `scripts/test_lims_e2e.sh` completes all 6 steps with "ALL STEPS PASSED"
- [ ] Docker: `docker compose -f docker-compose.lims.yml up -d` + E2E script passes
- [ ] Thesis: `docker compose -f docker-compose.dev.yml up -d` starts without errors
- [ ] Thesis: `uv run pytest main/tests/ -v` passes (all tests including thesis + LIMS)
- [ ] No LIMS imports in `main/src/core/` or `main/src/agents/`
- [ ] XLSX download produces valid 4-sheet file
- [ ] Export returns 403 before human approval in all test scenarios

---

## Sources

- [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html) — `@pytest.mark.integration`
- [FastAPI TestClient](https://fastapi.tiangolo.com/tutorial/testing/) — file uploads, JSON body
- [Docker Compose CLI](https://docs.docker.com/compose/reference/) — `up -d`, `down`, `logs`
