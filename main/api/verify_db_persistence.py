import asyncio
import os
import uuid
from datetime import datetime, UTC
import asyncpg
from main.api.job_repository import PostgresJobRepository
from main.api.models import JobRecord, JobStatus

# Use the same DATABASE_URL as the app
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:devpassword@postgres:5432/testgen")

async def verify():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    repo = PostgresJobRepository(pool)
    
    job_id = str(uuid.uuid4())
    print(f"Creating test job {job_id}...")
    
    job = JobRecord(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=datetime.now(UTC),
        urs_filename="test_verify.txt",
        urs_storage_key="test/key",
        urs_hash="hash",
        urs_size_bytes=123,
        user_id="test_user"
    )
    
    try:
        await repo.create(job)
        print("Job created successfully.")
    except Exception as e:
        print(f"Failed to create job: {e}")
        await pool.close()
        return

    print("Verifying get()...")
    fetched_job = await repo.get(job_id)
    if fetched_job:
        print(f"Job found: {fetched_job.job_id}, status={fetched_job.status}")
    else:
        print("Job NOT found via get()!")

    print("Verifying get_pending_jobs()...")
    pending_jobs = await repo.get_pending_jobs()
    found = any(j.job_id == job_id for j in pending_jobs)
    if found:
        print(f"Job {job_id} found in pending list.")
    else:
        print(f"Job {job_id} NOT found in pending list. Found: {[j.job_id for j in pending_jobs]}")

    await pool.close()

if __name__ == "__main__":
    asyncio.run(verify())
