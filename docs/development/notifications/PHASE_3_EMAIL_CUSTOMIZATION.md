# Phase 3: Email Template System & Customization

**Timeline**: Day 4
**Status**: Not Started
**Dependencies**: Phase 1 (Models), Phase 2 (AWS Infrastructure)

## Overview

This phase focuses on creating a professional, branded email template system with full customization support. We'll build reusable HTML email templates with logos, configurable colors, responsive design, and a management interface for non-technical users to customize branding.

## Objectives

1. Create base email template with RS Systems branding
2. Design notification-specific email templates (approval, denial, assignment, etc.)
3. Implement logo support with configurable upload
4. Build color scheme customization system
5. Create email template preview system
6. Implement responsive design for mobile devices
7. Support both HTML and plain text versions
8. Build admin interface for template customization

---

## Email Template Architecture

### Template Hierarchy

```
Base Template (branding, header, footer)
    ├── Transactional Template (repair notifications)
    │   ├── Repair Approved
    │   ├── Repair Denied
    │   ├── Repair Assigned
    │   ├── Repair Completed
    │   └── Batch Approval
    ├── Digest Template (daily summary)
    └── System Template (account, rewards, etc.)
```

**Inheritance Pattern:**
```django
{% extends "emails/base.html" %}
{% block content %}
    <!-- Notification-specific content -->
{% endblock %}
```

---

## Email Branding Configuration Model

### Branding Settings Model

**File**: `apps/core/models/email_branding.py`

