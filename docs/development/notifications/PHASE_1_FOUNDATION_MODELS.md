# Phase 1: Foundation & Models

**Timeline**: Days 1-2
**Status**: Not Started
**Dependencies**: None

## Overview

This phase establishes the database foundation for the notification system. We'll create models for storing notifications, user preferences, templates, and delivery logs. The architecture is designed to support multiple recipient types (customers, technicians, managers) with a 4-tier priority system.

## Objectives

1. Create unified notification models that work for all user types
2. Implement notification preference system for granular control
3. Build template system for consistent messaging
4. Add delivery tracking and audit logging
5. Standardize contact information fields across user models

## Architecture Decisions

### Why Unified Notification Model?

Instead of separate `TechnicianNotification` and `CustomerNotification` models, we'll use:
- **GenericForeignKey** for polymorphic recipient support
- **ContentType framework** to link to User, CustomerUser, or Technician
- **Single source of truth** for all notification data
- **Easier querying** across all notifications
- **Consistent notification behavior** regardless of recipient type

### Priority System Design

**4-Tier Priority Levels:**

| Priority | Delivery Channels | Use Cases | User Can Disable? |
|----------|------------------|-----------|-------------------|
| **URGENT** | SMS + Email + In-App | Approvals, denials, critical assignments | No (always sent) |
| **HIGH** | SMS + In-App | New requests, completions, reassignments | Partially (can disable SMS) |
| **MEDIUM** | Email + In-App | Status updates, photo uploads, rewards | Yes |
| **LOW** | In-App only | Notes, minor updates, informational | Yes |

**Implementation**: Stored as `CharField` with choices, indexed for fast filtering.

## Database Schema

### 1. Core Notification Model

**File**: `apps/core/models/notification.py`

```python
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class Notification(models.Model):
    """
    Unified notification model supporting all recipient types.

    Uses Django's ContentType framework for polymorphic recipients:
    - Can link to User, CustomerUser, Technician, or any other model
    - Enables querying all notifications regardless of recipient type
    - Supports batch operations and consistent notification behavior
    """

    # Priority levels (determines delivery channels)
    PRIORITY_URGENT = 'URGENT'    # SMS + Email + In-app
    PRIORITY_HIGH = 'HIGH'        # SMS + In-app
    PRIORITY_MEDIUM = 'MEDIUM'    # Email + In-app
    PRIORITY_LOW = 'LOW'          # In-app only

    PRIORITY_CHOICES = [
        (PRIORITY_URGENT, 'Urgent - SMS + Email'),
        (PRIORITY_HIGH, 'High - SMS'),
        (PRIORITY_MEDIUM, 'Medium - Email'),
        (PRIORITY_LOW, 'Low - In-app only'),
    ]

    # Notification categories for filtering and preferences
    CATEGORY_REPAIR_STATUS = 'repair_status'
    CATEGORY_ASSIGNMENT = 'assignment'
    CATEGORY_APPROVAL = 'approval'
    CATEGORY_REWARD = 'reward'
    CATEGORY_SYSTEM = 'system'

    CATEGORY_CHOICES = [
        (CATEGORY_REPAIR_STATUS, 'Repair Status Change'),
        (CATEGORY_ASSIGNMENT, 'Assignment/Reassignment'),
        (CATEGORY_APPROVAL, 'Approval/Denial'),
        (CATEGORY_REWARD, 'Reward/Referral'),
        (CATEGORY_SYSTEM, 'System Notification'),
    ]

    # Polymorphic recipient (User, CustomerUser, Technician, etc.)
    recipient_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of recipient (User, CustomerUser, Technician)"
    )
    recipient_id = models.PositiveIntegerField(
        help_text="The ID of the recipient object"
    )
    recipient = GenericForeignKey('recipient_type', 'recipient_id')

    # Notification content
    title = models.CharField(
        max_length=200,
        help_text="Short notification title (shown in list views)"
    )
    message = models.TextField(
        help_text="Full notification message (supports markdown)"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Category for filtering and preference management"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        db_index=True,
        help_text="Priority level determines delivery channels"
    )

    # Delivery tracking
    read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether recipient has marked as read"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when notification was read"
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether email was successfully sent"
    )
    sms_sent = models.BooleanField(
        default=False,
        help_text="Whether SMS was successfully sent"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional: schedule notification for future delivery"
    )

    # Related objects (optional links to repair, customer, etc.)
    repair = models.ForeignKey(
        'technician_portal.Repair',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Link to related repair if applicable"
    )
    repair_batch_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Link to batch of repairs if applicable"
    )
    customer = models.ForeignKey(
        'core.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Link to customer if applicable"
    )

    # Template support (for reusable notifications)
    template = models.ForeignKey(
        'NotificationTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional: template used to generate this notification"
    )
    template_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Context data used with template (stored for audit)"
    )

    # Action URL (optional deep link)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL to navigate to when notification clicked"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_type', 'recipient_id', '-created_at']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['category', 'read']),
            models.Index(fields=['repair_batch_id']),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.priority}] {self.title} → {self.recipient}"

    def mark_as_read(self):
        """Mark notification as read with timestamp"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])

    def get_delivery_channels(self):
        """Return list of delivery channels based on priority"""
        channels = ['in_app']  # Always include in-app

        if self.priority == self.PRIORITY_URGENT:
            channels.extend(['email', 'sms'])
        elif self.priority == self.PRIORITY_HIGH:
            channels.append('sms')
        elif self.priority == self.PRIORITY_MEDIUM:
            channels.append('email')

        return channels
```

