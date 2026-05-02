"""
Views for user authentication, registration, profile management,
OTP email verification, and password reset/change.
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.shortcuts import get_object_or_404

from core.frontend import build_frontend_payload, get_frontend_url_for_role
from core.permissions import IsAdmin
from .models import User, UserProfile, OTPVerification
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserListSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
    ResendOTPSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)


def _send_otp_email(user, otp):
    """
    Helper: logs the OTP to console in development.
    In production this should send a real email via Django's send_mail.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[OTP] User: {user.email} | Purpose: {otp.purpose} | "
        f"Code: {otp.otp_code} | Expires: {otp.expires_at}"
    )
    # TODO: replace with real email sending for production
    # from django.core.mail import send_mail
    # send_mail(subject, message, from_email, [user.email])


class RegisterView(generics.CreateAPIView):
    """
    POST /api/accounts/register/ — Register a new user.
    Creates user with is_verified=False and sends a 6-digit OTP to email.
    User must call /verify-email/ before they can log in.
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate and send OTP
        otp = OTPVerification.create_otp(user=user, purpose="registration")
        _send_otp_email(user, otp)

        payload = {
            "message": (
                "Registration successful. A 6-digit OTP has been sent to your email. "
                "Please verify your account before logging in."
            ),
            "email": user.email,
            "redirect_url": get_frontend_url_for_role(user.role),
            "frontend": build_frontend_payload(user.role),
        }
        if settings.DEBUG:
            payload["dev_otp"] = otp.otp_code

        return Response(payload, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """
    POST /api/accounts/verify-email/ — Verify email using OTP after registration.
    On success: marks user as verified and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        otp = serializer.validated_data["otp"]

        # Mark OTP as used and verify user
        otp.is_used = True
        otp.save()
        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)

        from services.audit_service import log_audit
        log_audit(user=user, action="EMAIL_VERIFIED", entity=f"User:{user.id}")

        return Response(
            {
                "message": "Email verified successfully. Welcome to The Creator's Bulwark!",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "redirect_url": get_frontend_url_for_role(user.role),
                "frontend": build_frontend_payload(user.role),
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    POST /api/accounts/resend-otp/ — Resend OTP for email verification or password reset.
    Body: { "email": "...", "purpose": "registration" | "password_reset" }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        purpose = serializer.validated_data["purpose"]

        otp = OTPVerification.create_otp(user=user, purpose=purpose)
        _send_otp_email(user, otp)

        payload = {"message": "A new OTP has been sent to your email."}
        if settings.DEBUG:
            payload["dev_otp"] = otp.otp_code
        return Response(payload, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    POST /api/accounts/forgot-password/ — Initiate password reset.
    Sends a 6-digit OTP to the registered email address.
    Body: { "email": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data["email"])
        otp = OTPVerification.create_otp(user=user, purpose="password_reset")
        _send_otp_email(user, otp)

        payload = {
            "message": (
                "A password reset OTP has been sent to your email. "
                "It expires in 10 minutes."
            )
        }
        if settings.DEBUG:
            payload["dev_otp"] = otp.otp_code

        return Response(payload, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    POST /api/accounts/reset-password/ — Complete password reset.
    Body: { "email": "...", "otp_code": "123456", "new_password": "...", "new_password_confirm": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        otp = serializer.validated_data["otp"]

        # Mark OTP used and update password
        otp.is_used = True
        otp.save()
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        from services.audit_service import log_audit
        log_audit(user=user, action="PASSWORD_RESET", entity=f"User:{user.id}")

        return Response(
            {"message": "Password reset successful. You can now log in with your new password."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """
    POST /api/accounts/change-password/ — Authenticated user changes their password.
    Body: { "current_password": "...", "new_password": "...", "new_password_confirm": "..." }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        from services.audit_service import log_audit
        log_audit(user=user, action="CHANGE_PASSWORD", entity=f"User:{user.id}")

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """POST /api/accounts/login/ — Authenticate and return JWT tokens."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        from services.audit_service import log_audit
        log_audit(user=user, action="LOGIN", entity=f"User:{user.id}")

        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "redirect_url": get_frontend_url_for_role(user.role),
                "frontend": build_frontend_payload(user.role),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """POST /api/accounts/logout/ — Blacklist the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK,
            )


class ProfileView(APIView):
    """
    GET  /api/accounts/profile/ — Get current user's profile.
    PUT  /api/accounts/profile/ — Update current user's profile (contact, address, institution).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UserListView(generics.ListAPIView):
    """GET /api/accounts/users/ — List all users (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserListSerializer
    queryset = User.objects.select_related("profile").all()
    filterset_fields = ["role", "is_verified", "is_active"]
    search_fields = ["full_name", "email"]
    ordering_fields = ["created_at", "full_name"]


class UserDetailView(APIView):
    """
    GET /api/accounts/users/<id>/ — Get user details (admin only).
    PUT /api/accounts/users/<id>/ — Update user role/status (admin only).
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return Response(UserSerializer(user).data)

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        allowed_fields = {"role", "is_verified", "is_active"}
        for field, value in request.data.items():
            if field in allowed_fields:
                setattr(user, field, value)
        user.save()

        from services.audit_service import log_audit
        log_audit(
            user=request.user,
            action="UPDATE_USER",
            entity=f"User:{user.id}",
        )

        return Response(UserSerializer(user).data)
