# Phase 4: Service Layer & Event Triggers

**Timeline**: Days 5-6
**Status**: Not Started
**Dependencies**: Phase 1 (Models), Phase 2 (AWS), Phase 3 (Templates)

## Overview

This phase builds the service layer that creates and delivers notifications, plus the signal-based event system that automatically triggers notifications when repairs change status. This is the "brain" of the notification system that connects everything together.

## Objectives

1. Build NotificationService for creating notifications with priority routing
2. Build EmailService for sending emails via AWS SES
3. Build SMSService for sending SMS via AWS SNS
4. Create Celery tasks for async delivery
5. Implement signal handlers for repair events
6. Map events to priority levels
7. Add delivery retry logic
8. Implement rate limiting and batching

---

## Service Layer Architecture

```
┌──────────────────────┐
│   Repair Event       │
│  (status changed)    │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│   Signal Handler     │
│  (post_save, etc.)   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│ NotificationService  │◄── Determines priority
│  .create_notification│    Applies preferences
└─────────┬────────────┘    Renders template
          │
          ▼
┌──────────────────────┐
│  Celery Task Queue   │
└──┬─────────────────┬─┘
   │                 │
   ▼                 ▼
┌──────────┐    ┌──────────┐
│  Email   │    │   SMS    │
│ Service  │    │ Service  │
└────┬─────┘    └────┬─────┘
     │               │
     ▼               ▼
┌──────────┐    ┌──────────┐
│ AWS SES  │    │ AWS SNS  │
└──────────┘    └──────────┘
```

---

## Core Services

### 1. NotificationService

**File**: `apps/core/services/notification_service.py`