**Key Features:**
- **Polymorphic recipients** via ContentType framework
- **4-tier priority system** with automatic channel routing
- **Category-based organization** for filtering
- **Delivery tracking** (email_sent, sms_sent flags)
- **Template support** with context storage
- **Action URLs** for deep linking
- **Scheduled delivery** support for future notifications
- **Optimized indexes** for common queries

---

### 2. Notification Preference Models

**File**: `apps/core/models/notification_preferences.py`

```python
from django.db import models
from django.contrib.auth.models import User

class BaseNotificationPreference(models.Model):
    """
    Abstract base class for notification preferences.

    Provides common fields for controlling notification delivery
    across different user types (technicians, customers, managers).
    """

    # Global preferences
    receive_email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications (MEDIUM/URGENT priority)"
    )
    receive_sms_notifications = models.BooleanField(
        default=False,  # Opt-in for SMS due to cost
        help_text="Receive SMS notifications (HIGH/URGENT priority)"
    )
    receive_in_app_notifications = models.BooleanField(
        default=True,
        help_text="Show in-app notifications (cannot disable URGENT)"
    )

    # Category-specific preferences (can disable non-critical categories)
    notify_repair_status = models.BooleanField(
        default=True,
        help_text="Notifications for repair status changes"
    )
    notify_assignments = models.BooleanField(
        default=True,
        help_text="Notifications for repair assignments/reassignments"
    )
    notify_approvals = models.BooleanField(
        default=True,
        help_text="Notifications for approvals/denials (URGENT - cannot fully disable)"
    )
    notify_rewards = models.BooleanField(
        default=True,
        help_text="Notifications for rewards and referrals"
    )
    notify_system = models.BooleanField(
        default=True,
        help_text="System notifications and announcements"
    )

    # Quiet hours (optional - don't send non-urgent notifications during these hours)
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text="Enable quiet hours for non-urgent notifications"
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of quiet hours (e.g., 22:00)"
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End of quiet hours (e.g., 08:00)"
    )

    # Contact verification
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether email address has been verified"
    )
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When email was verified"
    )
    phone_verified = models.BooleanField(
        default=False,
        help_text="Whether phone number has been verified"
    )
    phone_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When phone was verified"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def can_send_email(self):
        """Check if email notifications are enabled and verified"""
        return self.receive_email_notifications and self.email_verified

    def can_send_sms(self):
        """Check if SMS notifications are enabled and verified"""
        return self.receive_sms_notifications and self.phone_verified

    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False

        from django.utils import timezone
        now = timezone.localtime().time()

        # Handle quiet hours that span midnight
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class TechnicianNotificationPreference(BaseNotificationPreference):
    """
    Notification preferences for technicians.

    Extends base preferences with technician-specific options.
    """
    technician = models.OneToOneField(
        'technician_portal.Technician',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Technician-specific preferences
    notify_new_assignments = models.BooleanField(
        default=True,
        help_text="Get notified when assigned new repairs"
    )
    notify_reassignments = models.BooleanField(
        default=True,
        help_text="Get notified when repairs are reassigned away"
    )
    notify_customer_approvals = models.BooleanField(
        default=True,
        help_text="Get notified when customers approve/deny repairs"
    )
    notify_reward_redemptions = models.BooleanField(
        default=True,
        help_text="Get notified of reward redemptions to fulfill"
    )

    # Batch notification preferences
    digest_enabled = models.BooleanField(
        default=False,
        help_text="Receive daily digest instead of individual notifications"
    )
    digest_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time to send daily digest (e.g., 09:00)"
    )

    class Meta:
        verbose_name = "Technician Notification Preference"
        verbose_name_plural = "Technician Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.technician.user.get_full_name()}"


class CustomerNotificationPreference(BaseNotificationPreference):
    """
    Notification preferences for customers.

    Extends base preferences with customer-specific options.
    """
    customer = models.OneToOneField(
        'core.Customer',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Customer-specific preferences
    notify_new_requests = models.BooleanField(
        default=True,
        help_text="Get notified when repair requests are submitted"
    )
    notify_pending_approvals = models.BooleanField(
        default=True,
        help_text="Get notified when repairs need approval"
    )
    notify_completions = models.BooleanField(
        default=True,
        help_text="Get notified when repairs are completed"
    )
    notify_in_progress = models.BooleanField(
        default=True,
        help_text="Get notified when repairs start"
    )

    # Batch notifications
    batch_pending_approvals = models.BooleanField(
        default=False,
        help_text="Receive one notification for all pending approvals (daily)"
    )

    class Meta:
        verbose_name = "Customer Notification Preference"
        verbose_name_plural = "Customer Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.customer.company_name}"
```

