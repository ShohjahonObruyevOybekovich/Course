from django.urls import path
from .views import *

urlpatterns = [
    path('',UploadFileAPIView.as_view()),
    path('<uuid:pk>/',UploadDestroyAPIView.as_view()),

]