```python
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from apps.core.models import (
    Notification,
    NotificationTemplate,
    EmailBrandingConfig,
    NotificationDeliveryLog,
)
from apps.core.tasks import send_notification_email, send_notification_sms
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central service for creating and delivering notifications.

    Handles:
    - Creating notification records
    - Checking user preferences
    - Rendering templates
    - Queueing delivery tasks (email/SMS)
    - Logging delivery attempts
    """

    @staticmethod
    def create_notification(
        recipient,
        template_name,
        context,
        priority=None,
        category=None,
        action_url=None,
        repair=None,
        customer=None,
        repair_batch_id=None,
    ):
        """
        Create and deliver a notification.

        Args:
            recipient: User, CustomerUser, or Technician object
            template_name: Name of NotificationTemplate to use
            context: Dict of template variables
            priority: Override template default priority (URGENT, HIGH, MEDIUM, LOW)
            category: Notification category (repair_status, assignment, etc.)
            action_url: URL for notification action button
            repair: Related Repair object (optional)
            customer: Related Customer object (optional)
            repair_batch_id: Related batch ID (optional)

        Returns:
            Notification object
        """

        # Get notification template
        try:
            template = NotificationTemplate.objects.get(name=template_name, active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template '{template_name}' not found or inactive")
            return None

        # Validate context has required variables
        is_valid, missing = template.validate_context(context)
        if not is_valid:
            logger.error(f"Missing required context variables: {missing}")
            return None

        # Get branding configuration
        branding = EmailBrandingConfig.get_config()

        # Add branding to context
        full_context = {
            **context,
            **branding.to_template_context(),
            'action_url': action_url or '',
        }

        # Render template
        rendered = template.render(full_context)

        # Determine priority
        final_priority = priority or template.default_priority

        # Determine category
        final_category = category or template.category

        # Get recipient content type
        recipient_ct = ContentType.objects.get_for_model(recipient)

        # Create notification record
        notification = Notification.objects.create(
            recipient_type=recipient_ct,
            recipient_id=recipient.pk,
            title=rendered['title'],
            message=rendered['message'],
            category=final_category,
            priority=final_priority,
            template=template,
            template_context=context,
            action_url=rendered['action_url'],
            repair=repair,
            customer=customer,
            repair_batch_id=repair_batch_id,
        )

        # Get recipient preferences
        preferences = NotificationService._get_preferences(recipient)

        # Check if delivery is allowed
        if not NotificationService._should_deliver(notification, preferences):
            logger.info(f"Notification {notification.id} skipped due to user preferences")
            return notification

        # Queue delivery based on priority and preferences
        NotificationService._queue_delivery(
            notification=notification,
            rendered_content=rendered,
            preferences=preferences,
            recipient=recipient,
        )

        return notification

    @staticmethod
    def _get_preferences(recipient):
        """Get notification preferences for recipient"""
        from apps.core.models import TechnicianNotificationPreference, CustomerNotificationPreference

        # Determine recipient type and get preferences
        if hasattr(recipient, 'notification_preferences'):
            return recipient.notification_preferences

        # Create default preferences if they don't exist
        from apps.technician_portal.models import Technician
        from apps.core.models import Customer

        if isinstance(recipient, Technician):
            prefs, created = TechnicianNotificationPreference.objects.get_or_create(
                technician=recipient
            )
            return prefs
        elif isinstance(recipient, Customer):
            prefs, created = CustomerNotificationPreference.objects.get_or_create(
                customer=recipient
            )
            return prefs

        return None

    @staticmethod
    def _should_deliver(notification, preferences):
        """
        Check if notification should be delivered based on preferences.

        URGENT notifications are always delivered (critical business need).
        Other priorities respect user preferences.
        """

        if not preferences:
            return True  # No preferences = deliver everything

        # URGENT notifications always delivered
        if notification.priority == Notification.PRIORITY_URGENT:
            return True

        # Check quiet hours for non-urgent notifications
        if preferences.is_in_quiet_hours():
            logger.info(f"Notification {notification.id} delayed due to quiet hours")
            return False

        # Check category preferences
        category_map = {
            Notification.CATEGORY_REPAIR_STATUS: preferences.notify_repair_status,
            Notification.CATEGORY_ASSIGNMENT: preferences.notify_assignments,
            Notification.CATEGORY_APPROVAL: preferences.notify_approvals,
            Notification.CATEGORY_REWARD: preferences.notify_rewards,
            Notification.CATEGORY_SYSTEM: preferences.notify_system,
        }

        category_enabled = category_map.get(notification.category, True)
        if not category_enabled:
            logger.info(f"Notification {notification.id} skipped - category disabled")
            return False

        return True

    @staticmethod
    def _queue_delivery(notification, rendered_content, preferences, recipient):
        """
        Queue notification delivery tasks based on priority.

        Priority determines delivery channels:
        - URGENT: SMS + Email + In-app
        - HIGH: SMS + In-app
        - MEDIUM: Email + In-app
        - LOW: In-app only (already created)
        """

        # Get delivery channels from priority
        channels = notification.get_delivery_channels()

        # Email delivery
        if 'email' in channels and preferences.can_send_email():
            # Get recipient email
            email = NotificationService._get_recipient_email(recipient)
            if email:
                # Queue Celery task
                send_notification_email.delay(
                    notification_id=notification.id,
                    recipient_email=email,
                    subject=rendered_content['email_subject'],
                    html_content=rendered_content['email_html'],
                    text_content=rendered_content['email_text'],
                )
                logger.info(f"Email queued for notification {notification.id}")

        # SMS delivery
        if 'sms' in channels and preferences.can_send_sms():
            # Get recipient phone
            phone = NotificationService._get_recipient_phone(recipient)
            if phone:
                # Queue Celery task
                send_notification_sms.delay(
                    notification_id=notification.id,
                    recipient_phone=phone,
                    message=rendered_content['sms'],
                )
                logger.info(f"SMS queued for notification {notification.id}")

    @staticmethod
    def _get_recipient_email(recipient):
        """Extract email from recipient object"""
        if hasattr(recipient, 'user'):
            return recipient.user.email
        elif hasattr(recipient, 'email'):
            return recipient.email
        return None

    @staticmethod
    def _get_recipient_phone(recipient):
        """Extract phone from recipient object"""
        if hasattr(recipient, 'phone_number'):
            return recipient.phone_number
        elif hasattr(recipient, 'phone'):
            return recipient.phone
        return None


class NotificationBatchService:
    """
    Service for batch notification operations.

    Useful for daily digests, bulk notifications, etc.
    """

    @staticmethod
    def create_batch_notifications(recipients, template_name, context_fn, **kwargs):
        """
        Create notifications for multiple recipients.

        Args:
            recipients: List of recipient objects
            template_name: Template to use
            context_fn: Function that takes recipient and returns context dict
            **kwargs: Additional args passed to create_notification

        Returns:
            List of created Notification objects
        """
        notifications = []

        for recipient in recipients:
            context = context_fn(recipient)
            notification = NotificationService.create_notification(
                recipient=recipient,
                template_name=template_name,
                context=context,
                **kwargs
            )
            if notification:
                notifications.append(notification)

        logger.info(f"Created {len(notifications)} batch notifications")
        return notifications

    @staticmethod
    def send_daily_digest(recipient, notifications):
        """
        Send daily digest of notifications.

        Batches multiple notifications into single email.
        """
        # TODO: Implement digest template and sending
        pass
```

