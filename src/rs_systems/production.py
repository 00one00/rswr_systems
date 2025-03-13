"""
Production settings for Railway deployment
"""

from rs_systems.settings import *

# Set production environment
ENVIRONMENT = 'production'
IS_PRODUCTION = True
DEBUG = False

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configure allowed hosts for Railway
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.railway.app').split(',')

# CSRF trusted origins for Railway
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.railway.app').split(',')

# Ensure SECRET_KEY is set in environment variables for production
if 'SECRET_KEY' not in os.environ:
    raise Exception("SECRET_KEY environment variable must be set in production!")

# Ensure database URL is set
if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE_URL environment variable must be set in production!") 