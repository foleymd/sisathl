from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import Athlete, AthleteCcyys


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


def parse_athlete_ccyys(line):
    '''Takes a line of data representing a student athlete profile record and parses it, returning
    one athlete profile dictionary that includes ccyys info. mainframe dataset = NR.NRPBAEC1.PROFILE'''

    uin = line[:16].strip()
    ncaa_id = line[17:27].strip()
    sri = line[28:37].strip()
    eid = line[38:46].strip()
    name = line[47:72].strip()
    ccyys = line[73:78].strip()
    num_ft_semesters = line[79:82].strip()

    
    return {'uin': uin,
            'ncaa_id': ncaa_id,
            'sri': sri,
            'eid': eid,
            'name': name,
            'ccyys': ccyys,
            'num_ft_semesters': num_ft_semesters,
            }


def store_athletes():
    '''Updates athlete table and athleteccyys table.'''
 
    # first some environmental data to the "error" output.
    log ("storing athletes")
    log ("settings.DATABASES: {0}", settings.DATABASES)
    log ("argv: {0}", sys.argv)
    lineCount = 0

    try:
        f = sys.argv[2]
        input = open(f, 'r')
    except:
        input = sys.stdin
 
    for line in input:
#     for line in sys.stdin:
        lineCount += 1
        
        athlete_ccyys = parse_athlete_ccyys(line)
 
        if Athlete.objects.filter(uin = athlete_ccyys['uin']).count() > 0:
            athlete = update_athlete(athlete_ccyys)
        else:
            athlete = store_new_athlete(athlete_ccyys)
             
        if AthleteCcyys.objects.filter(athlete = athlete).filter(ccyys = athlete_ccyys['ccyys']).count() > 0:
            update_ccyys(athlete_ccyys, athlete)
        else:
            store_new_ccyys(athlete_ccyys, athlete)
    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 


def store_new_athlete(athlete):
    '''Add new profile record for a student-athlete'''
 
    g = Athlete.objects.create(uin = athlete['uin'],
                               ncaa_id = athlete['ncaa_id'],
                               sri = athlete['sri'],
                               eid = athlete['eid'],
                               name = athlete['name'])
    return g
    
    
def store_new_ccyys(athlete_ccyys, athlete):
    '''Add new ccyys record for a student-athlete.'''
 
    g = AthleteCcyys.objects.create(athlete = athlete,
                                    ccyys = athlete_ccyys['ccyys'],
                                    num_ft_semesters = athlete_ccyys['num_ft_semesters'])
    return g
  

def update_athlete(athlete):
    '''If there is already a profile entry for a student-athlete, this updates it when appropriate.'''
 
    try:
        athlete_to_update = Athlete.objects.get(uin = athlete['uin'])
    except MultipleObjectsReturned as e:
        xlog(1, "Multiple records found for " + athlete['uin'])
 
    athlete_to_update.uin = athlete['uin']
    athlete_to_update.ncaa_id = athlete['ncaa_id']
    athlete_to_update.sri = athlete['sri']
    athlete_to_update.eid = athlete['eid']
    athlete_to_update.name = athlete['name']
 
    athlete_to_update.save()
 
    return athlete_to_update
 
 
def update_ccyys(athlete_ccyys, athlete):
    '''If there is already a ccyys entry for a student-athlete, this updates it when appropriate.'''
 
    try:
        ccyys_to_update = AthleteCcyys.objects.get(athlete = athlete, ccyys = athlete_ccyys['ccyys'])
    except MultipleObjectsReturned as e:
        xlog(1, "Multiple records found for " + athlete_ccyys['uin'] + " " + str(athlete_ccyys[ccyys]))
 
    ccyys_to_update.ccyys = athlete_ccyys['ccyys']
    ccyys_to_update.num_ft_semesters = athlete_ccyys['num_ft_semesters']
 
    ccyys_to_update.save()
  
    
class Command(BaseCommand): #REQUIRED, must be at bottom
    store_athletes()
    quit(0)