```python
from django.db import models
from django.core.validators import RegexValidator
from PIL import Image
import os

def branding_logo_path(instance, filename):
    """Store logos in branding/logos/ directory"""
    ext = filename.split('.')[-1]
    return f'branding/logos/email_logo.{ext}'

class EmailBrandingConfig(models.Model):
    """
    Email branding and customization settings.

    Singleton model - only one configuration exists at a time.
    Allows customization of email appearance without code changes.
    """

    # Logo configuration
    logo = models.ImageField(
        upload_to=branding_logo_path,
        blank=True,
        null=True,
        help_text="Company logo for email header (recommended: 200x80px PNG with transparency)"
    )
    logo_width = models.PositiveIntegerField(
        default=200,
        help_text="Logo display width in pixels (height auto-scales)"
    )
    logo_alt_text = models.CharField(
        max_length=100,
        default="RS Systems",
        help_text="Alt text for logo (accessibility)"
    )

    # Color scheme
    primary_color = models.CharField(
        max_length=7,
        default="#2C5282",  # Professional blue
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #2C5282)'
            )
        ],
        help_text="Primary brand color (hex format: #RRGGBB)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#4299E1",  # Lighter blue
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #4299E1)'
            )
        ],
        help_text="Secondary accent color"
    )
    success_color = models.CharField(
        max_length=7,
        default="#38A169",  # Green
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #38A169)'
            )
        ],
        help_text="Color for success messages (approvals)"
    )
    danger_color = models.CharField(
        max_length=7,
        default="#E53E3E",  # Red
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #E53E3E)'
            )
        ],
        help_text="Color for danger/warning messages (denials)"
    )
    text_color = models.CharField(
        max_length=7,
        default="#2D3748",  # Dark gray
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #2D3748)'
            )
        ],
        help_text="Main text color"
    )
    background_color = models.CharField(
        max_length=7,
        default="#F7FAFC",  # Light gray
        validators=[
            RegexValidator(
                regex=r'^#[0-9A-Fa-f]{6}$',
                message='Enter a valid hex color (e.g., #F7FAFC)'
            )
        ],
        help_text="Email background color"
    )

    # Company information
    company_name = models.CharField(
        max_length=100,
        default="RS Systems",
        help_text="Company name displayed in emails"
    )
    company_address = models.TextField(
        blank=True,
        help_text="Company address for email footer (optional)"
    )
    support_email = models.EmailField(
        default="support@rssystems.com",
        help_text="Support email displayed in footer"
    )
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Support phone number (optional)"
    )
    website_url = models.URLField(
        default="https://rssystems.com",
        help_text="Company website URL"
    )

    # Social media links (optional)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Email footer customization
    footer_text = models.TextField(
        default="You're receiving this email because you have an account with RS Systems.",
        help_text="Footer disclaimer text"
    )
    show_social_links = models.BooleanField(
        default=False,
        help_text="Display social media icons in footer"
    )
    show_unsubscribe_link = models.BooleanField(
        default=True,
        help_text="Display unsubscribe link in footer"
    )

    # Button styling
    button_border_radius = models.PositiveIntegerField(
        default=6,
        help_text="Button corner roundness in pixels (0 = square, 20+ = pill-shaped)"
    )

    # Typography
    font_family = models.CharField(
        max_length=100,
        default="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        help_text="Font stack for email text"
    )
    heading_font_family = models.CharField(
        max_length=100,
        default="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        help_text="Font stack for headings"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who last updated branding"
    )

    class Meta:
        verbose_name = "Email Branding Configuration"
        verbose_name_plural = "Email Branding Configuration"

    def __str__(self):
        return f"Email Branding - {self.company_name}"

    def save(self, *args, **kwargs):
        """Ensure only one branding config exists (singleton)"""
        if not self.pk and EmailBrandingConfig.objects.exists():
            # Update existing instead of creating new
            existing = EmailBrandingConfig.objects.first()
            self.pk = existing.pk

        # Validate and resize logo if uploaded
        if self.logo:
            self._process_logo()

        super().save(*args, **kwargs)

    def _process_logo(self):
        """Validate and optimize uploaded logo"""
        if not self.logo:
            return

        # Open image
        img = Image.open(self.logo)

        # Convert RGBA to RGB if needed (for JPEGs)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Keep transparency for PNGs
            pass
        else:
            img = img.convert('RGB')

        # Resize if too large (max width 400px to avoid huge emails)
        max_width = 400
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Save optimized image
        img.save(self.logo.path, optimize=True, quality=85)

    @classmethod
    def get_config(cls):
        """Get or create singleton branding configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def get_logo_url(self, request=None):
        """Get absolute URL for logo (for email embedding)"""
        if not self.logo:
            return None

        if request:
            return request.build_absolute_uri(self.logo.url)
        else:
            from django.conf import settings
            # Fallback: construct URL from SITE_URL setting
            site_url = getattr(settings, 'SITE_URL', 'https://rssystems.com')
            return f"{site_url}{self.logo.url}"

    def to_template_context(self, request=None):
        """
        Convert branding config to template context dict.

        Returns all branding settings as a dictionary for use in email templates.
        """
        return {
            'branding': {
                'logo_url': self.get_logo_url(request),
                'logo_width': self.logo_width,
                'logo_alt_text': self.logo_alt_text,
                'primary_color': self.primary_color,
                'secondary_color': self.secondary_color,
                'success_color': self.success_color,
                'danger_color': self.danger_color,
                'text_color': self.text_color,
                'background_color': self.background_color,
                'company_name': self.company_name,
                'company_address': self.company_address,
                'support_email': self.support_email,
                'support_phone': self.support_phone,
                'website_url': self.website_url,
                'facebook_url': self.facebook_url,
                'twitter_url': self.twitter_url,
                'linkedin_url': self.linkedin_url,
                'footer_text': self.footer_text,
                'show_social_links': self.show_social_links,
                'show_unsubscribe_link': self.show_unsubscribe_link,
                'button_border_radius': self.button_border_radius,
                'font_family': self.font_family,
                'heading_font_family': self.heading_font_family,
            }
        }
```

**Key Features:**
- **Singleton pattern** - only one branding config exists
- **Logo upload** with automatic resizing and optimization
- **Complete color customization** with hex validation
- **Configurable company info** (name, address, contact details)
- **Social media integration** (optional)
- **Typography control** (font families)
- **Button styling** (border radius for modern/classic look)
- **Template context method** for easy use in templates

---

## Base Email Template

### HTML Email Structure

Email clients have limited CSS support. We use **inline styles** and **table-based layouts** for maximum compatibility.

**File**: `templates/emails/base.html`

