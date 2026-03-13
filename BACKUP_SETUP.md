# MongoDB Backup Setup for Reach Platform

## Overview
This document describes how to set up automated MongoDB backups for the Reach platform.

## Backup Methods

### 1. Manual Backup Script
Run the backup script manually:
```bash
cd /path/to/reach
python backup_mongodb.py
```

### 2. Automated Backups with Cron (Linux/Mac)
Add to crontab for daily backups at 2 AM:
```bash
# Edit crontab
crontab -e

# Add this line
0 2 * * * cd /path/to/reach && /usr/bin/python3 backup_mongodb.py >> /var/log/reach_backup.log 2>&1
```

### 3. Automated Backups with Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" at 2:00 AM
4. Action: "Start a program"
5. Program: `python.exe`
6. Arguments: `C:\path\to\reach\backup_mongodb.py`
7. Start in: `C:\path\to\reach`

## Configuration

### Environment Variables
Add these to your `.env` file in the `backend` directory:

```bash
# MongoDB Configuration (already exists)
MONGO_URL=mongodb://localhost:27017
DB_NAME=reach

# S3-Compatible Storage (optional)
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# For other S3-compatible services:
# DigitalOcean Spaces: https://nyc3.digitaloceanspaces.com
# Cloudflare R2: https://r2.cloudflarestorage.com
# MinIO: http://localhost:9000
```

### Local Backup Retention
The script automatically cleans up local backups after uploading to S3. If you want to keep local backups, modify the `cleanup_local()` function in `backup_mongodb.py`.

## Restore Procedure

### From Local Backup
```bash
# Restore from gzipped archive
mongorestore --uri="mongodb://localhost:27017" --archive=backup_file.gz --gzip
```

### From S3 Backup
```bash
# Download from S3 first
aws s3 cp s3://your-bucket/backups/db_20250101_020000.gz .

# Then restore
mongorestore --uri="mongodb://localhost:27017" --archive=db_20250101_020000.gz --gzip
```

## Monitoring

### Check Backup Logs
```bash
# View cron logs
tail -f /var/log/reach_backup.log

# Check script output
cd /path/to/reach
python backup_mongodb.py --verbose
```

### Verify Backups
Regularly test restore procedure to ensure backups are valid.

## Security Considerations

1. **S3 Credentials**: Store S3 credentials securely in `.env` file with restricted permissions:
   ```bash
   chmod 600 backend/.env
   ```

2. **Backup Encryption**: For sensitive data, enable server-side encryption on S3 bucket.

3. **Access Control**: Limit S3 bucket access with IAM policies.

4. **Backup Retention**: Configure S3 lifecycle policies to automatically delete old backups.

## Troubleshooting

### Common Issues

1. **mongodump not found**
   ```bash
   # Install MongoDB tools
   # Ubuntu/Debian
   sudo apt-get install mongodb-org-tools
   
   # MacOS
   brew install mongodb-community-tools
   
   # Windows: Download from MongoDB website
   ```

2. **Permission denied**
   ```bash
   # Make script executable
   chmod +x backup_mongodb.py
   ```

3. **S3 upload fails**
   - Verify S3 credentials
   - Check network connectivity
   - Verify bucket exists and is accessible

4. **Backup file too large**
   - Consider splitting backups by collection
   - Use incremental backups
   - Increase storage capacity

## Advanced Configuration

### Multiple Backup Locations
Modify the script to upload to multiple storage providers for redundancy.

### Encryption
Add encryption before uploading to S3:
```python
# Add to backup_mongodb.py
from cryptography.fernet import Fernet

def encrypt_backup(backup_file, key):
    """Encrypt backup file"""
    fernet = Fernet(key)
    with open(backup_file, 'rb') as f:
        encrypted = fernet.encrypt(f.read())
    encrypted_file = backup_file.with_suffix('.enc')
    with open(encrypted_file, 'wb') as f:
        f.write(encrypted)
    return encrypted_file
```

### Notification
Add email/Slack notifications for backup success/failure.

## Support
For issues with the backup system, check:
1. Script logs
2. MongoDB logs
3. S3 access logs
4. System resource usage during backup