import secrets
import logging
from datetime import timedelta

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from core.audit import create_audit_log, get_client_ip

from .models import User, OTPCode


logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
MAX_OTP_RESENDS = 3
RESEND_WINDOW_MINUTES = 15
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 5
INVALID_LOGIN_MESSAGE = "Invalid email or password. Please try again."
LOCKOUT_MESSAGE = "Too many failed login attempts. Please try again after 5 minutes."
ADMIN_PORTAL_DENIED_MESSAGE = "You are not authorized to access the Admin login portal."
EVALUATOR_PORTAL_DENIED_MESSAGE = "You are not authorized to access the Evaluator login portal."


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
    def print_dev_otp(user, purpose, code):
        if not getattr(settings, "DEBUG", False):
            return
        if not getattr(settings, "TCB_PRINT_OTP_TO_CONSOLE", False):
            return
        msg = f"[TCB DEV OTP] purpose={purpose} email={user.email} code={code} expires_in={OTP_TTL_MINUTES}m"
        logger.debug(msg)
        print(msg)

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
        OTPService.print_dev_otp(user, purpose, code)
        try:
            send_mail(
                subject="Your Creator's Bulwark OTP Code",
                message=f"Your OTP code is {code}. It expires in {OTP_TTL_MINUTES} minutes.",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
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
    def tokens_for_user(user, is_otp_verified=True):
        if not is_otp_verified:
            raise ValidationError("OTP verification is required.")
        refresh = RefreshToken.for_user(user)
        refresh["is_otp_verified"] = True
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @staticmethod
    def _portal_role(portal):
        normalized = str(portal or "").strip().lower()
        if normalized in ("superadmin", "admin"):
            return User.Role.ADMIN
        if normalized in ("reviewer", "evaluator"):
            return User.Role.EVALUATOR
        if normalized in ("applicant", "user"):
            return User.Role.APPLICANT
        return ""

    @staticmethod
    def _redirect_url_for_role(role):
        if role == User.Role.ADMIN:
            return "/admin/dashboard/"
        if role == User.Role.EVALUATOR:
            return "/evaluator/dashboard/"
        return "/applicant/dashboard/"

    @staticmethod
    def _get_user_by_login_identifier(identifier):
        lookup = str(identifier or "").strip()
        if not lookup:
            return None
        return User.objects.filter(Q(email__iexact=lookup) | Q(username__iexact=lookup)).first()

    @staticmethod
    def _unlock_if_lockout_expired(user):
        if user.status == User.Status.LOCKED and user.locked_until and user.locked_until <= timezone.now():
            user.status = User.Status.ACTIVE
            user.locked_until = None
            user.failed_login_attempts = 0
            user.save(update_fields=["status", "locked_until", "failed_login_attempts"])

    @staticmethod
    def _record_failed_login(user, request=None):
        User.objects.filter(pk=user.pk).update(failed_login_attempts=F("failed_login_attempts") + 1)
        user.refresh_from_db(fields=["failed_login_attempts"])
        locked = user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS
        if locked:
            user.locked_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
            user.status = User.Status.LOCKED
            user.save(update_fields=["locked_until", "status"])
        create_audit_log(request, user, "auth.login_failed", user.email, "Failed login attempt.")
        if locked:
            create_audit_log(
                request,
                user,
                "auth.account_locked",
                user.email,
                f"Account locked for {LOCKOUT_MINUTES} minutes after too many failed login attempts.",
            )
            raise AuthenticationFailed(LOCKOUT_MESSAGE)
        raise AuthenticationFailed(INVALID_LOGIN_MESSAGE)

    @staticmethod
    def _record_successful_credentials(user, request=None):
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == User.Status.LOCKED:
            user.status = User.Status.ACTIVE
        user.last_login_ip = get_client_ip(request) or None
        user.last_login_at = timezone.now()
        user.save(update_fields=["failed_login_attempts", "locked_until", "status", "last_login_ip", "last_login_at"])

    @staticmethod
    def _authenticate_credentials(identifier, password, request=None):
        user = AuthService._get_user_by_login_identifier(identifier)
        if not user:
            create_audit_log(request, None, "auth.login_failed", identifier, "Failed login attempt for unknown account.")
            raise AuthenticationFailed(INVALID_LOGIN_MESSAGE)

        AuthService._unlock_if_lockout_expired(user)
        if user.is_locked:
            raise AuthenticationFailed(LOCKOUT_MESSAGE)
        if not user.check_password(password):
            AuthService._record_failed_login(user, request)
            return None
        if not user.is_active:
            raise AuthenticationFailed("Account is not active. Please verify your email first.")

        AuthService._record_successful_credentials(user, request)
        return user

    @staticmethod
    def _enforce_login_portal(user, portal, request=None):
        portal_role = AuthService._portal_role(portal)
        if not portal_role:
            return
        if portal_role == user.role:
            return

        if portal_role == User.Role.ADMIN:
            message = ADMIN_PORTAL_DENIED_MESSAGE
        elif portal_role == User.Role.EVALUATOR:
            message = EVALUATOR_PORTAL_DENIED_MESSAGE
        else:
            message = "You are not authorized to access the Applicant login portal."
        create_audit_log(
            request,
            user,
            "auth.unauthorized_portal_access",
            user.email,
            f"Unauthorized role portal access. Requested {portal_role}, actual role {user.role}.",
        )
        raise AuthenticationFailed(message)

    @staticmethod
    def register_applicant(validated_data, request=None):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password")
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
    def login(identifier, password, portal=None, request=None):
        user = AuthService._authenticate_credentials(identifier, password, request)
        AuthService._enforce_login_portal(user, portal, request)

        OTPService.create_and_send(user, OTPCode.Purpose.LOGIN, request)
        return {"user": user, "otp_required": True}

    @staticmethod
    def request_login_otp(email, password, request=None):
        data = AuthService.login(email, password, portal=User.Role.APPLICANT, request=request)
        return data["user"]

    @staticmethod
    def verify_otp_and_issue_tokens(email, purpose, code, request=None):
        user = AuthService._get_user_by_login_identifier(email)
        if not user:
            raise ValidationError("Invalid OTP code. Please try again.")
        OTPService.verify(user, purpose, code, request)
        if purpose == OTPCode.Purpose.REGISTRATION and not user.is_active:
            user.status = User.Status.ACTIVE
            user.save(update_fields=["status"])
            create_audit_log(request, user, "auth.registration_verified", user.email, "Applicant email verified.")
        if purpose == OTPCode.Purpose.LOGIN:
            tokens = AuthService.tokens_for_user(user, is_otp_verified=True)
            action = "auth.login_success"
            if user.role == User.Role.ADMIN:
                action = "auth.admin_login_success"
            elif user.role == User.Role.EVALUATOR:
                action = "auth.evaluator_login_success"
            create_audit_log(request, user, action, user.email, "Successful login via OTP.")
            return {
                **tokens,
                "redirect_url": AuthService._redirect_url_for_role(user.role),
            }
        return {}

    @staticmethod
    def request_password_reset(email, request=None):
        try:
            user = User.objects.get(email__iexact=email, status=User.Status.ACTIVE)
        except User.DoesNotExist:
            return None
        otp = OTPService.create_and_send(user, OTPCode.Purpose.PASSWORD_RESET, request)
        create_audit_log(request, user, "auth.password_reset_requested", user.email, "Password reset requested.")
        return otp

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
