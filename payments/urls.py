from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FeeAssessmentViewSet, PaymentViewSet


router = DefaultRouter()
router.register("assessments", FeeAssessmentViewSet, basename="fee-assessments")
router.register("", PaymentViewSet, basename="payments")

urlpatterns = [path("", include(router.urls))]
