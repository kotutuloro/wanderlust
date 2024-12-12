"""
URL configuration for the accounts app.
"""

from django.urls import path, include
from django.views.generic.base import TemplateView
from .views import SignUpView

app_name = "accounts"
urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("settings/", TemplateView.as_view(template_name="registration/settings.html"), name="settings"),

]
