import sys, csv

from django.core.management.base import BaseCommand, CommandError #REQUIRED

from sisathl.sas.sp.models import AthleteCcyysSport, AthleteMajor, AthleteCcyysAdmin, Comments

argv = sys.argv

def log (fmt,*args):    # writes on stderr, which gets copied back to the Mainframe into the UNVERR DD.
  sys.stderr.write (argv[0] + "/" + argv[1] + ": ")  # identify the source of the message
  sys.stderr.write (str.format (fmt,*args) + "\n")
def xlog (exitCode, fmt, *args):    # log, then exit. Any non-zero exitCode indicates an error.
    log (fmt, *args)
    quit (exitCode)


def process_athletes():
    ''' Get some athletes, do some things so that we can have a collection of their percent progress data.'''

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
                  'Countable Hours',
                  'Total Hours Required',
                  'Percentage',
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

    # Getting a list of all percent forms for a given semester.
    athlete_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__ccyys=ccyys)\
        .filter(percentdegree__active=True)

    # Getting the max number sports, courses, and comments for any student in order to populate the header.
    max_sports = 0
    max_comments = 0

    for major in athlete_majors:
        sport_count = AthleteCcyysSport.objects.filter(athlete_ccyys = major.athlete_ccyys_admin.athlete_ccyys).count()
        if sport_count > max_sports:
            max_sports = sport_count
        form_id = major.percent_degree.id
        form_type = AthleteCcyysAdmin.PERCENT_FORM_TYPE(major.athlete_ccyys_admin)
        comment_count = Comments.objects.filter(form_id=form_id, form_type=form_type).count()
        if comment_count > max_comments:
            max_comments = comment_count

    # Adding sports to the header in the proper position.
    for i in range(1,max_sports+1):
        fieldnames.insert(i+3, 'Sport %d' % i) #places it in position and calls it Sport 1, 2, or 3 based on i value

    # Adding comments to the header.
    for i in range(1,max_comments+1):
        fieldnames.append('Comment %d' % i) #places it in position and calls it Comment 1, 2, or whatever based on i val

    # Writing the header based on fieldnames.
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
        fields['Countable Hours'] = major.percent_degree.projected_countable_hours
        fields['Total Hours Required'] = major.percent_degree.total_hours_required
        fields['Percentage'] = major.percent_degree.projected_percentage
        fields['Created By'] = major.percent_degree.created_by
        if major.percent_degree.created_by_date:
            fields['Created Date'] = major.percent_degree.created_by_date.strftime(timestamp_format)
        fields['Routed to Dean By'] = major.percent_degree.routed_to_dean_by
        if major.percent_degree.routed_to_dean_by_date:
            fields['Routed to Dean Date'] = major.percent_degree.routed_to_dean_by_date.strftime(timestamp_format)
        fields['Approved By Dean\'s Designee'] = major.percent_degree.approved_by_dean
        if major.percent_degree.approved_by_dean_date:
            fields['Approved By Dean Date'] = major.percent_degree.approved_by_dean_date.strftime(timestamp_format)
        fields['Routed To Registrar By'] = major.percent_degree.routed_to_reg_by
        if major.percent_degree.routed_to_reg_by_date:
            fields['Routed To Registrar Date'] = major.percent_degree.routed_to_reg_by_date.strftime(timestamp_format)
        fields['Approved By Registrar\'s Designee'] = major.percent_degree.approved_by_reg
        if major.percent_degree.approved_by_reg_date:
            fields['Approved By Registrar Date'] = major.percent_degree.approved_by_reg_date.strftime(timestamp_format)

        # Getting all athlete sports and then assigning them to the proper columns.
        athlete_sports = AthleteCcyysSport.objects.filter(athlete_ccyys=major.athlete_ccyys_admin.athlete_ccyys)
        for count, sport in enumerate(athlete_sports, start=1):
                fields['Sport %d' % count] = sport.sport

        # Getting comments on the form and adding them to the appropriate columns.
        form_id = major.percent_degree.id
        form_type = AthleteCcyysAdmin.PERCENT_FORM_TYPE(major.athlete_ccyys_admin)

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