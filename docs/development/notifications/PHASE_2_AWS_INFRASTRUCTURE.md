# Phase 2: AWS Infrastructure Setup

**Timeline**: Days 2-3
**Status**: Not Started
**Dependencies**: Phase 1 (Foundation & Models)

## Overview

This phase sets up the cloud infrastructure needed to deliver notifications via email (AWS SES) and SMS (AWS SNS). We'll also configure Celery with Redis for asynchronous task processing, ensuring notifications don't block web requests and can be retried on failure.

## Objectives

1. Configure AWS SES for email delivery with verified domain/sender
2. Configure AWS SNS for SMS delivery with spending limits
3. Set up Redis for Celery message broker (local + production)
4. Configure Celery for asynchronous task processing
5. Create email templates with branding and customization
6. Implement development/staging/production environment separation

## Architecture Overview

```
┌─────────────────┐
│  Django Views   │
│   (Triggers)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notification    │
│   Service       │ ← Creates Notification in DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Celery Tasks    │
│  (Async Queue)  │
└────┬────────┬───┘
     │        │
     ▼        ▼
┌─────────┐ ┌─────────┐
│   SES   │ │   SNS   │
│ (Email) │ │  (SMS)  │
└─────────┘ └─────────┘
```

**Flow:**
1. Django view triggers notification creation
2. NotificationService creates Notification record
3. Celery tasks queued for email/SMS delivery
4. Tasks execute asynchronously, calling SES/SNS
5. Delivery results logged in NotificationDeliveryLog
6. Failed deliveries automatically retried with backoff

---

## AWS SES Configuration

### What is AWS SES?

**Amazon Simple Email Service (SES)** is a cloud-based email sending service designed for:
- Transactional emails (notifications, confirmations, alerts)
- Marketing emails
- Bulk email delivery
- High deliverability rates

**Key Features:**
- $0.10 per 1,000 emails (extremely cost-effective)
- 62,000 free emails/month (if sending from EC2)
- Built-in bounce/complaint handling
- DKIM/SPF authentication for deliverability
- Detailed sending statistics and monitoring

### SES Sandbox vs Production

**Sandbox Mode** (Default):
- ✅ Free testing environment
- ✅ Can send to verified email addresses only
- ⚠️ Limited to 200 emails/day
- ⚠️ 1 email per second max send rate
- ❌ Cannot send to unverified recipients

**Production Mode** (Requires approval):
- ✅ Send to any email address
- ✅ 50,000+ emails/day (scalable)
- ✅ 14 emails/second send rate
- ✅ Full reputation monitoring
- ⚠️ Requires completing SES sending limit increase request

### Step 1: Set Up SES in AWS Console

**1.1 Access SES Console**
```
Navigate to: AWS Console → Services → Simple Email Service
Select Region: us-east-1 (or your preferred region)
```

**1.2 Verify Email Domain (Recommended)**

Verifying your domain allows sending from any address @yourdomain.com:

```
1. SES Console → Configuration → Verified Identities → Create Identity
2. Select "Domain"
3. Enter your domain (e.g., rssystems.com)
4. Enable DKIM signing (recommended for deliverability)
5. AWS provides DNS records (TXT, CNAME, MX)
6. Add these records to your DNS provider (Route 53, GoDaddy, etc.)
7. Wait for verification (usually 24-72 hours)
```

**DNS Records Example:**
```
# TXT Record for domain verification
_amazonses.rssystems.com  TXT  "abc123xyz..."

# CNAME Records for DKIM (3 records)
abc._domainkey.rssystems.com  CNAME  abc.dkim.amazonses.com
def._domainkey.rssystems.com  CNAME  def.dkim.amazonses.com
ghi._domainkey.rssystems.com  CNAME  ghi.dkim.amazonses.com

# MX Record for bounce handling (optional)
rssystems.com  MX  10 feedback-smtp.us-east-1.amazonses.com
```

**1.3 Verify Individual Email (For Testing)**

For development/testing before domain verification:

```
1. SES Console → Verified Identities → Create Identity
2. Select "Email Address"
3. Enter email: notifications@rssystems.com
4. Click "Create Identity"
5. Check email inbox for verification link
6. Click verification link
```

