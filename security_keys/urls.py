from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EncryptionKeyViewSet


router = DefaultRouter()
router.register("", EncryptionKeyViewSet, basename="security-keys")

urlpatterns = [path("", include(router.urls))]
