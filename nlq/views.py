from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import create_audit_log
from core.permissions import IsAdmin

from .serializers import NLQProcessSerializer
from .services import NLQService


class NLQProcessView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = NLQProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = NLQService.process(serializer.validated_data["query"], request.user)
        create_audit_log(
            request,
            request.user,
            "nlq.processed",
            "NLQ query",
            "Admin processed NLQ query.",
            target="nlq",
        )
        return Response(response)
