from .base import *  # noqa: F401,F403
from decouple import config


DEBUG = str(config("DEBUG", default="True")).lower() in {"1", "true", "yes", "on"}

# Default to console backend for development, but allow override from .env
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
