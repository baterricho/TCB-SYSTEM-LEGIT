"""
Encryption utilities using Fernet symmetric encryption.
Used for securing sensitive data before database storage.
"""

import os
from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet_key():
    """Get or generate the Fernet encryption key from environment."""
    key = os.getenv("FERNET_KEY", "")
    if not key:
        # Auto-generate key for development if not set
        key = Fernet.generate_key().decode()
        print(f"[WARNING] No FERNET_KEY set. Generated: {key}")
        print("Add this to your .env file for persistence.")
    return key.encode() if isinstance(key, str) else key


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string value."""
    f = Fernet(_get_fernet_key())
    return f.decrypt(ciphertext.encode()).decode()
