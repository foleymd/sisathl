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


def flush_athlete_db():
    
    if settings.PYPE_SERVICE == 'PROD':
        xlog('1984', 'Do not delete everything in PROD. That would be bad.')

    print 'preparing to flush db!'
        
    Comments.objects.all().delete()
    print 'Comments deleted.'
    
    AdditionalCourseLog.objects.all().delete()
    CourseLog.objects.all().delete()   
    SpdFormLog.objects.all().delete()
    print 'Log deleted.'
    
    PercentDegree.objects.all().delete()
    print 'Percent forms deleted.'
    
    AthleteCcyysSport.objects.all().delete()
    print 'Sports deleted.'
    
    FinalCourse.objects.all().delete()
    print "Final courses deleted."
    
    AdditionalCourse.objects.all().delete()
    Course.objects.all().delete()
    print "Courses deleted."
    
    AthleteMajor.objects.all().delete()
    print "Majors deleted."
    
    AthleteCcyysAdmin.objects.all().delete()
    print "SPD forms deleted."
    
    AthleteCcyys.objects.all().delete()
    print "Ccyys objects deleted."
    
    Athlete.objects.all().delete()
    print "Athletes deleted."
    
    print 'Database flush complete.'
    
class Command(BaseCommand): #REQUIRED, must be at bottom
    flush_athlete_db()
    quit(0)