### 2. EmailService

**File**: `apps/core/services/email_service.py`

```python
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from apps.core.models import NotificationDeliveryLog
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending emails via AWS SES.

    Handles:
    - Email composition (HTML + plain text)
    - Sending via Django email backend
    - Delivery logging
    - Error handling
    """

    @staticmethod
    def send_notification_email(
        notification_id,
        recipient_email,
        subject,
        html_content,
        text_content,
        attempt_number=1
    ):
        """
        Send notification email via AWS SES.

        Args:
            notification_id: Notification.id
            recipient_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            text_content: Plain text email body
            attempt_number: Retry attempt number

        Returns:
            bool: True if sent successfully, False otherwise
        """

        from apps.core.models import Notification

        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found")
            return False

        # Create delivery log
        delivery_log = NotificationDeliveryLog.objects.create(
            notification=notification,
            channel=NotificationDeliveryLog.CHANNEL_EMAIL,
            status=NotificationDeliveryLog.STATUS_PENDING,
            recipient_email=recipient_email,
            attempt_number=attempt_number,
            provider_name='AWS SES',
        )

        try:
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
                to=[recipient_email],
            )

            # Attach HTML version
            msg.attach_alternative(html_content, "text/html")

            # Send email
            msg.send(fail_silently=False)

            # Mark as sent
            delivery_log.mark_sent()
            notification.email_sent = True
            notification.save(update_fields=['email_sent'])

            logger.info(f"Email sent for notification {notification_id} to {recipient_email}")
            return True

        except Exception as e:
            # Mark as failed
            error_message = str(e)
            delivery_log.mark_failed(error_message)

            logger.error(f"Email failed for notification {notification_id}: {error_message}")

            # Schedule retry if attempts remain
            if delivery_log.should_retry():
                from apps.core.tasks import send_notification_email
                send_notification_email.apply_async(
                    args=[notification_id, recipient_email, subject, html_content, text_content, attempt_number + 1],
                    countdown=delivery_log.next_retry_at.timestamp() - delivery_log.created_at.timestamp()
                )
                logger.info(f"Email retry scheduled for notification {notification_id}")

            return False
```

### 3. SMSService

**File**: `apps/core/services/sms_service.py`

