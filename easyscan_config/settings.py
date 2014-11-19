"""
Django settings for easyscan_project project.

Environmental variables set in project's env/bin/activate, when using runserver,
  or env/bin/activate_this.py, when using apache via mod_wsgi or passenger.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import json, os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['EZSCAN__SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
temp_DEBUG = os.environ['EZSCAN__DEBUG']
assert temp_DEBUG in [ 'True', '' ], Exception( 'DEBUG env setting is, "%s"; must be either "True" or ""' % temp_DEBUG )
DEBUG = bool( temp_DEBUG )

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = json.loads( os.environ['EZSCAN__ALLOWED_HOSTS'] )  # list


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'easyscan_config.urls'

WSGI_APPLICATION = 'easyscan_config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ['EZSCAN__DATABASES_ENGINE'],
        'NAME': os.environ['EZSCAN__DATABASES_NAME'],
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = os.environ[u'EZSCAN__STATIC_URL']
