"""
User, UserProfile, and OTPVerification models.
Custom User model with email-based authentication and RBAC roles.

Updated per capstone document:
- UserProfile gains 'institution' field for external applicants.
- New OTPVerification model for email OTP verification and password reset.
"""

import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Custom manager for email-based User model."""

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for The Creator's Bulwark.
    Uses email for authentication and supports RBAC roles:
    - Applicant: submits and tracks IP applications
    - Evaluator: reviews assigned cases and provides deficiency remarks
    - Admin: manages all data, assigns evaluators, manages marketplace & encryption keys
    """

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("evaluator", "Evaluator"),
        ("applicant", "Applicant"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="applicant")
    is_verified = models.BooleanField(
        default=False,
        help_text="True after the user completes OTP email verification.",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class UserProfile(models.Model):
    """
    Extended profile for users.
    Auto-created via signal when a User is created.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    contact_number = models.CharField(max_length=20, blank=True, default="")
    address = models.TextField(blank=True, default="")
    institution = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="University or organization affiliation (e.g. Palawan State University).",
    )
    valid_id_file = models.FileField(
        upload_to="profiles/valid_ids/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Profile: {self.user.full_name}"


class OTPVerification(models.Model):
    """
    One-Time Password for email verification and password reset.
    Used during registration (purpose='registration') to verify email
    and during forgot password flow (purpose='password_reset').
    OTPs expire after 10 minutes and are single-use.
    """

    PURPOSE_CHOICES = (
        ("registration", "Email Verification"),
        ("password_reset", "Password Reset"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otp_verifications",
    )
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "purpose", "is_used"]),
        ]

    def __str__(self):
        return f"OTP({self.purpose}) for {self.user.email} — {'Used' if self.is_used else 'Active'}"

    @classmethod
    def create_otp(cls, user, purpose):
        """
        Generate a new 6-digit OTP for the given user and purpose.
        Invalidates any existing active OTPs for the same purpose.
        """
        import random
        # Invalidate previous active OTPs for this purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

        otp = cls.objects.create(
            user=user,
            otp_code=str(random.randint(100000, 999999)),
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        return otp

    def is_valid(self):
        """Returns True if OTP is not used and not expired."""
        return not self.is_used and timezone.now() < self.expires_at