```python
from django.conf import settings
from apps.core.models import NotificationDeliveryLog
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """
    Service for sending SMS via AWS SNS.

    Handles:
    - SMS composition and truncation
    - Sending via AWS SNS
    - Delivery logging
    - Cost tracking
    - Error handling
    """

    # US SMS cost (approximate)
    SMS_COST_USD = 0.00645

    @staticmethod
    def send_notification_sms(
        notification_id,
        recipient_phone,
        message,
        attempt_number=1
    ):
        """
        Send notification SMS via AWS SNS.

        Args:
            notification_id: Notification.id
            recipient_phone: Phone number in E.164 format (+12025551234)
            message: SMS message (will be truncated to 160 chars)
            attempt_number: Retry attempt number

        Returns:
            bool: True if sent successfully, False otherwise
        """

        from apps.core.models import Notification

        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found")
            return False

        # Validate phone format
        if not SMSService._validate_phone(recipient_phone):
            logger.error(f"Invalid phone format: {recipient_phone}")
            return False

        # Truncate message to 160 chars
        truncated_message = message[:160]
        if len(message) > 160:
            truncated_message = message[:157] + "..."
            logger.warning(f"SMS message truncated for notification {notification_id}")

        # Create delivery log
        delivery_log = NotificationDeliveryLog.objects.create(
            notification=notification,
            channel=NotificationDeliveryLog.CHANNEL_SMS,
            status=NotificationDeliveryLog.STATUS_PENDING,
            recipient_phone=recipient_phone,
            attempt_number=attempt_number,
            provider_name='AWS SNS',
            estimated_cost=SMSService.SMS_COST_USD,
        )

        try:
            # Initialize SNS client
            sns_client = boto3.client(
                'sns',
                region_name=settings.AWS_SNS_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            # Send SMS
            response = sns_client.publish(
                PhoneNumber=recipient_phone,
                Message=truncated_message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'  # High-priority delivery
                    },
                    'AWS.SNS.SMS.MaxPrice': {
                        'DataType': 'String',
                        'StringValue': str(settings.SMS_MAX_PRICE_USD)
                    }
                }
            )

            # Mark as sent
            message_id = response.get('MessageId')
            delivery_log.mark_sent(
                provider_message_id=message_id,
                provider_response=response
            )
            notification.sms_sent = True
            notification.save(update_fields=['sms_sent'])

            logger.info(f"SMS sent for notification {notification_id} to {recipient_phone}")
            return True

        except ClientError as e:
            # AWS-specific error
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            delivery_log.mark_failed(error_message, error_code)

            logger.error(f"SMS failed for notification {notification_id}: {error_message}")

            # Schedule retry if attempts remain
            if delivery_log.should_retry():
                from apps.core.tasks import send_notification_sms
                send_notification_sms.apply_async(
                    args=[notification_id, recipient_phone, message, attempt_number + 1],
                    countdown=delivery_log.next_retry_at.timestamp() - delivery_log.created_at.timestamp()
                )
                logger.info(f"SMS retry scheduled for notification {notification_id}")

            return False

        except Exception as e:
            # General error
            delivery_log.mark_failed(str(e))
            logger.error(f"SMS failed for notification {notification_id}: {str(e)}")
            return False

    @staticmethod
    def _validate_phone(phone):
        """Validate phone number is in E.164 format"""
        import re
        # E.164 format: +[country code][number] (max 15 digits)
        pattern = r'^\+[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None
```

---

## Celery Tasks

**File**: `apps/core/tasks.py`

