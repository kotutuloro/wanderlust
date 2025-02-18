"""
URL configuration for the accounts app.
"""

from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"
urlpatterns = [
    path("password_change/", auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy("accounts:password_change_done"))),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("settings/", views.AccountView.as_view(), name="settings"),
    path("edit/", views.EditAccountView.as_view(), name="edit"),
    path("delete/", views.DeleteAccountView.as_view(), name="delete"),
    path("", include("django.contrib.auth.urls")),
]
