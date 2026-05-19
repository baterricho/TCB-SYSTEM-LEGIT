import mimetypes
from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError


DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
MESSAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".docx"}
DOCUMENT_ERROR = "Unsupported file type. Allowed types are PDF, DOC, DOCX, JPG, JPEG, and PNG."
MESSAGE_SIZE_ERROR = "File upload failed. The selected file exceeds the 25 MB maximum size limit."


def validate_document_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in DOCUMENT_EXTENSIONS:
        raise ValidationError(DOCUMENT_ERROR)
    return mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"


def validate_message_attachment(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in MESSAGE_EXTENSIONS:
        raise ValidationError(DOCUMENT_ERROR)
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(MESSAGE_SIZE_ERROR)
    return mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
