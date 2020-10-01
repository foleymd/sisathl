import sys

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

def store_audit_results():
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

                major.catalog_begin=audit_results['catalog_begin']
                major.catalog_end=audit_results['catalog_end']
                major.save(updater="NRNWAEC6")
                
                print 'confirmed', major
                
                store_percentage_info(major, audit_results)

            else: 
                print 'rejected', major

    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 

def store_percentage_info(major, audit_results):
    '''Update percentage info for athlete'''
  
    try:
        percent = PercentDegree.objects.get(major = major)                                             
    except Exception as e:
        message = 'Confirmed major id: ' + str(major.id) + ', exception: ' + str(e)
        xlog(1984, message)
        
    countable_hours = int(Decimal(audit_results['total_hours_counted'])) / 100
    total_hours_required = int(Decimal(audit_results['total_hours_needed'])) / 100
    projected_percentage = Decimal(audit_results['percent_completed']) / 100
    
    projected_percentage = str(projected_percentage)
     
    percent.projected_countable_hours = countable_hours
    percent.total_hours_required = total_hours_required
    percent.projected_percentage = projected_percentage
     
    try:
        percent = percent.save()
    except:
        "Unexpected error:", sys.exc_info()[0]
       
    return percent


class Command(BaseCommand): #REQUIRED, must be at bottom
    store_audit_results()
    quit(0)