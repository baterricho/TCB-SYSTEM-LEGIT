import csv
from datetime import date
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone

from applications.models import IPApplication
from cases.models import Case
from inquiries.models import Inquiry
from marketplace.models import IPRecord, MarketListing
from payments.models import Payment
from reports.models import ReportExport
from accounts.models import User


class ReportService:
    @staticmethod
    def summary_metrics():
        case_counts = dict(Case.objects.values_list("status").annotate(count=Count("id")))
        return {
            "total_applications": IPApplication.objects.count(),
            "applications": IPApplication.objects.count(),
            "submitted_applications": IPApplication.objects.filter(status=IPApplication.Status.SUBMITTED).count(),
            "cases": Case.objects.count(),
            "pending_cases": case_counts.get(Case.Status.PENDING, 0),
            "under_review_cases": case_counts.get(Case.Status.UNDER_REVIEW, 0),
            "evaluated_cases": case_counts.get(Case.Status.EVALUATED, 0),
            "on_going_cases": case_counts.get(Case.Status.ON_GOING, 0),
            "certified_cases": case_counts.get(Case.Status.CERTIFIED, 0),
            "archived_cases": case_counts.get(Case.Status.ARCHIVED, 0),
            "overdue_cases": Case.objects.filter(deadline__lt=timezone.now()).exclude(status__in=[Case.Status.CERTIFIED, Case.Status.ARCHIVED]).count(),
            "active_evaluators": User.objects.filter(role=User.Role.EVALUATOR, status=User.Status.ACTIVE).count(),
            "total_inquiries": Inquiry.objects.count(),
            "unread_notifications": 0,
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


IP_TYPE_LABELS = {
    IPApplication.IPType.PATENT: "Patent",
    IPApplication.IPType.UTILITY_MODEL: "Utility Model",
    IPApplication.IPType.INDUSTRIAL_DESIGN: "Industrial Design",
    IPApplication.IPType.TRADEMARK: "Trademark",
    IPApplication.IPType.COPYRIGHT: "Copyright",
}

IP_TYPE_VALUES = {value.lower(): key for key, value in IP_TYPE_LABELS.items()}
IP_TYPE_VALUES.update({key.lower(): key for key in IP_TYPE_LABELS})

APPLICATION_STATUS_LABELS = {
    IPApplication.Status.DRAFT: "Draft",
    IPApplication.Status.SUBMITTED: "Submitted",
    IPApplication.Status.WITHDRAWN: "Withdrawn",
}

CASE_STATUS_LABELS = {
    Case.Status.PENDING: "Pending",
    Case.Status.UNDER_REVIEW: "Under Review",
    Case.Status.EVALUATED: "Evaluated",
    Case.Status.ON_GOING: "On Going",
    Case.Status.CERTIFIED: "Certified",
    Case.Status.ARCHIVED: "Archived",
}

CASE_PRIORITY_LABELS = {
    Case.PriorityLabel.LOW: "Low",
    Case.PriorityLabel.NORMAL: "Normal",
    Case.PriorityLabel.MEDIUM: "Medium",
    Case.PriorityLabel.HIGH: "High",
    Case.PriorityLabel.CRITICAL: "Critical",
}

STATUS_VALUES = {
    **{label.lower(): ("application", value) for value, label in APPLICATION_STATUS_LABELS.items()},
    **{value.lower(): ("application", value) for value in APPLICATION_STATUS_LABELS},
    **{label.lower(): ("case", value) for value, label in CASE_STATUS_LABELS.items()},
    **{value.lower(): ("case", value) for value in CASE_STATUS_LABELS},
    "validated": ("case", Case.Status.EVALUATED),
    "approved": ("case", Case.Status.CERTIFIED),
    "ongoing": ("case", Case.Status.ON_GOING),
}

RESULT_LABELS = [
    "Approved / Certified",
    "For Revision",
    "Rejected",
    "Pending",
    "No Result Yet",
]


def _blank(value):
    return value if value not in (None, "") else "-"


def _date(value):
    if not value:
        return "-"
    if hasattr(value, "date") and not isinstance(value, date):
        value = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _datetime(value):
    if not value:
        return "-"
    value = timezone.localtime(value) if timezone.is_aware(value) else value
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _user_label(user):
    if not user:
        return "System"
    full_name = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return full_name or getattr(user, "email", "") or "System"


def _normalize_choice(value):
    return str(value or "").strip().replace("_", " ").lower()


def _normalize_ip_type(value):
    if not value or value == "All":
        return ""
    return IP_TYPE_VALUES.get(_normalize_choice(value), str(value).strip())


def _normalize_status(value):
    if not value or value == "All":
        return None
    return STATUS_VALUES.get(_normalize_choice(value))


def _result_key(value):
    normalized = _normalize_choice(value)
    mapping = {
        "approved / certified": "Approved / Certified",
        "approved": "Approved / Certified",
        "certified": "Approved / Certified",
        "approved certified": "Approved / Certified",
        "for revision": "For Revision",
        "revision": "For Revision",
        "rejected": "Rejected",
        "pending": "Pending",
        "no result yet": "No Result Yet",
        "no_result_yet": "No Result Yet",
    }
    return mapping.get(normalized, "")


def _latest_evaluation(case):
    if not case:
        return None
    evaluations = list(getattr(case, "evaluations", []).all()) if hasattr(case, "evaluations") else []
    return evaluations[0] if evaluations else None


def _case_result(case, application=None):
    if case and case.status == Case.Status.CERTIFIED:
        return "Approved / Certified"

    latest_evaluation = _latest_evaluation(case)
    text = " ".join(
        str(part or "")
        for part in [
            getattr(case, "evaluation_summary", ""),
            getattr(case, "evaluator_recommendation", ""),
            getattr(latest_evaluation, "content", ""),
            getattr(latest_evaluation, "recommendation", ""),
        ]
    ).lower()

    if "reject" in text:
        return "Rejected"
    if any(token in text for token in ("revision", "revise", "correction", "resubmit")):
        return "For Revision"
    if case and case.status in {Case.Status.PENDING, Case.Status.UNDER_REVIEW, Case.Status.ON_GOING}:
        return "Pending"
    if application and application.status in {IPApplication.Status.SUBMITTED}:
        return "Pending"
    return "No Result Yet"


def _case_display_status(case, application=None):
    if case:
        return CASE_STATUS_LABELS.get(case.status, case.status)
    if application:
        return APPLICATION_STATUS_LABELS.get(application.status, application.status)
    return "-"


def _case_completed_date(case):
    if not case:
        return "-"
    record = getattr(case, "ip_record", None)
    if record and record.certification_date:
        return _date(record.certification_date)
    if case.status in {Case.Status.CERTIFIED, Case.Status.ARCHIVED}:
        return _datetime(case.updated_at)
    return "-"


def _apply_application_filters(queryset, params):
    ip_type = _normalize_ip_type(params.get("ip_service") or params.get("ip_type"))
    if ip_type:
        queryset = queryset.filter(ip_type=ip_type)

    year = params.get("year")
    if year and str(year) != "All":
        try:
            year = int(year)
            queryset = queryset.filter(created_at__year=year)
        except (TypeError, ValueError):
            pass

    date_from = params.get("date_from") or params.get("from")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    date_to = params.get("date_to") or params.get("to")
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    status = _normalize_status(params.get("status"))
    if status:
        source, value = status
        if source == "application":
            queryset = queryset.filter(status=value)
        else:
            queryset = queryset.filter(case__status=value)

    return queryset


def _filter_rows_by_result(rows, result_filter):
    result = _result_key(result_filter)
    if not result:
        return rows
    return [row for row in rows if row["result"] == result]


def _application_rows(queryset):
    rows = []
    for application in queryset:
        case = getattr(application, "case", None)
        evaluator = None
        if case:
            evaluator = getattr(case, "taken_by", None) or getattr(case, "assigned_evaluator", None)
        rows.append(
            {
                "application": application,
                "case": case,
                "result": _case_result(case, application),
                "case_number": getattr(case, "case_number", "") if case else "",
                "application_code": application.application_code,
                "applicant_name": _user_label(application.applicant),
                "ip_type": IP_TYPE_LABELS.get(application.ip_type, application.ip_type),
                "title": application.title,
                "status": _case_display_status(case, application),
                "evaluator": _user_label(evaluator) if evaluator else "-",
                "submission_date": _datetime(application.submitted_at or application.created_at),
                "deadline": _datetime(getattr(case, "deadline", None)) if case else "-",
                "completed_date": _case_completed_date(case),
            }
        )
    return rows


def _write_section(writer, title):
    writer.writerow([])
    writer.writerow([title])


def _write_key_values(writer, rows):
    for key, value in rows:
        writer.writerow([key, value])


def _csv_response(filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _selected_filter_rows(params, names):
    rows = []
    for label, key in names:
        rows.append([label, params.get(key) or "All"])
    return rows


def _normalize_priority(value):
    if not value or value == "All":
        return ""
    normalized = _normalize_choice(value)
    for priority, label in CASE_PRIORITY_LABELS.items():
        if normalized in {priority.lower(), label.lower()}:
            return priority
    return ""


def _apply_case_filters(queryset, params):
    ip_type = _normalize_ip_type(params.get("ip_type") or params.get("ip_service"))
    if ip_type:
        queryset = queryset.filter(application__ip_type=ip_type)

    status = _normalize_status(params.get("case_status") or params.get("status"))
    if status:
        source, value = status
        if source == "case":
            queryset = queryset.filter(status=value)

    priority = _normalize_priority(params.get("priority"))
    if priority:
        queryset = queryset.filter(priority_label=priority)

    year = params.get("year")
    if year and str(year) != "All":
        try:
            queryset = queryset.filter(created_at__year=int(year))
        except (TypeError, ValueError):
            pass

    date_from = params.get("date_from") or params.get("from")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    date_to = params.get("date_to") or params.get("to")
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    deadline_from = params.get("deadline_from")
    if deadline_from:
        queryset = queryset.filter(deadline__date__gte=deadline_from)
    deadline_to = params.get("deadline_to")
    if deadline_to:
        queryset = queryset.filter(deadline__date__lte=deadline_to)

    return queryset


def _deadline_status(case):
    if not case or not case.deadline:
        return "Cases with no deadline"
    deadline_date = timezone.localtime(case.deadline).date() if timezone.is_aware(case.deadline) else case.deadline.date()
    today = timezone.localdate()
    days_remaining = (deadline_date - today).days
    if days_remaining < 0:
        return "Overdue cases"
    if days_remaining == 0:
        return "Due today"
    if days_remaining <= 3:
        return "Due within 1-3 days"
    if days_remaining <= 7:
        return "Due within 4-7 days"
    return "Later deadlines"


def _latest_payment_status(case):
    payments = list(getattr(case, "payments", []).all()) if hasattr(case, "payments") else []
    if not payments:
        return "No receipt"
    latest_payment = payments[0]
    return latest_payment.get_payment_status_display() if hasattr(latest_payment, "get_payment_status_display") else latest_payment.payment_status


def _document_status(case):
    documents = list(getattr(case, "documents", []).all()) if hasattr(case, "documents") else []
    if not documents:
        return "No documents"
    return f"{len(documents)} document{'s' if len(documents) != 1 else ''} uploaded"


def _latest_evaluator_action(case, evaluator):
    timelines = list(getattr(case, "activity_timeline", []).all()) if hasattr(case, "activity_timeline") else []
    for entry in reversed(timelines):
        if getattr(entry, "performed_by_id", None) == getattr(evaluator, "id", None):
            return entry.action

    latest_evaluation = _latest_evaluation(case)
    if latest_evaluation and getattr(latest_evaluation, "evaluator_id", None) == getattr(evaluator, "id", None):
        return "Submitted evaluation"
    return "-"


def _case_unread_applicant_messages(case):
    unread = 0
    latest_message_date = None
    for conversation in list(getattr(case, "conversations", []).all()) if hasattr(case, "conversations") else []:
        for message in conversation.messages.all():
            if latest_message_date is None or message.sent_at > latest_message_date:
                latest_message_date = message.sent_at
            if message.sender_id == case.applicant_id and not message.is_read:
                unread += 1
    return unread, latest_message_date


def _evaluator_case_rows(queryset, evaluator):
    rows = []
    for case in queryset:
        application = case.application
        result = _case_result(case, application)
        rows.append(
            {
                "case": case,
                "application": application,
                "result": result,
                "case_number": case.case_number,
                "application_code": application.application_code,
                "applicant_name": _user_label(case.applicant),
                "ip_type": IP_TYPE_LABELS.get(application.ip_type, application.ip_type),
                "title": application.title,
                "status": CASE_STATUS_LABELS.get(case.status, case.status),
                "priority": CASE_PRIORITY_LABELS.get(case.priority_label, case.priority_label),
                "deadline": _datetime(case.deadline),
                "deadline_status": _deadline_status(case),
                "date_submitted": _datetime(application.submitted_at or application.created_at),
                "date_taken": _datetime(case.taken_at),
                "last_updated": _datetime(case.updated_at),
                "payment_receipt_status": _latest_payment_status(case),
                "document_status": _document_status(case),
                "latest_evaluator_action": _latest_evaluator_action(case, evaluator),
            }
        )
    return rows


class ExportReportService:
    @staticmethod
    def portfolio_analytics_csv(request):
        queryset = (
            IPApplication.objects.select_related(
                "applicant",
                "case",
                "case__applicant",
                "case__assigned_evaluator",
                "case__taken_by",
                "case__ip_record",
            )
            .prefetch_related("case__evaluations")
            .order_by("created_at")
        )
        queryset = _apply_application_filters(queryset, request.query_params)
        rows = _filter_rows_by_result(_application_rows(queryset), request.query_params.get("result"))
        applications = [row["application"] for row in rows]
        cases = [row["case"] for row in rows if row["case"]]
        app_ids = [application.id for application in applications]
        case_ids = [case.id for case in cases]
        records = IPRecord.objects.filter(application_id__in=app_ids)

        today = timezone.localdate()
        response = _csv_response(f"portfolio_analytics_{today.isoformat()}.csv")
        writer = csv.writer(response)

        _write_section(writer, "REPORT METADATA")
        _write_key_values(
            writer,
            [
                ["Report title", "Portfolio Analytics Report"],
                ["System name", "The Creator's Bulwark"],
                ["Institution", "Palawan State University"],
                ["Generated by", _user_label(request.user)],
                ["Generated date and time", _datetime(timezone.now())],
            ],
        )

        _write_section(writer, "SELECTED FILTERS")
        _write_key_values(
            writer,
            _selected_filter_rows(
                request.query_params,
                [
                    ("IP Service", "ip_service"),
                    ("Year", "year"),
                    ("Status", "status"),
                    ("Result", "result"),
                    ("Date From", "date_from"),
                    ("Date To", "date_to"),
                ],
            ),
        )

        _write_section(writer, "SUMMARY STATISTICS")
        status_counts = {status: 0 for status in CASE_STATUS_LABELS}
        for case in cases:
            status_counts[case.status] = status_counts.get(case.status, 0) + 1
        _write_key_values(
            writer,
            [
                ["Total portfolio records", records.count()],
                ["Total applications", len(applications)],
                ["Pending cases", status_counts.get(Case.Status.PENDING, 0)],
                ["Under review cases", status_counts.get(Case.Status.UNDER_REVIEW, 0)],
                ["Evaluated cases", status_counts.get(Case.Status.EVALUATED, 0)],
                ["Ongoing cases", status_counts.get(Case.Status.ON_GOING, 0)],
                ["Certified cases", status_counts.get(Case.Status.CERTIFIED, 0)],
                ["Archived cases", status_counts.get(Case.Status.ARCHIVED, 0)],
            ],
        )

        _write_section(writer, "MONTHLY ANALYTICS")
        writer.writerow(["Month", "Total Records", "Total Applications", "Certified Records", "Pending Cases", "Under Review Cases", "Evaluated Cases", "Ongoing Cases"])
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        for index, month_name in enumerate(month_names, start=1):
            month_apps = [app for app in applications if app.created_at.month == index]
            month_cases = [case for case in cases if case.created_at.month == index]
            month_app_ids = [app.id for app in month_apps]
            writer.writerow(
                [
                    month_name,
                    records.filter(application_id__in=month_app_ids).count(),
                    len(month_apps),
                    records.filter(application_id__in=month_app_ids, is_certified=True).count(),
                    sum(1 for case in month_cases if case.status == Case.Status.PENDING),
                    sum(1 for case in month_cases if case.status == Case.Status.UNDER_REVIEW),
                    sum(1 for case in month_cases if case.status == Case.Status.EVALUATED),
                    sum(1 for case in month_cases if case.status == Case.Status.ON_GOING),
                ]
            )

        _write_section(writer, "IP TYPE BREAKDOWN")
        writer.writerow(["IP Type", "Count"])
        for value, label in IP_TYPE_LABELS.items():
            writer.writerow([label, sum(1 for app in applications if app.ip_type == value)])

        _write_section(writer, "STATUS BREAKDOWN")
        writer.writerow(["Status", "Count"])
        for value, label in APPLICATION_STATUS_LABELS.items():
            writer.writerow([label, sum(1 for app in applications if app.status == value)])
        for value, label in CASE_STATUS_LABELS.items():
            writer.writerow([label, sum(1 for case in cases if case.status == value)])

        _write_section(writer, "RESULT BREAKDOWN")
        writer.writerow(["Result", "Count"])
        for label in RESULT_LABELS:
            writer.writerow([label, sum(1 for row in rows if row["result"] == label)])

        _write_section(writer, "DETAILED RECORDS")
        writer.writerow(["Case Number", "Application Code", "Applicant Name", "IP Type", "Title", "Status", "Result", "Evaluator", "Submission Date", "Deadline", "Completed Date"])
        if not rows:
            writer.writerow(["No portfolio records available for the selected filters."])
        for row in rows:
            writer.writerow(
                [
                    _blank(row["case_number"]),
                    row["application_code"],
                    row["applicant_name"],
                    row["ip_type"],
                    row["title"],
                    row["status"],
                    row["result"],
                    row["evaluator"],
                    row["submission_date"],
                    row["deadline"],
                    row["completed_date"],
                ]
            )

        ReportExport.objects.create(generated_by=request.user, report_type="portfolio_analytics")
        return response

    @staticmethod
    def evaluator_case_report_csv(request):
        evaluator = request.user
        queryset = (
            Case.objects.filter(Q(assigned_evaluator=evaluator) | Q(taken_by=evaluator))
            .distinct()
            .select_related("application", "applicant", "assigned_evaluator", "taken_by")
            .prefetch_related("evaluations", "payments", "documents", "activity_timeline", "conversations__messages")
            .order_by("deadline", "-created_at")
        )
        queryset = _apply_case_filters(queryset, request.query_params)
        rows = _filter_rows_by_result(_evaluator_case_rows(queryset, evaluator), request.query_params.get("result"))
        cases = [row["case"] for row in rows]

        today = timezone.localdate()
        response = _csv_response(f"evaluator_case_report_{today.isoformat()}.csv")
        writer = csv.writer(response)

        _write_section(writer, "REPORT METADATA")
        _write_key_values(
            writer,
            [
                ["Report title", "Evaluator Case Report"],
                ["System name", "The Creator's Bulwark"],
                ["Institution", "Palawan State University"],
                ["Generated by", _user_label(evaluator)],
                ["Generated date and time", _datetime(timezone.now())],
            ],
        )

        _write_section(writer, "SELECTED FILTERS")
        _write_key_values(
            writer,
            _selected_filter_rows(
                request.query_params,
                [
                    ("Case Status", "case_status"),
                    ("IP Type", "ip_type"),
                    ("Deadline From", "deadline_from"),
                    ("Deadline To", "deadline_to"),
                    ("Priority", "priority"),
                    ("Result", "result"),
                    ("Date From", "date_from"),
                    ("Date To", "date_to"),
                ],
            ),
        )

        unread_message_total = 0
        message_rows = []
        for case in cases:
            unread_count, latest_message_date = _case_unread_applicant_messages(case)
            unread_message_total += unread_count
            if unread_count or latest_message_date:
                message_rows.append(
                    [
                        case.case_number,
                        _user_label(case.applicant),
                        unread_count,
                        _datetime(latest_message_date),
                    ]
                )

        deadline_counts = {
            "Overdue cases": 0,
            "Due today": 0,
            "Due within 1-3 days": 0,
            "Due within 4-7 days": 0,
            "Later deadlines": 0,
            "Cases with no deadline": 0,
        }
        for case in cases:
            deadline_counts[_deadline_status(case)] += 1

        _write_section(writer, "SUMMARY STATISTICS")
        _write_key_values(
            writer,
            [
                ["Total assigned cases", sum(1 for case in cases if case.assigned_evaluator_id == evaluator.id)],
                ["Total taken cases", sum(1 for case in cases if case.taken_by_id == evaluator.id)],
                ["Total pending cases", sum(1 for case in cases if case.status == Case.Status.PENDING)],
                ["Total under review cases", sum(1 for case in cases if case.status == Case.Status.UNDER_REVIEW)],
                ["Total evaluated cases", sum(1 for case in cases if case.status == Case.Status.EVALUATED)],
                ["Total ongoing cases", sum(1 for case in cases if case.status == Case.Status.ON_GOING)],
                ["Total certified cases", sum(1 for case in cases if case.status == Case.Status.CERTIFIED)],
                ["Total overdue cases", deadline_counts["Overdue cases"]],
                ["Total cases due soon", deadline_counts["Due within 1-3 days"] + deadline_counts["Due within 4-7 days"]],
                ["Total unread applicant messages", unread_message_total],
            ],
        )

        _write_section(writer, "DEADLINE SUMMARY")
        writer.writerow(["Deadline Bucket", "Count"])
        for label, count in deadline_counts.items():
            writer.writerow([label, count])

        _write_section(writer, "IP TYPE BREAKDOWN")
        writer.writerow(["IP Type", "Count"])
        for value, label in IP_TYPE_LABELS.items():
            writer.writerow([label, sum(1 for case in cases if case.application.ip_type == value)])

        _write_section(writer, "STATUS BREAKDOWN")
        writer.writerow(["Status", "Count"])
        for value, label in CASE_STATUS_LABELS.items():
            writer.writerow([label, sum(1 for case in cases if case.status == value)])

        _write_section(writer, "RESULT BREAKDOWN")
        writer.writerow(["Result", "Count"])
        for label in RESULT_LABELS:
            writer.writerow([label, sum(1 for row in rows if row["result"] == label)])

        _write_section(writer, "DETAILED EVALUATOR CASES")
        writer.writerow(
            [
                "Case Number",
                "Application Code",
                "Applicant Name",
                "IP Type",
                "Title",
                "Current Status",
                "Evaluation Result",
                "Priority",
                "Deadline",
                "Deadline Status",
                "Date Submitted",
                "Date Taken",
                "Last Updated",
                "Payment Receipt Status",
                "Document Status",
                "Latest Evaluator Action",
            ]
        )
        if not rows:
            writer.writerow(["No evaluator case records available for the selected filters."])
        for row in rows:
            writer.writerow(
                [
                    row["case_number"],
                    row["application_code"],
                    row["applicant_name"],
                    row["ip_type"],
                    row["title"],
                    row["status"],
                    row["result"],
                    row["priority"],
                    row["deadline"],
                    row["deadline_status"],
                    row["date_submitted"],
                    row["date_taken"],
                    row["last_updated"],
                    row["payment_receipt_status"],
                    row["document_status"],
                    row["latest_evaluator_action"],
                ]
            )

        _write_section(writer, "MESSAGE SUMMARY")
        writer.writerow(["Case Number", "Applicant Name", "Unread Message Count", "Last Message Date"])
        if not message_rows:
            writer.writerow(["No unread applicant message activity for the selected filters."])
        for message_row in message_rows:
            writer.writerow(message_row)

        ReportExport.objects.create(generated_by=evaluator, report_type="evaluator_case_report")
        return response