```django
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="x-apple-disable-message-reformatting">
    <title>{% block email_title %}{{ subject }}{% endblock %}</title>

    <!--[if mso]>
    <style>
        * { font-family: sans-serif !important; }
    </style>
    <![endif]-->

    <style>
        /* Reset styles */
        body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
        table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
        img { -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }

        /* Mobile responsive */
        @media only screen and (max-width: 600px) {
            .email-container { width: 100% !important; margin: auto !important; }
            .stack-column { display: block !important; width: 100% !important; max-width: 100% !important; }
            .mobile-padding { padding: 20px !important; }
            .mobile-center { text-align: center !important; }
        }
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: {{ branding.background_color }}; font-family: {{ branding.font_family }};">
    <!-- Preview text (shows in email client preview) -->
    <div style="display: none; max-height: 0px; overflow: hidden;">
        {% block preview_text %}{% endblock %}
    </div>

    <!-- Email wrapper -->
    <table role="presentation" style="width: 100%; margin: 0; padding: 0; background-color: {{ branding.background_color }};" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding: 40px 10px;">
                <!-- Main email container (600px width for desktop) -->
                <table class="email-container" role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" border="0" cellpadding="0" cellspacing="0">

                    <!-- HEADER -->
                    <tr>
                        <td style="background-color: {{ branding.primary_color }}; padding: 30px 40px; text-align: center; border-radius: 8px 8px 0 0;">
                            {% if branding.logo_url %}
                                <a href="{{ branding.website_url }}" style="text-decoration: none;">
                                    <img src="{{ branding.logo_url }}"
                                         alt="{{ branding.logo_alt_text }}"
                                         width="{{ branding.logo_width }}"
                                         style="display: inline-block; max-width: {{ branding.logo_width }}px; height: auto;">
                                </a>
                            {% else %}
                                <h1 style="margin: 0; color: #ffffff; font-family: {{ branding.heading_font_family }}; font-size: 28px; font-weight: bold;">
                                    {{ branding.company_name }}
                                </h1>
                            {% endif %}
                        </td>
                    </tr>

                    <!-- CONTENT -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 40px 30px 40px; color: {{ branding.text_color }}; font-family: {{ branding.font_family }}; font-size: 16px; line-height: 24px;">
                            {% block content %}
                            <!-- Notification-specific content goes here -->
                            {% endblock %}
                        </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px 40px; border-radius: 0 0 8px 8px; border-top: 1px solid #e2e8f0;">
                            <!-- Company info -->
                            <table role="presentation" style="width: 100%;" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="text-align: center; color: #718096; font-size: 14px; line-height: 20px;">
                                        <p style="margin: 0 0 10px 0;">
                                            <strong>{{ branding.company_name }}</strong>
                                        </p>
                                        {% if branding.company_address %}
                                        <p style="margin: 0 0 10px 0;">
                                            {{ branding.company_address|linebreaks }}
                                        </p>
                                        {% endif %}
                                        <p style="margin: 0 0 10px 0;">
                                            {% if branding.support_phone %}
                                                {{ branding.support_phone }} &bull;
                                            {% endif %}
                                            <a href="mailto:{{ branding.support_email }}" style="color: {{ branding.primary_color }}; text-decoration: none;">
                                                {{ branding.support_email }}
                                            </a>
                                        </p>

                                        <!-- Social links -->
                                        {% if branding.show_social_links %}
                                        <table role="presentation" style="margin: 20px auto 0;" border="0" cellpadding="0" cellspacing="0">
                                            <tr>
                                                {% if branding.facebook_url %}
                                                <td style="padding: 0 10px;">
                                                    <a href="{{ branding.facebook_url }}" style="color: {{ branding.primary_color }}; text-decoration: none;">Facebook</a>
                                                </td>
                                                {% endif %}
                                                {% if branding.twitter_url %}
                                                <td style="padding: 0 10px;">
                                                    <a href="{{ branding.twitter_url }}" style="color: {{ branding.primary_color }}; text-decoration: none;">Twitter</a>
                                                </td>
                                                {% endif %}
                                                {% if branding.linkedin_url %}
                                                <td style="padding: 0 10px;">
                                                    <a href="{{ branding.linkedin_url }}" style="color: {{ branding.primary_color }}; text-decoration: none;">LinkedIn</a>
                                                </td>
                                                {% endif %}
                                            </tr>
                                        </table>
                                        {% endif %}

                                        <!-- Footer text -->
                                        <p style="margin: 20px 0 0 0; font-size: 12px; color: #a0aec0;">
                                            {{ branding.footer_text }}
                                        </p>

                                        <!-- Unsubscribe link -->
                                        {% if branding.show_unsubscribe_link %}
                                        <p style="margin: 10px 0 0 0; font-size: 12px;">
                                            <a href="{% url 'notification_preferences' %}" style="color: {{ branding.primary_color }}; text-decoration: underline;">
                                                Manage notification preferences
                                            </a>
                                        </p>
                                        {% endif %}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
```

