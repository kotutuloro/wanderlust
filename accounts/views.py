"""
Views for the accounts app
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import AccountCreationForm


class SignUpView(CreateView):
    """
    View for account registration.
    """

    form_class = AccountCreationForm
    success_url = reverse_lazy("accounts:login")
    template_name = "registration/signup.html"
