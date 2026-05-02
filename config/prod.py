"""
Production settings for The Creator's Bulwark.
"""

import os
from .base import *  # noqa: F401, F403
from .database import build_database_config, disable_server_side_cursors

DEBUG = False

# Database configuration via URL (Supabase/PostgreSQL)
DATABASES = build_database_config(BASE_DIR, require_database_url=True)
DISABLE_SERVER_SIDE_CURSORS = disable_server_side_cursors()

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = True

# Email - SMTP for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
