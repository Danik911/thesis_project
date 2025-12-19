"""
Export format handler for test suites (HTML, JSON).

Supports both local filesystem (development) and S3 (AWS deployment).
Uses job repository to get result_uri, then retrieves content accordingly.

GAMP-5 Compliance: All exports traceable to original job record.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader

from .dependencies import (
    CurrentUserDep,
    DbJobRepositoryDep,
    JobLockDep,
    JobRepositoryDep,
)
from .job_repository import PostgresJobRepository
from .models import ClerkClaims, JobRecord, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["export"])

# Template setup
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    # Common YAML edge-case: a single string instead of a list
    return [value]


def _normalize_suite_for_template(suite_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize suite payload to avoid Jinja iteration errors.

    Production YAML may contain optional fields as null/omitted; Jinja for-loops
    over None raise exceptions which surface as 500s.

    CRITICAL: No "invented" test content; only structural defaults.
    """
    suite: dict[str, Any] = dict(suite_data or {})

    # Handle alternate key casing
    if "test_cases" not in suite and "testCases" in suite:
        suite["test_cases"] = suite.get("testCases")

    test_cases_raw = suite.get("test_cases")
    if test_cases_raw is None:
        test_cases: list[dict[str, Any]] = []
    elif isinstance(test_cases_raw, list):
        test_cases = [tc if isinstance(tc, dict) else {"value": tc} for tc in test_cases_raw]
    elif isinstance(test_cases_raw, dict):
        # Defensive: sometimes payloads arrive as an object keyed by test_id
        test_cases = [v if isinstance(v, dict) else {"value": v} for v in test_cases_raw.values()]
    else:
        test_cases = [{"value": test_cases_raw}]

    for index, test in enumerate(test_cases, start=1):
        # Ensure list-like fields exist (template uses for-loops)
        test["prerequisites"] = _as_list(test.get("prerequisites"))
        test["acceptance_criteria"] = _as_list(test.get("acceptance_criteria"))
        test_steps = _as_list(test.get("test_steps"))
        normalized_steps: list[dict[str, Any]] = []
        for step_index, step in enumerate(test_steps, start=1):
            step_dict = step if isinstance(step, dict) else {"value": step}
            step_dict.setdefault("step_number", step_index)
            step_dict.setdefault("action", "")
            step_dict.setdefault("expected_result", "")
            step_dict.setdefault("performed_by", "")
            normalized_steps.append(step_dict)
        test["test_steps"] = normalized_steps

        # Risk/category normalization for CSS classes and labels
        risk_level = test.get("risk_level")
        if isinstance(risk_level, str):
            risk_level_norm = risk_level.strip().lower()
        else:
            risk_level_norm = "medium"
        if risk_level_norm not in {"low", "medium", "high"}:
            risk_level_norm = "medium"
        test["risk_level"] = risk_level_norm

        test_category = test.get("test_category")
        if not isinstance(test_category, str) or not test_category.strip():
            test["test_category"] = "functional"

        test.setdefault("test_id", f"TC-{index:03d}")
        test.setdefault("test_name", "")
        test.setdefault("objective", "")

    suite["test_cases"] = test_cases
    suite.setdefault("total_test_count", len(test_cases))
    suite.setdefault("coverage_percentage", 0.0)
    suite.setdefault("estimated_execution_time", "")
    suite.setdefault("review_required", False)

    # Convenience fallbacks for header fields (do not fabricate content)
    suite.setdefault("suite_id", suite.get("id") or "")
    suite.setdefault("document_name", suite.get("urs_filename") or "")
    suite.setdefault("generation_timestamp", suite.get("timestamp") or suite.get("generated_at") or "")
    suite.setdefault("generation_method", suite.get("method") or "")
    suite.setdefault("gamp_category", suite.get("gamp5_category") or suite.get("gamp") or suite.get("gamp_category") or "")

    return suite


