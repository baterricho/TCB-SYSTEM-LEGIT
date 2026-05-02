"""Database configuration helpers."""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_database_config(base_dir, require_database_url=False):
    """
    Build Django's DATABASES setting.

    Supabase should be configured through DATABASE_URL, preferably using the
    Supabase connection pooler URL on port 6543 with sslmode=require.
    Development falls back to local SQLite when DATABASE_URL is not set.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        if require_database_url:
            raise ImproperlyConfigured("DATABASE_URL is required in production.")
        database_url = f"sqlite:///{base_dir / 'db.sqlite3'}"

    conn_max_age = int(os.getenv("DATABASE_CONN_MAX_AGE", "600"))
    config = dj_database_url.parse(
        database_url,
        conn_max_age=conn_max_age,
        conn_health_checks=True,
    )

    if config.get("ENGINE") == "django.db.backends.postgresql":
        options = config.setdefault("OPTIONS", {})
        options.setdefault("sslmode", os.getenv("DATABASE_SSLMODE", "require"))

    return {"default": config}


def disable_server_side_cursors():
    """
    Supabase's transaction pooler does not work with server-side cursors.
    Keep this enabled by default for pooler-safe Django queries.
    """
    return _env_bool("DATABASE_DISABLE_SERVER_SIDE_CURSORS", True)
