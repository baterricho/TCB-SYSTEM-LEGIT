import magic
from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError


DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
MESSAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".docx"}
PAYMENT_RECEIPT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".docx"}

# Map extensions to allowed MIME types for content sniffing validation
ALLOWED_MIMES = {
    ".pdf": ["application/pdf"],
    ".doc": ["application/msword", "application/x-cfof"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".jpg": ["image/jpeg", "image/pjpeg"],
    ".jpeg": ["image/jpeg", "image/pjpeg"],
    ".png": ["image/png"],
}

DOCUMENT_ERROR = "Unsupported file type. Allowed types are PDF, DOC, DOCX, JPG, JPEG, and PNG."
ATTACHMENT_ERROR = "Unsupported file type. Allowed attachment types are JPG, JPEG, PNG, PDF, and DOCX."
PAYMENT_RECEIPT_ERROR = "Unsupported file type. Allowed payment receipt types are JPG, PNG, PDF, and DOCX."
MESSAGE_SIZE_ERROR = "File upload failed. The selected file exceeds the 25 MB maximum size limit."


def _validate_file_content(uploaded_file, allowed_extensions, error_message):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in allowed_extensions:
        raise ValidationError(error_message)
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(MESSAGE_SIZE_ERROR)

    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(2048)
        uploaded_file.seek(0)
        mime_type = magic.from_buffer(header, mime=True)
    except Exception as e:
        raise ValidationError(f"Could not validate file content: {str(e)}")

    expected_mimes = ALLOWED_MIMES.get(extension, [])
    if not any(mime_type.lower() == expected.lower() for expected in expected_mimes):
        if extension in {".doc", ".docx"} and mime_type in {"application/zip", "application/octet-stream", "application/x-zip-compressed"}:
            pass
        else:
            raise ValidationError(error_message)

    return mime_type


def validate_document_file(uploaded_file):
    return _validate_file_content(uploaded_file, DOCUMENT_EXTENSIONS, DOCUMENT_ERROR)


def validate_message_attachment(uploaded_file):
    return _validate_file_content(uploaded_file, MESSAGE_EXTENSIONS, ATTACHMENT_ERROR)


def validate_payment_receipt_file(uploaded_file):
    return _validate_file_content(uploaded_file, PAYMENT_RECEIPT_EXTENSIONS, PAYMENT_RECEIPT_ERROR)
