from django.test import TestCase

from ..models import User


class UserModelTests(TestCase):
    def test_user_creation(self):
        """
        Creating a new user works as expected.
        """
        user = User.objects.create(
            username="my-user", email="me@mine.me", first_name="kiko")
        self.assertEqual(user.username, "my-user")
        self.assertEqual(user.email, "me@mine.me")
        self.assertEqual(user.first_name, "kiko")
        self.assertEqual(user.last_name, "")
