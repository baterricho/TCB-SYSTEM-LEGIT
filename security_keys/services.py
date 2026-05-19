import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.audit import create_audit_log, get_client_ip

from .models import EncryptionKey, KeyActivityLog


def _decode_master_key():
    configured = settings.MASTER_KEY
    if not configured or configured.startswith("replace-with"):
        raise ImproperlyConfigured("MASTER_KEY must be set to a base64 encoded 32-byte key.")
    try:
        key = base64.urlsafe_b64decode(configured.encode())
    except Exception as exc:
        raise ImproperlyConfigured("MASTER_KEY must be base64 encoded.") from exc
    if len(key) != 32:
        raise ImproperlyConfigured("MASTER_KEY must decode to exactly 32 bytes.")
    return key


def _b64(data):
    return base64.urlsafe_b64encode(data).decode()


def _unb64(data):
    return base64.urlsafe_b64decode(data.encode())


class EncryptionKeyService:
    @staticmethod
    def _wrap_key(raw_key):
        master_key = _decode_master_key()
        nonce = os.urandom(12)
        encrypted = AESGCM(master_key).encrypt(nonce, raw_key, None)
        return json.dumps({"nonce": _b64(nonce), "ciphertext": _b64(encrypted)})

    @staticmethod
    def unwrap_key(encryption_key):
        master_key = _decode_master_key()
        payload = json.loads(encryption_key.encrypted_key_material)
        try:
            return AESGCM(master_key).decrypt(_unb64(payload["nonce"]), _unb64(payload["ciphertext"]), None)
        except InvalidTag as exc:
            raise ValidationError("Encryption key material could not be decrypted.") from exc

    @staticmethod
    def get_primary_key():
        key = EncryptionKey.objects.filter(status=EncryptionKey.Status.ACTIVE, is_primary=True).first()
        if not key:
            raise ValidationError("No active encryption key is configured.")
        return key

    @staticmethod
    @transaction.atomic
    def generate_key(*, user, request=None, key_name, rotation_policy="", is_primary=True, is_backup=False):
        raw_key = AESGCM.generate_key(bit_length=256)
        if is_primary:
            EncryptionKey.objects.filter(status=EncryptionKey.Status.ACTIVE, is_primary=True).update(
                status=EncryptionKey.Status.ROTATED,
                is_primary=False,
                rotated_at=timezone.now(),
            )
        key = EncryptionKey.objects.create(
            key_name=key_name,
            encrypted_key_material=EncryptionKeyService._wrap_key(raw_key),
            created_by=user,
            rotation_policy=rotation_policy,
            is_primary=is_primary,
            is_backup=is_backup,
        )
        EncryptionKeyService.log_key_event(key, "generated", user, request, "Encryption key generated.")
        create_audit_log(request, user, "encryption_key.generated", key.key_code, "Encryption key generated.")
        return key

    @staticmethod
    @transaction.atomic
    def rotate_primary_key(*, user, request=None, key_name=None, rotation_policy=""):
        old_key = EncryptionKey.objects.select_for_update().filter(status=EncryptionKey.Status.ACTIVE, is_primary=True).first()
        if old_key:
            old_key.status = EncryptionKey.Status.ROTATED
            old_key.is_primary = False
            old_key.rotated_at = timezone.now()
            old_key.save(update_fields=["status", "is_primary", "rotated_at"])
            EncryptionKeyService.log_key_event(old_key, "rotated", user, request, "Primary key rotated out.")
            create_audit_log(request, user, "encryption_key.rotated", old_key.key_code, "Primary key rotated out.")
        return EncryptionKeyService.generate_key(
            user=user,
            request=request,
            key_name=key_name or f"Primary Key {timezone.now():%Y-%m-%d %H:%M:%S}",
            rotation_policy=rotation_policy,
            is_primary=True,
        )

    @staticmethod
    @transaction.atomic
    def disable_key(*, key, user, request=None):
        if key.is_primary and key.status == EncryptionKey.Status.ACTIVE:
            raise ValidationError("Cannot disable the active primary encryption key. Rotate it first.")
        key.status = EncryptionKey.Status.DISABLED
        key.disabled_at = timezone.now()
        key.is_primary = False
        key.save(update_fields=["status", "disabled_at", "is_primary"])
        EncryptionKeyService.log_key_event(key, "disabled", user, request, "Encryption key disabled.")
        create_audit_log(request, user, "encryption_key.disabled", key.key_code, "Encryption key disabled.")
        return key

    @staticmethod
    def log_key_event(key, action, user, request=None, details=""):
        return KeyActivityLog.objects.create(
            key=key,
            action=action,
            performed_by=user,
            details=details,
            ip_address=get_client_ip(request) or None,
        )


class AESGCMDocumentCipher:
    @staticmethod
    def encrypt(plaintext, encryption_key=None):
        # Standard AES-256-GCM encryption with Custom Encryption Key Management.
        key_record = encryption_key or EncryptionKeyService.get_primary_key()
        raw_key = EncryptionKeyService.unwrap_key(key_record)
        nonce = os.urandom(12)
        ciphertext = AESGCM(raw_key).encrypt(nonce, plaintext, None)
        return key_record, _b64(nonce), ciphertext

    @staticmethod
    def decrypt(ciphertext, encryption_key, nonce):
        # Standard AES-256-GCM encryption with Custom Encryption Key Management.
        raw_key = EncryptionKeyService.unwrap_key(encryption_key)
        return AESGCM(raw_key).decrypt(_unb64(nonce), ciphertext, None)
