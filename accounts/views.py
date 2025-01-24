"""
Views for the accounts app
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from .forms import AccountCreationForm
from .models import User


class SignUpView(CreateView):
    """View for account registration."""
    form_class = AccountCreationForm
    success_url = reverse_lazy("accounts:login")
    template_name = "registration/signup.html"


class AccountView(DetailView):
    """View for account details."""
    model = User
    template_name = "registration/user_detail.html"

    def get_object(self, queryset=...):
        return self.request.user