**1.4 Request Production Access**

When ready to send to customers:

```
1. SES Console → Account Dashboard → "Request production access"
2. Fill out form:
   - Mail type: Transactional
   - Website URL: https://rssystems.com
   - Use case description: "Repair notification system for fleet managers and technicians.
     Sends transactional notifications for repair status changes, approvals, and assignments."
   - Compliance: Describe opt-out mechanism and privacy policy
   - Expected daily volume: Start with 1,000/day estimate
3. Submit request
4. AWS typically approves within 24-48 hours
```

### Step 2: Create IAM User for SES Access

**2.1 Create IAM Policy**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:SendTemplatedEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:GetSendStatistics",
        "ses:GetSendQuota"
      ],
      "Resource": "*"
    }
  ]
}
```

**2.2 Create IAM User**

```
1. IAM Console → Users → Add User
2. User name: ses-smtp-user
3. Access type: Programmatic access
4. Attach policy created above
5. Download credentials (Access Key ID and Secret Access Key)
6. Store securely in password manager
```

**2.3 (Alternative) Use SMTP Credentials**

SES also supports SMTP authentication:

```
1. SES Console → SMTP Settings → Create SMTP Credentials
2. IAM user name: ses-smtp-user-prod
3. Download SMTP credentials
4. Note SMTP endpoint: email-smtp.us-east-1.amazonaws.com
5. Port: 587 (TLS) or 465 (SSL)
```

### Step 3: Configure Django Settings

**File**: `rs_systems/settings.py` (Development)

```python
# Email Configuration (Development - Console Backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development: Emails print to console instead of sending
# This allows testing email content without actually sending

# For local SES testing, uncomment:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('AWS_SES_SMTP_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('AWS_SES_SMTP_PASSWORD')
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'notifications@rssystems.com')
```

**File**: `rs_systems/settings_aws.py` (Production)

```python
import os