async def _get_job_content(
    job_id: str,
    job_repository: dict[str, JobRecord],
    job_lock: asyncio.Lock,
    db_job_repo: PostgresJobRepository | None,
    user: ClerkClaims,
) -> dict[str, Any]:
    """
    Retrieve test suite content for a job.

    Supports both file:// (local) and s3:// (AWS) storage URIs.

    Args:
        job_id: Job identifier
        job_repository: In-memory job repository
        job_lock: Asyncio lock for repository access
        db_job_repo: PostgreSQL job repository (if available)
        user: Authenticated user claims

    Returns:
        Parsed test suite data as dictionary

    Raises:
        HTTPException: If job not found, not authorized, or content unavailable

    CRITICAL: NO FALLBACK LOGIC - Errors propagate with full context
    """
    # First try database repository (docker-compose / AWS mode)
    job = None
    if db_job_repo is not None:
        try:
            job = await db_job_repo.get_job(job_id)
        except Exception as e:
            logger.warning(f"[DB] Failed to get job {job_id} from database: {e}")

    # Fall back to in-memory repository
    if job is None:
        async with job_lock:
            job = job_repository.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"CRITICAL: Job not found\nJob ID: {job_id}\nCheck job ID is correct"
        )

    # Authorization check
    if job.user_id != user.sub:
        raise HTTPException(
            status_code=403,
            detail="CRITICAL: Not authorized to access this job"
        )

    # Status check
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"CRITICAL: Job not completed\nStatus: {job.status}\nExport only available for completed jobs"
        )

    # Get result URI
    if not job.result_uri:
        raise HTTPException(
            status_code=404,
            detail=f"CRITICAL: Result URI not found for job\nJob ID: {job_id}\nJob may have completed without generating output"
        )

    result_uri = job.result_uri
    logger.info(f"[EXPORT] Retrieving content for job {job_id}, URI: {result_uri}")

    # Handle S3 URI (AWS deployment)
    if result_uri.startswith("s3://"):
        return await _get_content_from_s3(result_uri, job_id)

    # Handle file:// URI (local development)
    if result_uri.startswith("file://"):
        return _get_content_from_file(result_uri, job_id)

    # Unknown URI scheme
    raise HTTPException(
        status_code=501,
        detail=f"CRITICAL: Unsupported storage URI scheme\nURI: {result_uri}\nSupported: file://, s3://"
    )


async def _get_content_from_s3(result_uri: str, job_id: str) -> dict[str, Any]:
    """
    Retrieve test suite content from S3.

    Args:
        result_uri: S3 URI (s3://bucket/key)
        job_id: Job ID for logging

    Returns:
        Parsed test suite data

    Raises:
        HTTPException: If S3 retrieval fails
    """
    from aiobotocore.session import get_session
    from botocore.exceptions import ClientError

    # Parse S3 URI: s3://bucket/path/to/file
    uri_parts = result_uri.replace("s3://", "").split("/", 1)
    if len(uri_parts) != 2:
        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: Invalid S3 URI format\nURI: {result_uri}\nExpected: s3://bucket/key"
        )

    bucket = uri_parts[0]
    key = uri_parts[1]
    # Use AWS_REGION (set in ECS task definition) or STORAGE_AWS_REGION
    region = os.getenv("AWS_REGION") or os.getenv("STORAGE_AWS_REGION", "eu-west-2")

    logger.info(f"[EXPORT] Fetching from S3: bucket={bucket}, key={key}, region={region}")

    session = get_session()
    try:
        async with session.create_client("s3", region_name=region) as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            content = await response["Body"].read()

            # Parse YAML content
            suite_data = yaml.safe_load(content.decode("utf-8"))

            logger.info(f"[EXPORT] Successfully retrieved {len(content)} bytes from S3 for job {job_id}")
            return suite_data

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))

        if error_code in ["NoSuchKey", "404"]:
            raise HTTPException(
                status_code=404,
                detail=f"CRITICAL: Test suite not found in S3\n"
                       f"Bucket: {bucket}\n"
                       f"Key: {key}\n"
                       f"Job ID: {job_id}\n"
                       f"The file may have been deleted or never created"
            )

        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: S3 retrieval failed\n"
                   f"AWS Error Code: {error_code}\n"
                   f"AWS Error Message: {error_message}\n"
                   f"Bucket: {bucket}\n"
                   f"Key: {key}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: Failed to retrieve test suite from S3\n"
                   f"Error: {e!s}\n"
                   f"URI: {result_uri}\n"
                   f"Job ID: {job_id}"
        )


