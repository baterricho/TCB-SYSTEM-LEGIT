"""URL patterns for the applications app."""

from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("requirements/", views.IPRequirementListView.as_view(), name="requirement-list"),
    path("", views.IPApplicationListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", views.IPApplicationDetailView.as_view(), name="detail"),
    path("<uuid:pk>/submit/", views.SubmitApplicationView.as_view(), name="submit"),
    path("<uuid:pk>/assign/", views.AssignEvaluatorView.as_view(), name="assign"),
    path("<uuid:pk>/archive/", views.ArchiveApplicationView.as_view(), name="archive"),
    # Marketplace consent (applicant-controlled)
    path("<uuid:pk>/consent/", views.UpdateMarketplaceConsentView.as_view(), name="consent"),
    # Payment / proof of deposit
    path("<uuid:pk>/payments/", views.PaymentRecordListCreateView.as_view(), name="payment-list"),
    path(
        "<uuid:pk>/payments/<uuid:payment_pk>/verify/",
        views.VerifyPaymentRecordView.as_view(),
        name="payment-verify",
    ),
    # Documents
    path("<uuid:pk>/documents/", views.IPDocumentUploadView.as_view(), name="document-upload"),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/",
        views.IPDocumentDeleteView.as_view(),
        name="document-delete",
    ),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/stamp/",
        views.StampDocumentView.as_view(),
        name="document-stamp",
    ),
    # Co-inventors
    path("<uuid:pk>/coinventors/", views.CoInventorListCreateView.as_view(), name="coinventor-list"),
    path(
        "<uuid:pk>/coinventors/<uuid:coinventor_pk>/",
        views.CoInventorDeleteView.as_view(),
        name="coinventor-delete",
    ),
]
