class DeprecateUnversionedApiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if it starts with /api/ but not /api/v1/
        if request.path.startswith("/api/") and not request.path.startswith("/api/v1/"):
            response["Deprecation"] = "true"
            response["Sunset"] = "2026-09-01"  # 90-day window
        return response