**Key Features:**
- **Responsive design** with mobile breakpoints
- **Table-based layout** for email client compatibility
- **Inline styles** (required for Gmail, Outlook)
- **MSO conditional comments** for Outlook
- **Preview text** support (first line in email preview)
- **Social media integration**
- **Unsubscribe link** (CAN-SPAM compliance)

---

## Notification Email Templates

### 1. Repair Approved Template

**File**: `templates/emails/notifications/repair_approved.html`

```django
{% extends "emails/base.html" %}

{% block preview_text %}
Your repair #{{ repair.id }} for {{ repair.unit_number }} has been approved! Cost: ${{ repair.cost }}
{% endblock %}

{% block content %}
<!-- Success icon/badge -->
<table role="presentation" style="width: 100%; margin-bottom: 20px;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center;">
            <div style="display: inline-block; background-color: {{ branding.success_color }}; color: white; padding: 12px 24px; border-radius: 50px; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                ✅ Approved
            </div>
        </td>
    </tr>
</table>

<!-- Greeting -->
<h2 style="margin: 0 0 20px 0; color: {{ branding.text_color }}; font-family: {{ branding.heading_font_family }}; font-size: 24px; font-weight: bold;">
    Great news, {{ technician.user.first_name }}!
</h2>

<!-- Main message -->
<p style="margin: 0 0 20px 0;">
    Your repair request has been <strong style="color: {{ branding.success_color }};">approved</strong> by {{ repair.customer.company_name }}.
</p>

<!-- Repair details card -->
<table role="presentation" style="width: 100%; background-color: #f8f9fa; border-left: 4px solid {{ branding.success_color }}; border-radius: 4px; margin: 20px 0;" border="0" cellpadding="20" cellspacing="0">
    <tr>
        <td>
            <table role="presentation" style="width: 100%;" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding-bottom: 10px;">
                        <strong style="color: #4a5568; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Repair Details</strong>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;">
                        <strong>Repair ID:</strong> #{{ repair.id }}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;">
                        <strong>Unit:</strong> {{ repair.unit_number }}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;">
                        <strong>Customer:</strong> {{ repair.customer.company_name }}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;">
                        <strong>Approved Cost:</strong> <span style="color: {{ branding.success_color }}; font-size: 18px; font-weight: bold;">${{ repair.cost }}</span>
                    </td>
                </tr>
                {% if repair.customer_notes %}
                <tr>
                    <td style="padding: 10px 0 0 0; border-top: 1px solid #e2e8f0; margin-top: 10px;">
                        <strong>Customer Notes:</strong><br>
                        <em style="color: #718096;">{{ repair.customer_notes }}</em>
                    </td>
                </tr>
                {% endif %}
            </table>
        </td>
    </tr>
</table>

<!-- Next steps -->
<h3 style="margin: 30px 0 15px 0; color: {{ branding.text_color }}; font-size: 18px; font-weight: bold;">
    What's Next?
</h3>
<ul style="margin: 0 0 30px 0; padding-left: 20px; color: {{ branding.text_color }};">
    <li style="margin-bottom: 10px;">You can now proceed with the repair</li>
    <li style="margin-bottom: 10px;">Update the status to "In Progress" when you begin work</li>
    <li style="margin-bottom: 10px;">Upload after photos when complete</li>
</ul>

<!-- CTA Button -->
<table role="presentation" style="margin: 30px 0;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center;">
            <a href="{{ action_url }}" style="display: inline-block; background-color: {{ branding.primary_color }}; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: {{ branding.button_border_radius }}px; font-weight: bold; font-size: 16px;">
                View Repair Details
            </a>
        </td>
    </tr>
</table>

<!-- Support message -->
<p style="margin: 30px 0 0 0; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #718096; font-size: 14px;">
    Questions? Contact <a href="mailto:{{ branding.support_email }}" style="color: {{ branding.primary_color }}; text-decoration: none;">{{ branding.support_email }}</a>
</p>
{% endblock %}
```

