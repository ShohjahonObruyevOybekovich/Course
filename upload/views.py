from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated

from .models import File
from .serializers import FileUploadSerializer


class UploadFileAPIView(ListCreateAPIView):

    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()


class UploadDestroyAPIView(DestroyAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
