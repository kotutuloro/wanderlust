"""
Views for the trips app.
"""

from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Trip, Destination


def index(request):
    """
    Render the app's homepage.
    """

    return render(request, "trips/index.html")


class UserTripsView(LoginRequiredMixin, ListView):
    """View for trips for a logged-in user."""
    context_object_name = "user_trip_list"
    template_name = "trips/profile.html"

    def get_queryset(self):
        return self.request.user.trip_set.all()


class TripDetailView(UserPassesTestMixin, DetailView):
    """View for single trip details."""
    model = Trip
    permission_denied_message = "You don't have access to this trip."

    def test_func(self):
        return self.request.user == self.get_object().owner


class CreateTripView(LoginRequiredMixin, CreateView):
    """View for creating a new trip."""
    pass


class CreateDestinationView(LoginRequiredMixin, CreateView):
    """View for creating a new destination."""
    pass
