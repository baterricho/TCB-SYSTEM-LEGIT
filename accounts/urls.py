from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminCreateApplicantView,
    AdminCreateEvaluatorView,
    ChangePasswordView,
    CurrentUserView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    RegisterApplicantView,
    ResendOTPView,
    ResetPasswordView,
    UserAdminViewSet,
    VerifyOTPView,
)


router = DefaultRouter()
router.register("users", UserAdminViewSet, basename="admin-users")

urlpatterns = [
    path("register-applicant/", RegisterApplicantView.as_view()),
    path("admin/create-applicant/", AdminCreateApplicantView.as_view()),
    path("admin/create-evaluator/", AdminCreateEvaluatorView.as_view()),
    path("login/", LoginView.as_view()),
    path("verify-otp/", VerifyOTPView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("me/", CurrentUserView.as_view()),
    path("", include(router.urls)),
]
