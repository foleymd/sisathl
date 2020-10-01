"""This command is not currently in use. It is intended to load degree audit information after grades have run.
The users do not currently want that functionality."""
# import sys
# 
# from decimal import Decimal
# 
# from django.core.management.base import BaseCommand, CommandError #REQUIRED
# from django.core.exceptions import MultipleObjectsReturned
# from django.conf import settings
# 
# from sisathl.spd.spd_form.models import Athlete, AthleteCcyys, AthleteCcyysAdmin, AthleteMajor, PercentDegree, Comments
# 
# 
# """
# Simple command copies stdin (UNVIN) to stdout (UNVOUT) and leaves a note at stdout (UNVERR)  
# """
# import sys
# argv = sys.argv
# 
# def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
#   sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message 
#   sys.stderr.write (str.format (fmt,*args) + "\n")
# def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
#     log (fmt, *args)
#     quit (exitCode)
# 
# def parse_audit_results(line):
#     '''Takes a line of data representing a student athlete major record and parses it, returning
#     major dictionary. mainframe dataset = NR.NRPBAEC1.MAJOR'''
# 
#     print line
# 
#     audit_id = line[:12]
#     uin = line[12:28]
#     catalog_begin_ccyys = line[28:33]
#     catalog_end_ccyys = line[33:38]
#     college_code = line[38:39]
#     major_code = line [39:44]
#     total_hours_counted = line[44:50]
#     total_hours_needed = line[50:56]
#     percent_completed = line[56:61]
#     relevant_ccyys = line [61:66]
#     
#     # some fields not returned here/only for use with projected audit info
#     
#     return {
#             'audit_id': audit_id,
#             'uin': uin,
#             'college_code': college_code,
#             'major_code': major_code,
#             'total_hours_counted': total_hours_counted,
#             'percent_completed': percent_completed,
#             'relevant_ccyys': relevant_ccyys,
#             }
# 
# def store_audit_results():
#     '''Stores administrative details to admin table and major details to major table.'''
#  
#     # first some environmental data to the "error" output.
#     log ("storing majors")
#     log ("settings.DATABASES: {0}", settings.DATABASES)
#     log ("argv: {0}", sys.argv)
#     lineCount = 0
# 
#     try:
#         f = sys.argv[2]
#         input = open(f, 'r')
#     except:
#         input = sys.stdin
#  
#     for line in input:
#         lineCount += 1
#         audit_results = parse_audit_results(line)
#         try:
#             athlete = Athlete.objects.get(uin = audit_results['uin'])
#         except Athlete.DoesNotExist:
#             xlog(1984, 'Cannot find uin ' + audit_results['uin'])
#         try:
#             athlete_ccyys = AthleteCcyys.objects.get(athlete = athlete, ccyys = audit_results['relevant_ccyys'])
#         except AthleteCcyys.DoesNotExist:
#             xlog(1984, 'Cannot find uin ccyys combo: ' + audit_results['uin'] + ' ' + audit_results['relevant_ccyys'])
#        
#         try:
#             athlete_ccyys_admin = AthleteCcyysAdmin.objects.filter(athlete_ccyys = athlete_ccyys)           
#         except AthleteCcyys.DoesNotExist:
#             xlog(1984, 'Cannot find athlete_ccyys_admin for: ' + audit_results['uin'] + ' ' + audit_results['relevant_ccyys'])
#        
#         for admin in athlete_ccyys_admin:
#             major = AthleteMajor.objects.get(athlete_ccyys_admin = admin)
#             if major.major_code == audit_results['major_code']:
#                 confirmed_major = major
#                 store_percentage_info(confirmed_major, audit_results)
#                 print 'confirmed', 'a', major.major_code, 'b', audit_results['major_code'], 'c', confirmed_major
#             else: 
#                 rejected_major = major 
#                 print 'reject', 'a', major.major_code, 'b', audit_results['major_code'], 'c', rejected_major
#        
#         if confirmed_major:
#             store_percentage_info(confirmed_major, audit_results)
# 
#     percent = PercentDegree.objects.get(major = confirmed_major)
# 
# 
# #     if audit_results['uin'] == '7AE695FDB166D216':
# # #     if percent.projected_percentage == 0
# #         print audit_results['uin'], percent.projected_percentage, countable_hours, total_hours_required, projected_percentage, audit_results['total_hours_counted'], audit_results['total_hours_needed'], audit_results['percent_completed']
# 
#     log("Success: {0} lines", lineCount)
# 
#     try:
#         f.close()
#     except:
#         pass 
# 
# def store_percentage_info(confirmed_major, audit_results):
#     '''Update percentage info for athlete'''
#   
#     try:
#         percent = PercentDegree.objects.get(major = confirmed_major)
#                                              
#     except Exception as e:
#         print 'except', confirmed_major.id
#         message = 'Confirmed major id: ' + str(confirmed_major.id) + ', exception: ' + str(e)
#         xlog(1984, message)
#         
#     countable_hours = int(Decimal(audit_results['total_hours_counted'])) / 100
#     final_percentage = Decimal(audit_results['percent_completed']) / 100
#     
#     final_percentage = str(projected_percentage)
#      
#     percent.final_countable_hours = countable_hours
#     percent.final_percentage = final_percentage
#      
#     try:
#         percent = percent.save()
#     except:
#         "Unexpected error B:", sys.exc_info()[0],
#        
#     return percent
# 
# 
# class Command(BaseCommand): #REQUIRED, must be at bottom
#     store_audit_results()
#     quit(0)