### 2. Repair Denied Template

**File**: `templates/emails/notifications/repair_denied.html`

```django
{% extends "emails/base.html" %}

{% block preview_text %}
Repair #{{ repair.id }} for {{ repair.unit_number }} was not approved. Reason: {{ repair.denial_reason|truncatewords:10 }}
{% endblock %}

{% block content %}
<!-- Denial badge -->
<table role="presentation" style="width: 100%; margin-bottom: 20px;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center;">
            <div style="display: inline-block; background-color: {{ branding.danger_color }}; color: white; padding: 12px 24px; border-radius: 50px; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                ❌ Not Approved
            </div>
        </td>
    </tr>
</table>

<!-- Greeting -->
<h2 style="margin: 0 0 20px 0; color: {{ branding.text_color }}; font-family: {{ branding.heading_font_family }}; font-size: 24px; font-weight: bold;">
    Update on Repair #{{ repair.id }}
</h2>

<!-- Main message -->
<p style="margin: 0 0 20px 0;">
    Your repair request for <strong>{{ repair.unit_number }}</strong> was not approved by {{ repair.customer.company_name }}.
</p>

<!-- Denial reason (highlighted) -->
<table role="presentation" style="width: 100%; background-color: #fff5f5; border-left: 4px solid {{ branding.danger_color }}; border-radius: 4px; margin: 20px 0;" border="0" cellpadding="20" cellspacing="0">
    <tr>
        <td>
            <strong style="color: {{ branding.danger_color }}; display: block; margin-bottom: 10px;">Reason:</strong>
            <p style="margin: 0; color: {{ branding.text_color }};">
                {{ repair.denial_reason|default:"No reason provided." }}
            </p>
        </td>
    </tr>
</table>

<!-- Repair details (collapsed) -->
<details style="margin: 20px 0;">
    <summary style="cursor: pointer; color: {{ branding.primary_color }}; font-weight: bold; margin-bottom: 10px;">
        View Repair Details
    </summary>
    <table role="presentation" style="width: 100%; background-color: #f8f9fa; border-radius: 4px; margin-top: 10px;" border="0" cellpadding="15" cellspacing="0">
        <tr>
            <td>
                <p style="margin: 5px 0;"><strong>Repair ID:</strong> #{{ repair.id }}</p>
                <p style="margin: 5px 0;"><strong>Unit:</strong> {{ repair.unit_number }}</p>
                <p style="margin: 5px 0;"><strong>Requested Cost:</strong> ${{ repair.cost }}</p>
                <p style="margin: 5px 0;"><strong>Break Description:</strong> {{ repair.break_description|truncatewords:20 }}</p>
            </td>
        </tr>
    </table>
</details>

<!-- Next steps -->
<h3 style="margin: 30px 0 15px 0; color: {{ branding.text_color }}; font-size: 18px; font-weight: bold;">
    What You Can Do
</h3>
<ul style="margin: 0 0 30px 0; padding-left: 20px;">
    <li style="margin-bottom: 10px;">Contact the customer to discuss concerns</li>
    <li style="margin-bottom: 10px;">Review and update the repair details if needed</li>
    <li style="margin-bottom: 10px;">Resubmit with adjustments</li>
</ul>

<!-- CTA Buttons (multiple options) -->
<table role="presentation" style="margin: 30px 0;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center; padding-bottom: 15px;">
            <a href="{{ action_url }}" style="display: inline-block; background-color: {{ branding.primary_color }}; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: {{ branding.button_border_radius }}px; font-weight: bold; font-size: 16px;">
                View Repair
            </a>
        </td>
    </tr>
    <tr>
        <td style="text-align: center;">
            <a href="mailto:{{ repair.customer.email }}" style="display: inline-block; background-color: transparent; border: 2px solid {{ branding.primary_color }}; color: {{ branding.primary_color }}; padding: 12px 32px; text-decoration: none; border-radius: {{ branding.button_border_radius }}px; font-weight: bold; font-size: 16px;">
                Contact Customer
            </a>
        </td>
    </tr>
</table>
{% endblock %}
```

