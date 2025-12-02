# Backward compatibility - import all models from the models package
from core.models.customer import Customer
from core.models.notification import Notification
from core.models.notification_preferences import (
    BaseNotificationPreference,
    TechnicianNotificationPreference,
    CustomerNotificationPreference
)
from core.models.notification_template import NotificationTemplate
from core.models.notification_delivery_log import NotificationDeliveryLog

__all__ = [
    'Customer',
    'Notification',
    'BaseNotificationPreference',
    'TechnicianNotificationPreference',
    'CustomerNotificationPreference',
    'NotificationTemplate',
    'NotificationDeliveryLog',
]
