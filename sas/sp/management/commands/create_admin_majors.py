import datetime

import csv
from django.core.management.base import BaseCommand, CommandError  # REQUIRED
from django.conf import settings

from sisathl.sas.utils.constants import SUMMER
from sisathl.sas.sp.models import (Athlete,
                                   AthleteCcyys,
                                   AthleteCcyysAdmin,
                                   AthleteMajor,
                                   School,
                                   PercentDegree,
                                   )

"""
Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)
"""
import sys

argv = sys.argv


def log(fmt,
        *args):  # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
    sys.stderr.write(
        argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
    sys.stderr.write(str.format(fmt, *args) + "\n")


def xlog(exitCode, fmt,
         *args):  # log, then exit. Any non-zero exitCode indicates an error.
    log(fmt, *args)
    quit(exitCode)


def parse_major(line):
    """Takes a line of data representing a student athlete major record and parses it, returning
    major dictionary. mainframe dataset = NR.NRJGAEC.MAJOR"""

    uin = line[:16].strip()
    ccyys = line[17:22].strip()
    college_code = line[23:24].strip()
    college_name = line[25:41].strip()
    major_code = line[42:47].strip()
    major_name = line[48:64].strip()
    first_or_second = line[65:66].strip()
    created_by = line[67:75].strip()

    return {
        'uin': uin,
        'ccyys': ccyys,
        'college_code': college_code,
        'college_name': college_name,
        'major_code': major_code,
        'major_name': major_name,
        'first_or_second': first_or_second,
        'created_by': created_by,
    }


def store_admin_and_major():
    """Stores administrative details to admin table and major details to major table."""

    # first some environmental data to the "error" output.
    log("storing majors")
    log("settings.DATABASES: {0}", settings.DATABASES)
    log("argv: {0}", sys.argv)
    lineCount = 0

    try:
        f = sys.argv[2]
        input = open(f, 'r')
    except:
        input = sys.stdin

    try:
        output_file = sys.argv[3]
        output = open(output_file, 'w')
    except:
        output = sys.stdout

    # These fieldnames are for the dictwriter--they are used to write the header and match field values later.
    fieldnames = ['EID',
                  'Name',
                  'CCYYS',
                  'Number of FT Semesters',
                  'SP Form made?',
                  'Percent Form made?',
                  ]
    # Writing the header.
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()

    for line in input:
        lineCount += 1
        major = parse_major(line)
        created_by = major['created_by']

        try:
            athlete = Athlete.objects.get(uin=major['uin'])
        except Athlete.DoesNotExist:
            xlog(1984, 'Cannot find uin ' + major['uin'])
        try:
            athlete_ccyys = AthleteCcyys.objects.get(athlete=athlete,
                                                     ccyys=major['ccyys'])
        except AthleteCcyys.DoesNotExist:
            xlog(1984,
                 'Cannot find uin ccyys combo: ' + major['uin'] + ' ' + major['ccyys'])

        fields_to_write = {}
        fields_to_write['EID'] = athlete.eid
        fields_to_write['Name'] = athlete.name
        fields_to_write["CCYYS"] = athlete_ccyys.ccyys
        fields_to_write['Number of FT Semesters'] = athlete_ccyys.num_ft_semesters

        try:

            school = School.objects.get(code=major['college_code'])

            if AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys).count() > 0:
                pass  # this is not the most elegant solution because it doesn't update information that's already there. but it does prevent a double load.
            else:
                athlete_ccyys_admin = store_new_admin(athlete_ccyys, major)
                if athlete_ccyys_admin.active:
                    fields_to_write['SP Form made?'] = 'Y'
                else:
                    fields_to_write['SP Form made?'] = ''
                major = store_new_major(major, athlete_ccyys_admin, school)
                percent_form = store_new_percent_degree(athlete_ccyys, major, created_by)
                if percent_form.active:
                    fields_to_write['Percent Form made?'] = 'Y'
                else:
                    fields_to_write['Percent Form made?'] = ''
        except:
            print "Could not store records for " + athlete.eid + " because of problem with college code " + major['college_code']

        try:
            writer.writerow(fields_to_write)
        except:
            xlog(1, "can't write stdout/UNVOUT")

    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass

    try:
        output_file.close()
    except:
        pass


