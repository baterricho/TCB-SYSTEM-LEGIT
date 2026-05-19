from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        is_active = extra_fields.pop("is_active", None)
        if is_active is not None:
            extra_fields.setdefault("status", User.Status.ACTIVE if is_active else User.Status.INACTIVE)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("status", User.Status.ACTIVE)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        EVALUATOR = "evaluator", "Evaluator"
        ADMIN = "admin", "Admin"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        LOCKED = "locked", "Locked"
        ARCHIVED = "archived", "Archived"

    id = models.BigAutoField(primary_key=True, db_column="user_id")
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPLICANT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    contact_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_staff = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        names = [self.first_name, self.middle_name, self.last_name]
        return " ".join(name for name in names if name).strip()

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @is_active.setter
    def is_active(self, value):
        self.status = self.Status.ACTIVE if value else self.Status.INACTIVE

    @property
    def is_locked(self):
        return self.status == self.Status.LOCKED or bool(self.locked_until and self.locked_until > timezone.now())


class OTPCode(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        REGISTRATION = "registration", "Registration"
        PASSWORD_RESET = "password_reset", "Password Reset"

    id = models.BigAutoField(primary_key=True, db_column="otp_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes", db_column="user_id")
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_code"
        indexes = [
            models.Index(fields=["user", "purpose", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} {self.purpose}"


class ApplicantProfile(models.Model):
    class ApplicantType(models.TextChoices):
        FACULTY = "faculty", "Faculty"
        STAFF = "staff", "Staff"
        STUDENT = "student", "Student"
        EXTERNAL = "external", "External"

    id = models.BigAutoField(primary_key=True, db_column="applicant_profile_id")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_profile", db_column="user_id")
    applicant_type = models.CharField(max_length=30, choices=ApplicantType.choices)
    institution = models.CharField(max_length=255, blank=True)
    student_or_employee_id = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to="profiles/applicants/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applicant_profile"

    def __str__(self):
        return self.user.email


class EvaluatorProfile(models.Model):
    class Specialization(models.TextChoices):
        PATENT_MECHANICAL = "patent_mechanical", "Patent - Mechanical"
        PATENT_ELECTRICAL = "patent_electrical", "Patent - Electrical"
        UTILITY_MODEL = "utility_model", "Utility Model"
        INDUSTRIAL_DESIGN = "industrial_design", "Industrial Design"
        TRADEMARK = "trademark", "Trademark"
        COPYRIGHT = "copyright", "Copyright"

    id = models.BigAutoField(primary_key=True, db_column="evaluator_profile_id")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="evaluator_profile", db_column="user_id")
    specialization = models.CharField(max_length=40, choices=Specialization.choices)
    workload_count = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluator_profile"

    def __str__(self):
        return f"{self.user.email} - {self.specialization}"


CustomUser = User
