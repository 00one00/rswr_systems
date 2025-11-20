# Phase 6: Monitoring, Testing & Deployment

**Timeline**: Days 7-8
**Status**: Not Started
**Dependencies**: All previous phases

## Overview

This final phase focuses on production readiness: comprehensive testing, monitoring setup, performance optimization, and deployment procedures. We'll ensure the notification system is reliable, scalable, and maintainable.

## Objectives

1. Create comprehensive test suite (unit, integration, end-to-end)
2. Set up monitoring and alerting (CloudWatch, Sentry, logs)
3. Implement performance optimizations
4. Create admin dashboard for notification management
5. Document deployment procedures
6. Create runbooks for common issues
7. Perform load testing
8. Plan gradual rollout strategy

---

## Testing Strategy

### Test Coverage Goals

- **Unit Tests**: 90%+ coverage for services and models
- **Integration Tests**: All signal handlers and workflows
- **End-to-End Tests**: Critical notification paths
- **Load Tests**: Handle 1000 notifications/minute

### Unit Tests

**File**: `apps/core/tests/test_notification_service.py`

```python
from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.models import (
    Notification,
    NotificationTemplate,
    EmailBrandingConfig,
    TechnicianNotificationPreference,
)
from apps.core.services.notification_service import NotificationService
from apps.technician_portal.models import Technician, Repair
from apps.core.models import Customer

class NotificationServiceTestCase(TestCase):
    """Test NotificationService functionality"""

    def setUp(self):
        """Set up test data"""
        # Create user and technician
        self.user = User.objects.create_user(
            username='testtech',
            email='tech@test.com',
            first_name='Test',
            last_name='Technician'
        )
        self.technician = Technician.objects.create(
            user=self.user,
            phone_number='+12025551234'
        )

        # Create customer
        self.customer = Customer.objects.create(
            company_name='Test Company',
            email='customer@test.com',
            phone='+12025555678'
        )

        # Create repair
        self.repair = Repair.objects.create(
            unit_number='TEST-001',
            customer=self.customer,
            technician=self.technician,
            queue_status='PENDING',
            cost=250.00,
            break_description='Test break'
        )

        # Create branding config
        EmailBrandingConfig.objects.create(
            company_name='RS Systems Test'
        )

        # Create notification template
        self.template = NotificationTemplate.objects.create(
            name='repair_approved',
            description='Repair approval notification',
            category='approval',
            default_priority='URGENT',
            title_template='Repair #{{ repair.id }} Approved',
            message_template='Your repair for {{ repair.unit_number }} has been approved!',
            email_subject_template='Repair Approved - #{{ repair.id }}',
            email_html_template='<p>Approved!</p>',
            email_text_template='Approved!',
            sms_template='Repair #{{ repair.id }} approved!',
            required_context=['repair', 'technician'],
            active=True
        )

        # Create preferences
        self.preferences = TechnicianNotificationPreference.objects.create(
            technician=self.technician,
            receive_email_notifications=True,
            receive_sms_notifications=True,
            email_verified=True,
            phone_verified=True
        )

    def test_create_notification_success(self):
        """Test successful notification creation"""
        notification = NotificationService.create_notification(
            recipient=self.technician,
            template_name='repair_approved',
            context={
                'repair': self.repair,
                'technician': self.technician,
            },
            action_url=f'/tech/repairs/{self.repair.id}/',
            repair=self.repair
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.priority, 'URGENT')
        self.assertEqual(notification.category, 'approval')
        self.assertIn(str(self.repair.id), notification.title)

    def test_create_notification_missing_template(self):
        """Test notification creation with non-existent template"""
        notification = NotificationService.create_notification(
            recipient=self.technician,
            template_name='nonexistent_template',
            context={'repair': self.repair}
        )

        self.assertIsNone(notification)

    def test_create_notification_missing_context(self):
        """Test notification creation with missing required context"""
        notification = NotificationService.create_notification(
            recipient=self.technician,
            template_name='repair_approved',
            context={'repair': self.repair},  # Missing 'technician'
        )

        self.assertIsNone(notification)

    def test_priority_determines_channels(self):
        """Test that priority correctly determines delivery channels"""
        notification = Notification.objects.create(
            recipient=self.technician,
            title='Test',
            message='Test message',
            category='system',
            priority='URGENT'
        )

        channels = notification.get_delivery_channels()
        self.assertIn('in_app', channels)
        self.assertIn('email', channels)
        self.assertIn('sms', channels)

        # Test MEDIUM priority
        notification.priority = 'MEDIUM'
        channels = notification.get_delivery_channels()
        self.assertIn('in_app', channels)
        self.assertIn('email', channels)
        self.assertNotIn('sms', channels)

    def test_preferences_respected(self):
        """Test that user preferences are honored"""
        # Disable SMS
        self.preferences.receive_sms_notifications = False
        self.preferences.save()

        notification = NotificationService.create_notification(
            recipient=self.technician,
            template_name='repair_approved',
            context={
                'repair': self.repair,
                'technician': self.technician,
            }
        )

        # SMS should not be queued (test via delivery logs)
        self.assertIsNotNone(notification)
        # Further assertions would check delivery logs

    def test_quiet_hours_respected(self):
        """Test that quiet hours prevent non-urgent notifications"""
        from datetime import time

        # Set quiet hours
        self.preferences.quiet_hours_enabled = True
        self.preferences.quiet_hours_start = time(22, 0)
        self.preferences.quiet_hours_end = time(8, 0)
        self.preferences.save()

        # Test during quiet hours (mock current time)
        # This would require time mocking
        pass


class EmailServiceTestCase(TestCase):
    """Test EmailService functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.technician = Technician.objects.create(user=self.user)

        # Create test notification
        self.notification = Notification.objects.create(
            recipient=self.technician,
            title='Test Notification',
            message='Test message',
            category='system',
            priority='MEDIUM'
        )

    def test_email_sent_successfully(self):
        """Test successful email sending"""
        from apps.core.services.email_service import EmailService
        from django.core import mail

        result = EmailService.send_notification_email(
            notification_id=self.notification.id,
            recipient_email='test@example.com',
            subject='Test Email',
            html_content='<p>Test</p>',
            text_content='Test'
        )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Email')

    def test_email_failure_logged(self):
        """Test that email failures are logged"""
        from apps.core.services.email_service import EmailService
        from apps.core.models import NotificationDeliveryLog

        # Use invalid configuration to force failure
        # (would require settings override)
        pass


class SMSServiceTestCase(TestCase):
    """Test SMSService functionality"""

    def test_phone_validation(self):
        """Test phone number validation"""
        from apps.core.services.sms_service import SMSService

        # Valid E.164 format
        self.assertTrue(SMSService._validate_phone('+12025551234'))
        self.assertTrue(SMSService._validate_phone('+442071234567'))

        # Invalid formats
        self.assertFalse(SMSService._validate_phone('2025551234'))
        self.assertFalse(SMSService._validate_phone('+1 202 555 1234'))
        self.assertFalse(SMSService._validate_phone('invalid'))

    def test_sms_truncation(self):
        """Test SMS message truncation to 160 chars"""
        long_message = "A" * 200
        # Test would verify truncation logic
        pass
```

