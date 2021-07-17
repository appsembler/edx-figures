"""
Django settings for the Figures devsite development server

This settings file is intended for operation only in a development environment
"""

from __future__ import absolute_import, unicode_literals

import os
import sys

import environ

from figures.settings.lms_production import (
    update_webpack_loader,
    update_celerybeat_schedule,
)

DEVSITE_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT_DIR = os.path.dirname(DEVSITE_BASE_DIR)

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, []),
    OPENEDX_RELEASE=(str, 'HAWTHORN'),
    FIGURES_IS_MULTISITE=(bool, False),
    ENABLE_DEVSITE_CELERY=(bool, True),
    ENABLE_OPENAPI_DOCS=(bool, False),
    SEED_DAYS_BACK=(int, 60),
    SEED_NUM_LEARNERS_PER_COURSE=(int, 25),
)

environ.Env.read_env(os.path.join(DEVSITE_BASE_DIR, '.env'))

OPENEDX_RELEASE = env('OPENEDX_RELEASE').upper()

if OPENEDX_RELEASE == 'GINKGO':
    ENABLE_DEVSITE_CELERY = False
else:
    ENABLE_DEVSITE_CELERY = env('ENABLE_DEVSITE_CELERY')

MOCKS_DIR = 'mocks/{}'.format(OPENEDX_RELEASE.lower())

# SECURITY WARNING: Use a real key when running in the cloud and keep it secret
SECRET_KEY = 'insecure-secret-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')
USE_TZ = True
TIME_ZONE = 'UTC'
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Set the default Site (django.contrib.sites.models.Site)
SITE_ID = 1


# Adds the mock edx-platform modules to the Python module search path
sys.path.append(os.path.normpath(os.path.join(PROJECT_ROOT_DIR, MOCKS_DIR)))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    # 'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'django_countries',
    'django_filters',
    'debug_toolbar',
    'webpack_loader',
    'organizations',
    'waffle',
    'devsite',
    'figures',

    # Include mock edx-platform apps.
    # These are apps on which Figures has dependencies
    # See: <figures repo>/tests/mocks/
    # Also note the paths set in edx-figures/pytest.ini
    'openedx.core.djangoapps.content.course_overviews',
    'openedx.core.djangoapps.course_groups',
    'student',
]

if ENABLE_DEVSITE_CELERY:
    INSTALLED_APPS.append('djcelery')

# certificates app
if OPENEDX_RELEASE == 'GINKGO':
    INSTALLED_APPS.append('certificates')
    INSTALLED_APPS.append('lms.djangoapps.courseware')
elif OPENEDX_RELEASE == 'HAWTHORN':
    INSTALLED_APPS.append('lms.djangoapps.certificates')
    INSTALLED_APPS.append('courseware')
else:
    INSTALLED_APPS.append('lms.djangoapps.certificates')
    INSTALLED_APPS.append('lms.djangoapps.courseware')


if OPENEDX_RELEASE == 'JUNIPER':
    MIDDLEWARE = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

ROOT_URLCONF = 'devsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join('devsite', 'devsite', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# Static content
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(DEVSITE_BASE_DIR, "staticfiles")

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

WSGI_APPLICATION = 'devsite.wsgi.application'


# Database setting
# To select a different database, such as MySQL, add the database url string to
# as 'DATABASE_URL=<database url string>' in the devsite/.env file
#
# Refs:
#   https://docs.djangoproject.com/en/1.8/ref/settings/#databases
#   https://github.com/joke2k/django-environ/tree/v0.4.5

DEFAULT_SQLITE_DB_URL = 'sqlite:///{}'.format(os.path.join(
    DEVSITE_BASE_DIR,
    'figures-{release}-db.sqlite3'.format(release=OPENEDX_RELEASE.lower())))

DATABASES = {
    'default': env.db(default=DEFAULT_SQLITE_DB_URL)
}

LOCALE_PATHS = [
   os.path.join(PROJECT_ROOT_DIR, 'figures', 'conf', 'locale')
]


LOGIN_REDIRECT_URL = '/'

# Open edX settings

COURSE_ID_PATTERN = r'(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'

# For initial testing. Later we want to enforce authorization
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}


if ENABLE_DEVSITE_CELERY:
    # TODO: update to allow environemnt variable overrides
    # the password seting is only for local development environments
    FIGURES_CELERY_USER = 'figures_user'
    FIGURES_CELERY_PASSWORD = 'figures_pwd'
    FIGURES_CELERY_VHOST = 'figures_vhost'

    BROKER_URL = 'amqp://{user}:{password}@localhost:5672/{vhost}'.format(
        user=FIGURES_CELERY_USER,
        password=FIGURES_CELERY_PASSWORD,
        vhost=FIGURES_CELERY_VHOST,
    )

    CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

    import djcelery
    djcelery.setup_loader()

#
# Declare empty dicts for settings required by Figures
#


# Webpack loader is required to load Figure's front-end
WEBPACK_LOADER = {}


# Blank dict declared so that the Figures settings dependencies
# Included here for completeness in having this settings file match behavior in
# the LMS settings
CELERYBEAT_SCHEDULE = {}
FEATURES = {
    'FIGURES_IS_MULTISITE': env('FIGURES_IS_MULTISITE')
}


# The LMS defines ``ENV_TOKENS`` to load settings declared in `lms.env.json`
# We have an empty dict here to replicate behavior in the LMS
ENV_TOKENS = {}

update_webpack_loader(WEBPACK_LOADER, ENV_TOKENS)
update_celerybeat_schedule(CELERYBEAT_SCHEDULE, ENV_TOKENS)

# Used by Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1'
]

DEVSITE_SEED = {
    'DAYS_BACK': env('SEED_DAYS_BACK'),
    'NUM_LEARNERS_PER_COURSE': env('SEED_NUM_LEARNERS_PER_COURSE')
}

ENABLE_OPENAPI_DOCS = env('ENABLE_OPENAPI_DOCS') and OPENEDX_RELEASE not in ['GINKGO', 'HAWTHORN']

if ENABLE_OPENAPI_DOCS:
    INSTALLED_APPS += ['drf_yasg2']
