"""Runs as part of job group NRJGSCHS S0001. The previous job creates a dataset of
schools and majors, and this parses them to store in the major and school
tables."""

from datetime import datetime
import sys
import csv

from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.conf import settings

from sisathl.sas.sp.models import *


# standard logging and error handling
argv = sys.argv
def log(fmt, *args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write(argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write(str.format (fmt, *args) + "\n")
def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log(fmt, *args)
    quit(exitCode)


def upload_schools_and_majors():
    # first some environmental data to the "error" output.
    log ("Uploading schools and majors")
    log ("settings.DATABASES: {0}", settings.DATABASES)
    log ("argv: {0}", sys.argv)
    
    # try to open from command line, else use sys.stdin from TM
    try:
        f = sys.argv[2]
        input = open(f, 'r')
    except:
        input = sys.stdin
 
    records = csv.DictReader(input, dialect='excel', delimiter='\t')
    
    for record in records:
        if not record['begin_ccyys']:
            record['begin_ccyys'] = 0
        if not record['end_ccyys']:
            record['end_ccyys'] = 0

        try:
            school = School.objects.get(code=record['school_code'])
        except School.DoesNotExist:
            school = School.objects.create(code=record['school_code'],
                                           name=record['school_name'],
                                           begin_ccyys = record['begin_ccyys'],
                                           end_ccyys = record['end_ccyys'],
                                           )
        # update end date for schools as needed
        # at this point, the ccyys in the db is an int
        # and we are trying to compare it to the string from the record
        if school.end_ccyys < int(record['end_ccyys']):
            school.end_ccyys = record['end_ccyys']
            school.save()
        
        # Some records are placeholders. The valid major codes will be all
        # numeric. Skip to the top if it's a placeholder.
        try:
            major_code = int(record['major_code'])
        except:
            continue
        
        try:
            major = Major.objects.get(school=school, code=record['major_code'])
        except Major.DoesNotExist:
            major = Major.objects.create(school=school,
                                         code=record['major_code'],
                                         short_desc=record['short_major_desc'],
                                         long_desc=record['long_major_desc'],
                                         full_title=record['full_major_title'],
                                         begin_ccyys=record['begin_ccyys'],
                                         end_ccyys=record['end_ccyys'],)
        # update end date for majors as needed
        if major.end_ccyys < int(record['end_ccyys']):
            major.end_ccyys = record['end_ccyys']
            major.save()
            
    # close out the dataset that's in memory
    try:
        f.close()
    except:
        pass 

class Command(BaseCommand):
    upload_schools_and_majors()
    quit()