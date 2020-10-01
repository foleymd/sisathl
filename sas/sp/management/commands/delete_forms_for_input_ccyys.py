"""Removes all ccyys-related data for a given semester, including all forms and the "forms loaded" switch."""

from django.core.management.base import BaseCommand, CommandError  # REQUIRED
from django.conf import settings

from sisathl.sas.sp.models import *

"""
Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)
"""
import sys

argv = sys.argv


def log(fmt,
        *args):  # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
    sys.stderr.write(argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
    sys.stderr.write(str.format(fmt, *args) + "\n")


def xlog(exitCode, fmt,
         *args):  # log, then exit. Any non-zero exitCode indicates an error.
    log(fmt, *args)
    quit(exitCode)


def delete_forms_for_input_ccyys():
    # These bits are just sorting out where it's getting the input from--either locally or from Task Manager.
    try:
       input_file = sys.argv[2]
       input = open(input_file, 'r')
       for line in input:
           ccyys = int(line)
    except:
       for line in sys.stdin:
           ccyys = int(line)
    #ccyys = sys.argv[2]

    #if settings.PYPE_SERVICE == 'PROD':
    #    xlog('1984', 'You must do extra work to delete forms in PROD.')  # :-D <3 --NRMDF

    print 'Preparing to remove forms for a given ccyys in {0}.'.format(settings.PYPE_SERVICE)

    athlete_ccyyses = AthleteCcyys.objects.filter(ccyys=ccyys)

    for athlete_ccyys in athlete_ccyyses:

        SpdFormLog.objects.filter(spd_form__athlete_ccyys=athlete_ccyys).delete()
        FinalCourse.objects.filter(athlete_ccyys=athlete_ccyys).delete()
        AthleteCcyysSport.objects.filter(athlete_ccyys=athlete_ccyys).delete()

        athlete_ccyys_admins = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys=athlete_ccyys)

        for athlete_ccyys_admin in athlete_ccyys_admins:
            try:
                athlete_major = AthleteMajor.objects.get(
                    athlete_ccyys_admin=athlete_ccyys_admin)
            except:
                pass
            try:
                percent_degree = PercentDegree.objects.get(major=athlete_major)
                percent_form_type = AthleteCcyysAdmin.PERCENT_FORM_TYPE(
                    athlete_ccyys_admin)
                Comments.objects.filter(form_id=percent_degree.id,
                                        form_type=percent_form_type).delete()
                percent_degree.delete()
            except:
                pass

            spd_form_type = AthleteCcyysAdmin.SPD_FORM_TYPE(athlete_ccyys_admin)
            Comments.objects.filter(form_id=athlete_ccyys_admin.id,
                                    form_type=spd_form_type).delete()

            try:
                Course.objects.filter(major=athlete_major).delete()
                AdditionalCourse.objects.filter(major=athlete_major).delete()

            except:
                pass

            try:
                athlete_major.delete()
            except:
                pass
            print 'Deleted eid/school/major:', athlete_ccyys_admin.athlete_ccyys.athlete.eid
            # athlete_major.school, athlete_major.major_name

        athlete_ccyys_admins.delete()

    athlete_ccyyses.delete()

    print 'Ccyys deletion complete.'

    ccyys_admin = CcyysAdmin.objects.get(ccyys=ccyys)
    ccyys_admin.forms_loaded = False
    ccyys_admin.save()
    print "Forms no longer marked as loaded."


class Command(BaseCommand):  # REQUIRED, must be at bottom
    delete_forms_for_input_ccyys()
    quit(0)
