# AWS Production Deployment Guide

Complete guide for deploying RS Systems to AWS Elastic Beanstalk with PostgreSQL, SSL/TLS, and production-grade security.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Database Configuration](#database-configuration)
- [SSL & Domain Setup](#ssl--domain-setup)
- [Security Configuration](#security-configuration)
- [Deployment Process](#deployment-process)
- [Backup & Recovery](#backup--recovery)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- **AWS CLI**: `pip install awscli` + `aws configure`
- **EB CLI**: `pip install awsebcli`
- **Git**: Version control
- **Python 3.8+**: Application runtime

### AWS Resources Required
- AWS Account with appropriate permissions
- RDS PostgreSQL database
- S3 bucket for backups
- (Optional) Route 53 for DNS management
- (Optional) ACM certificate for SSL

---

## Initial Setup

### 1. Initialize Elastic Beanstalk

```bash
cd /path/to/rs_systems_branch2
eb init

# Configuration:
# - Region: us-east-1 (N. Virginia)
# - Application name: rs_systems_branch2
# - Platform: Python 3.13
```

### 2. Set Environment Variables

```bash
# Database credentials (never commit to repo)
export DB_PASSWORD='your_secure_password'
export SECRET_KEY='your-django-secret-key'
export ADMIN_PASSWORD='secure-admin-password'
```

### 3. Create Environment

```bash
eb create rs-systems-prod \
    --database.engine postgres \
    --database.username rswradmin \
    --database.password $DB_PASSWORD \
    --database.name rswr_db \
    --envvars SECRET_KEY=$SECRET_KEY,ADMIN_PASSWORD=$ADMIN_PASSWORD,DB_PASSWORD=$DB_PASSWORD
```

---

## Database Configuration

### RDS PostgreSQL Setup

**Current Production Database:**
- **Endpoint**: `rswr-db-1.c49gy002i2n5.us-east-1.rds.amazonaws.com`
- **Port**: `5432`
- **Username**: `rswradmin`
- **Database Name**: `rswr_db`
- **Encryption**: Enabled (AWS KMS)
- **Backups**: 7-day retention

### Environment Variables

Set in `.ebextensions/04_env_vars.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    DB_NAME: rswr_db
    DB_USER: rswradmin
    DB_HOST: rswr-db-1.c49gy002i2n5.us-east-1.rds.amazonaws.com
    DB_PORT: 5432
    USE_HTTPS: true
    ENVIRONMENT: production
```

### Security Groups

Ensure RDS security group allows:
- Inbound PostgreSQL (port 5432) from EB environment security group
- No public access (security best practice)

---

## SSL & Domain Setup

### 1. Request SSL Certificate (ACM)

```bash
# Certificate for multiple domains
aws acm request-certificate \
  --domain-name rockstarwindshield.repair \
  --subject-alternative-names www.rockstarwindshield.repair app.rockstarwindshield.repair \
  --validation-method DNS \
  --region us-east-1
```

**Current Certificate ARN:**
```
arn:aws:acm:us-east-1:973196283632:certificate/b4b2be04-0d3d-4b5e-80cb-d6a98922b0d9
```

### 2. DNS Validation Records

Add to your DNS provider (e.g., Squarespace):

**Main domain validation:**
- **Name**: `_3a0a85810caea3024fc7dfc6887d89c9.rockstarwindshield.repair.`
- **Type**: CNAME
- **Value**: `_25d39035b5faed6186e94e8f8cb6a6cc.xlfgrmvvlj.acm-validations.aws.`

**www subdomain validation:**
- **Name**: `_3a0a85810caea3024fc7dfc6887d89c9.www.rockstarwindshield.repair.`
- **Type**: CNAME
- **Value**: `_25d39035b5faed6186e94e8f8cb6a6cc.xlfgrmvvlj.acm-validations.aws.`

**app subdomain validation:**
- **Name**: `_b0495e93dffe214ed843a2df8ef023a0.app.rockstarwindshield.repair.`
- **Type**: CNAME
- **Value**: `_1ef51ba7314f4da7314c2cbabec63b1f.xlfgrmvvlj.acm-validations.aws.`

### 3. Point Domain to Application

**Elastic Beanstalk CNAME:**
```
rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com
```

**DNS Records to Add:**

| Name | Type | Value |
|------|------|-------|
| `@` (root) | CNAME | `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com` |
| `www` | CNAME | `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com` |
| `app` | CNAME | `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com` |

### 4. Enable HTTPS Configuration

Once certificate status is "ISSUED":

1. Edit `.ebextensions/08_https_redirect.config`
2. Uncomment HTTPS listener configuration
3. Set environment variables:
   ```bash
   eb setenv HTTPS_AVAILABLE=true FORCE_HTTPS=true
   ```
4. Rename `09_https_redirect.config.disabled` to `09_https_redirect.config`
5. Deploy: `eb deploy`

### 5. Verify SSL Setup

```bash
# Check certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:973196283632:certificate/b4b2be04-0d3d-4b5e-80cb-d6a98922b0d9 \
  --region us-east-1

# Test HTTPS endpoints
curl -I https://rockstarwindshield.repair
curl -I https://www.rockstarwindshield.repair
curl -I https://app.rockstarwindshield.repair
```

---

## Security Configuration

### Production Security Headers

**Implemented in `apps/security/middleware.py`:**
- ✅ **Content Security Policy (CSP)** - XSS prevention
- ✅ **HTTP Strict Transport Security (HSTS)** - Force HTTPS
- ✅ **X-Frame-Options** - Clickjacking prevention
- ✅ **X-Content-Type-Options** - MIME-type sniffing prevention
- ✅ **Referrer-Policy** - Referrer information control
- ✅ **Permissions-Policy** - Browser feature restrictions
- ✅ **Cross-Origin Policies** - Cross-origin attack protection

### Session Security

```python
# settings_aws.py
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
```

### Rate Limiting

- **Login attempts**: 10/hour per IP
- **Registration**: 5/hour per IP
- **Bot protection**: Username validation, honeypot fields

### Gradual Security Enablement

If issues occur, disable security temporarily:

```python
# settings_aws.py
# Temporarily disable for troubleshooting
SECURE_SSL_REDIRECT = False  # Re-enable when HTTPS works
SESSION_COOKIE_SECURE = False  # Re-enable with HTTPS
CSRF_COOKIE_SECURE = False    # Re-enable with HTTPS
```

Then re-enable gradually after fixing issues.

---

## Deployment Process

### Initial Deployment

```bash
# 1. Ensure all environment variables are set
eb setenv KEY=value

# 2. Deploy application
eb deploy

# 3. Run database migrations
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate
exit

# 4. Create superuser
python manage.py createsu
```

### Subsequent Deployments

```bash
# 1. Commit changes
git add .
git commit -m "Description of changes"

# 2. Deploy
eb deploy

# 3. Check logs
eb logs

# 4. Open application
eb open
```

### Environment Management

```bash
# List environments
eb list

# Check environment health
eb health

# View configuration
eb config

# SSH into instance
eb ssh

# Tail logs in real-time
eb logs --stream
```

---

## Backup & Recovery

### Automated Backup System

**Backup Schedule:**
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days
- **Storage**: S3 bucket `rs-systems-backups-20250823`

**Components Backed Up:**
1. PostgreSQL database (full dump)
2. Media files (repair photos)
3. Application configuration

### Manual Backup

```bash
# Immediate database backup
eb ssh rs-systems-prod
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d).sql
aws s3 cp backup_*.sql s3://rs-systems-backups-20250823/manual/

# Media files backup
aws s3 sync /var/app/current/media/ s3://rs-systems-backups-20250823/media/
```

### Recovery Procedures

**Full System Recovery:**

```bash
# 1. Create new environment
eb create rs-systems-recovery --cfg rs-systems-prod

# 2. Restore database
aws s3 cp s3://rs-systems-backups-20250823/database/latest.sql ./
eb ssh rs-systems-recovery
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < latest.sql

# 3. Restore media files
aws s3 sync s3://rs-systems-backups-20250823/media/ /var/app/current/media/

# 4. Update DNS to point to recovery environment
```

**Partial Data Recovery:**

```bash
# Restore specific table
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME -t table_name backup.sql

# Restore specific media files
aws s3 cp s3://rs-systems-backups-20250823/media/path/to/file.jpg ./
```

### Backup Validation

```bash
# Check backup existence
aws s3 ls s3://rs-systems-backups-20250823/database/ --human-readable

# Test database backup integrity
pg_restore --list backup.sql

# Monthly recovery test
eb create rs-systems-test
# ... restore from backup ...
# ... verify functionality ...
eb terminate rs-systems-test
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check environment health
eb health

# View detailed health info
aws elasticbeanstalk describe-environment-health \
  --environment-name rs-systems-prod \
  --attribute-names All

# Check database performance
aws rds describe-db-instances \
  --db-instance-identifier rswr-db-1
```

### Log Monitoring

```bash
# View recent logs
eb logs

# Stream logs in real-time
eb logs --stream

# Download all logs
eb logs --all > production_logs.txt

# Check specific log file
eb logs --log-group /aws/elasticbeanstalk/rs-systems-prod/var/log/web.stdout.log
```

### Performance Monitoring

**CloudWatch Metrics:**
- CPU utilization
- Memory usage
- Request count
- Response time
- Error rate
- Database connections

**Database Monitoring:**
- Query performance (Performance Insights enabled)
- Connection count
- Storage usage
- Replication lag (if applicable)

### Maintenance Tasks

**Weekly:**
- Review application logs
- Check error rates
- Verify backup completion

**Monthly:**
- Review security settings
- Test backup recovery
- Update dependencies
- Review database performance

**Quarterly:**
- Security audit
- Cost optimization review
- SSL certificate renewal check
- Disaster recovery test

---

## Troubleshooting

### Deployment Issues

**502 Bad Gateway:**
```bash
# Check application logs
eb logs

# Common causes:
# 1. Django settings error
# 2. Gunicorn not starting
# 3. Health check endpoint failing

# Fix: Check /health endpoint
curl http://rs-systems-prod.elasticbeanstalk.com/health
```

**Database Connection Errors:**
```bash
# Verify security group allows EB → RDS
# Check environment variables
eb printenv

# Test database connection
eb ssh
python manage.py dbshell
```

**Static Files Not Loading:**
```bash
# Verify collectstatic ran
eb logs | grep collectstatic

# Manually run collectstatic
eb ssh
cd /var/app/current
python manage.py collectstatic --noinput
```

### SSL/HTTPS Issues

**Certificate Not Validating:**
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn ARN

# Verify DNS records are correct
nslookup _validation.rockstarwindshield.repair

# Wait up to 30 minutes for validation
```

**HTTPS Redirect Loop:**
```bash
# Check load balancer configuration
# Ensure X-Forwarded-Proto header is set
# Verify SECURE_PROXY_SSL_HEADER in settings

# Temporarily disable redirect
eb setenv FORCE_HTTPS=false
```

### Performance Issues

**High CPU Usage:**
```bash
# Check running processes
eb ssh
top

# Scale up instance type
eb scale 1 --instance-type t3.medium

# Or scale horizontally
eb scale 2
```

**Database Performance:**
```bash
# Check slow queries
# Enable Performance Insights in RDS console
# Add database indexes for frequently queried fields
```

### Common Error Patterns

| Error | Cause | Solution |
|-------|-------|----------|
| `DisallowedHost` | ALLOWED_HOSTS not configured | Add domain to ALLOWED_HOSTS |
| `CSRF verification failed` | CSRF_TRUSTED_ORIGINS missing | Add https://domain to setting |
| `OperationalError: connection refused` | Database not accessible | Check security group + DB endpoint |
| `ModuleNotFoundError` | Dependency missing | Add to requirements.txt + deploy |
| `Permission denied` | File permissions | `chown webapp:webapp` on EB instance |

---

## Production Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables configured
- [ ] Database migrations created
- [ ] Static files collected
- [ ] Secret key rotated for production
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configured
- [ ] Database backup created

### Deployment
- [ ] Code deployed successfully
- [ ] Database migrations applied
- [ ] Static files loading
- [ ] Health check passing
- [ ] All endpoints responding
- [ ] SSL certificate active
- [ ] HTTPS redirect working

### Post-Deployment
- [ ] Application functional end-to-end
- [ ] Login/authentication working
- [ ] Customer portal accessible
- [ ] Technician portal accessible
- [ ] Admin interface working
- [ ] Photo uploads functional
- [ ] Email notifications working (if configured)
- [ ] Backup system running
- [ ] Monitoring alerts configured
- [ ] DNS propagated fully

---

## Quick Reference

### Essential Commands

```bash
# Deploy
eb deploy

# View logs
eb logs

# SSH into instance
eb ssh

# Check health
eb health

# Set environment variable
eb setenv KEY=value

# Open in browser
eb open

# Restart application
eb restart

# Terminate environment
eb terminate ENVIRONMENT_NAME
```

### Important URLs

- **Production App**: https://rockstarwindshield.repair
- **Admin Interface**: https://rockstarwindshield.repair/admin/
- **API Docs**: https://rockstarwindshield.repair/api/schema/swagger-ui/
- **Health Check**: https://rockstarwindshield.repair/health

### Support Resources

- **AWS Documentation**: https://docs.aws.amazon.com/elasticbeanstalk/
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Internal Docs**: `/docs/` directory in repository

---

**Last Updated**: October 21, 2025
**Environment**: rs-systems-prod
**Region**: us-east-1
**Status**: Production Ready ✅
