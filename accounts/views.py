from django.contrib.auth import password_validation
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from core.audit import create_audit_log
from core.permissions import IsAdmin

from .models import CustomUser, OTPCode
from .serializers import (
    AdminCreateApplicantSerializer,
    AdminCreateEvaluatorSerializer,
    ApplicantRegistrationSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from .services import AuthService, OTPService


class RegisterApplicantView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ApplicantRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register_applicant(serializer.validated_data, request)
        return Response({"detail": "Registration received. Please verify the OTP sent to your email.", "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class AdminCreateApplicantView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AdminCreateApplicantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.create_user_by_admin(serializer.validated_data, CustomUser.Role.APPLICANT, request.user, request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminCreateEvaluatorView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AdminCreateEvaluatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.create_user_by_admin(serializer.validated_data, CustomUser.Role.EVALUATOR, request.user, request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.request_login_otp(serializer.validated_data["email"], serializer.validated_data["password"], request)
        return Response({"detail": "OTP sent to your email."})


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AuthService.verify_otp_and_issue_tokens(
            serializer.validated_data["email"],
            serializer.validated_data["purpose"],
            serializer.validated_data["otp_code"],
            request,
        )
        return Response({"detail": "OTP verified.", **data})


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(CustomUser, email__iexact=serializer.validated_data["email"])
        OTPService.create_and_send(user, serializer.validated_data["purpose"], request)
        return Response({"detail": "OTP sent to your email."})


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        create_audit_log(request, request.user, "auth.logout", request.user.email, "Refresh token blacklisted.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.request_password_reset(serializer.validated_data["email"], request)
        return Response({"detail": "If the account exists, a password reset OTP has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.reset_password(
            serializer.validated_data["email"],
            serializer.validated_data["otp_code"],
            serializer.validated_data["new_password"],
            request,
        )
        return Response({"detail": "Password reset completed."})


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        password_validation.validate_password(serializer.validated_data["new_password"], request.user)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        create_audit_log(request, request.user, "auth.password_changed", request.user.email, "Password changed by user.")
        return Response({"detail": "Password changed."})


class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all().order_by("-created_at")
    filterset_fields = ("role", "status")
    search_fields = ("email", "first_name", "middle_name", "last_name")
