"""Reads a dataset and updates the given panel with those students."""

import sys

import csv
import requests

from django.core.management.base import BaseCommand, CommandError  # REQUIRED

from sisathl.sas.compliance.functions.qualtrics import QualtricsRequest
from sisathl.sas.compliance.models import Year

argv = sys.argv

# standard logging info
def log(fmt, *args):
    sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
    sys.stderr.write (str.format(fmt, *args) + "\n")


def xlog(exit_code, fmt, *args):
    log(fmt, *args)
    quit(exit_code)

# Constants
DELIMITER = '\t'  # tab


def update_panel():
    try:
        file_name = sys.argv[2]
        input = open(file_name, 'r')
    except:
        input = sys.stdin

    records = csv.DictReader(input, delimiter=DELIMITER)

    # get panel, which should be the only thing on the first row
    for rec in records:
        panel_pk = rec['Year PK']
        break
    log('Panel PK: {0}'.format(str(panel_pk)))
    try:
        panel_id = Year.objects.get(pk=panel_pk).panel_id
    except Year.DoesNotExist:
        xlog('1984', 'Year has no existing panel.')

    qualtrics_request = QualtricsRequest()
    panel = qualtrics_request.get_panel(panel_id)

    # make a list of just the eids (well, the ExternalDataReference) so that we
    # have a concise list of who is already in the panel
    panel_eids = [student['ExternalDataReference'] for student in panel if student.get('ExternalDataReference', False)]

    temp = 0
    for student in records:
        if student['ExternalDataRef'] not in panel_eids:
            result = qualtrics_request.add_recipient(panel_id, student)

    try:
        file_name.close()
    except:
        pass

class Command(BaseCommand):  # REQUIRED, must be at bottom
    update_panel()
    quit(0)
