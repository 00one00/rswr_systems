from django.apps import AppConfig


class TechnicianPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.technician_portal'

    def ready(self):
        """
        Register pillow-heif plugin to enable HEIC/HEIF image support.
        This allows Django's ImageField to handle iPhone photos in HEIC format.

        Also import signal handlers to register notification triggers.
        """
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            # pillow-heif not installed, HEIC support will not be available
            pass

        # Import signal handlers to register them with Django
        # Wrap in try/except for graceful degradation if dependencies unavailable
        try:
            import apps.technician_portal.signals  # noqa: F401
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load signal handlers: {e}")
            logger.warning("Notifications may not trigger automatically") 