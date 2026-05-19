from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin

from .serializers import NLQProcessSerializer
from .services import NLQService


class NLQProcessView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = NLQProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(NLQService.process(serializer.validated_data["query"], request.user))
