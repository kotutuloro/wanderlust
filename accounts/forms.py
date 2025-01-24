# accounts/forms.py
"""
Forms for the accounts app.
"""
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import User


class AccountCreationForm(UserCreationForm):
    """Custom user creation form."""
    class Meta:
        """Custom user creation form data."""
        model = User
        fields = ("username", "email", "first_name")


class AccountForm(ModelForm):
    """Custom user model form."""
    class Meta:
        """Custom user model form data."""
        model = User
        fields = ("username", "email", "first_name")
