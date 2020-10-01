from django.db.models import Count

from sisathl.sas.sp.models import AthleteCcyysSport, AthleteMajor
from sisathl.sas.utils.utils import render_sp_error_page
from sisathl.sas.utils.csv_export import convert_dicts_to_CSV_response


def inbox_download(student_majors):
    """Creates a csv download of the student major records provided. Assumes that
    the last update info is attached to queryset as an annotation."""
    student_recs = []
    for major in student_majors:
        sports = ''
        for sport in major.athlete_ccyys_admin.athlete_ccyys.squads:
            sports += str(sport[1]) + ' '

        if major.catalog_begin:
            catalog = major.catalog_begin + '-' + major.catalog_end
        else:
            catalog = None

        try:
            last_update = major.last_update.strftime('%b %d, %Y, %I:%M %p')
        except AttributeError:
            last_update = "not available"

        student = {'ccyys': major.athlete_ccyys_admin.athlete_ccyys.display_ccyys,
                   'eid': major.athlete_ccyys_admin.athlete_ccyys.athlete.eid,
                   'name': major.athlete_ccyys_admin.athlete_ccyys.athlete.name,
                   'school': major.school,
                   'major_name': major.major_name,
                   'minor': major.minor,
                   'catalog': catalog,
                   'sports': sports,
                   'spd_status': major.athlete_ccyys_admin.status,
                   'pd_status': major.percent_degree.status,
                   'last_update': last_update,
                   }
        student_recs.append(student)

    field_keys = ['ccyys', 'eid', 'name', 'school', 'major_name', 'minor', 'catalog', 'sports',
                  'spd_status', 'pd_status', 'last_update']
    csv_title = 'athletic_forms_status'
    field_display_titles = ['Semester', 'EID', 'Name', 'School', 'Major', 'Minor', 'Catalog', 'Sport',
                            'SP Status', 'Percent Status', 'Last Update']
    response = convert_dicts_to_CSV_response(student_recs, field_keys, csv_title,
                                             header_msg=None, field_display_titles=field_display_titles)
    return response


def render_inbox_error_page(request, input):
    """Return a generic error if they have an invalid search. Not logging
    these because they will probably mostly be benign, like blanks."""
    msg = 'No forms were found for this search value: {0}'.format(input)
    return render_sp_error_page(request, msg)


def search_by_sport_code(sport_code):
    """Returns a queryset of student major records based on sports code."""
    # Can search for all track sports at once. See note in AthleteCcyysSport.
    if sport_code == AthleteCcyysSport.MENS_TRACK:
        athlete_ccyys = AthleteCcyysSport.objects.filter(sport__in=AthleteCcyysSport.MENS_TRACK_CODES)
        athlete_ccyys = athlete_ccyys.values('athlete_ccyys')
    elif sport_code == AthleteCcyysSport.WOMENS_TRACK:
        athlete_ccyys = AthleteCcyysSport.objects.filter(sport__in=AthleteCcyysSport.WOMENS_TRACK_CODES)
        athlete_ccyys = athlete_ccyys.values('athlete_ccyys')
    elif sport_code == AthleteCcyysSport.WOMENS_ROW_ALL:
        athlete_ccyys = AthleteCcyysSport.objects.filter(sport__in=AthleteCcyysSport.WOMENS_ROW_ALL_CODES)
        athlete_ccyys = athlete_ccyys.values('athlete_ccyys')
    else:
        athlete_ccyys = AthleteCcyysSport.objects.filter(sport=sport_code).values('athlete_ccyys')
    student_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__in=athlete_ccyys)
    return student_majors

# constants for sorting
# Define available sorting options and what syntax to use to get them
_VALID_SORTS = {
                'athlete': 'athlete_ccyys_admin__athlete_ccyys__athlete',
                'ccyys': 'athlete_ccyys_admin__athlete_ccyys',
                'school': 'school__name',
                'major': 'major_name',
                'minor': 'minor',
                'catalog': 'catalog_begin',
                'eid': 'athlete_ccyys_admin__athlete_ccyys__athlete__eid',
                'status_spd': 'status_spd',
                'status_pod': 'status_pod',
                'last_update': 'last_update',
               }

ASCENDING = 'A'
DESCENDING = 'D'
DEFAULT_SORT = 'athlete_ccyys_admin__athlete_ccyys__athlete'
DEFAULT_DIRECTION = ASCENDING


def sort_student_majors(student_majors, sort_key=DEFAULT_SORT, sort_direction=DEFAULT_DIRECTION):
    """Given a queryset of AthleteMajor objects, sorts them according to the key
    and direction. Also returns the next sort direction to use."""

    sort = _VALID_SORTS.get(sort_key, DEFAULT_SORT)

    # The big chunk below is for sorting. Mostly to sort by status.
    # Status is weird because it's not an actual field. We also
    # sort so inactive forms always appear last.
    if sort == 'status_spd':
        # this annotate statement should allow us to say if a field has anything in it
        student_majors = student_majors.annotate(has_routed_to_dean=Count('athlete_ccyys_admin__routed_to_dean_by')).annotate(has_approved_by_dean=Count('athlete_ccyys_admin__approved_by_dean')).annotate(has_routed_to_reg_by=Count('athlete_ccyys_admin__routed_to_reg_by')).annotate(has_approved_by_reg=Count('athlete_ccyys_admin__approved_by_reg'))
        INACTIVE_SORT = '-athlete_ccyys_admin__active'
    elif sort == 'status_pod':
        student_majors = student_majors.annotate(has_routed_to_dean=Count('percentdegree__routed_to_dean_by')).annotate(has_approved_by_dean=Count('percentdegree__approved_by_dean')).annotate(has_routed_to_reg_by=Count('percentdegree__routed_to_reg_by')).annotate(has_approved_by_reg=Count('percentdegree__approved_by_reg'))
        INACTIVE_SORT = '-percentdegree__active'

    if sort == 'status_spd' or sort == 'status_pod':  # either type of status sort
        if sort_direction == ASCENDING:
            # the '-has_blah' means that it will sort
            # items with stuff in that field first. 'has_blah'
            # means it will sort items with nothing in that
            # field first.
            student_majors = student_majors.order_by('has_routed_to_dean',
                                                     'has_approved_by_dean',
                                                     'has_routed_to_reg_by',
                                                     'has_approved_by_reg',
                                                     INACTIVE_SORT,
                                                     'athlete_ccyys_admin__athlete_ccyys__athlete')  # athlete name
        else:
            student_majors = student_majors.order_by('-has_approved_by_reg',
                                                     '-has_routed_to_reg_by',
                                                     '-has_approved_by_dean',
                                                     '-has_routed_to_dean',
                                                     INACTIVE_SORT,
                                                     'athlete_ccyys_admin__athlete_ccyys__athlete')  # athlete name
    else:  # sorting by a field other than status
        if sort_direction == DESCENDING:
            sort = '-' + sort
        student_majors = student_majors.order_by(sort)

    next_sort_direction = (ASCENDING if sort_direction == DESCENDING else DESCENDING)

    return student_majors, next_sort_direction
