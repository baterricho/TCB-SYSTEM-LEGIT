import re
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import CustomUser, OTPCode
from auditlog.models import AuditLog


TEST_MASTER_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="


def create_user(email, role="applicant", password="StrongPass123!", **extra):
    defaults = {
        "first_name": extra.pop("first_name", "Test"),
        "last_name": extra.pop("last_name", "User"),
        "is_active": extra.pop("is_active", True),
    }
    defaults.update(extra)
    return CustomUser.objects.create_user(email=email, password=password, role=role, **defaults)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MASTER_KEY=TEST_MASTER_KEY,
    REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}
)
class AuthLoginFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from rest_framework.throttling import SimpleRateThrottle
        self.patcher = patch.dict(SimpleRateThrottle.THROTTLE_RATES, {
            "auth": "10000/min",
            "otp": "10000/min",
            "registration": "10000/min",
            "password_reset": "10000/min",
        })
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_admin_login_requires_otp_and_succeeds(self):
        from django.core import mail
        admin = create_user(
            "admin@example.com",
            username="adminuser",
            role=CustomUser.Role.ADMIN,
            is_staff=True,
        )

        response = self.client.post(
            "/api/auth/login/",
            {"email": "adminuser", "password": "StrongPass123!", "portal": "admin"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["otp_required"])
        self.assertNotIn("access", response.data)

        # Verify OTP
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        verify_response = self.client.post(
            "/api/auth/verify-otp/",
            {
                "email": admin.email,
                "purpose": OTPCode.Purpose.LOGIN,
                "otp_code": code,
            },
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertIn("tokens", verify_response.data)
        self.assertIn("access", verify_response.data["tokens"])
        self.assertIn("refresh", verify_response.data["tokens"])
        self.assertEqual(verify_response.data["user"]["email"], admin.email)
        self.assertEqual(verify_response.data["user"]["role"], CustomUser.Role.ADMIN)
        self.assertEqual(verify_response.data["redirect_url"], "/admin/dashboard/")
        self.assertTrue(AuditLog.objects.filter(user=admin, action="auth.admin_login_success").exists())

    def test_evaluator_login_requires_otp_and_succeeds(self):
        from django.core import mail
        evaluator = create_user("evaluator@example.com", role=CustomUser.Role.EVALUATOR)

        response = self.client.post(
            "/api/auth/login/",
            {"email": evaluator.email, "password": "StrongPass123!", "portal": "evaluator"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["otp_required"])
        self.assertNotIn("access", response.data)

        # Verify OTP
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        verify_response = self.client.post(
            "/api/auth/verify-otp/",
            {
                "email": evaluator.email,
                "purpose": OTPCode.Purpose.LOGIN,
                "otp_code": code,
            },
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertIn("tokens", verify_response.data)
        self.assertIn("access", verify_response.data["tokens"])
        self.assertEqual(verify_response.data["user"]["role"], CustomUser.Role.EVALUATOR)
        self.assertEqual(verify_response.data["redirect_url"], "/evaluator/dashboard/")
        self.assertTrue(AuditLog.objects.filter(user=evaluator, action="auth.evaluator_login_success").exists())

    def test_applicant_login_still_requires_otp(self):
        applicant = create_user("applicant@example.com")

        response = self.client.post(
            "/api/auth/login/",
            {"email": applicant.email, "password": "StrongPass123!", "portal": "applicant"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["otp_required"])
        self.assertNotIn("access", response.data)
        self.assertTrue(OTPCode.objects.filter(user=applicant, purpose=OTPCode.Purpose.LOGIN).exists())

    def test_wrong_role_cannot_use_admin_portal(self):
        applicant = create_user("wrong-portal@example.com")

        response = self.client.post(
            "/api/auth/login/",
            {"email": applicant.email, "password": "StrongPass123!", "portal": "admin"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(str(response.data["detail"]), "You are not authorized to access the Admin login portal.")
        self.assertFalse(OTPCode.objects.filter(user=applicant, purpose=OTPCode.Purpose.LOGIN).exists())
        self.assertTrue(AuditLog.objects.filter(user=applicant, action="auth.unauthorized_portal_access").exists())

    def test_failed_logins_lock_account_with_expected_message(self):
        user = create_user("locked@example.com")

        for attempt in range(1, 4):
            response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "WrongPass123!", "portal": "admin"},
                format="json",
            )
            self.assertEqual(response.status_code, 401)
            if attempt < 3:
                self.assertEqual(str(response.data["detail"]), "Invalid email or password. Please try again.")
            else:
                self.assertEqual(
                    str(response.data["detail"]),
                    "Too many failed login attempts. Please try again after 5 minutes.",
                )

        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 3)
        self.assertIsNotNone(user.locked_until)
        self.assertTrue(AuditLog.objects.filter(user=user, action="auth.account_locked").exists())

    @override_settings(DEBUG=True, TCB_PRINT_OTP_TO_CONSOLE=True)
    def test_admin_password_reset_otp_is_printed_to_terminal_in_development(self):
        admin = create_user("reset-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)

        with patch("builtins.print") as mocked_print:
            response = self.client.post(
                "/api/auth/forgot-password/",
                {"email": admin.email},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        terminal_output = "\n".join(str(call.args[0]) for call in mocked_print.call_args_list if call.args)
        self.assertIn("[TCB DEV OTP]", terminal_output)
        self.assertIn("purpose=password_reset", terminal_output)
        self.assertIn(f"email={admin.email}", terminal_output)
        otp_code = re.search(r"code=(\d{6})", terminal_output).group(1)

        reset_response = self.client.post(
            "/api/auth/reset-password/",
            {
                "email": admin.email,
                "otp_code": otp_code,
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(reset_response.status_code, 200)
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("NewStrongPass123!"))
        self.assertTrue(AuditLog.objects.filter(user=admin, action="auth.password_reset").exists())
