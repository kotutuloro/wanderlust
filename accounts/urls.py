"""
URL configuration for the accounts app.
"""

from django.urls import path, include, reverse_lazy
from django.views.generic.base import TemplateView
from django.contrib.auth import views as auth_views
from .views import SignUpView

app_name = "accounts"
urlpatterns = [
    path("password_change/", auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy("accounts:password_change_done"))),
    path("", include("django.contrib.auth.urls")),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("settings/", TemplateView.as_view(template_name="registration/settings.html"), name="settings"),
]
