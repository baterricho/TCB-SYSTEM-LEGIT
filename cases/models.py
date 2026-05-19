import uuid

from django.conf import settings
from django.db import models


class Case(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        EVALUATED = "evaluated", "Evaluated"
        ON_GOING = "on_going", "On Going"
        CERTIFIED = "certified", "Certified"
        ARCHIVED = "archived", "Archived"

    class PriorityLabel(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.BigAutoField(primary_key=True, db_column="case_id")
    case_number = models.CharField(max_length=40, unique=True, editable=False)
    application = models.OneToOneField("applications.IPApplication", on_delete=models.PROTECT, related_name="case", db_column="application_id")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="applicant_cases", db_column="applicant_id")
    assigned_evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_cases", db_column="assigned_evaluator_id")
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="taken_cases", db_column="taken_by_id")
    is_taken = models.BooleanField(default=False)
    taken_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    priority_score = models.PositiveIntegerField(default=0)
    priority_label = models.CharField(max_length=20, choices=PriorityLabel.choices, default=PriorityLabel.NORMAL)
    deadline = models.DateTimeField(null=True, blank=True)
    sla_stage = models.CharField(max_length=100, blank=True)
    sla_due_date = models.DateTimeField(null=True, blank=True)
    evaluation_summary = models.TextField(blank=True)
    evaluator_recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "case"
        ordering = ("deadline", "-created_at")
        indexes = [
            models.Index(fields=["case_number"]),
            models.Index(fields=["applicant"]),
            models.Index(fields=["assigned_evaluator"]),
            models.Index(fields=["taken_by"]),
            models.Index(fields=["status"]),
            models.Index(fields=["deadline"]),
            models.Index(fields=["priority_score"]),
        ]

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = f"TCB-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.case_number


class CaseStatusHistory(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="status_history_id")
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="status_history", db_column="case_id")
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column="changed_by_id")
    remarks = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_status_history"
        ordering = ("-changed_at",)


class ActivityTimeline(models.Model):
    class RoleVisibility(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        ADMIN = "admin", "Admin"
        ALL = "all", "All"

    id = models.BigAutoField(primary_key=True, db_column="timeline_id")
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="activity_timeline", db_column="case_id")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column="performed_by_id")
    role_visibility = models.CharField(max_length=20, choices=RoleVisibility.choices)
    action = models.CharField(max_length=255)
    applicant_message = models.TextField(blank=True)
    admin_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_timeline"
        ordering = ("created_at",)


class CaseEvaluation(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="evaluations", db_column="case_id")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="case_evaluations", db_column="evaluator_id")
    content = models.TextField()
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "case_evaluation"
        ordering = ("-created_at",)
