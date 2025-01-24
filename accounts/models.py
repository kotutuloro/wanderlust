"""
Models for the accounts app.
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Representation of the custom User table"""
    pass
    # add additional fields in here
