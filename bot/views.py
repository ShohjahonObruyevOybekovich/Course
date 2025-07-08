from django.views.generic import TemplateView

class LandingPageView(TemplateView):
    template_name = "index.html"



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LeadSerializer

class LeadCreateView(APIView):
    def post(self, request):
        serializer = LeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
