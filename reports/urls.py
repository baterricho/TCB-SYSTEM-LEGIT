from django.urls import path

from .views import ReportView


urlpatterns = [
    path("<str:report_name>/", ReportView.as_view()),
]
