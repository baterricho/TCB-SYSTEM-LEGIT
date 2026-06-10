from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView


def service_worker(request):
    response = HttpResponse(
        """
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});
""".strip(),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-store"
    return response


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="landing_page"),
    path("service-worker.js", service_worker, name="service_worker"),
    path("login/", TemplateView.as_view(template_name="index.html"), name="applicant_login"),
    path("admin-login/", TemplateView.as_view(template_name="index.html"), name="admin_login"),
    path("evaluator-login/", TemplateView.as_view(template_name="index.html"), name="evaluator_login"),
    path("applicant/dashboard/", TemplateView.as_view(template_name="index.html"), name="applicant_dashboard"),
    path("admin/dashboard/", TemplateView.as_view(template_name="index.html"), name="admin_dashboard"),
    path("evaluator/dashboard/", TemplateView.as_view(template_name="index.html"), name="evaluator_dashboard"),
    path("evaluator/my-cases/", TemplateView.as_view(template_name="index.html"), name="evaluator_my_cases"),
    path("index.html", TemplateView.as_view(template_name="index.html"), name="frontend_index_compat"),
    path("main/index.html", TemplateView.as_view(template_name="index.html"), name="frontend_main_index_compat"),
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    path("api/v1/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
