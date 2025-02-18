"""
Views for the accounts app
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from .forms import AccountCreationForm, AccountForm
from .models import User


class SignUpView(CreateView):
    """View for account registration."""
    form_class = AccountCreationForm
    success_url = reverse_lazy("accounts:login")
    template_name = "registration/signup.html"


class AccountView(LoginRequiredMixin, DetailView):
    """View for account details."""
    model = User
    template_name = "registration/user_detail.html"

    def get_object(self, queryset=...):
        return self.request.user


class EditAccountView(LoginRequiredMixin, UpdateView):
    """View for editing account details."""
    model = User
    form_class = AccountForm
    template_name = "registration/user_update_form.html"
    success_url = reverse_lazy("accounts:settings")

    def get_object(self, queryset=...):
        return self.request.user


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    """View for deleting account."""
    model = User
    template_name = "registration/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:login")

    def get_object(self, queryset=...):
        return self.request.user
