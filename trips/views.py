"""
Views for the trips app.
"""

import os
import requests
from http import HTTPStatus
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Avg

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_trip_form"] = TripForm()
        context["create_dest_form"] = DestinationForm(user=self.request.user)
        context["mapbox_api_key"] = os.getenv("MAPBOX_ACCESS_TOKEN")
        mapbox_trips = self.request.user.trip_set.annotate(avg_latitude=Avg('destination__latitude'), avg_longitude=Avg(
            'destination__longitude')).exclude(avg_latitude=None).exclude(avg_longitude=None)
        context["mapbox_trips"] = [{
            'title': trip.title,
            'avg_latitude': trip.avg_latitude,
            'avg_longitude': trip.avg_longitude,
            'link': trip.get_absolute_url(),
        } for trip in mapbox_trips]
        return context

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
        mapbox_dests = self.object.destination_set.exclude(longitude=None).exclude(
            latitude=None).values('name', 'latitude', 'longitude')
        context["mapbox_destinations"] = list(mapbox_dests)
        context["mapbox_api_key"] = os.getenv("MAPBOX_ACCESS_TOKEN")
        return context


class CreateTripView(LoginRequiredMixin, CreateView):
    """View for creating a new trip."""

    template_name = "trips/create_trip.html"
    form_class = TripForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class EditTripView(UserPassesTestMixin, UpdateView):
    """View for updating a trip."""
    template_name_suffix = "_update_form"
    model = Trip
    form_class = TripForm
    permission_denied_message = "You don't have access to this trip."

    def test_func(self):
        return self.request.user == self.get_object().owner


class DeleteTripView(UserPassesTestMixin, DeleteView):
    """View for deleting a trip."""
    model = Trip
    success_url = reverse_lazy("trips:profile")
    permission_denied_message = "You don't have access to this trip."

    def test_func(self):
        return self.request.user == self.get_object().owner


class CreateDestinationView(UserPassesTestMixin, CreateView):
    """View for creating a new destination."""

    template_name = "trips/create_destination.html"
    form_class = DestinationForm
    permission_denied_message = "You don't have access to this trip."

    def setup(self, request, *args, **kwargs):
        self.trip = None
        trip_slug = kwargs.get("trip_slug")
        if trip_slug:
            self.trip = get_object_or_404(Trip, slug=trip_slug)

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        if self.trip:
            return self.request.user == self.trip.owner
        return self.request.user.is_authenticated

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.trip:
            kwargs["only_trip"] = self.trip
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("trips:trip-detail", args=[self.object.trip.slug])


class EditDestinationView(UserPassesTestMixin, UpdateView):
    """View for deleting a destination."""
    model = Destination
    form_class = DestinationForm
    template_name_suffix = "_update_form"
    permission_denied_message = "You don't have access to this trip."

    def setup(self, request, *args, **kwargs):
        trip_slug = kwargs.get("trip_slug")
        dest_pk = kwargs.get("pk")
        trip = get_object_or_404(Trip, slug=trip_slug)
        get_object_or_404(Destination, trip=trip, pk=dest_pk)

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        return self.request.user == self.get_object().trip.owner

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("trips:trip-detail", args=[self.object.trip.slug])


class DeleteDestinationView(UserPassesTestMixin, DeleteView):
    """View for deleting a destination."""
    model = Destination
    permission_denied_message = "You don't have access to this trip."

    def setup(self, request, *args, **kwargs):
        trip_slug = kwargs.get("trip_slug")
        dest_pk = kwargs.get("pk")
        trip = get_object_or_404(Trip, slug=trip_slug)
        get_object_or_404(Destination, trip=trip, pk=dest_pk)

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        return self.request.user == self.get_object().trip.owner

    def get_success_url(self):
        return reverse("trips:trip-detail", args=[self.object.trip.slug])


class SearchLocationView(LoginRequiredMixin, View):
    """View for searching a location with Mapbox."""

    def post(self, request, *args, **kwargs):
        q = request.POST.get("location")
        if not q:
            return HttpResponseBadRequest("Missing search query")

        mapbox_access_token = os.environ["MAPBOX_ACCESS_TOKEN"]
        params = {
            "q": q,
            "access_token": mapbox_access_token,
            "auto_complete": "true",
        }
        response = requests.get(
            "https://api.mapbox.com/search/searchbox/v1/forward", params=params)

        if not response.ok:
            err = str({
                "reason": response.reason,
                "response": response.json()
            })
            return HttpResponse(err, status=HTTPStatus.BAD_GATEWAY)

        results = []
        for feature in response.json()["features"]:
            props = feature["properties"]
            coords = props["coordinates"]
            results.append({
                "name": props["name"],
                "place": props.get("place_formatted"),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            })

        return render(request, "trips/location_search_results_snippet.html", {"locations": results})