```python
from celery import shared_task
from apps.core.services.email_service import EmailService
from apps.core.services.sms_service import SMSService
from apps.core.models import NotificationDeliveryLog
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id, recipient_email, subject, html_content, text_content, attempt_number=1):
    """
    Celery task for sending notification emails.

    Automatically retried on failure with exponential backoff.
    """
    try:
        return EmailService.send_notification_email(
            notification_id=notification_id,
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attempt_number=attempt_number,
        )
    except Exception as e:
        logger.error(f"Email task failed: {str(e)}")
        # Celery will automatically retry based on max_retries
        raise


@shared_task(bind=True, max_retries=3)
def send_notification_sms(self, notification_id, recipient_phone, message, attempt_number=1):
    """
    Celery task for sending notification SMS.

    Automatically retried on failure with exponential backoff.
    """
    try:
        return SMSService.send_notification_sms(
            notification_id=notification_id,
            recipient_phone=recipient_phone,
            message=message,
            attempt_number=attempt_number,
        )
    except Exception as e:
        logger.error(f"SMS task failed: {str(e)}")
        raise


@shared_task
def retry_failed_notifications():
    """
    Periodic task to retry failed notification deliveries.

    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()

    # Find failed deliveries ready for retry
    failed_deliveries = NotificationDeliveryLog.objects.filter(
        status=NotificationDeliveryLog.STATUS_FAILED,
        next_retry_at__lte=now,
        attempt_number__lt=3,  # Max 3 attempts
    )

    retry_count = 0
    for log in failed_deliveries:
        if log.channel == NotificationDeliveryLog.CHANNEL_EMAIL:
            # Retry email
            # Note: This requires storing rendered content - implementation detail
            logger.info(f"Retrying email delivery for notification {log.notification_id}")
            # send_notification_email.delay(...)
            retry_count += 1

        elif log.channel == NotificationDeliveryLog.CHANNEL_SMS:
            # Retry SMS
            logger.info(f"Retrying SMS delivery for notification {log.notification_id}")
            # send_notification_sms.delay(...)
            retry_count += 1

    logger.info(f"Retried {retry_count} failed deliveries")
    return retry_count


@shared_task
def send_daily_digests():
    """
    Send daily digest emails to users who have digest mode enabled.

    Runs daily at 9 AM via Celery Beat.
    """
    from apps.core.models import TechnicianNotificationPreference
    from apps.core.services.notification_service import NotificationBatchService

    # Get technicians with digest enabled
    digest_users = TechnicianNotificationPreference.objects.filter(
        digest_enabled=True
    )

    for pref in digest_users:
        # Get unread notifications from last 24 hours
        notifications = pref.technician.notifications.filter(
            read=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=1)
        )

        if notifications.exists():
            NotificationBatchService.send_daily_digest(
                recipient=pref.technician,
                notifications=notifications
            )

    logger.info(f"Sent {digest_users.count()} daily digests")


@shared_task
def cleanup_old_delivery_logs():
    """
    Clean up old delivery logs (older than 90 days).

    Runs weekly on Sunday at 2 AM via Celery Beat.
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=90)

    deleted_count = NotificationDeliveryLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]

    logger.info(f"Deleted {deleted_count} old delivery logs")
    return deleted_count
```

---

## Signal Handlers for Repair Events

### Repair Status Change Signals

**File**: `apps/technician_portal/signals.py`

