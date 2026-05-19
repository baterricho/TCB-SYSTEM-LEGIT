from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CaseViewSet


router = DefaultRouter()
router.register("", CaseViewSet, basename="cases")

urlpatterns = [path("", include(router.urls))]
