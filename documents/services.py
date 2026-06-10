import hashlib

from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from rest_framework.exceptions import PermissionDenied, ValidationError

from cases.models import Case
from core.audit import create_audit_log
from core.file_validators import validate_document_file
from security_keys.services import AESGCMDocumentCipher

from .models import Document


class DocumentService:
    @staticmethod
    def upload(*, uploaded_file, uploaded_by, document_type, case=None, application=None, request=None):
        if case and not isinstance(case, Case):
            case = Case.objects.get(pk=case)
        if not case:
            raise ValidationError("A case reference is required.")
        if uploaded_by.role == "applicant":
            if case.applicant_id != uploaded_by.id:
                raise PermissionDenied("You can upload documents only for your own record.")
        elif uploaded_by.role == "evaluator":
            if case.taken_by_id != uploaded_by.id:
                raise PermissionDenied("You can upload documents only for cases assigned to you.")
        elif uploaded_by.role != "admin":
            raise PermissionDenied("You do not have permission to upload documents.")
        mime_type = validate_document_file(uploaded_file)
        plaintext = uploaded_file.read()
        key, nonce, ciphertext = AESGCMDocumentCipher.encrypt(plaintext)
        original_filename = get_valid_filename(uploaded_file.name)
        encrypted_name = f"{hashlib.sha256(ciphertext).hexdigest()}-{original_filename}"
        document = Document.objects.create(
            case=case,
            uploaded_by=uploaded_by,
            document_type=document_type,
            original_filename=original_filename,
            file_size=uploaded_file.size,
            mime_type=mime_type,
            encryption_key=key,
            nonce=nonce,
            checksum=hashlib.sha256(ciphertext).hexdigest(),
        )
        document.encrypted_file_path.save(encrypted_name, ContentFile(ciphertext), save=True)
        create_audit_log(request, uploaded_by, "document.uploaded", document.original_filename, "Encrypted document uploaded.", related_case=case)
        return document

    @staticmethod
    def decrypt(document, user, request=None):
        if user.role == "admin":
            allowed = True
        else:
            allowed = document.uploaded_by_id == user.id
            if document.case_id:
                allowed = allowed or document.case.applicant_id == user.id or document.case.taken_by_id == user.id
        if not allowed:
            raise PermissionDenied("You do not have permission to access this document.")
        with document.encrypted_file_path.open("rb") as encrypted_file:
            ciphertext = encrypted_file.read()
        plaintext = AESGCMDocumentCipher.decrypt(ciphertext, document.encryption_key, document.nonce)
        create_audit_log(request, user, "document.downloaded", document.original_filename, "Encrypted document decrypted for authorized access.", related_case=document.case)
        return plaintext
