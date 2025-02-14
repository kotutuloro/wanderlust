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


class CreateDestinationViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("trips:create-dest")

        self.user = User.objects.create(username="myuser", password="testpw")
        self.client.force_login(self.user)

    def test_create_destination_get(self):
        """
        Displays the destination creation form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)

    def test_form_trip_displays_limited_to_user(self):
        """
        Only displays trip options owned by user in form on GET.
        """
        trip1 = Trip.objects.create(owner=self.user, title="my cool trip")
        trip2 = Trip.objects.create(owner=self.user, title="another trip")
        other_trip = Trip.objects.create(
            owner=User.objects.create(), title="someone else's trip")

        response = self.client.get(self.url)
        trip_choices = response.context["form"].fields["trip"]
        self.assertQuerySetEqual(trip_choices.queryset,
                                 [trip1, trip2], ordered=False)
        self.assertContains(response, trip1.title)
        self.assertContains(response, trip2.title)
        self.assertNotContains(response, other_trip.title)

    def test_create_destination_post_with_trip(self):
        """
        Saves a destination creation and redirects on a valid POST request.
        """
        trip = Trip.objects.create(owner=self.user, title="my cool trip")
        data = {
            "trip": trip.pk,
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }

        response = self.client.post(self.url, data)
        dest = Destination.objects.first()
        self.assertEqual(dest.name, data["name"])
        self.assertEqual(dest.start_time, datetime.datetime(
            2025, 1, 1, 12, 1, tzinfo=datetime.timezone.utc))
        self.assertEqual(dest.trip.pk, trip.pk)
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': trip.slug}))

    def test_create_destination_post_without_trip(self):
        """
        Saves a destination creation and creates a new trip if blank
        and redirects on a valid POST request.
        """
        data = {
            "trip": '',
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }
        response = self.client.post(self.url, data)
        dest = Destination.objects.first()
        self.assertEqual(dest.name, data["name"])
        self.assertEqual(dest.start_time, datetime.datetime(
            2025, 1, 1, 12, 1, tzinfo=datetime.timezone.utc))
        self.assertEqual(dest.trip.title, data["name"])
        self.assertEqual(dest.trip.owner.username, self.user.username)
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': dest.trip.slug}))

    def test_create_destination_post_invalid_data(self):
        """
        Does not save a destination creation on an invalid POST request.
        """

        data = {
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")
        self.assertEqual(Destination.objects.count(), 0)

    def test_create_destination_post_unowned_trip(self):
        """
        Does not accept trips that are not owned by user on POST.
        """
        other_trip = Trip.objects.create(
            owner=User.objects.create(), title="someone else's trip")
        data = {
            "trip": other_trip.pk,
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "Select a valid choice.")
        self.assertEqual(Destination.objects.count(), 0)


class CreateDestinationViewWithTripTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(owner=self.user, title="test trip")
        self.url = reverse("trips:create-dest-with-trip",
                           kwargs={'trip_slug': self.trip.slug})

        self.client.force_login(self.user)

    def test_create_destination_with_trip_get(self):
        """
        Displays the destination creation form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)

    def test_create_destination_with_nonexistant_trip_get(self):
        """
        Returns 404 if the trip slug in url does not exist on GET.
        """
        self.trip.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_create_destination_with_unowned_trip_get(self):
        """
        Returns 403 if the trip slug in url does not belong to owner on GET.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        response = self.client.get(self.url)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)

    def test_form_trip_displays_limited_to_trip(self):
        """
        Only displays url trip as trip option in form on GET.
        """
        other_trip = Trip.objects.create(
            owner=self.user, title="some other trip")

        response = self.client.get(self.url)
        trip_choices = response.context["form"].fields["trip"]
        self.assertQuerySetEqual(trip_choices.queryset, [self.trip])
        self.assertContains(response, self.trip.title)
        self.assertNotContains(response, other_trip.title)

    def test_create_destination_with_trip_post_valid_data(self):
        """
        Saves a destination creation and redirects on a valid POST request.
        """
        data = {
            "trip": self.trip.pk,
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }

        response = self.client.post(self.url, data)
        dest = Destination.objects.first()
        self.assertEqual(dest.name, data["name"])
        self.assertEqual(dest.start_time, datetime.datetime(
            2025, 1, 1, 12, 1, tzinfo=datetime.timezone.utc))
        self.assertEqual(dest.trip.pk, self.trip.pk)
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': self.trip.slug}))

    def test_create_destination_with_trip_post_invalid_data(self):
        """
        Does not save a destination creation on an invalid POST request.
        """
        data = {
            "trip": self.trip.pk,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")
        self.assertEqual(Destination.objects.count(), 0)

    def test_create_destination_with_trip_post_unrelated_trip(self):
        """
        Does not accept trips that are not in the url on POST.
        """
        other_trip = Trip.objects.create(
            owner=self.user, title="some other trip")
        data = {
            "trip": other_trip.pk,
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/create_destination.html")
        self.assertIsInstance(response.context["form"], DestinationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "Select a valid choice.")
        self.assertEqual(Destination.objects.count(), 0)

    def test_create_destination_with_trip_post_unowned(self):
        """
        Does not accept trips that are not owned by the user on POST.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)
        data = {
            "trip": self.trip.pk,
            "name": "nasa",
            "start_time": "2025-01-01 12:01Z",
        }

        response = self.client.post(self.url, data)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)
        self.assertEqual(Destination.objects.count(), 0)
