"""
Serializers for user registration, authentication, profile management,
OTP verification, and password reset.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, UserProfile, OTPVerification


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles user registration with password hashing. Email OTP sent post-registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    contact_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    institution = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "password",
            "password_confirm", "role", "contact_number",
            "address", "institution", "created_at",
        ]
        read_only_fields = ["id", "role", "created_at"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        profile_data = {
            "contact_number": validated_data.pop("contact_number", ""),
            "address": validated_data.pop("address", ""),
            "institution": validated_data.pop("institution", ""),
        }
        validated_data["role"] = "applicant"

        # New users are NOT verified until they complete OTP
        user = User.objects.create_user(**validated_data)
        user.is_verified = False
        user.save()
        UserProfile.objects.update_or_create(user=user, defaults=profile_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Validates login credentials (used alongside JWT)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            email=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated.")
        if not user.is_verified:
            raise serializers.ValidationError(
                "Email not verified. Please check your email for the OTP."
            )
        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile CRUD — includes institution field."""

    class Meta:
        model = UserProfile
        fields = ["id", "contact_number", "address", "institution", "valid_id_file"]
        read_only_fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with nested profile."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "role",
            "is_verified", "is_active", "created_at", "profile",
        ]
        read_only_fields = ["id", "created_at"]


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for list views."""

    institution = serializers.CharField(source="profile.institution", read_only=True, default="")
    contact_number = serializers.CharField(source="profile.contact_number", read_only=True, default="")

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "role",
            "institution", "contact_number",
            "is_verified", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ─── OTP / Password Reset Serializers ────────────────────────────────────────

class VerifyEmailSerializer(serializers.Serializer):
    """Submit the 6-digit OTP received by email to verify account."""

    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email."})

        otp = (
            OTPVerification.objects
            .filter(user=user, purpose="registration", is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or not otp.is_valid():
            raise serializers.ValidationError(
                {"otp_code": "OTP is invalid or has expired. Please request a new one."}
            )

        if otp.otp_code != attrs["otp_code"]:
            raise serializers.ValidationError({"otp_code": "Incorrect OTP code."})

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    """Request a new OTP for registration verification."""

    email = serializers.EmailField()
    purpose = serializers.ChoiceField(
        choices=["registration", "password_reset"],
        default="registration",
    )

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email."})

        if attrs["purpose"] == "registration" and user.is_verified:
            raise serializers.ValidationError({"email": "This account is already verified."})

        attrs["user"] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Initiate password reset — sends OTP to the registered email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Complete password reset using OTP + new password."""

    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email."})

        otp = (
            OTPVerification.objects
            .filter(user=user, purpose="password_reset", is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or not otp.is_valid():
            raise serializers.ValidationError(
                {"otp_code": "OTP is invalid or has expired. Please request a new one."}
            )

        if otp.otp_code != attrs["otp_code"]:
            raise serializers.ValidationError({"otp_code": "Incorrect OTP code."})

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Authenticated user changes their own password."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs
