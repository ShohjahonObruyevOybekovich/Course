from django.urls import path
from .views import LeadCreateView, LandingPageView

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("leads/", LeadCreateView.as_view(), name="lead-create"),
]
