"""
Production settings for Railway deployment
"""

import os
from dotenv import load_dotenv
from rs_systems.settings import *

# Load environment variables from .env file
load_dotenv()

# =========================================
# PRODUCTION ENVIRONMENT OVERRIDES
# =========================================

# Set production environment
ENVIRONMENT = 'production'
IS_PRODUCTION = True
DEBUG = False

# Force Railway DB in production
USE_RAILWAY_DB = True

# Security settings - already defined in base settings.py but enforced here
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

# Ensure essential environment variables are set in production
required_env_vars = ['SECRET_KEY', 'RAILWAY_DATABASE_URL']
missing_vars = [var for var in required_env_vars if var not in os.environ]

if missing_vars:
    raise Exception(f"The following required environment variables are missing: {', '.join(missing_vars)}")

# Override database with railway URL directly as fallback
if not os.environ.get('RAILWAY_DATABASE_URL') and os.environ.get('DATABASE_URL'):
    # For backward compatibility, use DATABASE_URL if RAILWAY_DATABASE_URL is not set
    print("Using DATABASE_URL as RAILWAY_DATABASE_URL")
    os.environ['RAILWAY_DATABASE_URL'] = os.environ.get('DATABASE_URL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
} 