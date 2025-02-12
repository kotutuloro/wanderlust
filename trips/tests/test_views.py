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
        The IndexView renders the index template.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/index.html")


class LoginRequiredTestMixin():
    def test_not_logged_in(self):
        """
        A logged out user cannot access the path set as the instance's url.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse("accounts:login")}?next={self.url}")


class UserTripsViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("trips:profile")

        self.user = User.objects.create(username="myuser", password="testpw")
        self.client.force_login(self.user)

    def test_shows_trips(self):
        """
        A user's trips are displayed.
        """

        trip1 = Trip.objects.create(owner=self.user, title="my cool trip")
        trip2 = Trip.objects.create(owner=self.user, title="another trip")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/profile.html")
        self.assertQuerySetEqual(
            response.context["user_trip_list"], [trip1, trip2], ordered=False)
        self.assertContains(response, trip1.title)
        self.assertContains(response, trip2.title)

    def test_shows_no_trips(self):
        """
        No trips are shown if a user does not have any.
        """
        response = self.client.get(self.url)
        self.assertQuerySetEqual(response.context["user_trip_list"], [])
        self.assertContains(response, "No trips for you")

    def test_shows_trips_only_for_logged_in_user(self):
        """
        Only trips owned by the logged in user are shown.
        """
        user_trip = Trip.objects.create(owner=self.user, title="my cool trip")
        other_trip = Trip.objects.create(
            owner=User.objects.create(), title="someone else's trip")

        response = self.client.get(self.url)
        self.assertQuerySetEqual(
            response.context["user_trip_list"], [user_trip])
        self.assertContains(response, user_trip.title)
        self.assertNotContains(response, other_trip.title)

    def test_includes_creation_forms(self):
        """
        Context includes forms for creating a trip and creating a destination.
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context["create_trip_form"], TripForm)
        self.assertIsInstance(
            response.context["create_dest_form"], DestinationForm)


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
