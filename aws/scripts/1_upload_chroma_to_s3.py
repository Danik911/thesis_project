#!/usr/bin/env python3
"""
Upload ChromaDB to S3 for Lambda deployment
Run from project root: python aws/scripts/1_upload_chroma_to_s3.py
"""
import os
import tarfile
import boto3
from pathlib import Path

# Configuration
CHROMA_DB_PATH = Path("chroma_db")
S3_BUCKET = "pharma-vectors-eu"
S3_KEY = "chroma_db.tar.gz"
AWS_REGION = "eu-west-2"

def create_tarball():
    """Create compressed tarball of ChromaDB"""
    print(f"📦 Creating tarball from {CHROMA_DB_PATH}...")
    
    if not CHROMA_DB_PATH.exists():
        raise FileNotFoundError(f"ChromaDB not found at {CHROMA_DB_PATH}")
    
    tarball_path = Path("chroma_db.tar.gz")
    
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(CHROMA_DB_PATH, arcname="chroma_db")
    
    size_mb = tarball_path.stat().st_size / (1024 * 1024)
    print(f"✅ Created {tarball_path} ({size_mb:.2f} MB)")
    
    return tarball_path

def upload_to_s3(tarball_path):
    """Upload tarball to S3"""
    print(f"☁️  Uploading to s3://{S3_BUCKET}/{S3_KEY}...")
    
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
    
    print(f"✅ Uploaded to s3://{S3_BUCKET}/{S3_KEY}")
    
    # Clean up local tarball
    tarball_path.unlink()
    print("🧹 Cleaned up local tarball")

def main():
    print("🚀 Starting ChromaDB S3 upload...\n")
    
    tarball = create_tarball()
    upload_to_s3(tarball)
    
    print("\n✅ Done! ChromaDB ready for Lambda deployment")
    print(f"   S3 URI: s3://{S3_BUCKET}/{S3_KEY}")

if __name__ == "__main__":
    main()
