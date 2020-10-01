import sys
import csv

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import (Athlete,
                                   AthleteCcyys,
                                   AthleteCcyysAdmin,
                                   AthleteMajor,
                                   PercentDegree,)


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

def parse_audit_results(line):
    '''Takes a line of data representing a student athlete major record and parses it, returning
    major dictionary. mainframe dataset = NR.NRJGAEC1.MAJOR'''

    audit_id = line[:12].strip()
    uin = line[12:28].strip()
    catalog_begin = line[28:32].strip()
    catalog_end = line[33:37].strip()
    college_code = line[38:39].strip()
    major_code = line [39:44].strip()
    total_hours_counted = line[44:50].strip()
    total_hours_needed = line[50:56].strip()
    percent_completed = line[56:61].strip()
    submission_ccyys = line[61:66].strip()

    return {
            'audit_id': audit_id,
            'uin': uin,
            'catalog_begin': catalog_begin,
            'catalog_end': catalog_end,
            'college_code': college_code,
            'major_code': major_code,
            'total_hours_counted': total_hours_counted,
            'total_hours_needed': total_hours_needed,
            'percent_completed': percent_completed,
            'submission_ccyys': submission_ccyys,
            }

def report_percent_discrepancies():
    '''Compares a dataset of degree audit information to forms in order to find discrepancies'''

    # first some environmental data to the "error" output.
    log ("reporting discrepancies")
    log ("settings.DATABASES: {0}", settings.DATABASES)
    log ("argv: {0}", sys.argv)
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

    fieldnames = ['EID',
                  'Name',
                  'CCYYS',
                  'College',
                  'Major Code',
                  'Major Name',
                  'Minor',
                  'Catalog',
                  'Feb 29 Audit Projected Countable Hours',
                  'Feb 29 Audit Total Hours Required',
                  'Feb 29 Audit Percentage of Degree',
                  'Final Form Countable Hours',
                  'Final Form Total Hours Required',
                  'Final Form Percentage of Degree',
                  'Differs?',
                  'Active?',
                  'Form Status',

                 ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator = '\n')
    writer.writeheader()

    for line in input:
        lineCount += 1
        audit_results = parse_audit_results(line)
        try:
            athlete = Athlete.objects.get(uin = audit_results['uin'])
        except Athlete.DoesNotExist:
            xlog(1984, 'Cannot find uin ' + audit_results['uin'])
        try:
            athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = audit_results['submission_ccyys'])
        except AthleteCcyys.DoesNotExist:
            xlog(1984, 'Cannot find uin ccyys combo: ' + audit_results['uin'] + ' ' + audit_results['submission_ccyys'])

        try:
            athlete_ccyys_admin = AthleteCcyysAdmin.objects.filter(athlete_ccyys = athlete_ccyys)

        except AthleteCcyys.DoesNotExist:
            xlog(1984, 'Cannot find athlete_ccyys_admin for: ' + audit_results['uin'] + ' ' + audit_results['ccyys'])

        for admin in athlete_ccyys_admin:
            major = AthleteMajor.objects.get(athlete_ccyys_admin = admin)

            if major.major_code == audit_results['major_code']:

                fields = {}
                fields['EID'] = major.athlete_ccyys_admin.athlete_ccyys.athlete.eid
                fields['Name'] = major.athlete_ccyys_admin.athlete_ccyys.athlete.name
                fields['CCYYS'] = major.athlete_ccyys_admin.athlete_ccyys.ccyys
                fields['College'] = major.school
                fields['Major Code'] = major.major_code
                fields['Major Name'] = major.major_name
                fields['Minor'] = major.minor
                if major.catalog_begin:
                    fields['Catalog'] = major.catalog_begin + '-' + major.catalog_end
                fields['Feb 29 Audit Projected Countable Hours'] = int(audit_results['total_hours_counted']) / 100
                fields['Feb 29 Audit Total Hours Required'] = int(audit_results['total_hours_needed']) / 100
                percentage = float(fields['Feb 29 Audit Projected Countable Hours']) / float(fields['Feb 29 Audit Total Hours Required']) * 100

                percentage_split = str(percentage).split('.')
                a = percentage_split[0]
                try:
                    b = percentage_split[1]
                except (ValueError, IndexError):     # in the case of an integer
                    projected_percentage = (Decimal(fields['Feb 29 Audit Projected Countable Hours']) / Decimal(fields['Feb 29 Audit Total Hours Required']) * 100)
                else:
                    projected_percentage = float(a + '.' + b[0:2])
                fields['Feb 29 Audit Percentage of Degree'] = projected_percentage
                fields['Final Form Countable Hours'] = major.percent_degree.projected_countable_hours
                fields['Final Form Total Hours Required'] = major.percent_degree.total_hours_required
                fields['Final Form Percentage of Degree'] = major.percent_degree.projected_percentage
                if major.percent_degree.status == 'Form Inactive':

                    fields['Active?'] = 'No'
                else:
                    fields['Active?'] = 'Yes'

                fields['Form Status'] = major.percent_degree.status

                if projected_percentage == major.percent_degree.projected_percentage:
                    fields['Differs?'] = 'No'
                else:
                    fields['Differs?'] = 'Yes'

                writer.writerow(fields)

            else:
                print 'rejected', major

    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass

    try:
        output_file.close()
    except:
        pass


class Command(BaseCommand): #REQUIRED, must be at bottom
    report_percent_discrepancies()
    quit(0)