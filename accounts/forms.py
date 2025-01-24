# accounts/forms.py
"""
Forms for the accounts app.
"""
from django.contrib.auth.forms import UserCreationForm
from .models import User


class AccountCreationForm(UserCreationForm):
    """Custom user creation form."""

    class Meta:
        """Cusstom user creation form data."""
        model = User
        fields = ("username", "email", "first_name")
