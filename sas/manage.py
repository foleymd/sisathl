#!/usr/bin/env python
import os
import sys
from utdirect.utils import setup_extra
 
# If you use an 'extra' folder with svn externals, uncomment the following lines:
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
setup_extra(os.path.join(CURRENT_DIR, 'extra'))

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
