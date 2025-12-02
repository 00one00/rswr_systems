"""
RS Systems Django application initialization.

This module ensures the Celery app is loaded when Django starts,
allowing Celery to discover tasks and process async notifications.
"""

# Import Celery app with graceful fallback
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import Celery app: {e}")
    logger.warning("App will start without Celery support")
    celery_app = None
    __all__ = ()
