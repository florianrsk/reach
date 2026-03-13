#!/usr/bin/env python3
"""
MongoDB Backup Script for Reach Platform
Automatically backs up MongoDB to S3-compatible storage
"""

import os
import sys
import subprocess
import boto3
from datetime import datetime
import logging
from pathlib import Path
import tempfile
import gzip
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip("\"'")
    else:
        logger.warning(f".env file not found at {env_path}")


def backup_mongodb():
    """Backup MongoDB database"""
    # Get MongoDB connection details
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "reach")

    # Create backup directory
    backup_dir = Path(tempfile.mkdtemp(prefix="mongodb_backup_"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{db_name}_{timestamp}.gz"

    logger.info(f"Starting MongoDB backup for database: {db_name}")
    logger.info(f"Backup file: {backup_file}")

    try:
        # Use mongodump to create backup
        cmd = [
            "mongodump",
            "--uri",
            mongo_url,
            "--db",
            db_name,
            "--archive",
            "--gzip",
            f"--out={backup_file}",
        ]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode == 0:
            logger.info("MongoDB backup completed successfully")
            return backup_file
        else:
            logger.error(f"MongoDB backup failed: {result.stderr}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB backup process error: {e}")
        return None
    except FileNotFoundError:
        logger.error("mongodump command not found. Please install MongoDB tools.")
        return None


def upload_to_s3(backup_file):
    """Upload backup file to S3-compatible storage"""
    # Get S3 configuration
    s3_endpoint = os.environ.get("S3_ENDPOINT")
    s3_bucket = os.environ.get("S3_BUCKET")
    s3_access_key = os.environ.get("S3_ACCESS_KEY")
    s3_secret_key = os.environ.get("S3_SECRET_KEY")

    if not all([s3_endpoint, s3_bucket, s3_access_key, s3_secret_key]):
        logger.warning("S3 configuration incomplete. Skipping upload.")
        return False

    try:
        # Create S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
        )

        # Upload file
        s3_key = f"backups/{backup_file.name}"
        logger.info(f"Uploading to S3: {s3_bucket}/{s3_key}")

        with open(backup_file, "rb") as f:
            s3_client.upload_fileobj(f, s3_bucket, s3_key)

        logger.info("Backup uploaded to S3 successfully")
        return True

    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return False


def cleanup_local(backup_file):
    """Clean up local backup files"""
    try:
        backup_dir = backup_file.parent
        shutil.rmtree(backup_dir)
        logger.info(f"Cleaned up local backup directory: {backup_dir}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


def main():
    """Main backup procedure"""
    logger.info("=" * 60)
    logger.info("Starting MongoDB Backup Procedure")
    logger.info("=" * 60)

    # Load environment variables
    load_env()

    # Create backup
    backup_file = backup_mongodb()
    if not backup_file:
        logger.error("Backup failed. Exiting.")
        sys.exit(1)

    # Upload to S3
    upload_success = upload_to_s3(backup_file)

    # Clean up local files
    cleanup_local(backup_file)

    # Log completion
    if upload_success:
        logger.info("✅ Backup completed and uploaded to S3")
    else:
        logger.info("✅ Backup completed (local only)")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
