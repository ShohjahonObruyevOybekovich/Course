from django.urls import path

from course.views import OpenMiniAppLinkView

urlpatterns = [
    path("", OpenMiniAppLinkView.as_view()),
]