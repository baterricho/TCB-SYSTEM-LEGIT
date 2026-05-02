"""
File validation utilities.
Ensures uploaded files meet security requirements.
"""

import os
import uuid
from django.core.exceptions import ValidationError

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_extension(file):
    """Validate that the uploaded file has an allowed extension."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not allowed. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(file):
    """Validate that the uploaded file does not exceed the maximum size."""
    if file.size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f"File size ({file.size / (1024 * 1024):.1f}MB) exceeds "
            f"maximum allowed size ({max_mb:.0f}MB)."
        )


def generate_upload_path(instance, filename):
    """
    Generate a secure, hashed upload path for documents.
    Pattern: media/applications/<uuid>/<filename>
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # Determine folder based on model type
    if hasattr(instance, "application"):
        app_id = str(instance.application.id)
        return f"applications/{app_id}/{unique_name}"
    elif hasattr(instance, "user"):
        user_id = str(instance.user.id)
        return f"profiles/{user_id}/{unique_name}"
    else:
        return f"uploads/{unique_name}"
