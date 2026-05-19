import re
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from applications.models import IPApplication
from cases.models import Case
from inquiries.models import Inquiry
from nlq.models import NLQQuery


UNCLEAR_MESSAGE = "Your query is unclear. Please specify the IP type, status, date range, or category."
NO_RESULTS_MESSAGE = "No matching records found for your query."

IP_TYPE_TERMS = {
    "patent": IPApplication.IPType.PATENT,
    "patents": IPApplication.IPType.PATENT,
    "utility model": IPApplication.IPType.UTILITY_MODEL,
    "utility models": IPApplication.IPType.UTILITY_MODEL,
    "industrial design": IPApplication.IPType.INDUSTRIAL_DESIGN,
    "industrial designs": IPApplication.IPType.INDUSTRIAL_DESIGN,
    "trademark": IPApplication.IPType.TRADEMARK,
    "trademarks": IPApplication.IPType.TRADEMARK,
    "copyright": IPApplication.IPType.COPYRIGHT,
    "copyrights": IPApplication.IPType.COPYRIGHT,
}


STATUS_TERMS = {
    "under review": "under_review",
    "under-review": "under_review",
    "under_review": "under_review",
    "pending": "pending",
    "approved": "approved",
    "rejected": "rejected",
    "completed": "completed",
    "evaluated": Case.Status.EVALUATED,
    "on going": Case.Status.ON_GOING,
    "ongoing": Case.Status.ON_GOING,
    "certified": Case.Status.CERTIFIED,
    "archived": Case.Status.ARCHIVED,
    "draft": IPApplication.Status.DRAFT,
    "submitted": IPApplication.Status.SUBMITTED,
    "withdrawn": IPApplication.Status.WITHDRAWN,
}


def term_in_text(text, term):
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def detect_ip_type(text):
    for term, value in sorted(IP_TYPE_TERMS.items(), key=lambda item: len(item[0]), reverse=True):
        if term_in_text(text, term):
            return value
    return None


def detect_status(text):
    for term, value in sorted(STATUS_TERMS.items(), key=lambda item: len(item[0]), reverse=True):
        if value and term_in_text(text, term):
            return value
    return None


def is_application_query(text):
    return term_in_text(text, "application") or term_in_text(text, "applications")


def is_case_query(text):
    return term_in_text(text, "case") or term_in_text(text, "cases")


def has_date_filter(text):
    return any(term in text for term in ("this month", "this year", "today"))


def case_status_filter_value(status):
    aliases = {
        "approved": Case.Status.CERTIFIED,
        "completed": Case.Status.CERTIFIED,
        "under_review": Case.Status.UNDER_REVIEW,
    }
    return aliases.get(status, status)


def apply_application_status_filter(queryset, status):
    status_queries = {
        "pending": Q(status="pending") | Q(status=IPApplication.Status.SUBMITTED) | Q(case__status=Case.Status.PENDING),
        "approved": Q(status="approved") | Q(case__status=Case.Status.CERTIFIED),
        "rejected": Q(status="rejected"),
        "under_review": Q(status="under_review") | Q(case__status=Case.Status.UNDER_REVIEW),
        "completed": Q(status="completed") | Q(case__status=Case.Status.CERTIFIED),
    }
    return queryset.filter(status_queries.get(status, Q(status=status)))


def apply_date_filter(queryset, text, field):
    now = timezone.now()
    if "this month" in text:
        return queryset.filter(**{f"{field}__year": now.year, f"{field}__month": now.month}), {"date_range": "this_month"}
    if "this year" in text:
        return queryset.filter(**{f"{field}__year": now.year}), {"date_range": "this_year"}
    if "today" in text:
        return queryset.filter(**{f"{field}__date": now.date()}), {"date_range": "today"}
    return queryset, {}