# Email Configuration (Production - AWS SES)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SES SMTP Settings
EMAIL_HOST = os.environ.get('AWS_SES_HOST', 'email-smtp.us-east-1.amazonaws.com')
EMAIL_PORT = int(os.environ.get('AWS_SES_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # Use TLS on port 587, not SSL

# SES Credentials (from IAM user)
EMAIL_HOST_USER = os.environ.get('AWS_SES_SMTP_USER')
EMAIL_HOST_PASSWORD = os.environ.get('AWS_SES_SMTP_PASSWORD')

# Sender information
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'notifications@rssystems.com')
DEFAULT_FROM_NAME = os.environ.get('DEFAULT_FROM_NAME', 'RS Systems')
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # For error emails

# SES Configuration
AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION', 'us-east-1')
AWS_SES_CONFIGURATION_SET = os.environ.get('AWS_SES_CONFIGURATION_SET', '')  # Optional: for tracking

# Email rate limiting (to avoid SES limits)
EMAIL_RATE_LIMIT = int(os.environ.get('EMAIL_RATE_LIMIT', 14))  # Emails per second (stay under SES limit)

# Bounce/Complaint handling
AWS_SES_BOUNCE_TOPIC_ARN = os.environ.get('AWS_SES_BOUNCE_TOPIC_ARN', '')
AWS_SES_COMPLAINT_TOPIC_ARN = os.environ.get('AWS_SES_COMPLAINT_TOPIC_ARN', '')
```

### Step 4: Environment Variables

**File**: `.env` (Add these variables)

```bash
# AWS SES Configuration
AWS_SES_SMTP_USER=AKIAIOSFODNN7EXAMPLE
AWS_SES_SMTP_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_SES_REGION=us-east-1
AWS_SES_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_PORT=587

# Email Settings
DEFAULT_FROM_EMAIL=notifications@rssystems.com
DEFAULT_FROM_NAME=RS Systems Notifications
ADMIN_EMAIL=admin@rssystems.com

# Optional: SES Configuration Set for tracking
AWS_SES_CONFIGURATION_SET=rs-systems-notifications
```

**Security Notes:**
- ⚠️ **NEVER commit `.env` to version control**
- ✅ Add `.env` to `.gitignore`
- ✅ Use AWS Secrets Manager for production credentials
- ✅ Rotate credentials regularly (every 90 days)

### Step 5: Test SES Configuration

**Create test management command**: `apps/core/management/commands/test_ses.py`

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test AWS SES email configuration'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        recipient = options['recipient']

        self.stdout.write(f'Sending test email to {recipient}...')

        try:
            send_mail(
                subject='RS Systems - SES Test Email',
                message='This is a test email from RS Systems notification system.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Email sent successfully to {recipient}'))
            self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
            self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email: {str(e)}'))
```

**Run test:**
```bash
# Development (console output)
python manage.py test_ses your.email@example.com

# Production (actual send)
USE_AWS_DB=true python manage.py test_ses your.verified@email.com
```

---

## AWS SNS Configuration

### What is AWS SNS?

**Amazon Simple Notification Service (SNS)** is a pub/sub messaging service that supports:
- SMS text messages
- Push notifications
- Email notifications
- Application-to-application messaging

**For our use case:** SMS delivery for high-priority notifications.

**Pricing:**
- $0.00645 per SMS (US)
- International rates vary ($0.02 - $0.50 per SMS)
- No monthly fees or minimum commitments

### Step 1: Enable SMS in SNS Console

**1.1 Access SNS Console**
```
Navigate to: AWS Console → Services → Simple Notification Service
Select Region: us-east-1 (SNS SMS is region-specific)
```

**1.2 Set SMS Preferences**

```
1. SNS Console → Text Messaging (SMS) → Text messaging preferences
2. Configure:
   - Default message type: Transactional (higher deliverability, higher cost)
   - Account spend limit: $10.00/month (adjust as needed)
   - Default sender ID: "RS Systems" (not supported in US, but works internationally)
   - Use case: Transactional notifications
3. Save preferences
```

**Message Types:**
- **Transactional**: Time-sensitive messages (OTP, alerts). Higher priority, higher cost.
- **Promotional**: Marketing messages. Lower priority, lower cost, may be throttled.

**1.3 Set Spending Limits**

```
1. SNS Console → Text Messaging (SMS) → Spending limits
2. Set monthly spending limit (e.g., $50)
3. Enable spend limit alerts:
   - Alert at 80% threshold → email to admin@rssystems.com
   - Alert at 100% threshold → email + stop sending
4. Save settings
```

**Why set limits?**
- Prevents unexpected costs from spam/abuse
- Alerts before hitting limit
- Production safety measure

### Step 2: Create IAM User for SNS Access

**2.1 Create IAM Policy**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish",
        "sns:PublishBatch"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:GetSMSAttributes",
        "sns:SetSMSAttributes"
      ],
      "Resource": "*"
    }
  ]
}
```

**2.2 Create IAM User**

```
1. IAM Console → Users → Add User
2. User name: sns-sms-user
3. Access type: Programmatic access
4. Attach policy created above
5. Download credentials (Access Key ID and Secret Access Key)
```

### Step 3: Configure Django Settings

**File**: `rs_systems/settings_aws.py`

```python
import os
import boto3

# AWS SNS Configuration (SMS)
AWS_SNS_REGION_NAME = os.environ.get('AWS_SNS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')  # Shared with S3
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')  # Shared with S3

# SNS Client (initialized in services)
# from boto3 import client
# sns_client = client(
#     'sns',
#     region_name=AWS_SNS_REGION_NAME,
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
# )

# SMS Settings
SMS_ENABLED = os.environ.get('SMS_ENABLED', 'False').lower() == 'true'
SMS_DEFAULT_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'RS Systems')  # Not used in US
SMS_MAX_PRICE_USD = float(os.environ.get('SMS_MAX_PRICE_USD', '0.50'))  # Max price per SMS

# SMS rate limiting
SMS_RATE_LIMIT = int(os.environ.get('SMS_RATE_LIMIT', 10))  # SMS per second
```

### Step 4: Environment Variables

**File**: `.env` (Add these variables)

```bash
# AWS SNS Configuration (SMS)
AWS_SNS_REGION=us-east-1
SMS_ENABLED=true
SMS_SENDER_ID=RS Systems
SMS_MAX_PRICE_USD=0.50

