"""
Core notification services for the RS Systems platform.

This package contains the service layer for the notification system:
- NotificationService: Creates and manages notifications
- EmailService: Handles email delivery via AWS SES
- SMSService: Handles SMS delivery via AWS SNS
"""

from .notification_service import NotificationService
from .email_service import EmailService
from .sms_service import SMSService

__all__ = ['NotificationService', 'EmailService', 'SMSService']
