import json
import datetime
from unittest import mock
from django.test import TestCase
from django.urls import reverse
from requests import Response as r_Response

from ..models import Trip, Destination
from ..forms import TripForm, DestinationForm
from accounts.models import User


def get_sample_file(name):
    import os
    test_dir = os.path.dirname(__file__)
    return os.path.join(test_dir, "sample", name)


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
    def test_not_logged_in(self, *args, **kwargs):
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
        self.user = User.objects.create(username="myuser")
        self.trip = Trip.objects.create(
            owner=self.user, title="test trip", notes="This is my super cool trip")
        self.dest1 = Destination.objects.create(trip=self.trip, name="nasa")
        self.dest2 = Destination.objects.create(trip=self.trip, name="arena")

        self.url = reverse("trips:trip-detail",
                           kwargs={'slug': self.trip.slug})
        self.client.force_login(self.user)

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
            owner=self.user, title="where is this")
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


class EditTripViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create(username="myuser", password="testpw")
        self.trip = Trip.objects.create(
            owner=self.user, title="test trip", notes="This is my super cool trip")
        self.url = reverse("trips:edit-trip",
                           kwargs={'slug': self.trip.slug})

        self.client.force_login(self.user)

    def test_edit_trip_get(self):
        """
        Displays the trip update form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/trip_update_form.html")
        self.assertIsInstance(response.context["form"], TripForm)

    def test_edit_trip_post_valid_data(self):
        """
        Saves a trip update and redirects on a valid POST request.
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

    def test_edit_trip_post_invalid_data(self):
        """
        Does not save a trip update on an invalid POST request.
        """
        prev_title = self.trip.title

        data = {
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/trip_update_form.html")
        self.assertIsInstance(response.context["form"], TripForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")
        self.assertEqual(Trip.objects.first().title, prev_title)

    def test_edit_trip_only_for_owner(self):
        """
        Does not allow non-owners to update trips.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        response = self.client.get(self.url)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)

        prev_title = self.trip.title
        data = {
            "title": "my cool trip",
            "start_date": "2025-01-01",
            "notes": "this is my very cool trip",
        }
        response = self.client.post(self.url, data)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)
        self.assertEqual(Trip.objects.first().title, prev_title)


class DeleteTripViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create(username="myuser", password="testpw")
        self.trip = Trip.objects.create(
            owner=self.user, title="test trip", notes="This is my super cool trip")
        self.url = reverse("trips:delete-trip",
                           kwargs={'slug': self.trip.slug})

        self.client.force_login(self.user)

    def test_get_trip_delete_form(self):
        """
        Displays a form to delete a trip.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/trip_confirm_delete.html")
        self.assertContains(response, self.trip.title)

    def test_get_trip_delete_only_for_owner(self):
        """
        Only allows owners to access the trip delete form.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        response = self.client.get(self.url)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)

    def test_post_trip_delete_valid_data(self):
        """
        Deletes a trip and redirects on a valid POST request.
        """
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("trips:profile"))
        self.assertEqual(Trip.objects.count(), 0)

    def test_post_trip_delete_only_for_owner(self):
        """
        Does not allow non-owners to delete trips.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        response = self.client.post(self.url)
        self.assertContains(
            response, "You don't have access to this trip.", status_code=403, html=True)
        self.assertEqual(Trip.objects.filter(pk=self.trip.pk).count(), 1)


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


class EditDestinationViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create(username="myuser", password="testpw")
        self.trip = Trip.objects.create(
            owner=self.user, title="test trip", notes="This is my super cool trip")
        self.dest = Destination.objects.create(trip=self.trip, name="nasa")

        self.update_data = {
            "trip": self.trip.pk,
            "name": "new name",
            "start_time": "2025-01-01 12:01Z",
        }
        self.url = reverse("trips:edit-dest",
                           kwargs={'trip_slug': self.trip.slug, 'pk': self.dest.pk})
        self.client.force_login(self.user)

    def test_get_destination_edit_form(self):
        """
        Displays the destination update form.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/destination_update_form.html")
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
                                 [trip1, trip2, self.trip], ordered=False)
        self.assertContains(response, trip1.title)
        self.assertContains(response, trip2.title)
        self.assertContains(response, self.trip.title)
        self.assertNotContains(response, other_trip.title)

    def test_post_destination_edit_valid_data(self):
        """
        Saves a destination update and redirects on a valid POST request.
        """
        response = self.client.post(self.url, self.update_data)
        dest = Destination.objects.get(pk=self.dest.pk)
        self.assertEqual(dest.name, self.update_data["name"])
        self.assertEqual(dest.start_time, datetime.datetime(
            2025, 1, 1, 12, 1, tzinfo=datetime.timezone.utc))
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': self.trip.slug}))

    def test_post_destination_edit_invalid_data(self):
        """
        Does not save a destination update on an invalid POST request.
        """
        prev_name = self.dest.name
        data = {
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "trips/destination_update_form.html")
        self.assertIsInstance(response.context["form"], DestinationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")

        dest = Destination.objects.get(pk=self.dest.pk)
        self.assertEqual(dest.name, prev_name)

    def test_destination_edit_only_for_owner(self):
        """
        Only allows trip owners to edit the destination.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)
        prev_name = self.dest.name

        get_response = self.client.get(self.url)
        self.assertContains(
            get_response, "You don't have access to this trip.", status_code=403, html=True)

        post_response = self.client.post(self.url, self.update_data)
        self.assertContains(
            post_response, "You don't have access to this trip.", status_code=403, html=True)
        dest = Destination.objects.get(pk=self.dest.pk)
        self.assertEqual(dest.name, prev_name)

    def test_destination_edit_nonexistant(self):
        """
        Returns 404 if the destination does not exist.
        """
        self.dest.delete()

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        post_response = self.client.post(self.url, self.update_data)
        self.assertEqual(post_response.status_code, 404)

    def test_destination_edit_with_nonexistant_trip(self):
        """
        Returns 404 if the trip slug in url does not exist.
        """
        prev_name = self.dest.name
        self.url = reverse("trips:edit-dest",
                           kwargs={'trip_slug': "asfghjk", 'pk': self.dest.pk})

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        post_response = self.client.post(self.url, self.update_data)
        self.assertEqual(post_response.status_code, 404)
        dest = Destination.objects.get(pk=self.dest.pk)
        self.assertEqual(dest.name, prev_name)

    def test_destination_edit_with_wrong_trip(self):
        """
        Returns 404 if the trip slug does not match the destination's trip.
        """
        prev_name = self.dest.name
        other_trip = Trip.objects.create(owner=self.user, title="another one")
        self.dest.trip = other_trip
        self.dest.save()

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        self.update_data["trip"] = other_trip.pk
        post_response = self.client.post(self.url, self.update_data)
        self.assertEqual(post_response.status_code, 404)
        dest = Destination.objects.get(pk=self.dest.pk)
        self.assertEqual(dest.name, prev_name)


class DeleteDestinationViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create(username="myuser", password="testpw")
        self.trip = Trip.objects.create(
            owner=self.user, title="test trip", notes="This is my super cool trip")
        self.dest = Destination.objects.create(trip=self.trip, name="nasa")

        self.url = reverse("trips:delete-dest",
                           kwargs={'trip_slug': self.trip.slug, 'pk': self.dest.pk})
        self.client.force_login(self.user)

    def test_get_destination_delete_form(self):
        """
        Displays a form to delete a destination.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "trips/destination_confirm_delete.html")
        self.assertContains(response, self.dest.name)
        self.assertContains(response, self.trip.title)

    def test_post_destination_delete_valid_data(self):
        """
        Deletes a destination and redirects on a valid POST request.
        """
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse(
            "trips:trip-detail", kwargs={'slug': self.trip.slug}))
        self.assertEqual(Destination.objects.count(), 0)

    def test_destination_delete_only_for_owner(self):
        """
        Only allows trip owners to access the destination delete form.
        """
        other_user = User.objects.create()
        self.client.force_login(other_user)

        get_response = self.client.get(self.url)
        self.assertContains(
            get_response, "You don't have access to this trip.", status_code=403, html=True)

        post_response = self.client.post(self.url)
        self.assertContains(
            post_response, "You don't have access to this trip.", status_code=403, html=True)
        self.assertEqual(Destination.objects.filter(
            pk=self.dest.pk).count(), 1)

    def test_destination_delete_nonexistant(self):
        """
        Returns 404 if the destination does not exist.
        """
        self.dest.delete()

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        post_response = self.client.post(self.url)
        self.assertEqual(post_response.status_code, 404)

    def test_destination_delete_with_nonexistant_trip(self):
        """
        Returns 404 if the trip slug in url does not exist.
        """
        self.url = reverse("trips:delete-dest",
                           kwargs={'trip_slug': "asfghjk", 'pk': self.dest.pk})

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        post_response = self.client.post(self.url)
        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(Destination.objects.filter(
            pk=self.dest.pk).count(), 1)

    def test_destination_delete_with_wrong_trip(self):
        """
        Returns 404 if the trip slug does not match the destination's trip.
        """
        other_trip = Trip.objects.create(owner=self.user, title="another one")
        self.dest.trip = other_trip
        self.dest.save()

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 404)

        post_response = self.client.post(self.url)
        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(Destination.objects.filter(
            pk=self.dest.pk).count(), 1)


@mock.patch("trips.views.requests", spec=True)
class SearchLocationViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("trips:search-loc")

        self.mapbox_access_token = "my-cool-mapbox-api-token"
        self.mapbox_url = "https://api.mapbox.com/search/geocode/v6/forward"

        self.user = User.objects.create(username="myuser", password="testpw")
        self.client.force_login(self.user)

        self.mock_env = mock.patch.dict(
            "os.environ", {"MAPBOX_ACCESS_TOKEN": self.mapbox_access_token})
        self.mock_env.start()

    def tearDown(self):
        self.mock_env.stop()
        return super().tearDown()

    def test_responds_to_search(self, mock_requests):
        """
        Calls the external api and returns a modified version of the response.
        """
        ext_response = r_Response()
        ext_response.status_code = 200
        ext_response.json = mock.MagicMock()
        with open(get_sample_file("mapbox_geocode_response.json")) as f:
            ext_response.json.return_value = json.load(f)
        mock_requests.get.return_value = ext_response

        search_text = "nemo"
        response = self.client.get(self.url, query_params={
                                   "query": search_text})

        self.assertEqual(response.status_code, 200)

        mapbox_params = {
            "access_token": self.mapbox_access_token,
            "q": search_text,
        }
        mock_requests.get.assert_called_once_with(
            self.mapbox_url, params=mapbox_params)

        expected = {
            "results": [
                {
                    "mapbox_id": "address.1255672540378118",
                    "name": "Nemobrug",
                    "place": "1011 VX Amsterdam, Netherlands"
                }, {
                    "mapbox_id": "dXJuOm1ieHBsYzpDbmtJVFE",
                    "name": "Nemours",
                    "place": "Seine-et-Marne, France"
                }, {
                    "mapbox_id": "dXJuOm1ieHBsYzpBWjJvT1E",
                    "name": "Nemojov",
                    "place": "Hradec Králové, Czech Republic"
                }, {
                    "mapbox_id": "dXJuOm1ieHBsYzpUQWd5",
                    "name": "Nemocón",
                    "place": "Cundinamarca, Colombia"
                }, {
                    "mapbox_id": "dXJuOm1ieHBsYzpEWmhJN0E",
                    "name": "Nemo",
                    "place": "Texas, United States"
                },
            ]
        }
        self.assertEqual(response.json(), expected)

    def test_errors_on_empty_access_token(self, mock_requests):
        """
        Errors if no mapbox access token is set.
        """
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesMessage(KeyError, "MAPBOX_ACCESS_TOKEN"):
                self.client.get(self.url, query_params={"query": "abc"})

        mock_requests.assert_not_called()
        mock_requests.get.assert_not_called()

    def test_bad_request_on_empty_search(self, mock_requests):
        """
        Returns 400 if the search term is empty.
        """
        response = self.client.get(self.url, query_params={"query": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"]["query"],
                         "Missing search query")
        mock_requests.assert_not_called()
        mock_requests.get.assert_not_called()

    def test_bad_gateway_on_mapbox_error(self, mock_requests):
        """
        Returns a 502 if the external API returns an error.
        """
        ext_response = r_Response()
        ext_response.status_code = 401
        ext_response.json = mock.MagicMock()
        expected_err = {
            "error_code": "INVALID_TOKEN",
            "message": "Not Authorized - Invalid Token"
        }
        ext_response.json.return_value = expected_err
        mock_requests.get.return_value = ext_response

        search_text = "nemo"
        response = self.client.get(self.url, query_params={
            "query": search_text})

        mapbox_params = {
            "access_token": self.mapbox_access_token,
            "q": search_text,
        }
        mock_requests.get.assert_called_once_with(
            self.mapbox_url, params=mapbox_params)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["errors"]["mapbox"]["response"],
                         expected_err)