**Key Features:**
- **Abstract base class** for shared preference logic
- **Contact verification** tracking (email and phone)
- **Quiet hours** support to avoid disturbing users
- **Category-based preferences** for granular control
- **Digest mode** for technicians (optional daily summary)
- **Batch approval** notifications for customers
- **Helper methods** for permission checking

---

### 3. Notification Template Model

**File**: `apps/core/models/notification_template.py`

```python
from django.db import models
from django.template import Template, Context
from django.utils.safestring import mark_safe

class NotificationTemplate(models.Model):
    """
    Reusable notification templates with variable substitution.

    Supports:
    - Django template syntax for dynamic content
    - Multiple delivery channels (in-app, email, SMS)
    - Preview generation for testing
    - Version tracking for template changes
    """

    # Template identification
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal name for the template (e.g., 'repair_approved')"
    )
    description = models.TextField(
        help_text="Description of when this template is used"
    )
    category = models.CharField(
        max_length=50,
        choices=Notification.CATEGORY_CHOICES,
        help_text="Notification category this template belongs to"
    )

    # Default priority (can be overridden when creating notification)
    default_priority = models.CharField(
        max_length=20,
        choices=Notification.PRIORITY_CHOICES,
        default=Notification.PRIORITY_MEDIUM
    )

    # Template content for different channels
    title_template = models.CharField(
        max_length=200,
        help_text="Template for notification title (Django template syntax)"
    )
    message_template = models.TextField(
        help_text="Template for in-app message (supports markdown and Django template syntax)"
    )

    # Email-specific content
    email_subject_template = models.CharField(
        max_length=200,
        blank=True,
        help_text="Email subject line template (plain text)"
    )
    email_html_template = models.TextField(
        blank=True,
        help_text="HTML email body template (full HTML with Django template syntax)"
    )
    email_text_template = models.TextField(
        blank=True,
        help_text="Plain text email body template (fallback for non-HTML clients)"
    )

    # SMS-specific content
    sms_template = models.CharField(
        max_length=160,
        blank=True,
        help_text="SMS message template (max 160 chars after rendering)"
    )

    # Action URL template (supports variables)
    action_url_template = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL template for notification action (e.g., '/tech/repairs/{{ repair.id }}/')"
    )

    # Template metadata
    active = models.BooleanField(
        default=True,
        help_text="Whether this template is currently active"
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Template version for tracking changes"
    )

    # Required context variables (for documentation)
    required_context = models.JSONField(
        default=list,
        help_text="List of required context variable names (e.g., ['repair', 'customer'])"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates'
    )

    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def render(self, context_dict):
        """
        Render all template fields with the provided context.

        Args:
            context_dict (dict): Context variables for template rendering

        Returns:
            dict: Rendered content for all channels
        """
        context = Context(context_dict)

        return {
            'title': Template(self.title_template).render(context),
            'message': Template(self.message_template).render(context),
            'email_subject': Template(self.email_subject_template).render(context) if self.email_subject_template else '',
            'email_html': Template(self.email_html_template).render(context) if self.email_html_template else '',
            'email_text': Template(self.email_text_template).render(context) if self.email_text_template else '',
            'sms': Template(self.sms_template).render(context) if self.sms_template else '',
            'action_url': Template(self.action_url_template).render(context) if self.action_url_template else '',
        }

    def preview(self, sample_context):
        """
        Generate preview with sample context for testing.

        Args:
            sample_context (dict): Sample data for preview

        Returns:
            dict: Preview of rendered content
        """
        return self.render(sample_context)

    def validate_context(self, context_dict):
        """
        Validate that all required context variables are present.

        Args:
            context_dict (dict): Context to validate

        Returns:
            tuple: (is_valid, missing_variables)
        """
        missing = [var for var in self.required_context if var not in context_dict]
        return (len(missing) == 0, missing)
```