### Integration Tests

**File**: `apps/technician_portal/tests/test_repair_signals.py`

```python
from django.test import TestCase
from apps.technician_portal.models import Repair
from apps.core.models import Notification, Customer
from django.contrib.auth.models import User
from apps.technician_portal.models import Technician

class RepairSignalTestCase(TestCase):
    """Test repair signals trigger notifications correctly"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tech', email='tech@test.com')
        self.technician = Technician.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            company_name='Test Co',
            email='customer@test.com'
        )

    def test_repair_approved_triggers_notification(self):
        """Test that approving repair creates notification"""
        repair = Repair.objects.create(
            unit_number='TEST-001',
            customer=self.customer,
            technician=self.technician,
            queue_status='PENDING',
            cost=100.00
        )

        # Change status to approved
        repair.queue_status = 'APPROVED'
        repair.save()

        # Check notification created
        notifications = Notification.objects.filter(
            repair=repair,
            category='approval'
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().priority, 'URGENT')

    def test_repair_denied_triggers_notification(self):
        """Test that denying repair creates notification"""
        repair = Repair.objects.create(
            unit_number='TEST-001',
            customer=self.customer,
            technician=self.technician,
            queue_status='PENDING',
            cost=100.00
        )

        repair.queue_status = 'DENIED'
        repair.denial_reason = 'Too expensive'
        repair.save()

        notifications = Notification.objects.filter(
            repair=repair,
            category='approval'
        )
        self.assertTrue(notifications.exists())

    def test_technician_assignment_triggers_notification(self):
        """Test that assigning technician creates notification"""
        repair = Repair.objects.create(
            unit_number='TEST-001',
            customer=self.customer,
            queue_status='REQUESTED',
            cost=100.00
        )

        # Assign technician
        repair.technician = self.technician
        repair.save()

        notifications = Notification.objects.filter(
            repair=repair,
            category='assignment'
        )
        self.assertTrue(notifications.exists())
```

