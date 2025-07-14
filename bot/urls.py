from django.urls import path
from .views import LeadCreateView, LandingPageView, telegram_webhook

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("leads/", LeadCreateView.as_view(), name="lead-create"),
    path("webhook/",telegram_webhook),
]