```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.technician_portal.models import Repair
from apps.core.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

# Track previous status for change detection
_repair_previous_status = {}

@receiver(pre_save, sender=Repair)
def track_repair_status_change(sender, instance, **kwargs):
    """
    Track repair status before save to detect changes.

    Stores previous status in module-level dict.
    """
    if instance.pk:
        try:
            old_repair = Repair.objects.get(pk=instance.pk)
            _repair_previous_status[instance.pk] = old_repair.queue_status
        except Repair.DoesNotExist:
            pass


@receiver(post_save, sender=Repair)
def handle_repair_status_change(sender, instance, created, **kwargs):
    """
    Send notifications when repair status changes.

    Triggers:
    - PENDING created → Notify customer (approval needed)
    - APPROVED → Notify technician (can proceed)
    - DENIED → Notify technician (reason provided)
    - IN_PROGRESS → Notify customer (work started)
    - COMPLETED → Notify customer (work done)
    """

    # Skip if no status change
    old_status = _repair_previous_status.get(instance.pk)
    if old_status == instance.queue_status and not created:
        return

    # Clean up tracking dict
    if instance.pk in _repair_previous_status:
        del _repair_previous_status[instance.pk]

    # Determine notification based on new status
    if instance.queue_status == 'PENDING' and created:
        # Pending repair created → notify customer
        _notify_customer_approval_needed(instance)

    elif instance.queue_status == 'APPROVED':
        # Repair approved → notify technician
        _notify_technician_approved(instance)

    elif instance.queue_status == 'DENIED':
        # Repair denied → notify technician
        _notify_technician_denied(instance)

    elif instance.queue_status == 'IN_PROGRESS':
        # Work started → notify customer
        _notify_customer_in_progress(instance)

    elif instance.queue_status == 'COMPLETED':
        # Work completed → notify customer
        _notify_customer_completed(instance)


def _notify_customer_approval_needed(repair):
    """Notify customer that repair needs approval"""
    NotificationService.create_notification(
        recipient=repair.customer,
        template_name='repair_pending_approval',
        context={
            'repair': repair,
            'customer': repair.customer,
        },
        priority='HIGH',  # SMS notification
        category='approval',
        action_url=f'/app/repairs/{repair.id}/',
        repair=repair,
        customer=repair.customer,
    )
    logger.info(f"Sent approval notification for repair {repair.id}")


def _notify_technician_approved(repair):
    """Notify technician that repair was approved"""
    if not repair.technician:
        logger.warning(f"Repair {repair.id} approved but no technician assigned")
        return

    NotificationService.create_notification(
        recipient=repair.technician,
        template_name='repair_approved',
        context={
            'repair': repair,
            'technician': repair.technician,
        },
        priority='URGENT',  # SMS + Email
        category='approval',
        action_url=f'/tech/repairs/{repair.id}/',
        repair=repair,
    )
    logger.info(f"Sent approval notification to technician for repair {repair.id}")


def _notify_technician_denied(repair):
    """Notify technician that repair was denied"""
    if not repair.technician:
        return

    NotificationService.create_notification(
        recipient=repair.technician,
        template_name='repair_denied',
        context={
            'repair': repair,
            'technician': repair.technician,
        },
        priority='URGENT',  # SMS + Email
        category='approval',
        action_url=f'/tech/repairs/{repair.id}/',
        repair=repair,
    )
    logger.info(f"Sent denial notification to technician for repair {repair.id}")


def _notify_customer_in_progress(repair):
    """Notify customer that work has started"""
    NotificationService.create_notification(
        recipient=repair.customer,
        template_name='repair_in_progress',
        context={
            'repair': repair,
            'customer': repair.customer,
            'technician': repair.technician,
        },
        priority='MEDIUM',  # Email only
        category='repair_status',
        action_url=f'/app/repairs/{repair.id}/',
        repair=repair,
        customer=repair.customer,
    )
    logger.info(f"Sent in-progress notification for repair {repair.id}")


def _notify_customer_completed(repair):
    """Notify customer that work is complete"""
    NotificationService.create_notification(
        recipient=repair.customer,
        template_name='repair_completed',
        context={
            'repair': repair,
            'customer': repair.customer,
            'technician': repair.technician,
        },
        priority='HIGH',  # SMS notification
        category='repair_status',
        action_url=f'/app/repairs/{repair.id}/',
        repair=repair,
        customer=repair.customer,
    )
    logger.info(f"Sent completion notification for repair {repair.id}")
```

### Assignment/Reassignment Signals

**File**: `apps/technician_portal/signals.py` (continued)

