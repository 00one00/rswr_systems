# Phase 5: User Preference Management

**Timeline**: Day 6
**Status**: Not Started
**Dependencies**: Phase 1 (Models), Phase 4 (Services)

## Overview

This phase builds the user interface for managing notification preferences. Both customers and technicians need intuitive controls to customize when and how they receive notifications, verify contact information, and set quiet hours.

## Objectives

1. Build notification preferences page for technicians
2. Build notification preferences page for customers
3. Implement contact verification workflow (email and phone)
4. Add quiet hours configuration
5. Create notification history view
6. Add mark-as-read functionality
7. Build notification center UI component

---

## Technician Notification Preferences

### Preferences View

**File**: `apps/technician_portal/views.py` (Add to existing file)

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.models import TechnicianNotificationPreference, Notification
from apps.technician_portal.models import Technician
from apps.technician_portal.forms import TechnicianNotificationPreferenceForm

@login_required
def notification_preferences(request):
    """
    Technician notification preferences management page.

    Allows technicians to:
    - Enable/disable notification channels (email, SMS, in-app)
    - Configure quiet hours
    - Set category preferences
    - Verify contact information
    - Enable daily digest mode
    """

    try:
        technician = request.user.technician
    except Technician.DoesNotExist:
        messages.error(request, "Technician profile not found.")
        return redirect('technician_dashboard')

    # Get or create preferences
    preferences, created = TechnicianNotificationPreference.objects.get_or_create(
        technician=technician
    )

    if request.method == 'POST':
        form = TechnicianNotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully!")
            return redirect('notification_preferences')
    else:
        form = TechnicianNotificationPreferenceForm(instance=preferences)

    # Get notification statistics
    unread_count = Notification.objects.filter(
        recipient_type__model='technician',
        recipient_id=technician.id,
        read=False
    ).count()

    total_notifications = Notification.objects.filter(
        recipient_type__model='technician',
        recipient_id=technician.id
    ).count()

    context = {
        'form': form,
        'preferences': preferences,
        'technician': technician,
        'unread_count': unread_count,
        'total_notifications': total_notifications,
    }

    return render(request, 'technician_portal/notification_preferences.html', context)


@login_required
def verify_email(request):
    """
    Send email verification link to technician.

    Sends verification email with unique token.
    """
    try:
        technician = request.user.technician
        preferences = technician.notification_preferences
    except (Technician.DoesNotExist, TechnicianNotificationPreference.DoesNotExist):
        messages.error(request, "Unable to verify email.")
        return redirect('notification_preferences')

    # Generate verification token
    from django.contrib.auth.tokens import default_token_generator
    token = default_token_generator.make_token(request.user)

    # Send verification email
    from apps.core.services.email_service import EmailService
    verification_url = request.build_absolute_uri(
        f'/tech/verify-email/{request.user.pk}/{token}/'
    )

    # TODO: Send verification email with link

    messages.success(request, f"Verification email sent to {request.user.email}")
    return redirect('notification_preferences')


@login_required
def verify_phone(request):
    """
    Send SMS verification code to technician.

    Sends 6-digit verification code via SMS.
    """
    try:
        technician = request.user.technician
        preferences = technician.notification_preferences
    except (Technician.DoesNotExist, TechnicianNotificationPreference.DoesNotExist):
        messages.error(request, "Unable to verify phone.")
        return redirect('notification_preferences')

    if not technician.phone_number:
        messages.error(request, "Please add a phone number first.")
        return redirect('notification_preferences')

    # Generate 6-digit code
    import random
    code = f"{random.randint(100000, 999999)}"

    # Store code in session
    request.session['phone_verification_code'] = code
    request.session['phone_verification_number'] = technician.phone_number

    # Send verification SMS
    from apps.core.services.sms_service import SMSService
    message = f"Your RS Systems verification code is: {code}"

    # TODO: Send verification SMS

    messages.success(request, f"Verification code sent to {technician.phone_number}")
    return redirect('notification_preferences')


