#!/usr/bin/env python
"""
WSGI config for RS Systems project for AWS Elastic Beanstalk.
"""
import os
import logging
from django.core.wsgi import get_wsgi_application

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rs_systems.settings_aws')

# Get Django application
django_application = get_wsgi_application()

# Set up logging
logger = logging.getLogger(__name__)

def application(environ, start_response):
    """
    WSGI application wrapper that handles missing CONTENT_LENGTH header
    """
    # Handle missing CONTENT_LENGTH header
    if 'CONTENT_LENGTH' not in environ:
        environ['CONTENT_LENGTH'] = '0'
    
    # Log the request for debugging
    logger.info(f"Received request: {environ.get('REQUEST_METHOD', 'UNKNOWN')} {environ.get('PATH_INFO', '/')}")
    
    return django_application(environ, start_response) 