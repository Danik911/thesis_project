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
import shutil
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
        # Note: The tarball contains a 'chroma_db' directory that needs to be
        # flattened to avoid nested /app/chroma_db/chroma_db/ structure
        with tarfile.open(tmp_path, "r:gz") as tar:
            # Security: Check for path traversal
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    raise RuntimeError(
                        f"Unsafe path in tarball: {member.name}"
                    )

            # Extract to temp directory first to handle nested structure
            extract_dir = chroma_path.parent / "chroma_extract_tmp"
            extract_dir.mkdir(parents=True, exist_ok=True)
            tar.extractall(extract_dir)

        # Handle nested chroma_db directory from tarball
        # Tarball structure: chroma_db/chroma.sqlite3, chroma_db/collections/...
        # We need: /app/chroma_db/chroma.sqlite3 (not /app/chroma_db/chroma_db/)
        nested_dir = extract_dir / "chroma_db"
        if nested_dir.exists() and nested_dir.is_dir():
            logger.info(f"Flattening nested chroma_db directory from tarball")
            # Ensure target directory exists
            chroma_path.mkdir(parents=True, exist_ok=True)
            # Move contents from nested directory to target
            for item in nested_dir.iterdir():
                dest = chroma_path / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            # Clean up temp extraction directory
            shutil.rmtree(extract_dir)
        else:
            # Direct extraction (tarball structure doesn't have nested dir)
            logger.info(f"Direct extraction (no nested directory)")
            chroma_path.mkdir(parents=True, exist_ok=True)
            for item in extract_dir.iterdir():
                dest = chroma_path / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            shutil.rmtree(extract_dir)

        # Clean up temp file
        tmp_path.unlink()

        # Verify extraction - file exists
        if not (chroma_path / "chroma.sqlite3").exists():
            raise RuntimeError(
                f"ChromaDB extraction failed: {chroma_path / 'chroma.sqlite3'} not found. "
                "Check tarball structure - should contain 'chroma_db/chroma.sqlite3'"
            )

        logger.info(f"ChromaDB extracted to {chroma_path}")

        # DEBUG: Verify what ChromaDB actually contains BEFORE Context Provider initializes
        # NOTE: Must use SAME settings as context_provider.py to avoid
        # "An instance of Chroma already exists with different settings" error
        try:
            import chromadb
            logger.info(f"DEBUG: Opening ChromaDB at {chroma_path} to verify contents...")
            # Use matching settings to avoid conflict with Context Provider
            debug_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=chromadb.Settings(
                    anonymized_telemetry=False  # Must match context_provider.py
                )
            )
            collections = debug_client.list_collections()
            logger.info(f"DEBUG: Found {len(collections)} collections in extracted ChromaDB:")
            for col in collections:
                count = col.count()
                logger.info(f"DEBUG:   - {col.name}: {count} documents")
            # Close client to release SQLite lock - use proper reset
            # Note: del alone doesn't fully release ChromaDB instance tracking
            # The matching settings now ensures compatibility with Context Provider
            del debug_client
            logger.info("DEBUG: ChromaDB verification complete, client closed")
        except Exception as e:
            logger.error(f"DEBUG: Failed to verify ChromaDB contents: {e}")

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
