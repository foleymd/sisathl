"""Writes a report of inconsistencies between the classes that a student has on the mainframe and
those on the SP forms"""


from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import (Athlete,
                                   AthleteCcyys,
                                   AthleteCcyysAdmin,
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

def parse_classes(line):
    '''Takes a line of data representing a student athlete major record and parses it, returning
    major dictionary. mainframe dataset = NR.NRJGAEC.MAJOR'''

    line_split = str(line).split(' ')

    eid = line_split[0]
    courses = line_split[1:8]

    return {
            'eid': eid,
            'courses': courses,
            }

def compare_classes():
    '''Stores administrative details to admin table and major details to major table.'''

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
        student_class = parse_classes(line)
        eid = student_class['eid']

        try:
            athlete = Athlete.objects.get(eid = student_class['eid'])
            athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = '20162')
            athlete_ccyys_admin = AthleteCcyysAdmin.objects.filter(athlete_ccyys = athlete_ccyys)
            for admin in athlete_ccyys_admin:
                if admin.status == 'Form Inactive':
                    status = 'Inactive'
                else:
                    status = 'Active'
                major = AthleteMajor.objects.get(athlete_ccyys_admin = admin)

                form_courses = Course.objects.filter(major = major)

                for form_course in form_courses:
                    form_course_unique = form_course.unique.zfill(5)
                    match = False
                    for unique in student_class['courses']:
                        unique = unique.replace('\r\n', '').zfill(5)
                        if form_course_unique == unique:
                            match = True
                    if match == False:
                       print eid  + ', ' + status + ', ' + major.school.name + ', Class on form not on mainframe, ' + form_course_unique.zfill(5)

                for unique in student_class['courses']:
                    unique = unique.replace('\r\n', '').zfill(5)
                    try:
                        course = Course.objects.get(major = major, unique = unique)
                    except:
                        print eid + ', ' + status + ', ' + major.school.name + ', Class on mainframe not on form, ' + unique.zfill(5)

        except Athlete.DoesNotExist:
            pass

        except AthleteCcyys.DoesNotExist:
            pass

    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass


class Command(BaseCommand): #REQUIRED, must be at bottom
    compare_classes()
    quit(0)