### End-to-End Tests

**File**: `apps/core/tests/test_notification_e2e.py`

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.technician_portal.models import Technician, Repair
from apps.core.models import Customer, Notification

class NotificationEndToEndTestCase(TestCase):
    """End-to-end notification workflow tests"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tech',
            password='testpass123',
            email='tech@test.com'
        )
        self.technician = Technician.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            company_name='Test Co',
            email='customer@test.com'
        )

    def test_full_approval_workflow(self):
        """Test complete approval workflow from creation to notification"""
        # 1. Create pending repair
        repair = Repair.objects.create(
            unit_number='TEST-001',
            customer=self.customer,
            technician=self.technician,
            queue_status='PENDING',
            cost=250.00,
            break_description='Test break'
        )

        # 2. Simulate customer approval
        repair.queue_status = 'APPROVED'
        repair.save()

        # 3. Verify notification created
        notification = Notification.objects.filter(
            repair=repair,
            category='approval'
        ).first()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.priority, 'URGENT')

        # 4. Login as technician and check notification appears
        self.client.login(username='tech', password='testpass123')
        response = self.client.get('/tech/dashboard/')

        self.assertEqual(response.status_code, 200)
        # Verify notification in context
        # self.assertIn(notification, response.context['recent_notifications'])
```

### Load Testing

**File**: `load_tests/notification_load_test.py`

```python
"""
Load test for notification system using Locust.

Install: pip install locust
Run: locust -f load_tests/notification_load_test.py
"""

from locust import HttpUser, task, between
import random

class NotificationUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before tests"""
        self.client.post('/tech/login/', {
            'username': 'testtech',
            'password': 'testpass123'
        })

    @task(3)
    def view_dashboard(self):
        """View dashboard (loads notifications)"""
        self.client.get('/tech/dashboard/')

    @task(2)
    def view_notification_history(self):
        """View notification history"""
        self.client.get('/tech/notifications/history/')

    @task(1)
    def mark_notification_read(self):
        """Mark random notification as read"""
        notification_id = random.randint(1, 100)
        self.client.post(f'/tech/notifications/{notification_id}/mark-read/')

    @task(1)
    def check_unread_count(self):
        """Check unread count (polling simulation)"""
        self.client.get('/tech/notifications/unread-count/')
