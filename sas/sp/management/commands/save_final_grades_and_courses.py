
from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import Athlete, AthleteCcyys, AthleteMajor, Course, FinalCourse

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

def parse_final_course(line):
    '''Takes a line of data containing a student's courses and parses it, returning
     dictionary that includes course info. mainframe dataset = NR.NRJGAED.CLASSES'''

    
    uin = line[:16].strip()
    unique = line[17:22].zfill(5)
    course_category = line[23:26].strip()
    course_number = line[27:33].strip()
    credit_hours = line[34:35].strip()
    grade = line[36:38].strip()
    ccyys = line[39:44].strip()
    
    return {
            'uin': uin,
            'unique': unique,
            'course_category': course_category,
            'course_number': course_number,
            'credit_hours': credit_hours,
            'grade': grade,
            'ccyys': ccyys,
            }

def store_final_courses():
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
        
        final_course = parse_final_course(line)
        grade = final_course['grade']   
        unique = final_course['unique']     
        athlete = Athlete.objects.get(uin = final_course['uin'])
        athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = final_course['ccyys'])       
        final_course = store_new_final_course(final_course, athlete_ccyys)
              
        store_grade(grade, unique, athlete_ccyys)
            
    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 

def store_new_final_course(final_course, athlete_ccyys):
    '''Stores courses on table.'''
  
    g = FinalCourse.objects.get_or_create(athlete_ccyys=athlete_ccyys,
                                   unique = final_course['unique'],
                                   course_category = final_course['course_category'],
                                   course_number = final_course['course_number'],
                                   credit_hours = final_course['credit_hours']
                                   )
    return g

def store_grade(grade, unique, athlete_ccyys):

    majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys = athlete_ccyys)
    for major in majors:
        try:
             matched_class = Course.objects.get(major = major, unique = unique)
             matched_class.grade = grade
             matched_class.save()
        except Course.DoesNotExist:
             print 'major id', major.id, athlete_ccyys.id
             print 'Course with unique ' + str(unique) + ' not found.'


class Command(BaseCommand): #REQUIRED, must be at bottom
    print 'starting'
    store_final_courses()
    quit(0)