def store_new_admin(athlete_ccyys, major):
    """Business rules from Kelsey about when students need Percent forms:
    Number of FT semesters complete (for summer only)
    4 - Percent
    5 - SP
    6 - SP + Percent
    7 - SP
    8 - SP + Percent
    9 - SP

    Number of FT semesters complete (for fall and spring)
    3 - Percent
    4 - SP
    5 - SP + Percent
    6 - SP
    7 - SP + Percent
    8 - SP
    9 - SP (Percent only needed if they will need summer. This is something Kelsey would manually activate since it is rare)
    """
    if str(athlete_ccyys.ccyys).endswith(SUMMER):  # summer semester
        active = athlete_ccyys.num_ft_semesters >= 5
    else:
        active = athlete_ccyys.num_ft_semesters >= 4  # athletes are evaluated for their progress at the fifth semester and every semester following

    try:
        g = AthleteCcyysAdmin.objects.create(athlete_ccyys=athlete_ccyys,
                                             total_countable_degree_hours=0,
                                             created_by=major['created_by'],
                                             created_by_date=datetime.datetime.now(),
                                             routed_to_dean_by='',
                                             approved_by_dean='',
                                             routed_to_reg_by='',
                                             approved_by_reg='',
                                             active=active,
                                             )
    except Exception as e:
        message = 'Athlete_ccyys id: ' + str(athlete_ccyys.id) + ', exception: ' + str(e)
        xlog(1984, message)
    return g


def store_new_major(major, athlete_ccyys_admin, school):
    """Add new major for a student-athlete"""

    g = AthleteMajor(athlete_ccyys_admin=athlete_ccyys_admin,
                     school=school,
                     major_code=major['major_code'],
                     major_name=major['major_name'],
                     catalog_begin='',
                     # this info is updated by the degree audit portion of this system
                     catalog_end='',
                     first_or_second=major['first_or_second'],
                     )
    try:
        g.save("NRNWAEC2")
    except Exception as e:
        message = str(e) + 'Athlete_ccyys_admin id: ' + str(
            athlete_ccyys_admin.id) + ', exception: ' + str(e)
        xlog(1984, message)
    return g


def store_new_percent_degree(athlete_ccyys, major, created_by):
    """Business rules from Kelsey about when students need Percent forms:
    Number of FT semesters complete (for summer only)
    4 - Percent
    5 - SP
    6 - SP + Percent
    7 - SP
    8 - SP + Percent
    9 - SP

    Number of FT semesters complete (for fall and spring)
    3 - Percent
    4 - SP
    5 - SP + Percent
    6 - SP
    7 - SP + Percent
    8 - SP
    9 - SP (Percent only needed if they will need summer. This is something Kelsey would manually activate since it is rare)
    """

    if str(athlete_ccyys.ccyys).endswith(SUMMER):  # summer semester
        active = (athlete_ccyys.num_ft_semesters >= 4 and athlete_ccyys.num_ft_semesters % 2 == 0)  # checks if the number is at least 4 and even
    else:
        active = (athlete_ccyys.num_ft_semesters >= 3 and athlete_ccyys.num_ft_semesters % 2 == 1)  # checks if the number is at least 3 and odd

    try:
        g = PercentDegree(major=major,
                          created_by=created_by,
                          created_by_date=datetime.datetime.now(),
                          active=active)

    except Exception as e:
        message = str(e) + 'AthleteMajor code: ' + str(major.id) + ', exception: ' + str(
            e)
        xlog(1984, message)
    g.save("NRNWAEC2")
    return g


class Command(BaseCommand):  # REQUIRED, must be at bottom
    store_admin_and_major()
    quit(0)
