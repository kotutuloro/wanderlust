from django.test import TestCase
from django.urls import reverse

from ..models import User
from ..forms import AccountCreationForm, AccountForm


class SignUpViewTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:signup")

    def test_sign_up_view_get(self):
        """
        The SignUpView renders the template for account registration.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_sign_up_view_post_valid_data(self):
        """
        Saves a user creation and redirects on a valid POST request.
        """
        data = {
            "username": "mycooluser",
            "email": "me@mine.me",
            "password1": "123abcme",
            "password2": "123abcme",
        }
        response = self.client.post(self.url, data)
        user = User.objects.first()
        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.email, data["email"])
        self.assertRedirects(response, reverse("accounts:login"))

    def test_sign_up_view_post_invalid_data(self):
        """
        Does not save a user creation on an invalid POST request.
        """
        data = {
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertIsInstance(response.context["form"], AccountCreationForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")
        self.assertEqual(User.objects.count(), 0)


class LoginRequiredTestMixin():
    def test_not_logged_in(self):
        """
        A logged out user cannot access the path set as the instance's url.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse("accounts:login")}?next={self.url}")


class AccountViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("accounts:settings")

        self.user = User.objects.create(
            username="myuser", email="my@user.me", first_name="kiko")
        self.client.force_login(self.user)

    def test_show_user_details(self):
        """
        A user's details and destinations are displayed.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/user_detail.html")
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.first_name)


class EditAccountViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("accounts:edit")

        self.user = User.objects.create(
            username="myuser", email="my@user.me", first_name="kiko")
        self.client.force_login(self.user)

    def test_edit_account_view_get(self):
        """
        Displays the user update form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/user_update_form.html")

    def test_edit_account_post_valid_data(self):
        """
        Saves an account update and redirects on a valid POST request.
        """
        data = {
            "username": self.user.username,
            "first_name": "kiko",
        }
        response = self.client.post(self.url, data)
        user = User.objects.first()
        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.email, "")
        self.assertRedirects(response, reverse("accounts:settings"))

    def test_edit_account_post_invalid_data(self):
        """
        Does not save an account update on an invalid POST request.
        """
        data = {
        }
        prev_email = self.user.email

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/user_update_form.html")
        self.assertIsInstance(response.context["form"], AccountForm)
        self.assertFalse(response.context["form"].is_valid())
        self.assertContains(response, "This field is required.")

        user = User.objects.first()
        self.assertEqual(user.email, prev_email)


class DeleteAccountViewTests(LoginRequiredTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("accounts:delete")

        self.user = User.objects.create(
            username="myuser", email="my@user.me", first_name="kiko")
        self.client.force_login(self.user)

    def test_delete_account_view_get(self):
        """
        Displays the user delete form on GET.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "registration/user_confirm_delete.html")

    def test_delete_account_post_valid_data(self):
        """
        Saves an account delete and redirects on a valid POST request.
        """
        response = self.client.post(self.url)
        self.assertEqual(User.objects.count(), 0)
        self.assertRedirects(response, reverse("accounts:login"))
