import datetime
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


class TripDetailViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(
            owner=self.owner, title="test trip", notes="This is my super cool trip")
        self.dest1 = Destination.objects.create(trip=self.trip, name="nasa")
        self.dest2 = Destination.objects.create(trip=self.trip, name="arena")

        self.url = reverse("trips:trip-detail",
                           kwargs={'slug': self.trip.slug})
        self.client.force_login(self.owner)

    def test_show_trip_details(self):
        """
        A trip's details and destinations are displayed.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertContains(response, self.trip.title)
        self.assertContains(response, self.trip.notes)
        self.assertContains(response, self.dest1.name)
        self.assertContains(response, self.dest2.name)

    def test_no_other_destinations(self):
        """
        Destinations for other trips are not displayed.
        """
        other_trip = Trip.objects.create(
            owner=self.owner, title="where is this")
        other_dest = Destination.objects.create(
            trip=other_trip, name="what is this")

        other_owner_trip = Trip.objects.create(
            owner=User.objects.create(), title="someone else")
        other_owner_dest = Destination.objects.create(
            trip=other_owner_trip, name="somewhere else")

        response = self.client.get(self.url)
        self.assertNotContains(response, other_dest.name)
        self.assertNotContains(response, other_owner_dest.name)

    def test_show_trip_details_only_for_owner(self):
        """
        A user cannot access details for someone else's trip.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        response = self.client.get(self.url)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)

    def test_includes_destination_creation_form(self):
        """
        Context includes form for creating a destination.
        """
        response = self.client.get(self.url)
        self.assertIsInstance(
            response.context["create_dest_form"], DestinationForm)


class CreateTripViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("trips:create-trip")

        self.user = User.objects.create(username="myuser", password="testpw")
        self.client.force_login(self.user)

    def test_create_trip_get(self):
        """
        Displays the trip creation form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_trip.html")
        self.assertIsInstance(response.context["form"], TripForm)

    def test_create_trip_post_valid_data(self):
        """
        Saves a trip creation and redirects on a valid POST request.
        """
        data = {
            "title": "my cool trip",
            "start_date": "2025-01-01",
            "notes": "this is my very cool trip",
        }
        response = self.client.post(self.url, data)
        trip = Trip.objects.first()
        self.assertEqual(trip.owner.username, self.user.username)
        self.assertEqual(trip.title, data["title"])
        self.assertEqual(trip.start_date, datetime.date(2025, 1, 1))
        self.assertEqual(trip.notes, data["notes"])
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': trip.slug}))

    def test_create_trip_post_invalid_data(self):
        """
        Does not save a trip creation on an invalid POST request.
        """

        data = {
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_trip.html")
        self.assertIsInstance(response.context["form"], TripForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")
        self.assertEqual(Trip.objects.count(), 0)


class CreateDestinationViewTests(TestCase):
    def setUp(self):
        self.url = reverse("trips:create-dest")


class CreateDestinationViewWithTripTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(owner=self.owner, title="test trip")
        self.url = reverse("trips:create-dest-with-trip",
                           kwargs={'slug': self.trip.slug})
