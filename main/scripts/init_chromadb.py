"""Initialize ChromaDB from S3 on worker startup.

Task 4.2: S3 + Embedded ChromaDB Deployment

This script downloads the ChromaDB tarball from S3 and extracts it to the
local filesystem. Used by ECS worker on production startup.

Environment Variables:
    S3_CHROMADB_BUCKET: S3 bucket containing ChromaDB tarball
    S3_CHROMADB_KEY: S3 object key (default: chroma_db.tar.gz)
    RAG_VECTOR_STORE_PATH: Local path to extract ChromaDB (default: /app/chroma_db)
    AWS_REGION: AWS region for S3 (default: eu-west-2)

GAMP-5 Compliance:
    - Downloads regulatory document embeddings for RAG retrieval
    - Supports versioned S3 objects for audit trail
    - Logs all operations for traceability
"""

import logging
import os
import tarfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_chromadb_from_s3() -> Path:
    """Download and extract ChromaDB from S3 if not present.

    Returns:
        Path to the extracted ChromaDB directory.

    Raises:
        RuntimeError: If S3 download or extraction fails.
    """
    chroma_path = Path(
        os.environ.get("RAG_VECTOR_STORE_PATH", "/app/chroma_db")
    )

    # Skip if already exists (container restart or warm cache)
    if (chroma_path / "chroma.sqlite3").exists():
        logger.info(f"ChromaDB already exists at {chroma_path}")
        return chroma_path

    # Get S3 configuration
    bucket = os.environ.get("S3_CHROMADB_BUCKET")
    if not bucket:
        raise RuntimeError(
            "S3_CHROMADB_BUCKET environment variable not set. "
            "Cannot download ChromaDB for RAG retrieval."
        )

    key = os.environ.get("S3_CHROMADB_KEY", "chroma_db.tar.gz")
    region = os.environ.get("AWS_REGION", "eu-west-2")

    logger.info(f"Downloading ChromaDB from s3://{bucket}/{key}")

    try:
        s3 = boto3.client("s3", region_name=region)

        # Download to temp location
        tmp_path = Path("/tmp/chroma_db.tar.gz")
        s3.download_file(bucket, key, str(tmp_path))
        logger.info(f"Downloaded {tmp_path.stat().st_size / 1024 / 1024:.2f} MB")

        # Create parent directory if needed
        chroma_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract tarball
        # Note: The tarball should contain a 'chroma_db' directory
        with tarfile.open(tmp_path, "r:gz") as tar:
            # Security: Check for path traversal
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    raise RuntimeError(
                        f"Unsafe path in tarball: {member.name}"
                    )
            tar.extractall(chroma_path.parent)

        # Clean up temp file
        tmp_path.unlink()

        # Verify extraction
        if not (chroma_path / "chroma.sqlite3").exists():
            raise RuntimeError(
                f"ChromaDB extraction failed: {chroma_path / 'chroma.sqlite3'} not found. "
                "Check tarball structure - should contain 'chroma_db/chroma.sqlite3'"
            )

        logger.info(f"ChromaDB extracted to {chroma_path}")
        return chroma_path

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(
            f"S3 download failed ({error_code}): {e}. "
            f"Check bucket permissions and verify s3://{bucket}/{key} exists."
        ) from e


def main() -> None:
    """Entry point for script execution."""
    try:
        path = init_chromadb_from_s3()
        print(f"ChromaDB ready at: {path}")
    except RuntimeError as e:
        logger.error(str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