# AWS Credentials (shared with S3, SES)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Step 5: Test SNS Configuration

**Create test management command**: `apps/core/management/commands/test_sns.py`

```python
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

class Command(BaseCommand):
    help = 'Test AWS SNS SMS configuration'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Phone number in E.164 format (+12025551234)')

    def handle(self, *args, **options):
        phone = options['phone']

        # Validate E.164 format
        if not phone.startswith('+'):
            self.stdout.write(self.style.ERROR('❌ Phone must be in E.164 format: +12025551234'))
            return

        self.stdout.write(f'Sending test SMS to {phone}...')

        try:
            sns_client = boto3.client(
                'sns',
                region_name=settings.AWS_SNS_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            response = sns_client.publish(
                PhoneNumber=phone,
                Message='This is a test SMS from RS Systems notification system.',
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )

            self.stdout.write(self.style.SUCCESS(f'✅ SMS sent successfully!'))
            self.stdout.write(f'Message ID: {response["MessageId"]}')
            self.stdout.write(f'Region: {settings.AWS_SNS_REGION_NAME}')

        except ClientError as e:
            self.stdout.write(self.style.ERROR(f'❌ AWS Error: {e.response["Error"]["Message"]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send SMS: {str(e)}'))
```

**Run test:**
```bash
python manage.py test_sns +12025551234
```

---

## Celery Configuration

### What is Celery?

**Celery** is a distributed task queue for Python that enables:
- **Asynchronous execution**: Don't block web requests waiting for email/SMS
- **Task scheduling**: Schedule notifications for future delivery
- **Retry logic**: Automatically retry failed deliveries
- **Rate limiting**: Control delivery speed to avoid provider limits
- **Monitoring**: Track task status and failures

### Why Celery for Notifications?

**Without Celery (Synchronous):**
```python
def approve_repair(request, repair_id):
    repair = Repair.objects.get(id=repair_id)
    repair.status = 'APPROVED'
    repair.save()

    # This blocks the request for 2-5 seconds!
    send_email(repair.technician.email, 'Repair Approved', ...)
    send_sms(repair.technician.phone_number, 'Repair #123 approved')

    return JsonResponse({'success': True})
```

**With Celery (Asynchronous):**
```python
def approve_repair(request, repair_id):
    repair = Repair.objects.get(id=repair_id)
    repair.status = 'APPROVED'
    repair.save()

    # Queue tasks and return immediately (~50ms)
    send_notification_email.delay(repair.id, 'approved')
    send_notification_sms.delay(repair.id, 'approved')

    return JsonResponse({'success': True})  # Returns instantly!
```

**Benefits:**
- ✅ Fast response times (no waiting for external APIs)
- ✅ Automatic retries on failure
- ✅ Rate limiting to avoid provider throttling
- ✅ Scalable (add more workers as volume grows)
- ✅ Monitoring and alerting

### Step 1: Install Celery and Redis

**Update**: `requirements.txt`

```txt
# Existing dependencies...

# Celery for async task processing
celery==5.3.4
redis==5.0.1

# Celery monitoring (optional)
flower==2.0.1  # Web UI for monitoring Celery tasks
```

**Install:**
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Redis

**Redis** is the message broker that stores Celery tasks.

**Development (Local Redis):**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

**Production (AWS ElastiCache):**

```
1. AWS Console → ElastiCache → Redis → Create
2. Configuration:
   - Engine: Redis
   - Version: 7.0 or latest
   - Node type: cache.t3.micro (starts small, can scale)
   - Number of replicas: 1 (for high availability)
3. Subnet group: Place in same VPC as Django app
4. Security group: Allow port 6379 from Django security group
5. Create cluster
6. Note endpoint: rs-systems-redis.abc123.0001.use1.cache.amazonaws.com:6379
```

### Step 3: Configure Celery

**File**: `rs_systems/celery.py` (Create new file)

