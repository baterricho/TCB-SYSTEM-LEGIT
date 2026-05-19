from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from applications.models import IPApplication
from cases.models import Case
from inquiries.models import Inquiry
from marketplace.models import MarketListing
from payments.models import Payment


class ReportService:
    @staticmethod
    def summary_metrics():
        return {
            "applications": IPApplication.objects.count(),
            "submitted_applications": IPApplication.objects.filter(status=IPApplication.Status.SUBMITTED).count(),
            "cases": Case.objects.count(),
            "pending_cases": Case.objects.filter(status=Case.Status.PENDING).count(),
            "overdue_cases": Case.objects.filter(deadline__lt=timezone.now()).exclude(status__in=[Case.Status.CERTIFIED, Case.Status.ARCHIVED]).count(),
            "payment_receipts_pending": Payment.objects.filter(payment_status=Payment.Status.PENDING).count(),
            "published_marketplace_listings": MarketListing.objects.filter(status=MarketListing.Status.PUBLISHED, is_active=True).count(),
            "open_inquiries": Inquiry.objects.filter(status=Inquiry.Status.NEW).count(),
        }

    @staticmethod
    def applications_by_ip_type():
        return list(IPApplication.objects.values("ip_type").annotate(count=Count("id")).order_by("ip_type"))

    @staticmethod
    def monthly_submissions():
        return list(
            IPApplication.objects.filter(submitted_at__isnull=False)
            .annotate(month=TruncMonth("submitted_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

    @staticmethod
    def case_status_distribution():
        return list(Case.objects.values("status").annotate(count=Count("id")).order_by("status"))

    @staticmethod
    def evaluator_workload():
        return list(
            Case.objects.filter(taken_by__isnull=False)
            .values("taken_by__id", "taken_by__first_name", "taken_by__last_name", "taken_by__email")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    @staticmethod
    def deadline_monitoring():
        now = timezone.now()
        return {
            "overdue": Case.objects.filter(deadline__lt=now).exclude(status__in=[Case.Status.CERTIFIED, Case.Status.ARCHIVED]).count(),
            "due_today": Case.objects.filter(deadline__date=now.date()).count(),
            "due_soon": Case.objects.filter(deadline__gt=now, deadline__lte=now + timedelta(days=7)).count(),
            "no_deadline": Case.objects.filter(deadline__isnull=True).count(),
        }

    @staticmethod
    def inquiry_popularity():
        return list(Inquiry.objects.order_by("-popularity_count").values("inquiry_code", "subject", "popularity_count", "status")[:50])

    @staticmethod
    def marketplace_interest():
        return list(
            MarketListing.objects.annotate(bookmark_count=Count("bookmarks"))
            .values("listing_code", "title", "status", "bookmark_count")
            .order_by("-bookmark_count")
        )
