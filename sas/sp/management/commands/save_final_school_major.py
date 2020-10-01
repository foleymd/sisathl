
from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import Athlete, AthleteCcyys, AthleteMajor

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

def parse_final_school_major(line):
    '''Takes a line of data containing a student's courses and parses it, returning
     dictionary that includes course info. mainframe dataset = NR.NRPBAEC1.CLASSES'''   
    
    uin = line[:16].strip()
    ccyys = line[17:22].strip()
    college_code = line[23:24].strip()
    college_name = line[25:41].strip()
    major_code = line[42:47].strip()
    major_name = line[48:64].strip()
    catalog_begin = line[65:69].strip()
    catalog_end = line[70:74].strip()
    first_or_second = line[75:76].strip()
    updater_eid = line[77:85].strip()
    
    return {
            'uin': uin,
            'ccyys': ccyys,
            'college_code': college_code,
            'college_name': college_name,
            'major_code': major_code,
            'major_name': major_name,
            'catalog_begin': catalog_begin,
            'catalog_end': catalog_end,
            'first_or_second': first_or_second,
            'updater_eid': updater_eid,
            }

def store_final_school_major():
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
        
        final_school_major = parse_final_school_major(line)
    
        athlete = Athlete.objects.get(uin = final_school_major['uin'])
        athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = final_school_major['ccyys'])
        
        final_school_major = store_new_final_school_major(final_school_major, athlete_ccyys)
        
           
    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 

def store_new_final_school_major(final_school_major, athlete_ccyys):
    '''Stores final catalog, college, and major info.'''

    try:
        major = AthleteMajor.objects.get(athlete_ccyys_admin__athlete_ccyys = athlete_ccyys,
                                         first_or_second = final_school_major['first_or_second'])
        major.final_college_code = final_school_major['college_code']
        major.final_college_name = final_school_major['college_name']
        major.final_major_code = final_school_major['major_code']
        major.final_major_name = final_school_major['major_name']
        major.final_catalog_begin = final_school_major['catalog_begin']
        major.final_catalog_end = final_school_major['catalog_end']
        major.save(updater = final_school_major['updater_eid'])

    except AthleteMajor.DoesNotExist:
        '''if first_or_second is not filled because it's not a major of record, which happens with custom forms'''
        try:
            majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys = athlete_ccyys,
                                             first_or_second=None)
            for major in majors:
                if not final_school_major['first_or_second']:
                    major.final_college_code = final_school_major['college_code']
                    major.final_college_name = final_school_major['college_name']
                    major.final_major_code = final_school_major['major_code']
                    major.final_major_name = final_school_major['major_name']
                    major.final_catalog_begin = final_school_major['catalog_begin']
                    major.final_catalog_end = final_school_major['catalog_end']
                    major.save(updater = final_school_major['updater_eid'])
        except AthleteMajor.DoesNotExist:
            print 'AthleteMajor for ' + final_school_major['uin'] + ' ' + final_school_major['first_or_second'] + ' not found.'



class Command(BaseCommand): #REQUIRED, must be at bottom
    print 'starting'
    store_final_school_major()
    quit(0)