from .base import *

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = ['.localhost', '127.0.0.1', '[::1]']

STATIC_ROOT = BASE_DIR / "staticfiles"
