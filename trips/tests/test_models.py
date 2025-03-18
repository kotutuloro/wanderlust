from django.test import TestCase

from ..models import Trip, Destination
from accounts.models import User


class TripModelTests(TestCase):
    def test_trip_creation(self):
        """
        Creating a new trip works as expected
        """
        user = User.objects.create(username="my-user")
        trip = Trip.objects.create(
            owner=user, title="test trip", start_date="2025-01-01")
        self.assertIsNotNone(trip.slug)
        self.assertIs(trip.owner, user)
        self.assertEqual(trip.title, "test trip")
        self.assertEqual(trip.start_date, "2025-01-01")
        self.assertIsNone(trip.end_date)
        self.assertIs(trip.scheduled, False)

    def test_get_absolute_url(self):
        """
        get_absolute_url() returns a url for a trip using its slug attribute.
        """
        trip = Trip.objects.create(owner=User.objects.create(), title="test")
        self.assertEqual(trip.get_absolute_url(), f'/trip/{trip.slug}/')

    def test_get_absolute_url_with_custom_slug(self):
        """
        get_absolute_url() uses the trip's custom slug.
        """

        slug = "my-cool-slug"
        trip = Trip.objects.create(
            slug=slug, owner=User.objects.create(), title="test")
        self.assertEqual(trip.get_absolute_url(), f'/trip/{slug}/')


class DestinationModelTests(TestCase):
    def test_destination_creation(self):
        """
        Creating a new destination works as expected
        """
        trip = Trip.objects.create(owner=User.objects.create(), title="trip")
        dest = Destination.objects.create(
            trip=trip, name="test dest", mapbox_id="address.12345678910", start_time="2025-01-01 12:01Z")
        self.assertEqual(dest.name, "test dest")
        self.assertIs(dest.trip, trip)
        self.assertEqual(dest.mapbox_id, "address.12345678910")
        self.assertEqual(dest.start_time, "2025-01-01 12:01Z")
        self.assertIsNone(dest.end_time)
