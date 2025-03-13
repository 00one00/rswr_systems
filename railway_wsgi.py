"""
WSGI config for rs_systems project when deployed on Railway.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railway_settings')

application = get_wsgi_application() 