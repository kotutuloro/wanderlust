"""
URL configuration for the trips app.
"""

from django.urls import path
from . import views

app_name = "trips"
urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", views.UserTripsView.as_view(), name="profile"),
    path("trip/new/", views.CreateTripView.as_view(), name="create-trip"),
    path("trip/<slug:slug>/", views.TripDetailView.as_view(), name="trip-detail"),
    path("trip/<slug:slug>/delete/",
         views.DeleteTripView.as_view(), name="delete-trip"),
    path("destination/new/", views.CreateDestinationView.as_view(), name="create-dest"),
    path("trip/<slug:trip_slug>/destination/new/",
         views.CreateDestinationView.as_view(), name="create-dest-with-trip"),
    path("trip/<slug:trip_slug>/destination/<int:pk>/delete/",
         views.DeleteDestinationView.as_view(), name="delete-dest"),
]
