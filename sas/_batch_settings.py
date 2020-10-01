# install as /pype/stage/code/<group>/<project>/_batch_settings.py

# BUGBUG next two should be parameterized, or edited when installed to reflect proper group.project info,
BATCHGROUP="sisathl"
BATCHPROJECT="sas"

import os
from settings import *
import logging
import superpypelogging

# Settings we glean from the settings file in SVN, but can be overridden by the
# user (see _local_settings below).
#DEBUG = False
#TEMPLATE_DEBUG = False
DATABASE_PASSWORD = ''
EMAIL_HOST_PASSWORD = ''
LANGUAGE_COOKIE_NAME = 'django_language-' + BATCHGROUP + '.' + BATCHPROJECT + '-Test'
SESSION_COOKIE_NAME = 'sessionid-' + BATCHGROUP + '.' + BATCHPROJECT + '-Test'
CSRF_COOKIE_NAME = 'csrftoken-' + BATCHGROUP + '.' + BATCHPROJECT + '-Test'

# Attempt to load stage-specific settings defined by the user.  These get
# entered by the user in the web interface, then stored in the database and
# written out when the project is deployed.
try:
   from _local_settings import *
except ImportError:
   pass

# Other settings to force.
FILE_UPLOAD_PERMISSIONS = 0600

# batch logging
root_logger = logging.getLogger()
root_logger.addHandler(superpypelogging.pype_handler())
root_logger.setLevel(logging.INFO)