@login_required
def notification_history(request):
    """
    View all notifications for technician.

    Paginated list with filters (read/unread, category, date range).
    """
    try:
        technician = request.user.technician
    except Technician.DoesNotExist:
        messages.error(request, "Technician profile not found.")
        return redirect('technician_dashboard')

    from django.contrib.contenttypes.models import ContentType
    technician_ct = ContentType.objects.get_for_model(Technician)

    # Get notifications
    notifications = Notification.objects.filter(
        recipient_type=technician_ct,
        recipient_id=technician.id
    ).select_related('repair', 'customer')

    # Filters
    show_read = request.GET.get('show_read', 'false') == 'true'
    category = request.GET.get('category', '')

    if not show_read:
        notifications = notifications.filter(read=False)

    if category:
        notifications = notifications.filter(category=category)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 25)  # 25 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'notifications': page_obj,
        'show_read': show_read,
        'category': category,
        'categories': Notification.CATEGORY_CHOICES,
    }

    return render(request, 'technician_portal/notification_history.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark single notification as read"""
    try:
        technician = request.user.technician
        technician_ct = ContentType.objects.get_for_model(Technician)

        notification = Notification.objects.get(
            id=notification_id,
            recipient_type=technician_ct,
            recipient_id=technician.id
        )

        notification.mark_as_read()
        return JsonResponse({'success': True})

    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def mark_all_read(request):
    """Mark all notifications as read for technician"""
    try:
        technician = request.user.technician
        technician_ct = ContentType.objects.get_for_model(Technician)

        updated = Notification.objects.filter(
            recipient_type=technician_ct,
            recipient_id=technician.id,
            read=False
        ).update(read=True, read_at=timezone.now())

        return JsonResponse({'success': True, 'count': updated})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### Preferences Form

**File**: `apps/technician_portal/forms.py` (Add to existing file)

```python
from django import forms
from apps.core.models import TechnicianNotificationPreference

class TechnicianNotificationPreferenceForm(forms.ModelForm):
    """
    Form for technician notification preferences.

    Groups settings into logical sections with helpful descriptions.
    """

    class Meta:
        model = TechnicianNotificationPreference
        fields = [
            # Global preferences
            'receive_email_notifications',
            'receive_sms_notifications',
            'receive_in_app_notifications',

            # Category preferences
            'notify_repair_status',
            'notify_new_assignments',
            'notify_reassignments',
            'notify_customer_approvals',
            'notify_reward_redemptions',
            'notify_system',

            # Quiet hours
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',

            # Digest mode
            'digest_enabled',
            'digest_time',
        ]

        widgets = {
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time'}),
            'digest_time': forms.TimeInput(attrs={'type': 'time'}),
        }

        help_texts = {
            'receive_sms_notifications': 'Receive high-priority notifications via text message (standard SMS rates may apply)',
            'quiet_hours_enabled': 'Pause non-urgent notifications during specified hours',
            'digest_enabled': 'Receive one daily email summary instead of individual notifications',
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validate quiet hours
        quiet_enabled = cleaned_data.get('quiet_hours_enabled')
        quiet_start = cleaned_data.get('quiet_hours_start')
        quiet_end = cleaned_data.get('quiet_hours_end')

        if quiet_enabled and (not quiet_start or not quiet_end):
            raise forms.ValidationError(
                "Quiet hours start and end times are required when quiet hours are enabled."
            )

        # Validate digest settings
        digest_enabled = cleaned_data.get('digest_enabled')
        digest_time = cleaned_data.get('digest_time')

        if digest_enabled and not digest_time:
            raise forms.ValidationError(
                "Digest time is required when daily digest is enabled."
            )

        return cleaned_data
```

### Preferences Template

**File**: `templates/technician_portal/notification_preferences.html`

```django
{% extends "technician_portal/base.html" %}
{% load static %}

{% block title %}Notification Preferences{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h2 class="mb-0">Notification Preferences</h2>
                    <p class="text-muted mb-0">Manage how and when you receive notifications</p>
                </div>
                <div class="card-body">
                    <!-- Contact Verification Status -->
                    <div class="alert alert-info mb-4">
                        <h5 class="alert-heading">Contact Verification</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Email:</strong> {{ user.email }}
                                {% if preferences.email_verified %}
                                    <span class="badge bg-success">✓ Verified</span>
                                {% else %}
                                    <span class="badge bg-warning">Not Verified</span>
                                    <a href="{% url 'verify_email' %}" class="btn btn-sm btn-primary ms-2">Verify Email</a>
                                {% endif %}
                            </div>
                            <div class="col-md-6">
                                <strong>Phone:</strong> {{ technician.phone_number|default:"Not provided" }}
                                {% if preferences.phone_verified %}
                                    <span class="badge bg-success">✓ Verified</span>
                                {% else %}
                                    {% if technician.phone_number %}
                                        <span class="badge bg-warning">Not Verified</span>
                                        <a href="{% url 'verify_phone' %}" class="btn btn-sm btn-primary ms-2">Verify Phone</a>
                                    {% else %}
                                        <a href="{% url 'technician_profile_edit' %}" class="btn btn-sm btn-secondary ms-2">Add Phone Number</a>
                                    {% endif %}
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- Preferences Form -->
                    <form method="post" id="preferences-form">
                        {% csrf_token %}

                        <!-- Delivery Channels -->
                        <div class="mb-4">
                            <h4 class="mb-3">Delivery Channels</h4>
                            <p class="text-muted">Choose how you want to receive notifications</p>

                            <div class="form-check form-switch mb-3">
                                {{ form.receive_in_app_notifications }}
                                <label class="form-check-label" for="{{ form.receive_in_app_notifications.id_for_label }}">
                                    <strong>In-App Notifications</strong><br>
                                    <small class="text-muted">Show notifications in the dashboard (always enabled for urgent notifications)</small>
                                </label>
                            </div>

                            <div class="form-check form-switch mb-3">
                                {{ form.receive_email_notifications }}
                                <label class="form-check-label" for="{{ form.receive_email_notifications.id_for_label }}">
                                    <strong>Email Notifications</strong><br>
                                    <small class="text-muted">Receive medium-priority notifications via email</small>
                                </label>
                            </div>

                            <div class="form-check form-switch mb-3">
                                {{ form.receive_sms_notifications }}
                                <label class="form-check-label" for="{{ form.receive_sms_notifications.id_for_label }}">
                                    <strong>SMS Notifications</strong><br>
                                    <small class="text-muted">{{ form.receive_sms_notifications.help_text }}</small>
                                </label>
                            </div>
                        </div>

                        <hr class="my-4">

                        <!-- Category Preferences -->
                        <div class="mb-4">
                            <h4 class="mb-3">Notification Categories</h4>
                            <p class="text-muted">Choose which types of notifications you want to receive</p>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-check mb-3">
                                        {{ form.notify_new_assignments }}
                                        <label class="form-check-label" for="{{ form.notify_new_assignments.id_for_label }}">
                                            <strong>New Assignments</strong><br>
                                            <small class="text-muted">When you're assigned new repairs</small>
                                        </label>
                                    </div>

                                    <div class="form-check mb-3">
                                        {{ form.notify_reassignments }}
                                        <label class="form-check-label" for="{{ form.notify_reassignments.id_for_label }}">
                                            <strong>Reassignments</strong><br>
                                            <small class="text-muted">When repairs are reassigned away from you</small>
                                        </label>
                                    </div>

                                    <div class="form-check mb-3">
                                        {{ form.notify_customer_approvals }}
                                        <label class="form-check-label" for="{{ form.notify_customer_approvals.id_for_label }}">
                                            <strong>Customer Approvals/Denials</strong><br>
                                            <small class="text-muted">When customers approve or deny your repairs (always urgent)</small>
                                        </label>
                                    </div>
                                </div>

                                <div class="col-md-6">
                                    <div class="form-check mb-3">
                                        {{ form.notify_repair_status }}
                                        <label class="form-check-label" for="{{ form.notify_repair_status.id_for_label }}">
                                            <strong>Repair Status Changes</strong><br>
                                            <small class="text-muted">Updates on repair progress</small>
                                        </label>
                                    </div>

                                    <div class="form-check mb-3">
                                        {{ form.notify_reward_redemptions }}
                                        <label class="form-check-label" for="{{ form.notify_reward_redemptions.id_for_label }}">
                                            <strong>Reward Redemptions</strong><br>
                                            <small class="text-muted">When rewards are available or redeemed</small>
                                        </label>
                                    </div>

                                    <div class="form-check mb-3">
                                        {{ form.notify_system }}
                                        <label class="form-check-label" for="{{ form.notify_system.id_for_label }}">
                                            <strong>System Announcements</strong><br>
                                            <small class="text-muted">Important system updates and announcements</small>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <hr class="my-4">

                        <!-- Quiet Hours -->
                        <div class="mb-4">
                            <h4 class="mb-3">Quiet Hours</h4>
                            <p class="text-muted">Pause non-urgent notifications during specified hours</p>

                            <div class="form-check form-switch mb-3">
                                {{ form.quiet_hours_enabled }}
                                <label class="form-check-label" for="{{ form.quiet_hours_enabled.id_for_label }}">
                                    <strong>Enable Quiet Hours</strong>
                                </label>
                            </div>

                            <div class="row" id="quiet-hours-settings" style="display: {% if form.quiet_hours_enabled.value %}block{% else %}none{% endif %};">
                                <div class="col-md-6">
                                    <label for="{{ form.quiet_hours_start.id_for_label }}" class="form-label">Start Time</label>
                                    {{ form.quiet_hours_start }}
                                </div>
                                <div class="col-md-6">
                                    <label for="{{ form.quiet_hours_end.id_for_label }}" class="form-label">End Time</label>
                                    {{ form.quiet_hours_end }}
                                </div>
                            </div>
                        </div>

                        <hr class="my-4">

                        <!-- Daily Digest -->
                        <div class="mb-4">
                            <h4 class="mb-3">Daily Digest</h4>
                            <p class="text-muted">Receive one daily summary email instead of individual notifications</p>

                            <div class="form-check form-switch mb-3">
                                {{ form.digest_enabled }}
                                <label class="form-check-label" for="{{ form.digest_enabled.id_for_label }}">
                                    <strong>Enable Daily Digest</strong>
                                </label>
                            </div>

                            <div id="digest-settings" style="display: {% if form.digest_enabled.value %}block{% else %}none{% endif %};">
                                <label for="{{ form.digest_time.id_for_label }}" class="form-label">Digest Time</label>
                                {{ form.digest_time }}
                                <small class="form-text text-muted">Time to receive daily notification summary</small>
                            </div>
                        </div>

                        <!-- Save Button -->
                        <div class="text-end">
                            <a href="{% url 'technician_dashboard' %}" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">Save Preferences</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Notification Statistics -->
            <div class="card mt-4">
                <div class="card-header">
                    <h4 class="mb-0">Notification Statistics</h4>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-md-4">
                            <h3 class="text-primary">{{ unread_count }}</h3>
                            <p class="text-muted">Unread Notifications</p>
                        </div>
                        <div class="col-md-4">
                            <h3 class="text-secondary">{{ total_notifications }}</h3>
                            <p class="text-muted">Total Notifications</p>
                        </div>
                        <div class="col-md-4">
                            <a href="{% url 'notification_history' %}" class="btn btn-outline-primary">
                                View Notification History
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Show/hide quiet hours settings
document.getElementById('{{ form.quiet_hours_enabled.id_for_label }}').addEventListener('change', function() {
    document.getElementById('quiet-hours-settings').style.display = this.checked ? 'block' : 'none';
});

// Show/hide digest settings
document.getElementById('{{ form.digest_enabled.id_for_label }}').addEventListener('change', function() {
    document.getElementById('digest-settings').style.display = this.checked ? 'block' : 'none';
});
</script>
{% endblock %}
```

---

## Notification Center Component

### Header Notification Bell

**File**: `templates/technician_portal/includes/notification_bell.html`

```django
{% load static %}

<!-- Notification Bell Icon -->
<div class="dropdown" id="notification-dropdown">
    <a class="nav-link dropdown-toggle position-relative" href="#" id="notificationDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
        <i class="fas fa-bell" style="font-size: 1.25rem;"></i>
        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" id="unread-count" style="display: {% if unread_count > 0 %}inline{% else %}none{% endif %};">
            {{ unread_count }}
            <span class="visually-hidden">unread notifications</span>
        </span>
    </a>

    <ul class="dropdown-menu dropdown-menu-end notification-dropdown" aria-labelledby="notificationDropdown" style="width: 350px; max-height: 500px; overflow-y: auto;">
        <!-- Header -->
        <li class="dropdown-header d-flex justify-content-between align-items-center">
            <span><strong>Notifications</strong></span>
            <a href="#" id="mark-all-read" class="text-primary text-decoration-none" style="font-size: 0.875rem;">Mark all read</a>
        </li>
        <li><hr class="dropdown-divider"></li>

        <!-- Notifications List -->
        <div id="notification-list">
            {% if recent_notifications %}
                {% for notification in recent_notifications %}
                <li>
                    <a class="dropdown-item notification-item {% if not notification.read %}unread{% endif %}" href="{{ notification.action_url }}" data-notification-id="{{ notification.id }}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <strong>{{ notification.title }}</strong>
                                <p class="mb-1 text-muted small">{{ notification.message|truncatewords:15 }}</p>
                                <small class="text-muted">{{ notification.created_at|timesince }} ago</small>
                            </div>
                            {% if not notification.read %}
                            <span class="badge bg-primary">New</span>
                            {% endif %}
                        </div>
                    </a>
                </li>
                {% if not forloop.last %}<li><hr class="dropdown-divider"></li>{% endif %}
                {% endfor %}
            {% else %}
                <li class="dropdown-item text-center text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>No notifications</p>
                </li>
            {% endif %}
        </div>

        <!-- Footer -->
        <li><hr class="dropdown-divider"></li>
        <li>
            <a class="dropdown-item text-center text-primary" href="{% url 'notification_history' %}">
                View All Notifications
            </a>
        </li>
    </ul>
</div>

<style>
.notification-item.unread {
    background-color: #f0f7ff;
    border-left: 3px solid #0d6efd;
}

.notification-item:hover {
    background-color: #f8f9fa;
}

.notification-dropdown {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
</style>

<script>
// Mark notification as read when clicked
document.querySelectorAll('.notification-item').forEach(item => {
    item.addEventListener('click', function(e) {
        const notificationId = this.dataset.notificationId;
        if (notificationId) {
            markNotificationRead(notificationId);
        }
    });
});

// Mark all notifications as read
document.getElementById('mark-all-read').addEventListener('click', function(e) {
    e.preventDefault();
    markAllRead();
});

function markNotificationRead(notificationId) {
    fetch(`/tech/notifications/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    }).then(response => {
        if (response.ok) {
            updateUnreadCount(-1);
        }
    });
}