### 3. New Assignment Template

**File**: `templates/emails/notifications/repair_assigned.html`

```django
{% extends "emails/base.html" %}

{% block preview_text %}
You've been assigned repair #{{ repair.id }} for {{ repair.customer.company_name }} - Unit {{ repair.unit_number }}
{% endblock %}

{% block content %}
<!-- Assignment badge -->
<table role="presentation" style="width: 100%; margin-bottom: 20px;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center;">
            <div style="display: inline-block; background-color: {{ branding.secondary_color }}; color: white; padding: 12px 24px; border-radius: 50px; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                📋 New Assignment
            </div>
        </td>
    </tr>
</table>

<!-- Greeting -->
<h2 style="margin: 0 0 20px 0; color: {{ branding.text_color }}; font-family: {{ branding.heading_font_family }}; font-size: 24px; font-weight: bold;">
    New Repair Assigned
</h2>

<!-- Main message -->
<p style="margin: 0 0 20px 0;">
    Hi {{ technician.user.first_name }}, you've been assigned a new repair.
</p>

<!-- Repair details card (prominent) -->
<table role="presentation" style="width: 100%; background: linear-gradient(135deg, {{ branding.primary_color }} 0%, {{ branding.secondary_color }} 100%); border-radius: 8px; margin: 20px 0;" border="0" cellpadding="25" cellspacing="0">
    <tr>
        <td style="color: #ffffff;">
            <h3 style="margin: 0 0 15px 0; color: #ffffff; font-size: 20px;">
                Repair #{{ repair.id }}
            </h3>
            <p style="margin: 5px 0; font-size: 16px;"><strong>Customer:</strong> {{ repair.customer.company_name }}</p>
            <p style="margin: 5px 0; font-size: 16px;"><strong>Unit:</strong> {{ repair.unit_number }}</p>
            <p style="margin: 5px 0; font-size: 16px;"><strong>Status:</strong> {{ repair.get_queue_status_display }}</p>
            {% if repair.customer.location %}
            <p style="margin: 5px 0; font-size: 16px;"><strong>Location:</strong> {{ repair.customer.location }}</p>
            {% endif %}
        </td>
    </tr>
</table>

<!-- Break description -->
<h3 style="margin: 25px 0 10px 0; color: {{ branding.text_color }}; font-size: 18px; font-weight: bold;">
    Break Description
</h3>
<p style="margin: 0 0 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 4px; color: {{ branding.text_color }};">
    {{ repair.break_description }}
</p>

<!-- Photos if available -->
{% if repair.damage_photo_before %}
<p style="margin: 20px 0 10px 0; font-weight: bold;">Damage Photo:</p>
<img src="{{ repair.damage_photo_before.url }}" alt="Damage photo" style="max-width: 100%; height: auto; border-radius: 4px; border: 1px solid #e2e8f0;">
{% endif %}

<!-- CTA Button -->
<table role="presentation" style="margin: 30px 0;" border="0" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center;">
            <a href="{{ action_url }}" style="display: inline-block; background-color: {{ branding.primary_color }}; color: #ffffff; padding: 16px 40px; text-decoration: none; border-radius: {{ branding.button_border_radius }}px; font-weight: bold; font-size: 18px;">
                View Full Details
            </a>
        </td>
    </tr>
</table>
{% endblock %}
```

---

## Plain Text Templates

Always include plain text versions for accessibility and spam filter compliance.

**File**: `templates/emails/notifications/repair_approved.txt`

