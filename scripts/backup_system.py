#!/usr/bin/env python3
"""
Production Backup System for RS Systems
Backs up SQLite database and media files to S3
"""
import os
import sys
import boto3
import datetime
import subprocess
from pathlib import Path

# Configuration
S3_BUCKET = 'rs-systems-backups-20250823'
APP_DIR = '/var/app/current'  # Production EB path
LOCAL_APP_DIR = Path(__file__).parent.parent  # For local testing

def get_app_directory():
    """Get the correct application directory based on environment"""
    if os.path.exists(APP_DIR):
        return Path(APP_DIR)
    return LOCAL_APP_DIR

def backup_database():
    """Backup SQLite database to S3"""
    app_dir = get_app_directory()
    db_path = app_dir / 'db.sqlite3'
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    # Create timestamped backup filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'database_backup_{timestamp}.sqlite3'
    
    try:
        # Upload to S3
        s3 = boto3.client('s3')
        s3.upload_file(str(db_path), S3_BUCKET, f'database/{backup_filename}')
        print(f"Database backed up to S3: {backup_filename}")
        return True
    except Exception as e:
        print(f"Database backup failed: {e}")
        return False

def backup_media_files():
    """Backup media files to S3"""
    app_dir = get_app_directory()
    media_dir = app_dir / 'media'
    
    if not media_dir.exists():
        print(f"Media directory not found at {media_dir}")
        return False
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Sync media directory to S3
        cmd = [
            'aws', 's3', 'sync', 
            str(media_dir), 
            f's3://{S3_BUCKET}/media_{timestamp}/',
            '--delete'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Media files backed up to S3: media_{timestamp}/")
            return True
        else:
            print(f"Media backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Media backup failed: {e}")
        return False

def cleanup_old_backups(days_to_keep=30):
    """Remove backups older than specified days"""
    try:
        s3 = boto3.client('s3')
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        
        # List and delete old database backups
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='database/')
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    s3.delete_object(Bucket=S3_BUCKET, Key=obj['Key'])
                    print(f"Deleted old backup: {obj['Key']}")
        
        # List and delete old media backups
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='media_')
        if 'Contents' in response:
            old_prefixes = set()
            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    # Extract the media backup prefix (media_YYYYMMDD_HHMMSS)
                    prefix = '/'.join(obj['Key'].split('/')[:1]) + '/'
                    old_prefixes.add(prefix)
            
            # Delete entire old media backup directories
            for prefix in old_prefixes:
                objects_to_delete = []
                response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
                if 'Contents' in response:
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                if objects_to_delete:
                    s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': objects_to_delete})
                    print(f"Deleted old media backup: {prefix}")
        
        return True
        
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False

def main():
    """Main backup function"""
    print(f"Starting backup at {datetime.datetime.now()}")
    print(f"Backup bucket: {S3_BUCKET}")
    
    # Perform backups
    db_success = backup_database()
    media_success = backup_media_files()
    
    # Cleanup old backups
    cleanup_success = cleanup_old_backups()
    
    if db_success and media_success and cleanup_success:
        print("Backup completed successfully")
        return 0
    else:
        print("Backup completed with errors")
        return 1

if __name__ == '__main__':
    sys.exit(main())