function markAllRead() {
    fetch('/tech/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              updateUnreadCount(-data.count);
              // Remove "unread" class from all items
              document.querySelectorAll('.notification-item.unread').forEach(item => {
                  item.classList.remove('unread');
                  item.querySelector('.badge').remove();
              });
          }
      });
}

function updateUnreadCount(delta) {
    const badge = document.getElementById('unread-count');
    const currentCount = parseInt(badge.textContent) || 0;
    const newCount = Math.max(0, currentCount + delta);

    badge.textContent = newCount;
    badge.style.display = newCount > 0 ? 'inline' : 'none';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Poll for new notifications every 30 seconds
setInterval(function() {
    fetch('/tech/notifications/unread-count/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('unread-count');
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'inline' : 'none';
        });
}, 30000);
</script>
```

---

## Customer Notification Preferences

### Customer Preferences View

**File**: `apps/customer_portal/views.py` (Add to existing file)

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.models import CustomerNotificationPreference
from apps.customer_portal.forms import CustomerNotificationPreferenceForm

@login_required
def customer_notification_preferences(request):
    """
    Customer notification preferences management page.

    Similar to technician preferences but with customer-specific categories.
    """

    try:
        customer_user = request.user.customeruser
        customer = customer_user.customer
    except CustomerUser.DoesNotExist:
        messages.error(request, "Customer profile not found.")
        return redirect('customer_dashboard')

    # Get or create preferences
    preferences, created = CustomerNotificationPreference.objects.get_or_create(
        customer=customer
    )

    if request.method == 'POST':
        form = CustomerNotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully!")
            return redirect('customer_notification_preferences')
    else:
        form = CustomerNotificationPreferenceForm(instance=preferences)

    context = {
        'form': form,
        'preferences': preferences,
        'customer': customer,
    }

    return render(request, 'customer_portal/notification_preferences.html', context)
```

