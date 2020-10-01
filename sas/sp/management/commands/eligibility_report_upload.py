# Install in /pype/stage/code/<group>/<project>/<optional_child_folder(s)>/management/commands/template_batch.py
#Your Django scripts must be in the Command(BaseCommand) class
from django.core.management.base import BaseCommand, CommandError #REQUIRED
# from <module> import <command>
# from your_module import your_function
from sisathl.sas.sp.models import Athlete, AthleteCcyys, AthleteCcyysAdmin, AthleteMajor, PercentDegree
"""
Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)
"""

from django.conf import settings

import sys, csv, time

argv = sys.argv
def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message 
  sys.stderr.write (str.format (fmt,*args) + "\n")
def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log (fmt, *args)
    quit (exitCode)


def process_athlete():

  try:
    a = sys.argv[2]
    input = open(a, 'r')
  except: 
    input = sys.stdin

  try: 
    b = sys.argv[3]
    output = open(b, 'w')
  except:
    output = sys.stdout   
    
  try: 
    c = sys.argv[4]
    warnings = open(c, 'w')
  except:
    warnings = sys.stderr         
  
  ''' these fieldnames are for the dictwriter, and the names don't have to match up
  with the names in the dictreader'''
  
  fieldnames = ['EID',       
                'Name',                              
                'Eligibility Status',  
                'Seasons Used',        
                'Initial Collegiate Enrollment',        
                'Enrollment at UT',              
                'Five Year Expiration',
                'Q/NQ/Academic Redshirt',    
                'FT Terms Completed',    
                'Eval Semester Hours',    
                'Regular Hours',       
                'Summer Hours',                  
                'Hrs Toward Degree',
                'Req Hrs for Grad',
                'Degree Percentage',
                'Cum GPA',               
               ]                       
  
  
  writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator = '\n')
   
  warning_fieldnames = ['EID',        
                        'Message',              
                       ]     
  
  warning_writer = csv.DictWriter(warnings, fieldnames=warning_fieldnames, lineterminator = '\n')
  
  reader = csv.DictReader(input)
  
  line = 0
    
  for row in reader:
            
      line += 1

      if line == 1:

          output.write("Big 12 Conference Eligibility Report" + "\n" +
                        "Institution" + "," + "The University of Texas at Austin" + "\n" +
                        "Evaluation Semester" + "," + row['eval_ccyys'] + "\n" +
                        "Creation Semester" + "," + row['current_ccyys'] + "\n" +
                        "Creation Date" + "," + time.strftime("%m/%d/%Y") + "\n" +
                        "Sport" + "," + row['sport'] + "\n" +
                        "First Competition" + "\n" +
                        "Post. Comp. Date" + "\n" + "\n"
                       )
          warnings.write("Big 12 Conference Eligibility Report Warnings" + "\n" +
                        "Institution" + "," + "The University of Texas at Austin" + "\n" +
                        "Evaluation Semester" + "," + row['eval_ccyys'] + "\n" +
                        "Creation Semester" + "," + row['current_ccyys'] + "\n" +
                        "Creation Date" + "," + time.strftime("%m/%d/%Y") + "\n" +
                        "Sport" + "," + row['sport'] + "\n" + "\n"
                        )
          writer.writeheader()
          warning_writer.writeheader()

      athlete = None
      athlete_ccyys = None
      athlete_majors = None      
      eval_major = None
      career_countable_hours = None        
      total_hours_required = None
      percentage = None
      eval_ccyys_hours = None
      hours_prev_ccyys = None
      summer_hours = None     
      eval_ccyys_in_system = None
      prev_ccyys_in_system = None
      prev_summer_in_system = None
      percent_degree = None
      num_ft_semesters = None


      ''' the row['x'] names must line up with the header in the dataset 
      that is being read--so, in other words, these names need to match
      the names created by the Natural program NRPBB121'''
                 
      eid                    = row['eid'].strip()                 
      eval_ccyys             = row['eval_ccyys'].strip()        
      current_ccyys          = row['current_ccyys'].strip() 
      ccyys_previous_to_eval = row['ccyys_previous_to_eval'].strip()  
      ccyys_previous_summer  = row['ccyys_previous_summer'].strip()                  
      name                   = row['name'].strip()
      name                   = name.replace('"', '')
      num_ft_semesters       = row['num_ft_semesters'].strip()  
      import_school          = row['school'].strip()                                         
      import_major           = row['major'].strip()  
      
      try:
          athlete = Athlete.objects.get(eid=eid)
      except Athlete.DoesNotExist:
          message = 'No record for eid ' + eid + ' in SP system.'          
          try:
              warning_writer.writerow({'EID':     eid,      
                                       'Message': message,}) 
          except:
              xlog (1, "can't write stderr/UNVERR", eid, message) 
      
      if athlete:
          try:
              athlete_ccyys = AthleteCcyys.objects.get(athlete=athlete, ccyys=eval_ccyys)
          except AthleteCcyys.DoesNotExist: 
              message = 'No record for eid/ccyys combo', eid, eval_ccyys, 'in SP system.'        
              try:
                  warning_writer.writerow({'EID':     eid,      
                                           'Message': message,}) 
              except:
                  xlog (1, "can't write stderr/UNVERR", eid, message) 
                                
      if athlete_ccyys:
          try:
              athlete_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__exact=athlete_ccyys)
          except AthleteMajor.DoesNotExist:     
              message = 'No major records for eid/ccyys', eid, eval_ccyys, 'in SP system.'         
              try:
                  warning_writer.writerow({'EID':     eid,      
                                           'Message': message,}) 
              except:
                  xlog (1, "can't write stderr/UNVERR", eid, message)               
      
      if athlete_majors:
          for major in athlete_majors:  
                 
              try: 
                  percent_degree = PercentDegree.objects.get(major=major)
              except PercentDegree.DoesNotExist:
                  message = 'No percent degree records for eid/ccyys', eid, eval_ccyys, 'in SP system.'
                  try:
                      warning_writer.writerow({'EID':     eid,      
                                               'Message': message,}) 
                  except:
                      xlog (1, "can't write stderr/UNVERR", eid, message)                     
              else:    
                  '''getting percent degree stuff first. if we're looking for a specific major,
                  then load it. if we're not, get the the greatest one. '''
                  if percent_degree.active:
                      if import_major and major.major_code == import_major and major.school.code == import_school:
                          eval_major = major
                          career_countable_hours = percent_degree.projected_countable_hours
                          total_hours_required = percent_degree.total_hours_required
                          percentage = percent_degree.projected_percentage

                      elif not import_major:
                          if percent_degree.projected_percentage >= percentage:
                              eval_major = major
                              percentage = percent_degree.projected_percentage
                              career_countable_hours = percent_degree.projected_countable_hours
                              total_hours_required = percent_degree.total_hours_required
                        
                  ''' Next, get the countable hours for the eval semester, if available. '''
                  if eval_ccyys != current_ccyys:
                      try:
                          eval_major_admin = AthleteCcyysAdmin.objects.get(pk=eval_major.athlete_ccyys_admin.id)  
                          eval_ccyys_hours = eval_major_admin.total_countable_degree_hours
                          eval_ccyys_in_system = True
                          
                      except:
                          message = 'Countable hours not available for eval ccyys for', eid        
                          try:
                              warning_writer.writerow({'EID':     eid,      
                                                       'Message': message,}) 
                          except:
                              xlog (1, "can't write stderr/UNVERR", eid, message)   
                                                             
                  ''' next, get the countable hours for the prev semester, if available.
                  processing is different for 2 semesters vs anything else.'''
                  if num_ft_semesters != '2':              
                             
                      try:
                          athlete_prev_ccyys = AthleteCcyys.objects.get(athlete=athlete, ccyys=ccyys_previous_to_eval)
                          athlete_prev_ccyys_major = AthleteMajor.objects.get(athlete_ccyys_admin__athlete_ccyys__exact=athlete_prev_ccyys,

                                                                                    )
                          prev_ccyys_major_admin = AthleteCcyysAdmin.objects.get(pk=athlete_prev_ccyys_major.athlete_ccyys_admin.id) 
                          hours_prev_ccyys = prev_ccyys_major_admin.total_countable_degree_hours 
                          prev_ccyys_in_system = True   
                      except:
                          message = 'Countable hours not available for previous long ccyys for ' + eid        
                          try:
                              warning_writer.writerow({'EID':     eid,      
                                                       'Message': message,}) 
                          except:
                              xlog (1, "can't write stderr/UNVERR", eid, message)                             
                         
                      ''' next, get the countable hours for the prev summer, if available '''    
                      try:
            
                          athlete_prev_summer_ccyys = AthleteCcyys.objects.get(athlete=athlete, ccyys=ccyys_previous_summer)
                          prev_summer_ccyys_major = AthleteMajor.objects.get(athlete_ccyys_admin__athlete_ccyys__exact=athlete_prev_summer_ccyys, 
                                                                             major_code = eval_major.major_code,
                                                                             school = eval_major.school) 
                          prev_summer_major_admin = AthleteCcyysAdmin.objects.get(pk=prev_summer_ccyys_major.athlete_ccyys_admin.id) 
                          summer_hours = prev_summer_major_admin.total_countable_degree_hours
                          prev_summer_in_system = True    
                      except:
                          message = 'Countable hours not available for previous summer for '  + eid             
                          try:
                              warning_writer.writerow({'EID':     eid,      
                                                       'Message': message,}) 
                          except:
                              xlog (1, "can't write stderr/UNVERR", eid, message)                                   
                            
      ''' pick actual values for eval, regular, and summer hours here based on whether or not there are spud records.'''
      if not eval_ccyys_in_system: 
          eval_ccyys_hours       = row['eval_ccyys_hours'].strip()
      if not prev_ccyys_in_system:
          hours_prev_ccyys       = row['hours_prev_ccyys'].strip()    
      if not prev_summer_in_system:    
          summer_hours           = row['summer_hours'].strip()                   


      ''' the rules are different if you have 2 FT semesters, but luckily the Natural program has what we need '''
      if num_ft_semesters != '2':
          regular_hours = int(eval_ccyys_hours) + int(hours_prev_ccyys) 
      else: 
          regular_hours = row['regular_hours'].strip()
          summer_hours = row['summer_hours'].strip()     
 
      try:
          writer.writerow({                
                        'EID':                             row['eid'],                       
                        'Name':                            name,                              
                        'Eligibility Status':              row['eligibility status'],  
                        'Seasons Used':                    row['seasons_used'],        
                        'Initial Collegiate Enrollment':   row['fse_anywhere'],        
                        'Enrollment at UT':                row['fse_ut'],              
                        'Five Year Expiration':            row['five_year_expiration'],
                        'Q/NQ/Academic Redshirt':          row['qualifier_status'],    
                        'FT Terms Completed':              row['num_ft_semesters'],    
                        'Eval Semester Hours':             eval_ccyys_hours,    
                        'Regular Hours':                   regular_hours,       
                        'Summer Hours':                    summer_hours,                  
                        'Hrs Toward Degree':               career_countable_hours,
                        'Req Hrs for Grad':                total_hours_required,
                        'Degree Percentage':               percentage,      
                        'Cum GPA':                         row['cum_gpa'],               
                       }) 

      except:
        xlog (1, "can't write stdout/UNVOUT", row['eid'])

      try:
          a.close()
      except:
          pass 
      
      try:
          b.close()
      except:
          pass 
      
      try:
          c.close()
      except:
          pass 


class Command(BaseCommand): #REQUIRED
    process_athlete()    
    quit(0)