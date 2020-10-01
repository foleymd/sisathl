
from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import (Athlete,
                                   AthleteCcyys,
                                   AthleteMajor,
                                   Course,
                                  )

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

def parse_course(line):
    '''Takes a line of data containing a student's courses and parses it, returning
     dictionary that includes course info. mainframe dataset = NR.NRPBAEC1.COURSES'''
    
    uin = line[:16].strip()
    ccyys = line[17:22].strip()
    unique = line[23:28].zfill(5)
    course_category = line[29:32].strip()
    course_number = line[33:39].strip()
    credit_hours = line[40:41].strip()
    course_type = line [42:45].strip()
    
    return {
            'uin': uin,
            'ccyys': ccyys,
            'unique': unique,
            'course_category': course_category,
            'course_number': course_number,
            'credit_hours': credit_hours,
            'course_type': course_type,
            }

def store_courses():
    '''Stores athlete's courses on course tables.'''
 
    # first some environmental data to the "error" output.
    log ("storing majors")
    log ("settings.DATABASES: {0}", settings.DATABASES)
    log ("argv: {0}", sys.argv)
    lineCount = 0

    try:
        f = sys.argv[2]
        input = open(f, 'r')
    except:
        input = sys.stdin
 
    for line in input:
        lineCount += 1
        
        majors = []
        course = parse_course(line)
        
        athlete = Athlete.objects.get(uin = course['uin'])
        athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = course['ccyys'])
        
        majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__exact=athlete_ccyys)

        for major in majors:
            if Course.objects.filter(major = major, unique = course['unique']).count() > 0:
                pass
            else:
                store_new_course(course, major)
            
    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 

def store_new_course(course, major):
    '''Stores courses on table.'''
  
    g = Course.objects.create(major = major,
                                      course_category = course['course_category'],
                                      course_number = course['course_number'],
                                      unique = course['unique'],
                                      course_type = course['course_type'],
                                      credit_hours = course['credit_hours']
                                     )
    return g

class Command(BaseCommand): #REQUIRED, must be at bottom
    store_courses()
    quit(0)