"""
Views for the trips app.
"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse

from .models import Trip, Destination
from .forms import TripForm, DestinationForm


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_dest_form"] = DestinationForm(only_trip=self.object)
        return context


class CreateTripView(LoginRequiredMixin, CreateView):
    """View for creating a new trip."""

    template_name = "trips/create_trip.html"
    form_class = TripForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CreateDestinationView(UserPassesTestMixin, CreateView):
    """View for creating a new destination."""

    template_name = "trips/create_destination.html"
    form_class = DestinationForm
    permission_denied_message = "You don't have access to this trip."

    def setup(self, request, *args, **kwargs):
        trip_slug = kwargs.get("trip_slug")
        if trip_slug:
            trip = get_object_or_404(Trip, slug=trip_slug)
            self.trip = trip

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        if self.trip:
            return self.request.user == self.trip.owner
        return True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.trip:
            kwargs["only_trip"] = self.trip
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("trips:trip-detail", args=[self.object.trip.slug])
