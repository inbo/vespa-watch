"""
Django settings for djangoproject project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<SOMETHING_SECRET_TO_REDEFINE_HERE>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # From Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # From others
    'crispy_forms',
    'markdownx',
    'modeltranslation',

    # Local helpers
    'page_fragments',


    'vespawatch'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

ROOT_URLCONF = 'djangoproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export'
            ],
        },
    },
]

WSGI_APPLICATION = 'djangoproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Brussels'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ('nl', _('Dutch')),
    ('en', _('English')),
]

LANGUAGES_AVAILABLE_IN_SELECTOR = [
    ('nl', _('Dutch')),
    ('en', _('English')),
]

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/img/'

VESPAWATCH_PROJECT_ID = 22865  # Vespa-Watch project ID @ iNaturalist
VESPAWATCH_USER_ID = 1263313  # vespawatch user ID @ iNaturalist

WEBSITE_NAME = "Vespa-Watch"

SETTINGS_EXPORT = [
    'DEBUG',
    'JS_DEBUG',
    'WEBSITE_NAME',
    'LANGUAGES',
    'LANGUAGES_AVAILABLE_IN_SELECTOR',
    'VESPAWATCH_ID_OBS_FIELD_ID',
    'VESPAWATCH_EVIDENCE_OBS_FIELD_ID'
]

PAGE_FRAGMENTS_FALLBACK_LANGUAGE = 'nl'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

VESPAWATCH_ID_OBS_FIELD_ID = 9613 # # The identifier of the "vespawatch_id" observation field @iNaturalist
VESPAWATCH_EVIDENCE_OBS_FIELD_ID = 9770  # The identifier of the "vespawatch_evidence" observation field @iNaturalist

MAP_CIRCLE_FILL_OPACITY = 0.5
MAP_CIRCLE_STROKE_OPACITY = 0.8
MAP_CIRCLE_STROKE_WIDTH = 1
MAP_CIRCLE_NEST_RADIUS = 12
MAP_CIRCLE_INDIVIDUAL_RADIUS = 5
MAP_CIRCLE_INDIVIDUAL_COLOR = '#FD9126'
MAP_CIRCLE_NEST_COLOR = {  # This depend of the management action
    'finished': '#9CCB19',
    'unfinished': '#EE4000',
    'DEFAULT': '#3678ff'
}
MAP_CIRCLE_UNKNOWN_COLOR = '#000' # if the subject is not 'Individual' or 'Nest'
MAP_INITIAL_POSITION = [50.85, 4.35]
MAP_INITIAL_ZOOM = 8

MAP_TILELAYER_BASE_URL = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png'
MAP_TILELAYER_OPTIONS = {
    'attribution': '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://carto.com/attributions">CARTO</a>',
    'subdomains': 'abcd',
    'maxZoom': 20
}

JS_DEBUG = False