```python
import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rs_systems.settings')

# Determine which settings to use
if os.environ.get('ENVIRONMENT') == 'production':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'rs_systems.settings_aws'

# Create Celery app
app = Celery('rs_systems')

# Load configuration from Django settings (CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic task schedule (for retries, digests, etc.)
app.conf.beat_schedule = {
    # Retry failed notification deliveries every 5 minutes
    'retry-failed-notifications': {
        'task': 'apps.core.tasks.retry_failed_notifications',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },

    # Send daily digest emails at 9 AM
    'send-daily-digests': {
        'task': 'apps.core.tasks.send_daily_digests',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },

    # Cleanup old notification logs weekly
    'cleanup-old-logs': {
        'task': 'apps.core.tasks.cleanup_old_delivery_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # 2 AM Sunday
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f'Request: {self.request!r}')
```

**File**: `rs_systems/__init__.py` (Update existing file)

```python
# Existing imports...

# Import Celery app to ensure it's loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Step 4: Configure Django Settings for Celery

**File**: `rs_systems/settings.py` (Development)

```python
import os

# Celery Configuration (Development - Local Redis)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Celery settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/New_York'  # Match your application timezone
CELERY_ENABLE_UTC = True

# Task routing (send notification tasks to specific queue)
CELERY_TASK_ROUTES = {
    'apps.core.tasks.send_notification_email': {'queue': 'notifications'},
    'apps.core.tasks.send_notification_sms': {'queue': 'notifications'},
    'apps.core.tasks.retry_failed_notifications': {'queue': 'notifications'},
}

# Task time limits (prevent hanging tasks)
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit

# Retry configuration
CELERY_TASK_ACKS_LATE = True  # Tasks acknowledged after completion (safer)
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Requeue if worker crashes

# Concurrency (number of worker processes)
CELERY_WORKER_CONCURRENCY = 4  # Adjust based on server resources

# Development: Eager execution (tasks run synchronously for easier debugging)
# Uncomment to disable async during development:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True
```

**File**: `rs_systems/settings_aws.py` (Production)

```python
import os

# Celery Configuration (Production - AWS ElastiCache)
CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL',
    'redis://rs-systems-redis.abc123.0001.use1.cache.amazonaws.com:6379/0'
)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)

# Production Celery settings (inherit from settings.py and override)
CELERY_WORKER_CONCURRENCY = int(os.environ.get('CELERY_CONCURRENCY', 8))
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart workers after 1000 tasks (prevents memory leaks)

# Production: Never use eager mode
CELERY_TASK_ALWAYS_EAGER = False

# Rate limiting for external APIs
CELERY_ANNOTATIONS = {
    'apps.core.tasks.send_notification_email': {
        'rate_limit': '14/s',  # Match SES limit (14 emails/second)
    },
    'apps.core.tasks.send_notification_sms': {
        'rate_limit': '10/s',  # Conservative SMS rate limit
    },
}

# Monitoring (optional: integrate with Sentry, Datadog, etc.)
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_SEND_TASK_SENT_EVENT = True
```

### Step 5: Environment Variables

**File**: `.env`

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_CONCURRENCY=4

# Production (ElastiCache)
# CELERY_BROKER_URL=redis://rs-systems-redis.abc123.0001.use1.cache.amazonaws.com:6379/0
```

### Step 6: Run Celery Workers

**Development:**

```bash
# Terminal 1: Run Django development server
python manage.py runserver

# Terminal 2: Run Celery worker
celery -A rs_systems worker --loglevel=info --concurrency=4

# Terminal 3: Run Celery beat (for scheduled tasks)
celery -A rs_systems beat --loglevel=info

# Terminal 4 (Optional): Run Flower (monitoring UI)
celery -A rs_systems flower
# Access at http://localhost:5555
```

**Production (Systemd Service):**

**File**: `/etc/systemd/system/celery-worker.service`

```ini
[Unit]
Description=Celery Worker for RS Systems
After=network.target redis.target

[Service]
Type=forking
User=django
Group=django
WorkingDirectory=/var/www/rs_systems
Environment="PATH=/var/www/rs_systems/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=rs_systems.settings_aws"
ExecStart=/var/www/rs_systems/venv/bin/celery -A rs_systems worker \
    --loglevel=info \
    --concurrency=8 \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**File**: `/etc/systemd/system/celery-beat.service`

```ini
[Unit]
Description=Celery Beat Scheduler for RS Systems
After=network.target redis.target

