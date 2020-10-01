
from django.core.management.base import BaseCommand, CommandError #REQUIRED
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings

from sisathl.sas.sp.models import Athlete, AthleteCcyys, AthleteCcyysSport


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


def parse_athlete_sport(line):
    '''Takes a line of data representing a student athlete sport record and parses it, returning
    one athlete sport dictionary. mainframe dataset = NR.NRPBAEC1.SPORTS'''

    uin = line[:16].strip()
    ccyys = line[17:22].strip()
    sport = line[23:26].strip()
    sport_description = line[27:87].strip()
    
    return {
            'uin': uin,
            'ccyys': ccyys,
            'sport': sport,
            'sport_description': sport_description,
            }

def store_sports():
    '''Stores all athletes' sports.'''
 
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
        
        athlete_sport = parse_athlete_sport(line)
        athlete = Athlete.objects.get(uin = athlete_sport['uin'])
        athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = athlete_sport['ccyys'])
    
        if AthleteCcyysSport.objects.filter(athlete_ccyys = athlete_ccyys, sport = athlete_sport['sport']).count() > 0:
            pass
        else:
            athlete_ccyys_sport = store_new_sport(athlete_sport, athlete_ccyys)
             

    log("Success: {0} lines", lineCount)

    try:
        f.close()
    except:
        pass 

def store_new_sport(athlete_sport, athlete_ccyys):
    '''Add new sport record per student/sport.'''
  
    g = AthleteCcyysSport.objects.create(athlete_ccyys = athlete_ccyys,
                                        sport = athlete_sport['sport'],
                                        sport_description = athlete_sport['sport_description'],
                                         )
    return g
  

class Command(BaseCommand): #REQUIRED, must be at bottom
    store_sports()
    quit(0)