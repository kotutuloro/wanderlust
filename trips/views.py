"""
Views for the trips app.
"""

from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin


def index(request):
    """
    Render the app's homepage.
    """

    return render(request, "trips/index.html")


class UserTripsView(LoginRequiredMixin, ListView):
    """View for trips for a logged-in user."""
    pass


class GetTripView(LoginRequiredMixin, DetailView):
    """View for single trip details."""
    pass


class CreateTripView(LoginRequiredMixin, CreateView):
    """View for creating a new trip."""
    pass


class CreateDestinationView(LoginRequiredMixin, CreateView):
    """View for creating a new destination."""
    pass
