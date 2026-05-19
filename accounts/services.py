import secrets
from datetime import timedelta

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from core.audit import create_audit_log, get_client_ip

from .models import User, OTPCode


OTP_TTL_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
MAX_OTP_RESENDS = 3
RESEND_WINDOW_MINUTES = 15
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 5


class OTPService:
    @staticmethod
    def generate_otp_code():
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def enforce_resend_limit(user, purpose):
        window_start = timezone.now() - timedelta(minutes=RESEND_WINDOW_MINUTES)
        recent_count = OTPCode.objects.filter(user=user, purpose=purpose, created_at__gte=window_start).count()
        if recent_count >= MAX_OTP_RESENDS:
            raise ValidationError("Too many OTP resend attempts. Please try again later.")

    @staticmethod
    def create_and_send(user, purpose, request=None):
        OTPService.enforce_resend_limit(user, purpose)
        code = OTPService.generate_otp_code()
        otp = OTPCode.objects.create(
            user=user,
            purpose=purpose,
            otp_hash=make_password(code),
            expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
        )
        send_mail(
            subject="Your Creator's Bulwark OTP Code",
            message=f"Your OTP code is {code}. It expires in {OTP_TTL_MINUTES} minutes.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        create_audit_log(request, user, "otp.generated", purpose, "OTP generated and sent by email.")
        return otp

    @staticmethod
    @transaction.atomic
    def verify(user, purpose, code, request=None):
        otp = (
            OTPCode.objects.select_for_update()
            .filter(user=user, purpose=purpose)
            .order_by("-created_at")
            .first()
        )
        if not otp:
            raise ValidationError("Invalid OTP code. Please try again.")
        if otp.used_at:
            raise ValidationError("This OTP code has already been used.")
        if otp.attempts >= MAX_OTP_ATTEMPTS:
            raise ValidationError("Too many OTP attempts. Please request a new OTP.")
        if otp.expires_at <= timezone.now():
            raise ValidationError("OTP code has expired. Please request a new one.")
        if not check_password(code, otp.otp_hash):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            if otp.attempts >= MAX_OTP_ATTEMPTS:
                raise ValidationError("Too many OTP attempts. Please request a new OTP.")
            raise ValidationError("Invalid OTP code. Please try again.")
        otp.used_at = timezone.now()
        otp.save(update_fields=["used_at"])
        create_audit_log(request, user, "otp.verified", purpose, "OTP verified.")
        return otp


class AuthService:
    @staticmethod
    def tokens_for_user(user):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @staticmethod
    def register_applicant(validated_data, request=None):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password")
        password_validation.validate_password(password)
        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                role=User.Role.APPLICANT,
                is_active=False,
                **validated_data,
            )
            if profile_data:
                from .models import ApplicantProfile

                ApplicantProfile.objects.create(user=user, **profile_data)
            OTPService.create_and_send(user, OTPCode.Purpose.REGISTRATION, request)
            create_audit_log(request, user, "auth.register_applicant", user.email, "Applicant registered pending OTP verification.")
        return user

    @staticmethod
    def create_user_by_admin(validated_data, role, admin_user, request=None):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password")
        password_validation.validate_password(password)
        with transaction.atomic():
            user = User.objects.create_user(password=password, role=role, status=User.Status.ACTIVE, **validated_data)
            if role == User.Role.APPLICANT:
                from .models import ApplicantProfile

                ApplicantProfile.objects.create(user=user, **profile_data)
            if role == User.Role.EVALUATOR:
                from .models import EvaluatorProfile

                EvaluatorProfile.objects.create(user=user, **profile_data)
            create_audit_log(request, admin_user, f"auth.admin_create_{role}", user.email, f"Admin created {role} account.")
        return user

    @staticmethod
    def request_login_otp(email, password, request=None):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid email or password.") from exc
        if user.status == User.Status.LOCKED and user.locked_until and user.locked_until <= timezone.now():
            user.status = User.Status.ACTIVE
            user.locked_until = None
            user.failed_login_attempts = 0
            user.save(update_fields=["status", "locked_until", "failed_login_attempts"])
        if user.is_locked:
            raise AuthenticationFailed("Account is temporarily locked. Please try again later.")
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
                user.status = User.Status.LOCKED
            user.save(update_fields=["failed_login_attempts", "locked_until", "status"])
            create_audit_log(request, user, "auth.login_failed", user.email, "Failed login attempt.")
            raise AuthenticationFailed("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationFailed("Account is not active. Please verify your email first.")
        user.failed_login_attempts = 0
        user.locked_until = None
        user.status = User.Status.ACTIVE
        user.last_login_ip = get_client_ip(request) or None
        user.last_login_at = timezone.now()
        user.save(update_fields=["failed_login_attempts", "locked_until", "status", "last_login_ip", "last_login_at"])
        OTPService.create_and_send(user, OTPCode.Purpose.LOGIN, request)
        return user

    @staticmethod
    def verify_otp_and_issue_tokens(email, purpose, code, request=None):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise ValidationError("Invalid OTP code. Please try again.") from exc
        OTPService.verify(user, purpose, code, request)
        if purpose == OTPCode.Purpose.REGISTRATION and not user.is_active:
            user.is_active = True
            user.save(update_fields=["status"])
            create_audit_log(request, user, "auth.registration_verified", user.email, "Applicant email verified.")
        if purpose == OTPCode.Purpose.LOGIN:
            return AuthService.tokens_for_user(user)
        return {}

    @staticmethod
    def request_password_reset(email, request=None):
        try:
            user = User.objects.get(email__iexact=email, status=User.Status.ACTIVE)
        except User.DoesNotExist:
            return None
        return OTPService.create_and_send(user, OTPCode.Purpose.PASSWORD_RESET, request)

    @staticmethod
    def reset_password(email, code, new_password, request=None):
        try:
            user = User.objects.get(email__iexact=email, status=User.Status.ACTIVE)
        except User.DoesNotExist as exc:
            raise ValidationError("Invalid OTP code. Please try again.") from exc
        password_validation.validate_password(new_password, user)
        OTPService.verify(user, OTPCode.Purpose.PASSWORD_RESET, code, request)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        create_audit_log(request, user, "auth.password_reset", user.email, "Password reset completed.")
        return user
