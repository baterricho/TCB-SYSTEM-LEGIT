from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IPApplicationViewSet


router = DefaultRouter()
router.register("", IPApplicationViewSet, basename="applications")

urlpatterns = [path("", include(router.urls))]