---

## URL Configuration

**File**: `apps/technician_portal/urls.py` (Add to existing patterns)

```python
from django.urls import path
from apps.technician_portal import views

urlpatterns = [
    # ... existing patterns ...

    # Notification management
    path('notifications/preferences/', views.notification_preferences, name='notification_preferences'),
    path('notifications/history/', views.notification_history, name='notification_history'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),

    # Contact verification
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),

    # AJAX endpoints
    path('notifications/unread-count/', views.get_unread_count, name='get_unread_count'),
]
```

---

## Implementation Checklist

### Views & Forms
- [ ] Create notification preferences view (technician)
- [ ] Create notification preferences view (customer)
- [ ] Create notification history view
- [ ] Create mark-as-read endpoints
- [ ] Create preference forms with validation
- [ ] Add email/phone verification views

### Templates
- [ ] Create preferences page template (technician)
- [ ] Create preferences page template (customer)
- [ ] Create notification history template
- [ ] Create notification bell component
- [ ] Add notification dropdown
- [ ] Style unread notifications

### JavaScript
- [ ] Add mark-as-read functionality
- [ ] Add notification polling
- [ ] Add quiet hours toggle
- [ ] Add digest mode toggle
- [ ] Add notification count updates

### Testing
- [ ] Test preference saving
- [ ] Test quiet hours logic
- [ ] Test notification filtering
- [ ] Test mark-as-read functionality
- [ ] Test notification bell updates
- [ ] Test mobile responsiveness

---

## Success Criteria

✅ Preference pages functional for both user types
✅ Contact verification working
✅ Quiet hours respected
✅ Notification bell showing unread count
✅ Mark-as-read functionality working
✅ Notification history paginated and filterable
✅ Mobile-responsive design
✅ Preferences persisted correctly

---

## Next Phase

Once Phase 5 is complete, proceed to:
**Phase 6: Monitoring & Testing** - Set up monitoring, create comprehensive tests, and prepare for production deployment.
