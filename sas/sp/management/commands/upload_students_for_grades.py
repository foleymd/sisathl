from django.core.management.base import BaseCommand, CommandError #REQUIRED
from sisathl.sas.sp.models import Athlete, AthleteCcyys


from django.conf import settings

import sys
argv = sys.argv
def log (fmt,*args):   
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  
  sys.stderr.write (str.format (fmt,*args) + "\n")
def xlog (exitCode, fmt, *args):   
    log (fmt, *args)
    quit (exitCode)

def write_students():    
    log ("Django called me, I don't know why.")
    log ("settings.DATABASES: {0}", settings.DATABASES)
    log ("argv: {0}", sys.argv)
    lineCount = 0

    try:
        f = sys.argv[2]
        input = open(f, 'r')
    except:
        input = sys.stdin
    
    for item in input:
        previous_ccyys = int(item)

    students = AthleteCcyys.objects.filter(ccyys = previous_ccyys) 
    
    for student in students:
        lineCount += 1
        uin = (student.athlete.uin)
        try:
            sys.stdout.write(uin + "\n") # sys.stdout is the dataset associated with the UNVOUT DD in the PyPE step.
        except:
            xlog (1, "can't write stdout/UNVOUT", uin)
    log ("Success: {0} lines", lineCount)


    try:
        f.close()
    except:
        pass


class Command(BaseCommand): #REQUIRED
    write_students()    
    quit(0)