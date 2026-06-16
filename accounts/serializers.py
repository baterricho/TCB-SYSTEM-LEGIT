from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import ApplicantProfile, User, EvaluatorProfile, OTPCode


class ApplicantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicantProfile
        fields = ("applicant_type", "institution", "student_or_employee_id", "profile_photo")


class EvaluatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluatorProfile
        fields = ("specialization", "workload_count", "is_available")
        read_only_fields = ("workload_count",)


class UserSerializer(serializers.ModelSerializer):
    applicant_profile = ApplicantProfileSerializer(read_only=True)
    evaluator_profile = EvaluatorProfileSerializer(read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "username", "first_name", "middle_name", "last_name", "full_name", "role",
            "status", "contact_number", "address", "is_active", "is_staff", "last_login_at",
            "created_at", "updated_at", "applicant_profile", "evaluator_profile",
        )
        read_only_fields = ("id", "role", "status", "is_active", "is_staff", "last_login_at", "created_at", "updated_at")


class AdminUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = (
            "id", "email", "username", "first_name", "middle_name", "last_name", "full_name", "role",
            "status", "contact_number", "address", "is_active", "is_staff", "last_login_ip", "last_login_at",
            "created_at", "updated_at", "applicant_profile", "evaluator_profile",
        )
        read_only_fields = ("id", "role", "status", "is_active", "is_staff", "last_login_ip", "last_login_at", "created_at", "updated_at")


class ApplicantRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profile = ApplicantProfileSerializer(required=True, write_only=True)

    class Meta:
        model = User
        fields = ("email", "username", "password", "first_name", "middle_name", "last_name", "contact_number", "address", "profile")

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class AdminCreateApplicantSerializer(ApplicantRegistrationSerializer):
    pass


class AdminCreateEvaluatorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profile = EvaluatorProfileSerializer(required=True, write_only=True)

    class Meta:
        model = User
        fields = ("email", "username", "password", "first_name", "middle_name", "last_name", "contact_number", "address", "profile")

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    portal = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, allow_blank=True)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.CharField()
    purpose = serializers.ChoiceField(choices=OTPCode.Purpose.choices)
    otp_code = serializers.CharField(min_length=6, max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.CharField()
    purpose = serializers.ChoiceField(choices=OTPCode.Purpose.choices)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value
