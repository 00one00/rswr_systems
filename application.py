#!/usr/bin/env python
"""
WSGI config for RS Systems project for AWS Elastic Beanstalk.
"""
import os
from django.core.wsgi import get_wsgi_application

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rs_systems.settings')

# Get Django application
application = get_wsgi_application() 