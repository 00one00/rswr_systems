# RS Systems Backup & Recovery Guide

## Production Data Storage Overview

### Current Data Locations
- **Database**: SQLite file at `/var/app/current/db.sqlite3` on EC2 instance (~365KB)
- **Photos**: Media files at `/var/app/current/media/` on EC2 instance (~2.1MB, 19 images)
- **Static Files**: Served by WhiteNoise from application bundle
- **Application Code**: Deployed via Elastic Beanstalk to EC2 instance

### Data Types Stored
- **Customer Data**: Company profiles, contact information, repair requests
- **Technician Data**: User accounts, profiles, assigned repairs
- **Repair Records**: Status tracking, damage assessments, cost calculations
- **Photo Documentation**: Before/after repair images, damage documentation
- **Rewards/Referrals**: Points tracking, redemption history, referral codes

## Automated Backup System

### Backup Schedule
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days of backups kept automatically
- **Storage**: S3 bucket `rs-systems-backups-20250823`

### Backup Components
1. **Database Backup**: Complete SQLite file with timestamp
2. **Media Backup**: All repair photos and documentation
3. **Automatic Cleanup**: Removes backups older than 30 days

### Backup File Structure
```
s3://rs-systems-backups-20250823/
├── database/
│   ├── database_backup_20250823_020000.sqlite3
│   ├── database_backup_20250824_020000.sqlite3
│   └── ...
└── media_20250823_020000/
    └── repair_photos/
        ├── before/
        └── after/
```

## Manual Backup Procedures

### Immediate Backup (Emergency)
```bash
# SSH into production server
eb ssh rs-systems-production

# Run backup script manually
sudo /usr/bin/python3 /opt/backup_system.py
```

### Download Current Data (Local Development)
```bash
# Backup database from production
aws s3 cp s3://rs-systems-backups-20250823/database/database_backup_LATEST.sqlite3 ./db_backup.sqlite3

# Backup media files
aws s3 sync s3://rs-systems-backups-20250823/media_LATEST/ ./media_backup/
```

## Recovery Procedures

### Full System Recovery

1. **Deploy New Environment**
   ```bash
   eb create rs-systems-recovery --cfg rs-systems-production
   ```

2. **Restore Database**
   ```bash
   # Get latest backup
   aws s3 cp s3://rs-systems-backups-20250823/database/ ./ --recursive
   
   # Copy latest backup to new environment
   eb ssh rs-systems-recovery
   sudo cp /tmp/database_backup_LATEST.sqlite3 /var/app/current/db.sqlite3
   sudo chown webapp:webapp /var/app/current/db.sqlite3
   ```

3. **Restore Media Files**
   ```bash
   # Sync media files from latest backup
   aws s3 sync s3://rs-systems-backups-20250823/media_LATEST/ /var/app/current/media/
   sudo chown -R webapp:webapp /var/app/current/media/
   ```

4. **Update DNS**
   ```bash
   # Update domain to point to recovery environment
   aws route53 change-resource-record-sets --hosted-zone-id Z00152269ZHHL7BWWEO5 --change-batch '{
     "Changes": [{
       "Action": "UPSERT",
       "ResourceRecordSet": {
         "Name": "rockstarwindshield.repair",
         "Type": "A",
         "AliasTarget": {
           "DNSName": "NEW_LOAD_BALANCER_DNS",
           "EvaluateTargetHealth": false,
           "HostedZoneId": "Z35SXDOTRQ7X7K"
         }
       }
     }]
   }'
   ```

### Partial Data Recovery

#### Restore Specific Repair Data
```bash
# Download specific backup
aws s3 cp s3://rs-systems-backups-20250823/database/database_backup_YYYYMMDD_HHMMSS.sqlite3 ./restore.sqlite3

# Extract specific data using sqlite3
sqlite3 restore.sqlite3 "SELECT * FROM technician_portal_repair WHERE id = 'REPAIR_ID';"
```

#### Restore Lost Photos
```bash
# Find photo in backup
aws s3 ls s3://rs-systems-backups-20250823/media_YYYYMMDD_HHMMSS/repair_photos/ --recursive

# Download specific photo
aws s3 cp s3://rs-systems-backups-20250823/media_YYYYMMDD_HHMMSS/repair_photos/before/photo.jpg ./
```

## Monitoring & Alerts

### Check Backup Status
```bash
# View backup logs
eb logs rs-systems-production --all

# Check S3 backup contents
aws s3 ls s3://rs-systems-backups-20250823/database/ --human-readable
```

### Backup Validation
```bash
# Test database integrity
sqlite3 backup.sqlite3 "PRAGMA integrity_check;"

# Check backup file sizes
aws s3 ls s3://rs-systems-backups-20250823/ --recursive --human-readable --summarize
```

## Cost Optimization Notes

### Backup Storage Costs
- **Current Estimate**: ~$1-2/month for 30 days of backups
- **Database**: ~365KB per backup = ~11MB/month
- **Media**: ~2.1MB per backup = ~63MB/month
- **Total**: ~74MB/month ≈ $0.02/month storage + request costs

### Long-term Archival (Optional)
```bash
# Move old backups to Glacier for long-term storage
aws s3 cp s3://rs-systems-backups-20250823/database/old_backup.sqlite3 s3://rs-systems-archive/database/ --storage-class GLACIER
```

## Security Considerations

- **Bucket Access**: Restricted to production environment IAM role
- **Encryption**: S3 server-side encryption enabled by default
- **Access Logs**: S3 access logging should be enabled for audit trails
- **Data Retention**: Complies with business requirements for data retention

## Testing Recovery Procedures

### Monthly Recovery Test (Recommended)
```bash
# 1. Create test environment
eb create rs-systems-test

# 2. Restore from backup
# (Follow restoration procedures above)

# 3. Verify data integrity
# - Check database records
# - Verify photo uploads work
# - Test application functionality

# 4. Cleanup
eb terminate rs-systems-test
```

## Emergency Contacts & Escalation
- **Primary**: System Administrator
- **Backup**: Development Team
- **AWS Support**: Available for critical infrastructure issues

---
**Last Updated**: August 23, 2025
**Next Review**: September 23, 2025