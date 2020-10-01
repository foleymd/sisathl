"""Truncates (removes data from) all tables related to specific athletes,
leaving the admin table data."""

from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.conf import settings

from sisathl.sas.sp.models import *


"""
Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)
"""
import sys
argv = sys.argv

def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write (str.format (fmt,*args) + "\n")
def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log (fmt, *args)
    quit (exitCode)


def save_percents():


    percent_degrees = PercentDegree.objects.all()

    for percent in percent_degrees:
        before = percent.projected_percentage
        percent.save()
        print percent.major.athlete_ccyys_admin.athlete_ccyys.athlete.eid, before, percent.projected_percentage


class Command(BaseCommand): #REQUIRED, must be at bottom
    save_percents()
    quit(0)