"""Sweeps through the user table and deactives any users who are no longer
employees at UT. Sends an email with that list."""

from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.conf import settings
from django.core.mail import send_mail

from sisathl.sas.sp.models import User
from sisathl.sas.utils.ted import TEDConnection

"""
Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)
"""
import sys
argv = sys.argv


def log (fmt,*args):
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write (str.format(fmt, *args) + "\n")


def xlog(exitCode, fmt, *args):
    log(fmt, *args)
    quit(exitCode)


def sweep_users():

    print 'Preparing to sweep users in ' + settings.PYPE_SERVICE

    expired_users = []
    eids_not_found = []

    ted_conn = TEDConnection(eid=settings.TED_SERVICE_EID, password=settings.TED_SERVICE_PASSWORD)
    attrs = ['utexasEduPersonUin', 'utexasEduPersonAffCode', 'mail']

    users = User.objects.filter(active=True)

    for user in users:
        try:
            ted_user = ted_conn.get_by_eid(user.eid, attrs=attrs)
        except Exception as e:
            print str(e)
            eids_not_found.append(user)
            continue

        if '0SFCU' not in ted_user['utexasEduPersonAffCode'] and '0FCCU' not in ted_user['utexasEduPersonAffCode']:
            expired_users.append(user)
            # they're expired! deactivate them!
            user.active = False
            user.save()

    if len(expired_users) > 0 or len(eids_not_found) > 0:
        email_recipients = [settings.ADMINS[0][1]]

        subject = 'ASPs user updated'

        message = 'The Athletic Satisfactory Progress system were swept for outdated users.\n\n'
        if len(expired_users) > 0:
            message += 'The following users were deactivated because they are no longer staff or faculty:\n'
            message += ''.join([user.eid + ' ' + user.name + '\n' for user in expired_users])
            message += '\n'
        if len(eids_not_found) > 0:
            message += 'The following users EIDs could not be found in the UT system. They may need manual correction:\n'
            message += ''.join([user.eid + ' ' + user.name + '\n' for user in eids_not_found])
            message += '\n'

        send_mail(subject, message, settings.ADMINS[0][1],
                  email_recipients, fail_silently=False)

    print 'Total active user records read: ' + str(users.count())
    print 'EIDs not found: ' + str(len(eids_not_found))
    print 'Total expired records deactivated: ' + str(len(expired_users))


class Command(BaseCommand):  # REQUIRED, must be at bottom
    sweep_users()
    quit(0)