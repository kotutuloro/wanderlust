"""
URL configuration for the accounts app.
"""

from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import SignUpView, AccountView, EditAccountView

app_name = "accounts"
urlpatterns = [
    path("password_change/", auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy("accounts:password_change_done"))),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("settings/", AccountView.as_view(), name="settings"),
    path("edit/", EditAccountView.as_view(), name="edit"),
    path("", include("django.contrib.auth.urls")),
]