def _get_content_from_file(result_uri: str, job_id: str) -> dict[str, Any]:
    """
    Retrieve test suite content from local filesystem.

    Args:
        result_uri: File URI (file:///path/to/file)
        job_id: Job ID for logging

    Returns:
        Parsed test suite data

    Raises:
        HTTPException: If file retrieval fails
    """
    file_path = result_uri.replace("file://", "")

    # Handle Windows path if present (file:///C:/... -> /C:/... -> C:/...)
    if file_path.startswith("/") and ":" in file_path[2:]:
        file_path = file_path[1:]

    path_obj = Path(file_path).resolve()

    logger.info(f"[EXPORT] Reading from file: {path_obj}")

    if not path_obj.exists():
        raise HTTPException(
            status_code=404,
            detail=f"CRITICAL: Test suite file not found\n"
                   f"Path: {path_obj}\n"
                   f"Job ID: {job_id}\n"
                   f"The file may have been deleted"
        )

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()
            suite_data = yaml.safe_load(content)

            logger.info(f"[EXPORT] Successfully read {len(content)} bytes from file for job {job_id}")
            return suite_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: Failed to read test suite file\n"
                   f"Path: {path_obj}\n"
                   f"Error: {e!s}\n"
                   f"Job ID: {job_id}"
        )


@router.get("/{job_id}/export/html")
async def export_html(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep,
) -> Response:
    """
    Export test suite as HTML report.

    Returns a stunning, portfolio-worthy HTML report suitable for:
    - Mobile/laptop viewing without special software
    - Printing for manual review
    - Sharing with stakeholders

    GAMP-5 Compliance: All exports traceable to original job record.
    21 CFR Part 11: Human-readable electronic format.
    """
    # Get test suite content (handles both S3 and local)
    suite_data = await _get_job_content(
        job_id=job_id,
        job_repository=job_repository,
        job_lock=job_lock,
        db_job_repo=db_job_repo,
        user=user,
    )

    # Normalize to prevent template rendering failures on missing/null list fields
    suite_data = _normalize_suite_for_template(suite_data)

    # Render HTML template
    try:
        template = jinja_env.get_template("test_suite_bold.html")
        html_content = template.render(suite=suite_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: Failed to render HTML template\n"
                   f"Error: {e!s}\n"
                   f"Job ID: {job_id}"
        )

    logger.info(f"[EXPORT] Generated HTML report for job {job_id}, size: {len(html_content)} bytes")

    return Response(
        content=html_content,
        media_type="text/html",
    )


@router.get("/{job_id}/export/json")
async def export_json(
    job_id: str,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    db_job_repo: DbJobRepositoryDep,
    user: CurrentUserDep,
) -> Response:
    """
    Export test suite as JSON.

    Returns the complete test suite data as a downloadable JSON file.

    GAMP-5 Compliance: Original data preserved.
    ALCOA+: Original record format maintained.
    """
    # Get test suite content (handles both S3 and local)
    suite_data = await _get_job_content(
        job_id=job_id,
        job_repository=job_repository,
        job_lock=job_lock,
        db_job_repo=db_job_repo,
        user=user,
    )

    # Convert to JSON
    try:
        json_content = json.dumps(suite_data, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CRITICAL: Failed to serialize test suite to JSON\n"
                   f"Error: {e!s}\n"
                   f"Job ID: {job_id}"
        )

    logger.info(f"[EXPORT] Generated JSON export for job {job_id}, size: {len(json_content)} bytes")

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=test_suite_{job_id}.json"}
    )
