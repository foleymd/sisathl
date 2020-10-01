from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import Athlete, AthleteCcyys, PercentDegree

import sys
argv = sys.argv
def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message 
  sys.stderr.write (str.format (fmt,*args) + "\n")
def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log (fmt, *args)
    quit (exitCode)

def your_function():    # This trivally demonstrates reading and writing datasets from mainframe
  # first some environmental data to the "error" output.
  log ("Django called me, I don't know why.")
  log ("settings.DATABASES: {0}", settings.DATABASES)
  log ("argv: {0}", sys.argv)
  # now the real "work"
  lineCount = 0
  for aLine in sys.stdin:   # sys.stdin is the dataset associated with the UNVIN DD in the PyPE step.
    lineCount += 1
    try:
      sys.stdout.write (aLine)  # sys.stdout is the dataset associated with the UNVOUT DD in the PyPE step.
    except:
         xlog (1, "can't write stdout/UNVOUT")
  log ("Success: {0} lines", lineCount)


class Command(BaseCommand): #REQUIRED
    your_function()    
    quit(0)