**Key Features:**
- **Multi-channel templates** (in-app, email HTML/text, SMS)
- **Django template syntax** for variable substitution
- **Version tracking** for template history
- **Required context validation** prevents rendering errors
- **Preview generation** for testing
- **Active/inactive toggle** for template management

---

### 4. Notification Delivery Log Model

**File**: `apps/core/models/notification_delivery_log.py`

```python
from django.db import models
from django.utils import timezone

class NotificationDeliveryLog(models.Model):
    """
    Audit log for notification delivery attempts.

    Tracks every attempt to send notifications via email/SMS,
    including success/failure status, error messages, and retry attempts.
    Essential for debugging delivery issues and monitoring costs.
    """

    # Delivery channels
    CHANNEL_EMAIL = 'email'
    CHANNEL_SMS = 'sms'
    CHANNEL_IN_APP = 'in_app'

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_SMS, 'SMS'),
        (CHANNEL_IN_APP, 'In-App'),
    ]

    # Delivery statuses
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_BOUNCED = 'bounced'
    STATUS_OPTED_OUT = 'opted_out'
    STATUS_SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent Successfully'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_BOUNCED, 'Bounced'),
        (STATUS_OPTED_OUT, 'User Opted Out'),
        (STATUS_SKIPPED, 'Skipped (preferences/quiet hours)'),
    ]

    # Related notification
    notification = models.ForeignKey(
        'Notification',
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )

    # Delivery details
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    # Recipient contact info (snapshot at time of sending)
    recipient_email = models.EmailField(
        blank=True,
        help_text="Email address used for delivery"
    )
    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number used for delivery"
    )

    # Provider-specific details
    provider_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Service provider (AWS SES, AWS SNS, etc.)"
    )
    provider_message_id = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        help_text="Provider's unique message ID for tracking"
    )
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full provider API response (for debugging)"
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if delivery failed"
    )
    error_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Error code from provider"
    )

    # Retry tracking
    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Delivery attempt number (1, 2, 3...)"
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled time for next retry attempt"
    )

    # Cost tracking (for SMS)
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Estimated cost in USD (primarily for SMS)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was successfully sent"
    )
    failed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When delivery failed"
    )

    # Celery task tracking
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Celery task ID for async delivery tracking"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['provider_message_id']),
            models.Index(fields=['created_at', 'channel']),
        ]
        verbose_name = "Notification Delivery Log"
        verbose_name_plural = "Notification Delivery Logs"

    def __str__(self):
        return f"{self.channel} to {self.recipient_email or self.recipient_phone} - {self.status}"

    def mark_sent(self, provider_message_id=None, provider_response=None):
        """Mark delivery as successful"""
        self.status = self.STATUS_SENT
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        if provider_response:
            self.provider_response = provider_response
        self.save(update_fields=['status', 'sent_at', 'provider_message_id', 'provider_response'])

    def mark_failed(self, error_message, error_code=None):
        """Mark delivery as failed and schedule retry if attempts remain"""
        self.status = self.STATUS_FAILED
        self.failed_at = timezone.now()
        self.error_message = error_message
        self.error_code = error_code or ''

        # Schedule retry with exponential backoff
        if self.attempt_number < self.max_attempts:
            from datetime import timedelta
            backoff_minutes = 5 * (2 ** (self.attempt_number - 1))  # 5, 10, 20 minutes
            self.next_retry_at = timezone.now() + timedelta(minutes=backoff_minutes)

        self.save(update_fields=['status', 'failed_at', 'error_message', 'error_code', 'next_retry_at'])

    def should_retry(self):
        """Check if this delivery should be retried"""
        return (
            self.status == self.STATUS_FAILED and
            self.attempt_number < self.max_attempts and
            self.next_retry_at and
            timezone.now() >= self.next_retry_at
        )
```