```django
{% autoescape off %}
REPAIR APPROVED ✅

Hi {{ technician.user.first_name }},

Great news! Your repair request has been approved by {{ repair.customer.company_name }}.

REPAIR DETAILS
--------------
Repair ID: #{{ repair.id }}
Unit: {{ repair.unit_number }}
Customer: {{ repair.customer.company_name }}
Approved Cost: ${{ repair.cost }}

{% if repair.customer_notes %}
Customer Notes:
{{ repair.customer_notes }}
{% endif %}

WHAT'S NEXT?
------------
* You can now proceed with the repair
* Update the status to "In Progress" when you begin work
* Upload after photos when complete

View repair details: {{ action_url }}

Questions? Contact {{ branding.support_email }}

---
{{ branding.company_name }}
{% if branding.company_address %}{{ branding.company_address }}{% endif %}
{{ branding.support_email }}{% if branding.support_phone %} | {{ branding.support_phone }}{% endif %}

Manage notification preferences: {{ preferences_url }}
{% endautoescape %}
```

---

## Admin Interface for Branding

### Branding Admin

**File**: `apps/core/admin.py` (Add to existing file)

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import EmailBrandingConfig

@admin.register(EmailBrandingConfig)
class EmailBrandingConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for email branding customization.

    Provides live preview of color scheme and logo.
    """

    fieldsets = (
        ('Logo Configuration', {
            'fields': ('logo', 'logo_preview', 'logo_width', 'logo_alt_text'),
            'description': 'Upload and configure your company logo for email headers.'
        }),
        ('Color Scheme', {
            'fields': (
                ('primary_color', 'secondary_color'),
                ('success_color', 'danger_color'),
                ('text_color', 'background_color'),
            ),
            'description': 'Customize colors using hex codes (e.g., #2C5282). Changes apply to all email templates.'
        }),
        ('Company Information', {
            'fields': (
                'company_name',
                'company_address',
                ('support_email', 'support_phone'),
                'website_url',
            ),
        }),
        ('Social Media Links', {
            'fields': (
                'show_social_links',
                'facebook_url',
                'twitter_url',
                'linkedin_url',
            ),
            'classes': ('collapse',),
        }),
        ('Footer Customization', {
            'fields': (
                'footer_text',
                'show_unsubscribe_link',
            ),
        }),
        ('Typography & Styling', {
            'fields': (
                'font_family',
                'heading_font_family',
                'button_border_radius',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('logo_preview', 'updated_at', 'updated_by')

    def logo_preview(self, obj):
        """Display logo preview in admin"""
        if obj.logo:
            return format_html(
                '<img src="{}" width="{}" style="background: #f0f0f0; padding: 20px; border-radius: 8px;"><br><small>Current logo</small>',
                obj.logo.url,
                obj.logo_width
            )
        return format_html('<em>No logo uploaded</em>')
    logo_preview.short_description = "Logo Preview"

    def save_model(self, request, obj, form, change):
        """Track who updated the branding"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Only allow one branding config (singleton)"""
        return not EmailBrandingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of branding config"""
        return False

    class Media:
        css = {
            'all': ('admin/css/email_branding.css',)
        }
        js = ('admin/js/color_picker.js',)
```

### Color Picker Enhancement

**File**: `static/admin/js/color_picker.js`

```javascript
// Add color picker widgets to hex color fields
document.addEventListener('DOMContentLoaded', function() {
    const colorFields = document.querySelectorAll('input[type="text"][name*="color"]');

    colorFields.forEach(field => {
        // Create color input
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = field.value || '#000000';
        colorPicker.style.marginLeft = '10px';
        colorPicker.style.verticalAlign = 'middle';
        colorPicker.style.cursor = 'pointer';

        // Sync color picker with text field
        colorPicker.addEventListener('change', function() {
            field.value = this.value;
        });

        field.addEventListener('input', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                colorPicker.value = this.value;
            }
        });

        // Insert color picker after text field
        field.parentNode.insertBefore(colorPicker, field.nextSibling);

        // Add live preview swatch
        const swatch = document.createElement('span');
        swatch.style.display = 'inline-block';
        swatch.style.width = '30px';
        swatch.style.height = '30px';
        swatch.style.marginLeft = '10px';
        swatch.style.borderRadius = '4px';
        swatch.style.border = '2px solid #ccc';
        swatch.style.backgroundColor = field.value;
        swatch.style.verticalAlign = 'middle';

        field.addEventListener('input', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                swatch.style.backgroundColor = this.value;
            }
        });

        field.parentNode.insertBefore(swatch, colorPicker.nextSibling);
    });
});
```

---

## Email Preview System

### Preview View

**File**: `apps/core/views/email_preview.py`

```python
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from apps.core.models import EmailBrandingConfig, NotificationTemplate
from apps.technician_portal.models import Repair, Technician

@staff_member_required
def preview_email_template(request, template_name):
    """
    Preview email template with sample data.

    Accessible only to staff users for testing template changes.
    """
    branding = EmailBrandingConfig.get_config()

    # Sample data for preview
    sample_repair = Repair.objects.first() or create_sample_repair()
    sample_technician = Technician.objects.first() or create_sample_technician()

    context = {
        **branding.to_template_context(request),
        'repair': sample_repair,
        'technician': sample_technician,
        'action_url': request.build_absolute_uri(f'/tech/repairs/{sample_repair.id}/'),
        'preferences_url': request.build_absolute_uri('/tech/settings/notifications/'),
    }

    template_path = f'emails/notifications/{template_name}.html'

    return render(request, template_path, context)

def create_sample_repair():
    """Create sample repair data for preview"""
    from apps.core.models import Customer
    from apps.technician_portal.models import Repair

    customer = Customer.objects.first()
    return Repair(
        id=12345,
        unit_number='SAMPLE-001',
        break_description='Sample break description for email preview',
        cost=250.00,
        queue_status='PENDING',
        customer=customer,
        customer_notes='This is a sample customer note.',
    )

def create_sample_technician():
    """Create sample technician data for preview"""
    from django.contrib.auth.models import User
    from apps.technician_portal.models import Technician

    user = User.objects.filter(is_staff=True).first()
    return Technician(
        user=user,
        phone_number='+12025551234',
    )
```

### Preview URLs

**File**: `rs_systems/urls.py` (Add to existing URLs)

```python
from apps.core.views.email_preview import preview_email_template

urlpatterns = [
    # ... existing patterns ...

    # Email template previews (staff only)
    path('admin/email-preview/<str:template_name>/', preview_email_template, name='email_preview'),
]
```

---

## Implementation Checklist

### Models
- [ ] Create `EmailBrandingConfig` model
- [ ] Run migrations
- [ ] Create initial branding config via admin
- [ ] Upload company logo

### Templates
- [ ] Create `templates/emails/base.html`
- [ ] Create repair approved template (HTML + TXT)
- [ ] Create repair denied template (HTML + TXT)
- [ ] Create repair assigned template (HTML + TXT)
- [ ] Create repair completed template
- [ ] Create batch approval template
- [ ] Test templates in multiple email clients

### Admin Interface
- [ ] Register `EmailBrandingConfig` in admin
- [ ] Add color picker JavaScript
- [ ] Add logo preview functionality
- [ ] Create admin CSS for branding page
- [ ] Test branding updates

### Preview System
- [ ] Create email preview view
- [ ] Add preview URLs
- [ ] Create sample data generators
- [ ] Test previews for all templates

### Testing
- [ ] Test in Gmail (web, mobile)
- [ ] Test in Outlook (desktop, web)
- [ ] Test in Apple Mail
- [ ] Test plain text fallback
- [ ] Test responsive design on mobile
- [ ] Validate HTML (W3C validator)

---

## Success Criteria

✅ Professional branded email templates created
✅ Logo uploads and displays correctly
✅ Color customization working in admin
✅ All notification types have HTML + plain text versions
✅ Emails render correctly in major email clients
✅ Responsive design works on mobile devices
✅ Preview system functional for testing
✅ Admin interface intuitive for non-technical users

---

## Next Phase

Once Phase 3 is complete, proceed to:
**Phase 4: Service Layer & Event Triggers** - Build notification services and connect to repair events.
