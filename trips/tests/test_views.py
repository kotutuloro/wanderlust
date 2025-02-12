from django.test import TestCase
from django.urls import reverse

from ..models import Trip, Destination
from ..forms import TripForm, DestinationForm
from accounts.models import User


class IndexViewTests(TestCase):
    def setUp(self):
        self.url = reverse("trips:index")

    def test_index_view_get(self):
        """
        Test that the IndexView renders the index template.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/index.html")


class UserTripsViewTests(TestCase):
    def setUp(self):
        self.url = reverse("trips:profile")


class TripDetailViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(owner=self.owner, title="test trip")
        self.url = reverse("trips:trip-detail",
                           kwargs={'slug': self.trip.slug})


class CreateTripViewTests(TestCase):
    def setUp(self):
        self.url = reverse("trips:create-trip")


class CreateDestinationViewTests(TestCase):
    def setUp(self):
        self.url = reverse("trips:create-dest")


class CreateDestinationViewWithTripTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(owner=self.owner, title="test trip")
        self.url = reverse("trips:create-dest-with-trip",
                           kwargs={'slug': self.trip.slug})
