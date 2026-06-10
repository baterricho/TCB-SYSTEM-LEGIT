from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet, MessageAttachmentViewSet


router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversations")
router.register("attachments", MessageAttachmentViewSet, basename="attachments")

urlpatterns = [path("", include(router.urls))]
