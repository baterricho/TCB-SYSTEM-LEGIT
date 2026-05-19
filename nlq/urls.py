from django.urls import path

from .views import NLQProcessView


urlpatterns = [
    path("process/", NLQProcessView.as_view()),
]
