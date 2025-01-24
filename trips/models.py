"""
Models for the trips app.
"""

from nanoid import generate as generate_nanoid
from django.db import models
from django.conf import settings


def generate_random_slug():
    """Generates a 12 character nanoid"""
    return generate_nanoid(size=12)


class Trip(models.Model):
    """Representation of the trip table"""

    # primary key: id (auto set by django)
    slug = models.SlugField(default=generate_random_slug,
                            unique=True, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    scheduled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.title} ({self.slug})'


class Destination(models.Model):
    """Representation of the destination table"""
    # primary key: id (auto set by django)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.name} [from Trip: {self.trip}]'
