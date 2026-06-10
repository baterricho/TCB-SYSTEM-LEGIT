from django.urls import path

from .views import PortfolioAnalyticsExportView, ReportView


urlpatterns = [
    path("portfolio-analytics/export/", PortfolioAnalyticsExportView.as_view(), name="portfolio-analytics-export"),
    path("<str:report_name>/", ReportView.as_view()),
]
