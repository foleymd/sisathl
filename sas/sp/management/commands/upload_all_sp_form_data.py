import sys, csv

from django.core.management.base import BaseCommand, CommandError #REQUIRED

from sisathl.sas.sp.models import AthleteCcyysSport, AthleteMajor, Course, AdditionalCourse, AthleteCcyysAdmin, Comments

argv = sys.argv

def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write (str.format (fmt,*args) + "\n")

def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log (fmt, *args)
    quit (exitCode)


def process_athletes():
    ''' get some athletes, do some things so that we can have a collection of their satisfactory progress data'''

    # These bits are just sorting out where it's getting the input from--either locally or from Task Manager.
    try:
        input_file = sys.argv[2]
        input = open(input_file, 'r')
        for line in input:
            ccyys = line
    except:
        for line in sys.stdin:
            ccyys = int(line)

    try:
        output_file = sys.argv[3]
        output = open(output_file, 'w')
    except:
        output = sys.stdout

    # These fieldnames are for the dictwriter--they are used to write the header and match field values later.
    fieldnames = ['EID',
                  'Name',
                  'CCYYS',
                  'Number of FT Semesters',
                  'College',
                  'Major Code',
                  'Major Name',
                  'Minor',
                  'Catalog',
                  'Hours Undertaken',
                  'Projected Countable Hours',
                  'Final Countable Hours',
                  'Created By',
                  'Created Date',
                  'Routed to Dean By',
                  'Routed to Dean Date',
                  'Approved By Dean\'s Designee',
                  'Approved By Dean Date',
                  'Routed To Registrar By',
                  'Routed To Registrar Date',
                  'Approved By Registrar\'s Designee',
                  'Approved By Registrar Date',
                 ]



    # Getting a list of all sp forms for a given semester.
    athlete_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__ccyys=ccyys)\
        .filter(athlete_ccyys_admin__active=True)

    # Getting the max number sports, courses, and comments for any student in order to populate the header.
    max_sports = 0
    max_courses = 0
    max_additional_courses = 0
    max_comments = 0

    for major in athlete_majors:
        sport_count = AthleteCcyysSport.objects.filter(athlete_ccyys = major.athlete_ccyys_admin.athlete_ccyys).count()
        if sport_count > max_sports:
            max_sports = sport_count
        course_count = Course.objects.filter(major=major).count()
        if course_count > max_courses:
            max_courses = course_count
        additional_course_count = AdditionalCourse.objects.filter(major=major).count()
        if additional_course_count > max_additional_courses:
            max_additional_courses = additional_course_count
        form_id = major.athlete_ccyys_admin.id
        form_type = AthleteCcyysAdmin.SPD_FORM_TYPE(major.athlete_ccyys_admin)
        comment_count = Comments.objects.filter(form_id=form_id, form_type=form_type).count()
        if comment_count > max_comments:
            max_comments = comment_count

    # Adding sports to the header in the proper position.
    for i in range(1,max_sports+1):
        fieldnames.insert(i+3, 'Sport %d' % i)  #places it in position and calls it Sport 1, 2, or 3 based on i value

    # Making a list of shared parts of the header.
    course_header_list = ['FOS',
                          'Number',
                          'Unique',
                          'Credit Hours',
                          'Countable',
                          'Min. Grade Req.',
                          'P/F Accepted',
                          'Grade']

    # Adding the course header parts to the header for each course and type of course.
    for i in range(1, max_courses+1):  #regular courses
        fieldnames.extend(['Course %d %s' % (i, name) for name in course_header_list])

    for i in range(1, max_additional_courses+1):  #additional courses
        fieldnames.extend(['T/CBE/EXO Course %d %s' % (i, name) for name in course_header_list])

    # Adding comments to the header.
    for i in range(1,max_comments+1):
        fieldnames.append('Comment %d' % i) #places it in position and calls it Comment 1, 2, or whatever based on i val

    # Writing the header.
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator = '\n')
    writer.writeheader()

    # Centralizing timestamp format in case we want to change it all later.
    timestamp_format = '%Y-%m-%d %H:%M:%S %Z'

    # Now let's get that sweet major data and routing/approval data, woohoo.
    for major in athlete_majors:
        fields = {}
        fields['EID'] = major.athlete_ccyys_admin.athlete_ccyys.athlete.eid
        fields['Name'] = major.athlete_ccyys_admin.athlete_ccyys.athlete.name
        fields['CCYYS'] = major.athlete_ccyys_admin.athlete_ccyys.ccyys
        fields['Number of FT Semesters'] = major.athlete_ccyys_admin.athlete_ccyys.num_ft_semesters
        fields['College'] = major.school
        fields['Major Code'] = major.major_code
        fields['Major Name'] = major.major_name
        fields['Minor'] = major.minor
        if major.catalog_begin:
            fields['Catalog'] = major.catalog_begin + '-' + major.catalog_end
        fields['Hours Undertaken'] = major.athlete_ccyys_admin.total_possible_countable_degree_hours
        fields['Projected Countable Hours'] = major.athlete_ccyys_admin.total_projected_degree_hours
        fields['Final Countable Hours'] = major.athlete_ccyys_admin.total_countable_degree_hours
        fields['Created By'] = major.athlete_ccyys_admin.created_by
        if major.athlete_ccyys_admin.created_by_date:
            fields['Created Date'] = major.athlete_ccyys_admin.created_by_date.strftime(timestamp_format)
        fields['Routed to Dean By'] = major.athlete_ccyys_admin.routed_to_dean_by
        if major.athlete_ccyys_admin.routed_to_dean_by_date:
            fields['Routed to Dean Date'] = major.athlete_ccyys_admin.routed_to_dean_by_date.strftime(timestamp_format)
        fields['Approved By Dean\'s Designee'] = major.athlete_ccyys_admin.approved_by_dean
        if major.athlete_ccyys_admin.approved_by_dean_date:
            fields['Approved By Dean Date'] = major.athlete_ccyys_admin.approved_by_dean_date.strftime(timestamp_format)
        fields['Routed To Registrar By'] = major.athlete_ccyys_admin.routed_to_reg_by
        if major.athlete_ccyys_admin.routed_to_reg_by_date:
            fields['Routed To Registrar Date'] = major.athlete_ccyys_admin.routed_to_reg_by_date\
                .strftime(timestamp_format)
        fields['Approved By Registrar\'s Designee'] = major.athlete_ccyys_admin.approved_by_reg
        if major.athlete_ccyys_admin.approved_by_reg_date:
            fields['Approved By Registrar Date'] = major.athlete_ccyys_admin.approved_by_reg_date\
                .strftime(timestamp_format)

        # getting all athlete sports and then assigning up to three to the proper columns
        athlete_sports = AthleteCcyysSport.objects.filter(athlete_ccyys=major.athlete_ccyys_admin.athlete_ccyys)

        for count, sport in enumerate(athlete_sports, start=1):
            fields['Sport %d' % count] = sport.sport

        # Getting a student's courses and then adding them to the appropriate columns.
        courses = Course.objects.filter(major=major)
        additional_courses = AdditionalCourse.objects.filter(major=major)

        for count, course in enumerate(courses, start=1):
            fields['Course %d FOS' % count] = course.course_category
            fields['Course %d Number' % count] = course.course_number
            fields['Course %d Unique' % count] = course.unique
            fields['Course %d Credit Hours' % count] = course.credit_hours
            fields['Course %d Countable' % count] = course.countable
            fields['Course %d Min. Grade Req.' % count] = course.min_grade_required
            fields['Course %d P/F Accepted' % count] = course.pass_fail_accepted
            fields['Course %d Grade' % count] = course.grade

        for count, course in enumerate(additional_courses, start=1):
            fields['T/CBE/EXO Course %d FOS' % count] = course.course_category
            fields['T/CBE/EXO Course %d Number' % count] = course.course_number
            fields['T/CBE/EXO Course %d Unique' % count] = course.unique
            fields['T/CBE/EXO Course %d Credit Hours' % count] = course.credit_hours
            fields['T/CBE/EXO Course %d Countable' % count] = course.countable
            fields['T/CBE/EXO Course %d Min. Grade Req.' % count] = course.min_grade_required
            fields['T/CBE/EXO Course %d P/F Accepted' % count] = course.pass_fail_accepted
            fields['T/CBE/EXO Course %d Grade' % count] = course.grade

        # Getting comments on the form and adding them to the appropriate columns.
        form_id = major.athlete_ccyys_admin.id
        form_type = AthleteCcyysAdmin.SPD_FORM_TYPE(major.athlete_ccyys_admin)

        comments = Comments.objects.filter(form_id=form_id, form_type=form_type)

        for count, comment in enumerate(comments, start=1):
            fields['Comment %d' % count] = comment.comments

        try:
            writer.writerow(fields)

        except:
            xlog(1, "can't write stdout/UNVOUT")

    # Closing any open files if we need to.
    try:
        input_file.close()
    except:
        pass

    try:
        output_file.close()
    except:
        pass


class Command(BaseCommand): #REQUIRED
    process_athletes()
    quit(0)