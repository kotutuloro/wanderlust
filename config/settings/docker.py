from .local import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wanderlust',
        'HOST': 'db',
        'USER': 'admin',
    }
}
