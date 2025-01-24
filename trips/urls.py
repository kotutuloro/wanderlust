"""
URL configuration for the trips app.
"""

from django.urls import path
from . import views

app_name = "trips"
urlpatterns = [
    path("", views.index, name="index"),
]