```python
@receiver(post_save, sender=Repair)
def handle_technician_assignment(sender, instance, created, **kwargs):
    """
    Send notification when technician is assigned to repair.

    Also handles reassignments (technician changed).
    """

    # Skip if no technician
    if not instance.technician:
        return

    # Check if this is a new assignment or reassignment
    old_status = _repair_previous_status.get(instance.pk)

    if created and instance.technician:
        # New repair with technician assigned
        _notify_technician_assigned(instance)

    elif not created and instance.pk:
        # Check if technician changed
        try:
            old_repair = Repair.objects.get(pk=instance.pk)
            if old_repair.technician != instance.technician:
                # Technician changed (reassignment)
                _notify_technician_reassigned(instance, old_repair.technician)
        except Repair.DoesNotExist:
            pass


def _notify_technician_assigned(repair):
    """Notify technician of new assignment"""
    NotificationService.create_notification(
        recipient=repair.technician,
        template_name='repair_assigned',
        context={
            'repair': repair,
            'technician': repair.technician,
        },
        priority='HIGH',  # SMS notification
        category='assignment',
        action_url=f'/tech/repairs/{repair.id}/',
        repair=repair,
    )
    logger.info(f"Sent assignment notification to {repair.technician.user.username}")


def _notify_technician_reassigned(repair, old_technician):
    """Notify old technician of reassignment"""
    if old_technician:
        NotificationService.create_notification(
            recipient=old_technician,
            template_name='repair_reassigned_away',
            context={
                'repair': repair,
                'technician': old_technician,
                'new_technician': repair.technician,
            },
            priority='MEDIUM',  # Email only
            category='assignment',
            action_url=f'/tech/repairs/{repair.id}/',
            repair=repair,
        )
        logger.info(f"Sent reassignment notification to {old_technician.user.username}")

    # Notify new technician
    _notify_technician_assigned(repair)
```

### Signal Registration

**File**: `apps/technician_portal/apps.py`

```python
from django.apps import AppConfig

class TechnicianPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.technician_portal'

    def ready(self):
        """Import signals when app is ready"""
        import apps.technician_portal.signals  # noqa
```

---

## Event-to-Priority Mapping

| Event | Recipient | Priority | Channels | Reason |
|-------|-----------|----------|----------|--------|
| Repair Created (PENDING) | Customer | HIGH | SMS + In-app | Needs immediate approval |
| Repair Approved | Technician | URGENT | SMS + Email + In-app | Can proceed with work |
| Repair Denied | Technician | URGENT | SMS + Email + In-app | Must know reason |
| Technician Assigned | Technician | HIGH | SMS + In-app | New work assignment |
| Repair In Progress | Customer | MEDIUM | Email + In-app | Status update |
| Repair Completed | Customer | HIGH | SMS + In-app | Work finished |
| Batch Approved | Technician | URGENT | SMS + Email + In-app | Multiple repairs approved |
| Batch Denied | Technician | URGENT | SMS + Email + In-app | Multiple repairs denied |
| Reward Redemption | Technician | MEDIUM | Email + In-app | Reward available |

---

## Implementation Checklist

### Services
- [ ] Create NotificationService
- [ ] Create EmailService
- [ ] Create SMSService
- [ ] Create NotificationBatchService
- [ ] Add helper methods for recipient data extraction

### Celery Tasks
- [ ] Create send_notification_email task
- [ ] Create send_notification_sms task
- [ ] Create retry_failed_notifications task
- [ ] Create send_daily_digests task
- [ ] Create cleanup_old_delivery_logs task
- [ ] Configure task routing in settings

### Signal Handlers
- [ ] Create signals.py in technician_portal
- [ ] Add repair status change handler
- [ ] Add technician assignment handler
- [ ] Add batch approval handlers
- [ ] Register signals in apps.py
- [ ] Test signal firing

### Templates
- [ ] Create NotificationTemplate records in database
- [ ] Map template names to events
- [ ] Test template rendering with sample data

### Testing
- [ ] Unit tests for NotificationService
- [ ] Unit tests for EmailService
- [ ] Unit tests for SMSService
- [ ] Integration tests for signal handlers
- [ ] Test Celery task execution
- [ ] Test retry logic
- [ ] Test preference enforcement

---

## Success Criteria

✅ Services created and tested
✅ Celery tasks executing successfully
✅ Signal handlers firing on repair changes
✅ Notifications created with correct priority
✅ Emails sending via SES
✅ SMS sending via SNS
✅ Delivery logs recording all attempts
✅ Retry logic working for failures
✅ User preferences honored

---

## Next Phase

Once Phase 4 is complete, proceed to:
**Phase 5: User Preference Management** - Build UI for users to control notification settings.
