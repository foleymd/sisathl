# Django settings for Student Athletics System (sas) project.
# Auto generated on Thu Mar 29 11:14:14 2012 for PyPE version 26.3.2
# modified 10/23/2013 by NRSDG to conver to pype 26.3.4.

import os
import sys
import posixpath

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

############################################################################
# !!! Important! These settings should be for development only.
# !!! Edit the project settings online to add your debug settings.
# !!! These settings will be overwritten on the utdirect servers.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Oracle stuff - points to your app
os.environ['TNS_ADMIN'] = os.path.join(CURRENT_DIR, 'oracle')

############################################################################
#############################################################################

# TEMPLATE_STRING_IF_INVALID = '%s'

#############################################################################
############################################################################
# PYPE settings

# The default service to use when calling broker.
PYPE_SERVICE = 'TEST'

# Directory to use for temporary files.  You can change this to something
# valid on your workstation for developing locally.
PYPE_TEMP_DIR = '/tmp'
############################################################################

############################################################################
# import statement above pulls in databases from local_settings.py
#
# !!! Important! These settings should be for development only.
# !!! Edit the project settings online to add your database settings.
# !!! These settings will be overwritten on the utdirect servers.
# DATABASES = DATABASES
# {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',          # 'django.db.backends.mysql' or
#                                # 'django.db.backends.oracle' or
#
#         'NAME': 'django.db.sqlite3',
#                                  # Or path to database file if using sqlite3.
#         'USER': '',            # Not used with sqlite3.
#         'PASSWORD': '',        # Not used with sqlite3.
#         'HOST': '',            # Set to empty string for localhost. Not used with sqlite3.
#         'PORT': '',            # Set to empty string for default. Not used with sqlite3.
#     }
# }
############################################################################

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True
DATE_INPUT_FORMATS = ('%d-%m-%Y','%Y-%m-%d')

# Absolute path to the directory that holds static content such as
# images, css, and javascript files.
# Example: "/home/media/media.lawrence.com/"
STATIC_ROOT = os.path.join(CURRENT_DIR, 'static', '')

# URL that handles the media served from STATIC_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com", "http://example.com/media/"
STATIC_URL = '/apps/sisathl/sas/static/'

# MEDIA_ROOT and MEDIA_URL are intended for user-uploaded files. Since
# Pype doesn't have this capacity yet, they are set to None.
MEDIA_ROOT = None
MEDIA_URL = None

# Make this unique, and don't share it with anybody.
#redacted

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'utdirect.middleware.HttpHeaderMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'sisathl.sas.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(CURRENT_DIR, 'templates'),
    os.path.join(CURRENT_DIR, 'extra/ferpa/'),
)


# These are hosts allowed to access your server.  This will be
# overwritten on the Pype servers with the appropriate utdirect
# servers.
ALLOWED_HOSTS = ['local.utexas.edu',]

# This is the amount of time, in seconds, that Django will leave DB
# connections open.  600 is enforced on the servers.
CONN_MAX_AGE = 600

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    'utdirect',
    # Add your apps created with 'python manage.py my_app':
    'sisathl.sas.portal',
    'sisathl.sas.sp',
    'sisathl.sas.compliance',
    'sisathl.sas.extra.crispy_forms',
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG
BASE_TEMPLATE = 'spd_base.html'  # used by FERPA check
USE_UTDIRECT = False             # used by FERPA check
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
#redacted

try:
    from local_settings import (DATABASES,
                                PYPE_SERVICE,
                                DEBUG,
                                TED_SERVICE_EID,
                                TED_SERVICE_PASSWORD)
except ImportError:
    pass

# this creates a temporary sqlite database if you are
# are running the test command
if 'test' in sys.argv:
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',          # 'django.db.backends.mysql' or
                               # 'django.db.backends.oracle' or
                               # 'django.db.backends.sqlite3'
        'NAME': '',            # Or path to database file if using sqlite3.
        'USER': '',            # Not used with sqlite3.
        'PASSWORD': '',        # Not used with sqlite3.
        'HOST': '',            # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',            # Set to empty string for default. Not used with sqlite3.
    }
}


#redacted

MANAGERS = ADMINS

try:
    from local_settings import QUALTRICS_PARAMS
except ImportError:
    pass

# The student portal has a link to med forms that usually shows 100% of the time
# but we occassionally get asked to hide it when the vendor has issues.
try:
    from local_settings import SHOW_MED_LINK
except ImportError:
    SHOW_MED_LINK = True
