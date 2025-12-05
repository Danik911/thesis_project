#!/usr/bin/env python3
"""
Upload ChromaDB to S3 for Lambda deployment
Run from project root: python aws/scripts/1_upload_chroma_to_s3.py

CRITICAL FIXES (2025-12-04):
- Changed source from lib/chroma_db to main/chroma_db (active data)
- Added client closure before tarball creation (prevents SQLite corruption)
- Added post-tarball verification (detects empty collections before upload)
"""
import os
import tarfile
import tempfile
import boto3
from pathlib import Path

# Configuration
CHROMA_DB_PATH = Path("main/chroma_db_v1020")  # FIXED: Created with chromadb 1.0.20 (same as Docker runtime)
S3_BUCKET = "pharma-test-gen-chromadb-275333454012"  # ECS worker bucket (from task definition)
S3_KEY = "chroma_db.tar.gz"
AWS_REGION = "eu-west-2"

def create_tarball():
    """Create compressed tarball of ChromaDB.

    IMPORTANT: Creates tarball with 'chroma_db/' as root directory.
    The init_chromadb.py script in Docker containers handles extraction
    by flattening the nested structure.

    Tarball structure:
        chroma_db.tar.gz
        └── chroma_db/
            ├── chroma.sqlite3
            └── collections/...

    Extraction target: /app/chroma_db/
    After extraction: /app/chroma_db/chroma.sqlite3 (flattened by init_chromadb.py)
    """
    print(f"[*] Creating tarball from {CHROMA_DB_PATH}...")

    if not CHROMA_DB_PATH.exists():
        raise FileNotFoundError(f"ChromaDB not found at {CHROMA_DB_PATH}")

    # Verify ChromaDB has data
    sqlite_path = CHROMA_DB_PATH / "chroma.sqlite3"
    if not sqlite_path.exists():
        raise FileNotFoundError(
            f"ChromaDB database not found at {sqlite_path}. "
            "Run seed_chroma.py first to populate collections."
        )

    # Check collection count
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        collections = client.list_collections()
        total_docs = sum(col.count() for col in collections)
        print(f"[*] Found {len(collections)} collections with {total_docs} total documents:")
        for col in collections:
            print(f"    - {col.name}: {col.count()} chunks")
        if total_docs == 0:
            raise ValueError(
                "ChromaDB collections are EMPTY! "
                "Run seed_chroma.py first to populate collections."
            )
        # CRITICAL FIX: Close client before tarball creation to prevent SQLite corruption
        del client
        print("[*] ChromaDB client closed (SQLite connection released)")
    except ImportError:
        print("[!] Warning: chromadb not installed, skipping validation")

    tarball_path = Path("chroma_db.tar.gz")

    with tarfile.open(tarball_path, "w:gz") as tar:
        # Add with 'chroma_db' as root - init_chromadb.py handles flattening
        tar.add(CHROMA_DB_PATH, arcname="chroma_db")

    size_mb = tarball_path.stat().st_size / (1024 * 1024)
    print(f"[+] Created {tarball_path} ({size_mb:.2f} MB)")

    # Verify tarball integrity before upload
    verify_tarball(tarball_path)

    return tarball_path


def verify_tarball(tarball_path):
    """Verify tarball contains populated ChromaDB.

    CRITICAL: This catches corruption where SQLite collections table is empty
    due to open client connection during tarball creation.
    """
    print(f"[*] Verifying tarball integrity...")

    with tempfile.TemporaryDirectory() as tmp:
        # Extract tarball to temp directory
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(tmp)

        # Find chroma.sqlite3
        sqlite_path = Path(tmp) / "chroma_db" / "chroma.sqlite3"
        if not sqlite_path.exists():
            raise RuntimeError(
                f"TARBALL CORRUPTION: chroma.sqlite3 not found at expected path.\n"
                f"Expected: {sqlite_path}\n"
                f"Tarball contents: {list(Path(tmp).rglob('*'))}"
            )

        # Verify collections have data
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(Path(tmp) / "chroma_db"))
            collections = client.list_collections()
            total_docs = sum(col.count() for col in collections)

            print(f"[*] Tarball verification - {len(collections)} collections, {total_docs} documents:")
            for col in collections:
                status = "OK" if col.count() > 0 else "EMPTY"
                print(f"    - {col.name}: {col.count()} chunks [{status}]")

            del client  # Close before raising exception

            if total_docs == 0:
                raise RuntimeError(
                    "TARBALL CORRUPTION DETECTED: All collections are EMPTY!\n"
                    "This indicates SQLite was captured in inconsistent state.\n"
                    "Ensure chromadb client is closed before tarball creation."
                )

            print(f"[+] Tarball verified: {total_docs} documents intact")

        except ImportError:
            print("[!] Warning: chromadb not installed, skipping tarball verification")

def upload_to_s3(tarball_path):
    """Upload tarball to S3"""
    print(f"[*] Uploading to s3://{S3_BUCKET}/{S3_KEY}...")
    
    s3 = boto3.client('s3', region_name=AWS_REGION)
    
    # Create bucket if not exists
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except:
        print(f"Creating bucket {S3_BUCKET}...")
        s3.create_bucket(
            Bucket=S3_BUCKET,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        
        # Enable versioning (compliance)
        s3.put_bucket_versioning(
            Bucket=S3_BUCKET,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=S3_BUCKET,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
    
    # Upload with metadata
    s3.upload_file(
        str(tarball_path),
        S3_BUCKET,
        S3_KEY,
        ExtraArgs={
            'Metadata': {
                'source': 'thesis_project',
                'documents': '26',
                'version': '1.0'
            }
        }
    )
    
    print(f"[+] Uploaded to s3://{S3_BUCKET}/{S3_KEY}")

    # Clean up local tarball
    tarball_path.unlink()
    print("[+] Cleaned up local tarball")

def main():
    print("[*] Starting ChromaDB S3 upload...\n")

    tarball = create_tarball()
    upload_to_s3(tarball)

    print("\n[+] Done! ChromaDB ready for ECS worker")
    print(f"    S3 URI: s3://{S3_BUCKET}/{S3_KEY}")

if __name__ == "__main__":
    main()
