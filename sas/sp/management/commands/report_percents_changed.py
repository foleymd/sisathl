import sys
import csv
import time

from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.conf import settings

from sisathl.sas.sp.models import SpdFormLog


argv = sys.argv
def log(fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write(argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write(str.format(fmt, *args) + "\n")
def xlog(exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log(fmt, *args)
    quit(exitCode)


def produce_report():
    try:
        ccyys = sys.argv[2]
    except:
        xlog("No ccyys.")

    try:
        file_name = sys.argv[3]
        output = open(file_name, 'w')
    except:
        output = sys.stdout

    total_changes = 0
    timestamp_format = '%Y-%m-%d %H:%M:%S %Z'

    output.write("Report of Changes of Percentage of Degree in ASPs" + "\n" +
                 "The University of Texas at Austin" + "\n" +
                 "Evaluation Semester" + "," + ccyys + "\n" +
                 "Environment" + "," + settings.PYPE_SERVICE + "\n"
                )

    fieldnames = ['Student EID', 'Updater EID', 'Update Time', 'Original Projected Countable Hours',
                  'Original Total Hours Required', 'Original Projected Percentage',
                  'Changed Projected Countable Hours', 'Changed Total Hours Required',
                  'Changed Projected Percentage']
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()

    logs = SpdFormLog.objects.all()
    for log in logs:
        prev = log.previous_record
        if prev:
            if (prev.projected_percentage > 0) and (log.projected_percentage > 0) and (prev.projected_percentage != log.projected_percentage):
                total_changes += 1
                writer.writerow(
                        {'Student EID': log.spd_form.athlete_ccyys.athlete.eid,
                         'Updater EID': log.updater,
                         'Update Time': log.update_datetime.strftime(timestamp_format),
                         'Original Projected Countable Hours': prev.projected_countable_hours,
                         'Original Total Hours Required': prev.total_hours_required,
                         'Original Projected Percentage': prev.projected_percentage,
                         'Changed Projected Countable Hours': log.projected_countable_hours,
                         'Changed Total Hours Required': log.total_hours_required,
                         'Changed Projected Percentage': log.projected_percentage
                         }
                )
    output.write('\n' + 'Total changes: ' + str(total_changes))

    output.close()

class Command(BaseCommand): #REQUIRED
    produce_report()
    quit(0)