**Key Features:**
- **Complete audit trail** for all delivery attempts
- **Retry logic** with exponential backoff
- **Provider tracking** (message IDs, responses)
- **Cost tracking** for SMS notifications
- **Error logging** with codes and messages
- **Celery integration** for async task tracking
- **Status tracking** (pending, sent, failed, bounced, etc.)

---

## Database Migrations

### Migration Order

1. **Add phone validation to existing models**
2. **Create new notification models**
3. **Create preference models**
4. **Migrate existing TechnicianNotification data**
5. **Add indexes for performance**

### Migration 1: Update Contact Fields

**File**: `apps/core/migrations/0XXX_update_contact_fields.py`

```python
from django.db import migrations, models
import django.core.validators

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0XXX_previous_migration'),
        ('technician_portal', '0XXX_previous_migration'),
    ]

    operations = [
        # Standardize phone field on Customer model
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.CharField(
                max_length=20,
                blank=True,
                validators=[
                    django.core.validators.RegexValidator(
                        regex=r'^\+?1?\d{9,15}$',
                        message="Phone number must be entered in format: '+999999999'. Up to 15 digits allowed."
                    )
                ],
                help_text="Contact phone number in E.164 format (e.g., +12025551234)"
            ),
        ),

        # Add verified contact fields to Customer
        migrations.AddField(
            model_name='customer',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),

        # Update Technician phone_number field with validation
        migrations.AlterField(
            model_name='technician',
            name='phone_number',
            field=models.CharField(
                max_length=20,
                blank=True,
                validators=[
                    django.core.validators.RegexValidator(
                        regex=r'^\+?1?\d{9,15}$',
                        message="Phone number must be entered in format: '+999999999'. Up to 15 digits allowed."
                    )
                ],
                help_text="Contact phone number in E.164 format (e.g., +12025551234)"
            ),
        ),

        # Add verified contact fields to Technician
        migrations.AddField(
            model_name='technician',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='technician',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
    ]
```

### Migration 2: Create Notification Models

Standard Django migration for creating `Notification`, `NotificationTemplate`, and `NotificationDeliveryLog` models.

### Migration 3: Create Preference Models

Standard Django migration for creating `TechnicianNotificationPreference` and `CustomerNotificationPreference` models.

### Migration 4: Data Migration

**File**: `apps/core/migrations/0XXX_migrate_technician_notifications.py`