```

---

## Monitoring & Alerting

### CloudWatch Metrics

**Custom Metrics to Track:**

1. **Notification Volume**
   - Total notifications created per hour
   - Notifications by priority (URGENT, HIGH, MEDIUM, LOW)
   - Notifications by category

2. **Delivery Metrics**
   - Email delivery success rate
   - SMS delivery success rate
   - Average delivery time

3. **Failure Metrics**
   - Failed email deliveries
   - Failed SMS deliveries
   - Retry attempts

4. **Cost Metrics**
   - SES cost per hour
   - SNS cost per hour
   - Total notification cost

**File**: `apps/core/services/metrics_service.py`

```python
import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    """Service for publishing CloudWatch metrics"""

    def __init__(self):
        self.cloudwatch = boto3.client(
            'cloudwatch',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def log_notification_created(self, priority, category):
        """Log notification creation metric"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='RSystems/Notifications',
                MetricData=[
                    {
                        'MetricName': 'NotificationsCreated',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Priority', 'Value': priority},
                            {'Name': 'Category', 'Value': category}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to log CloudWatch metric: {e}")

    def log_delivery_success(self, channel, duration_ms):
        """Log successful delivery"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='RSystems/Notifications',
                MetricData=[
                    {
                        'MetricName': 'DeliverySuccess',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Channel', 'Value': channel}
                        ]
                    },
                    {
                        'MetricName': 'DeliveryDuration',
                        'Value': duration_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {'Name': 'Channel', 'Value': channel}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to log delivery metric: {e}")

    def log_delivery_failure(self, channel, error_code):
        """Log failed delivery"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='RSystems/Notifications',
                MetricData=[
                    {
                        'MetricName': 'DeliveryFailure',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Channel', 'Value': channel},
                            {'Name': 'ErrorCode', 'Value': error_code}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to log failure metric: {e}")
```

### CloudWatch Alarms

**Create these alarms in AWS Console:**

1. **High Email Failure Rate**
   - Metric: DeliveryFailure (Email)
   - Threshold: >5% failure rate over 5 minutes
   - Action: SNS topic → Email to admin

2. **High SMS Cost**
   - Metric: Estimated SNS cost
   - Threshold: >$20/hour
   - Action: SNS topic → Email + SMS to admin

3. **Celery Worker Down**
   - Metric: Custom heartbeat metric
   - Threshold: No heartbeat for 5 minutes
   - Action: SNS topic → Email to admin

4. **Notification Queue Backlog**
   - Metric: Celery queue depth
   - Threshold: >1000 pending tasks
   - Action: SNS topic → Email to admin

### Sentry Integration

**File**: `rs_systems/settings_aws.py` (Add to existing)

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# Sentry error tracking
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    environment=os.environ.get('ENVIRONMENT', 'production'),
    traces_sample_rate=0.1,  # 10% transaction sampling
    send_default_pii=False,  # Don't send user data
)

# Sentry tags for filtering
sentry_sdk.set_tag('application', 'rs-systems')
sentry_sdk.set_tag('component', 'notifications')
```

---

## Admin Dashboard

### Notification Admin Enhancements

**File**: `apps/core/admin.py` (Enhanced)

```python
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from apps.core.models import (
    Notification,
    NotificationDeliveryLog,
    NotificationTemplate,
    EmailBrandingConfig
)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Enhanced admin for notifications with stats"""

    list_display = [
        'id',
        'title_truncated',
        'recipient_display',
        'priority_badge',
        'category',
        'delivery_status',
        'created_at',
        'read_status'
    ]

    list_filter = [
        'priority',
        'category',
        'read',
        'email_sent',
        'sms_sent',
        'created_at'
    ]

    search_fields = [
        'title',
        'message',
        'recipient_id'
    ]

    readonly_fields = [
        'created_at',
        'read_at',
        'template_context'
    ]

    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Title'

    def recipient_display(self, obj):
        return f"{obj.recipient_type.model} #{obj.recipient_id}"
    recipient_display.short_description = 'Recipient'

    def priority_badge(self, obj):
        colors = {
            'URGENT': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'blue',
            'LOW': 'gray'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.priority
        )
    priority_badge.short_description = 'Priority'

    def delivery_status(self, obj):
        status = []
        if obj.email_sent:
            status.append('📧')
        if obj.sms_sent:
            status.append('📱')
        return ' '.join(status) or '—'
    delivery_status.short_description = 'Delivered'

    def read_status(self, obj):
        return '✓' if obj.read else '—'
    read_status.short_description = 'Read'

    def changelist_view(self, request, extra_context=None):
        """Add statistics to change list page"""
        extra_context = extra_context or {}

        # Aggregate stats
        stats = Notification.objects.aggregate(
            total=Count('id'),
            unread=Count('id', filter=Q(read=False)),
            urgent=Count('id', filter=Q(priority='URGENT')),
            email_sent=Count('id', filter=Q(email_sent=True)),
            sms_sent=Count('id', filter=Q(sms_sent=True)),
        )

        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context)


@admin.register(NotificationDeliveryLog)
class DeliveryLogAdmin(admin.ModelAdmin):
    """Admin for delivery logs with retry actions"""

    list_display = [
        'id',
        'notification_id',
        'channel',
        'status_badge',
        'recipient',
        'attempt_number',
        'created_at'
    ]

    list_filter = [
        'channel',
        'status',
        'created_at',
        'provider_name'
    ]

    search_fields = [
        'notification__title',
        'recipient_email',
        'recipient_phone',
        'provider_message_id'
    ]

    readonly_fields = [
        'notification',
        'provider_response',
        'created_at',
        'sent_at',
        'failed_at'
    ]

    actions = ['retry_failed_deliveries']

    def status_badge(self, obj):
        colors = {
            'sent': 'green',
            'failed': 'red',
            'pending': 'orange',
            'bounced': 'red',
            'opted_out': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def recipient(self, obj):
        return obj.recipient_email or obj.recipient_phone
    recipient.short_description = 'Recipient'

    def retry_failed_deliveries(self, request, queryset):
        """Admin action to retry failed deliveries"""
        failed_logs = queryset.filter(status='failed', attempt_number__lt=3)

        for log in failed_logs:
            # Queue retry task
            if log.channel == 'email':
                # Retry email
                pass
            elif log.channel == 'sms':
                # Retry SMS
                pass

        self.message_user(request, f"Queued {failed_logs.count()} deliveries for retry")
    retry_failed_deliveries.short_description = "Retry failed deliveries"
```

---

## Deployment Procedures

### Pre-Deployment Checklist

**Infrastructure:**
- [ ] AWS SES domain verified and out of sandbox
- [ ] AWS SNS spending limits configured
- [ ] Redis/ElastiCache cluster running
- [ ] Celery workers deployed and running
- [ ] CloudWatch alarms configured
- [ ] Sentry project created

**Database:**
- [ ] All migrations tested on staging
- [ ] NotificationTemplate records created
- [ ] EmailBrandingConfig configured
- [ ] Test notification preferences created

**Environment Variables:**
- [ ] All AWS credentials set
- [ ] Email/SMS settings configured
- [ ] Celery broker URL set
- [ ] Sentry DSN configured

**Testing:**
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Load tests successful
- [ ] Manual testing complete

### Deployment Steps

**1. Database Migration**
```bash
# Run migrations
python manage.py migrate

# Create notification templates
python manage.py create_notification_templates

# Configure email branding
python manage.py setup_email_branding
```

**2. Deploy Celery Workers**
```bash
# Start Celery worker service
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# Verify workers running
celery -A rs_systems inspect active
```

**3. Deploy Django Application**
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Restart Django
sudo systemctl restart gunicorn
```

**4. Verify Deployment**
```bash
# Test SES connection
python manage.py test_ses admin@rssystems.com

# Test SNS connection
python manage.py test_sns +12025551234

# Verify Celery tasks
celery -A rs_systems inspect stats

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics --namespace RSystems/Notifications
```

### Gradual Rollout Strategy

**Phase 1: Internal Testing (Week 1)**
- Enable for staff users only
- Test all notification types
- Monitor error rates
- Gather feedback

**Phase 2: Technician Rollout (Week 2)**
- Enable for 25% of technicians
- Monitor SMS costs
- Check delivery rates
- Adjust templates based on feedback

**Phase 3: Full Technician Rollout (Week 3)**
- Enable for all technicians
- Monitor system performance
- Optimize based on usage patterns

**Phase 4: Customer Rollout (Week 4)**
- Enable for customers
- Monitor approval workflow
- Ensure email deliverability
- Full system launch

---

## Troubleshooting Runbook

### Issue: Emails Not Sending

**Symptoms:**
- Email delivery logs show "failed" status
- Users not receiving email notifications

**Diagnosis:**
```bash
# Check SES sending quota
aws ses get-send-quota

# Check SES sending statistics
aws ses get-send-statistics

# Check recent bounces/complaints
aws ses list-identities
```

**Solutions:**
1. Verify SES is out of sandbox mode
2. Check AWS credentials are correct
3. Verify sender domain/email is verified
4. Check for bounces or complaints
5. Review CloudWatch logs for errors

### Issue: High SMS Costs

**Symptoms:**
- AWS bill higher than expected
- SNS spending limit alerts

**Diagnosis:**
```bash
# Check SNS usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/SNS \
  --metric-name SMSSuccessRate \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

**Solutions:**
1. Review notification priorities (reduce HIGH priority usage)
2. Encourage users to disable SMS for non-critical categories
3. Implement SMS rate limiting
4. Consider email-first strategy for MEDIUM priority
5. Add cost monitoring dashboard

### Issue: Celery Workers Not Processing Tasks

**Symptoms:**
- Notifications created but not delivered
- Celery queue depth increasing

**Diagnosis:**
```bash
# Check Celery worker status
celery -A rs_systems inspect active

# Check queue depth
celery -A rs_systems inspect reserved

# Check worker logs
sudo journalctl -u celery-worker -f
```

**Solutions:**
1. Restart Celery workers: `sudo systemctl restart celery-worker`
2. Check Redis connection: `redis-cli ping`
3. Increase worker concurrency
4. Check for stuck tasks
5. Review error logs for exceptions

---

## Performance Optimizations

### Database Query Optimization

```python
# Use select_related for foreign keys
notifications = Notification.objects.select_related(
    'repair',
    'customer',
    'template'
).filter(recipient_id=user.id)

# Use prefetch_related for reverse foreign keys
technician = Technician.objects.prefetch_related(
    'notifications',
    'notification_preferences'
).get(id=technician_id)
```

### Caching Strategy

```python
from django.core.cache import cache

def get_unread_count(technician_id):
    """Get unread count with caching"""
    cache_key = f'unread_count_{technician_id}'
    count = cache.get(cache_key)

    if count is None:
        count = Notification.objects.filter(
            recipient_id=technician_id,
            read=False
        ).count()
        cache.set(cache_key, count, timeout=300)  # 5 minutes

    return count
```

---

## Success Criteria

✅ All tests passing (90%+ coverage)
✅ Monitoring dashboards configured
✅ CloudWatch alarms active
✅ Load testing successful (1000 notifications/min)
✅ Deployment runbooks created
✅ Rollout plan documented
✅ Admin dashboard functional
✅ Performance optimizations implemented
✅ Error handling comprehensive
✅ Documentation complete

---

## Post-Launch Monitoring

### First 24 Hours
- Monitor error rates every hour
- Check SMS costs every 4 hours
- Review delivery success rates
- Gather user feedback

### First Week
- Daily review of CloudWatch metrics
- Weekly cost analysis
- User satisfaction survey
- Performance optimization as needed

### Ongoing
- Monthly cost review
- Quarterly template optimization
- Bi-annual load testing
- Continuous monitoring and improvement
