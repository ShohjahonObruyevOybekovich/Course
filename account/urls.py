from django.urls import path
from .views import *

urlpatterns = [
    path('token', JWTtokenGenerator.as_view(), name='auth'),
    path('refresh', JWTtokenRefresh.as_view(), name='refresh'),
    path('me', Me.as_view(), name='me'),
]