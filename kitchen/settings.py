"""Django settings for the Kitchen project"""
import os

import djcelery
djcelery.setup_loader()


DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# Kitchen settings #
REPO_BASE_PATH = os.path.join(BASE_PATH, "dashboard")
REPO = {
    'NAME': "testrepo",
    'URL': "",
    'SYNC_SCHEDULE': 60,  # seconds
    'KITCHEN_SUBDIR': '',
    'EXCLUDE_ROLE_PREFIX': 'env',
    'DEFAULT_ENV': 'production',
    'DEFAULT_VIRT': 'guest',
}
SHOW_VIRT_VIEW = True

LOG_FILE = '/tmp/kitchen.log'
##

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'kitchen.sql',
    }
}

# Celery broker url
BROKER_URL = "django://"

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = os.path.join(BASE_PATH, 'dashboard', 'static')
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'i#5u!2+wpw+4&8tzom)&@-4p(h4jai7#)r5@^i=sl%_-8-2mb*'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'kitchen.urls'

TEMPLATE_DIRS = (
    BASE_PATH + '/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "djcelery",
    "djkombu",
    "kitchen.dashboard",
    "kitchen.dashboard.templatetags",
    'django_nose',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