class NLQService:
    @staticmethod
    def process(raw_query, user):
        text = raw_query.strip().lower()
        intent = ""
        filters = {}
        results = []
        message = ""

        if "overdue" in text and "case" in text:
            intent = "overdue_cases"
            qs = Case.objects.filter(deadline__lt=timezone.now()).exclude(status__in=[Case.Status.CERTIFIED, Case.Status.ARCHIVED])
            results = list(qs.values("case_number", "status", "deadline", "application__ip_type")[:100])
        elif "most popular inquiries" in text:
            intent = "popular_inquiries"
            qs = Inquiry.objects.all()
            qs, date_filters = apply_date_filter(qs, text, "created_at")
            filters.update(date_filters)
            results = list(qs.order_by("-popularity_count").values("inquiry_id", "subject", "popularity_count", "status")[:100])
        elif "unanswered marketplace inquiries" in text:
            intent = "unanswered_marketplace_inquiries"
            qs = Inquiry.objects.filter(status=Inquiry.Status.NEW, category__icontains="marketplace")
            results = list(qs.values("inquiry_id", "subject", "email", "created_at")[:100])
        elif "handled by" in text and "case" in text:
            intent = "cases_by_evaluator"
            name = re.split(r"handled by", text, maxsplit=1)[-1].strip().rstrip(".")
            if not name:
                return NLQService._record(user, raw_query, intent, filters, [], UNCLEAR_MESSAGE)
            name_parts = [part for part in name.split() if part]
            query = Q()
            for part in name_parts:
                query |= Q(taken_by__first_name__icontains=part) | Q(taken_by__middle_name__icontains=part) | Q(taken_by__last_name__icontains=part)
            qs = Case.objects.filter(query, taken_by__isnull=False)
            filters["evaluator_name"] = name
            results = list(qs.values("case_number", "status", "deadline", "taken_by__first_name", "taken_by__last_name")[:100])
        elif "certified cases by ip type" in text:
            intent = "certified_cases_by_ip_type"
            results = list(
                Case.objects.filter(status=Case.Status.CERTIFIED)
                .values("application__ip_type")
                .annotate(count=Count("id"))
                .order_by("application__ip_type")
            )
        elif "applications with missing documents" in text:
            intent = "applications_missing_documents"
            results = list(
                IPApplication.objects.filter(case__documents__isnull=True)
                .distinct()
                .values("application_code", "title", "ip_type", "status")[:100]
            )
        elif is_application_query(text):
            intent = "filtered_applications"
            qs = IPApplication.objects.select_related("applicant")
            ip_type = detect_ip_type(text)
            status = detect_status(text)
            if ip_type:
                qs = qs.filter(ip_type=ip_type)
                filters["ip_type"] = ip_type
            if status:
                qs = apply_application_status_filter(qs, status)
                filters["status"] = status
            qs, date_filters = apply_date_filter(qs, text, "created_at")
            filters.update(date_filters)
            results = list(
                qs.distinct().values(
                    "application_code",
                    "title",
                    "ip_type",
                    "status",
                    "created_at",
                    "submitted_at",
                    "case__case_number",
                    "case__status",
                )[:100]
            )
        elif is_case_query(text) or ("show" in text and (detect_ip_type(text) or detect_status(text) or has_date_filter(text))):
            intent = "filtered_cases"
            qs = Case.objects.select_related("application")
            ip_type = detect_ip_type(text)
            status = detect_status(text)
            if ip_type:
                qs = qs.filter(application__ip_type=ip_type)
                filters["ip_type"] = ip_type
            if status:
                qs = qs.filter(status=case_status_filter_value(status))
                filters["status"] = status
            qs, date_filters = apply_date_filter(qs, text, "created_at")
            filters.update(date_filters)
            if not filters and "all" not in text:
                return NLQService._record(user, raw_query, intent, filters, [], UNCLEAR_MESSAGE)
            results = list(qs.values("case_number", "status", "deadline", "application__ip_type", "created_at")[:100])
        else:
            return NLQService._record(user, raw_query, intent, filters, [], UNCLEAR_MESSAGE)

        if not results:
            message = NO_RESULTS_MESSAGE
        return NLQService._record(user, raw_query, intent, filters, results, message)

    @staticmethod
    def _record(user, raw_query, intent, filters, results, message):
        NLQQuery.objects.create(
            user=user,
            raw_query=raw_query,
            detected_intent=intent,
            extracted_filters=filters,
            result_count=len(results),
        )
        return {"intent": intent, "filters": filters, "result_count": len(results), "results": results, "message": message}
