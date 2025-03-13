# Add this code to the bottom of your settings.py file to import Railway-specific settings
# when the app is deployed on Railway

import os

# Check if we're running on Railway
if 'RAILWAY_ENVIRONMENT' in os.environ:
    try:
        from .settings_railway import *
    except ImportError:
        pass 