```python
from django.db import migrations

def migrate_existing_notifications(apps, schema_editor):
    """
    Migrate data from old TechnicianNotification to new Notification model.

    This preserves existing notification data while transitioning to the
    new unified notification system.
    """
    TechnicianNotification = apps.get_model('technician_portal', 'TechnicianNotification')
    Notification = apps.get_model('core', 'Notification')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Technician = apps.get_model('technician_portal', 'Technician')

    technician_ct = ContentType.objects.get_for_model(Technician)

    for old_notif in TechnicianNotification.objects.all():
        # Determine priority based on message content
        priority = 'MEDIUM'
        if 'APPROVED' in old_notif.message or 'DENIED' in old_notif.message:
            priority = 'URGENT'
        elif 'assigned' in old_notif.message.lower():
            priority = 'HIGH'

        # Determine category
        category = 'system'
        if old_notif.redemption_id:
            category = 'reward'
        elif 'APPROVED' in old_notif.message or 'DENIED' in old_notif.message:
            category = 'approval'
        elif 'assigned' in old_notif.message.lower():
            category = 'assignment'

        # Create new notification
        Notification.objects.create(
            recipient_type=technician_ct,
            recipient_id=old_notif.technician_id,
            title=old_notif.message[:100],  # First 100 chars as title
            message=old_notif.message,
            category=category,
            priority=priority,
            read=old_notif.read,
            created_at=old_notif.created_at,
            repair_id=old_notif.repair_id,
            repair_batch_id=old_notif.repair_batch_id,
        )

def reverse_migration(apps, schema_editor):
    """Clean up if migration is reversed"""
    Notification = apps.get_model('core', 'Notification')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Technician = apps.get_model('technician_portal', 'Technician')

    technician_ct = ContentType.objects.get_for_model(Technician)
    Notification.objects.filter(recipient_type=technician_ct).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0XXX_create_notification_models'),
        ('technician_portal', '0XXX_previous_migration'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_notifications, reverse_migration),
    ]
```

---

## Implementation Checklist

### Models

- [ ] Create `apps/core/models/notification.py`
- [ ] Create `apps/core/models/notification_preferences.py`
- [ ] Create `apps/core/models/notification_template.py`
- [ ] Create `apps/core/models/notification_delivery_log.py`
- [ ] Update `apps/core/models/__init__.py` to import all models
- [ ] Register models in `apps/core/admin.py`

### Migrations

- [ ] Create migration for contact field updates
- [ ] Run `python manage.py makemigrations core`
- [ ] Create migration for new notification models
- [ ] Create data migration for existing notifications
- [ ] Test migrations on development database
- [ ] Document rollback procedures

### Database Updates

- [ ] Add phone validation to Customer model
- [ ] Add phone validation to Technician model
- [ ] Add email_verified/phone_verified fields
- [ ] Create database indexes for performance
- [ ] Test queries with new indexes

### Admin Interface

- [ ] Create `NotificationAdmin` with filters and search
- [ ] Create `NotificationTemplateAdmin` with preview
- [ ] Create `NotificationPreferenceAdmin` (inline on User/Customer)
- [ ] Create `DeliveryLogAdmin` with retry actions
- [ ] Add bulk actions for marking read/unread

### Testing

- [ ] Unit tests for Notification model methods
- [ ] Unit tests for preference validation
- [ ] Unit tests for template rendering
- [ ] Unit tests for delivery log retry logic
- [ ] Integration tests for preference checking
- [ ] Migration tests (forward and reverse)

---

## Success Criteria

✅ All models created with proper fields and relationships
✅ Migrations run successfully without errors
✅ Existing TechnicianNotification data migrated to new system
✅ Phone validation working on Customer and Technician models
✅ Admin interface functional for all models
✅ Unit tests passing at 100% coverage
✅ Documentation complete with examples

---

## Next Phase

Once Phase 1 is complete, proceed to:
**Phase 2: AWS Infrastructure Setup** - Configure SES, SNS, and Celery for actual notification delivery.

---

## Notes & Considerations

### Performance Optimization

- **Indexes**: Added on frequently queried fields (priority, category, read status)
- **Select Related**: Use `select_related()` for ContentType queries
- **Prefetch Related**: Use for notification lists with related repairs/customers
- **Caching**: Consider caching unread notification counts per user

### Security Considerations

- **Contact Verification**: Require email/phone verification before sending
- **Rate Limiting**: Implement per-user notification rate limits
- **Opt-out Compliance**: Honor unsubscribe preferences (especially for SMS)
- **Data Privacy**: Consider GDPR/CCPA compliance for notification logs

### Scalability

- **Partitioning**: Consider partitioning DeliveryLog by date (monthly)
- **Archiving**: Archive old notifications (>90 days) to separate table
- **Cleanup**: Implement automatic cleanup of old delivery logs
- **Bulk Operations**: Use `bulk_create()` for batch notification creation

### Future Enhancements

- **Push Notifications**: Add support for mobile push via Firebase/APNs
- **Webhook Support**: Allow external integrations via webhooks
- **Notification Channels**: Add Slack, Microsoft Teams integration
- **A/B Testing**: Test different template versions for engagement
- **Analytics**: Track open rates, click rates, engagement metrics