[Service]
Type=simple
User=django
Group=django
WorkingDirectory=/var/www/rs_systems
Environment="PATH=/var/www/rs_systems/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=rs_systems.settings_aws"
ExecStart=/var/www/rs_systems/venv/bin/celery -A rs_systems beat \
    --loglevel=info \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

---

## Implementation Checklist

### AWS SES
- [ ] Verify email domain in SES console
- [ ] Add DNS records (TXT, CNAME for DKIM)
- [ ] Wait for domain verification (24-72 hours)
- [ ] Create IAM user with SES permissions
- [ ] Add SES credentials to `.env`
- [ ] Configure Django email settings
- [ ] Test email sending with management command
- [ ] Request production access (exit sandbox)

### AWS SNS
- [ ] Enable SMS in SNS console
- [ ] Set spending limits and alerts
- [ ] Create IAM user with SNS permissions
- [ ] Add SNS credentials to `.env`
- [ ] Configure Django SNS settings
- [ ] Test SMS sending with management command
- [ ] Monitor costs in first week

### Celery & Redis
- [ ] Install Redis (local or ElastiCache)
- [ ] Install Celery and dependencies
- [ ] Create `celery.py` configuration
- [ ] Update Django settings for Celery
- [ ] Test Celery worker locally
- [ ] Configure Celery Beat for scheduled tasks
- [ ] Set up Flower monitoring (optional)
- [ ] Create systemd services for production
- [ ] Test task execution and retries

### Environment Setup
- [ ] Add all environment variables to `.env`
- [ ] Document environment variables in README
- [ ] Set up separate .env files for dev/staging/prod
- [ ] Configure environment variable loading in settings

---

## Success Criteria

✅ Domain verified in SES, can send emails to any address
✅ SMS enabled in SNS, spending limits configured
✅ Celery workers running and processing tasks
✅ Redis connected and stable
✅ Test emails delivered successfully
✅ Test SMS delivered successfully
✅ Celery Beat scheduling periodic tasks
✅ Monitoring configured (Flower or equivalent)

---

## Next Phase

Once Phase 2 is complete, proceed to:
**Phase 3: Service Layer** - Build NotificationService, EmailService, and SMSService for actual notification delivery.

---

## Cost Estimates

### Monthly Cost Projection

**Assumptions:**
- 100 technicians, 50 customers
- Average 10 notifications/user/day = 1,500 notifications/day = 45,000/month

**Email (SES):**
- 45,000 emails/month × 60% medium priority = 27,000 emails
- 27,000 × $0.0001 = **$2.70/month**

**SMS (SNS):**
- 45,000 notifications/month × 30% high/urgent priority = 13,500 SMS
- 13,500 × $0.00645 = **$87.08/month**

**Redis (ElastiCache):**
- cache.t3.micro: **$12.96/month**
- cache.t3.small (if needed): **$25.92/month**

**Total Monthly Cost: ~$102/month**

**Cost Optimization:**
- Use email for non-urgent notifications (much cheaper)
- Allow users to opt out of SMS for non-critical notifications
- Batch daily digest emails instead of individual emails
- Monitor SMS usage weekly, adjust preferences as needed

---

## Monitoring & Alerts

### CloudWatch Alarms (Set up in AWS Console)

**SES Monitoring:**
- Bounce rate > 5% → Alert
- Complaint rate > 0.1% → Alert
- Daily send volume approaching limit → Alert

**SNS Monitoring:**
- SMS spend > $50/month → Alert at 80%
- SMS failures > 5% → Alert
- Daily SMS volume spike (>500 in hour) → Alert

**Celery Monitoring (Flower):**
- Worker offline → Alert
- Task failure rate > 10% → Alert
- Queue depth > 1000 → Alert (backlog building)

### Logging

**Configure logging in settings.py:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/rs_systems/celery.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
        },
    },
}
```
