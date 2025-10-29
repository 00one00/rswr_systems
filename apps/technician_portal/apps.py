from django.apps import AppConfig


class TechnicianPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.technician_portal'

    def ready(self):
        """
        Register pillow-heif plugin to enable HEIC/HEIF image support.
        This allows Django's ImageField to handle iPhone photos in HEIC format.
        """
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            # pillow-heif not installed, HEIC support will not be available
            pass 