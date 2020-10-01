from decimal import Decimal
import logging

from django.contrib import messages
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.core.paginator import Paginator
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from utbroker.errors import UTBrokerError

from sisathl.sas.sp.pdas.nrdpaec4 import Nrdpaec4
from sisathl.sas.sp.pdas.nrdpaec5 import Nrdpaec5
from sisathl.sas.utils.constants import *


logger = logging.getLogger(__name__)


# The following are all constants of grade display names
# It includes any that we could expect to be on a student
# record on the mainframe.
A_PLUS = 'A+'
A = 'A'
A_MINUS = 'A-'
B_PLUS = 'B+'
B = 'B'
B_MINUS = 'B-'
C_PLUS = 'C+'
C = 'C'
C_MINUS = 'C-'
D_PLUS = 'D+'
D = 'D'
D_MINUS = 'D-'
F = 'F'

CREDIT = 'CR'
NO_CREDIT = 'NC'

Z = 'Z'
X = 'X'
I = 'I'
Q_DROP = 'Q'
WITHDRAWAL = 'W'
OBLIT = 'O'

GRADES = {
          A_PLUS: 4.00,
          A: 4.00,
          A_MINUS: 3.67,
          B_PLUS: 3.33,
          B: 3.00,
          B_MINUS: 2.67,
          C_PLUS: 2.33,
          C: 2.00,
          C_MINUS: 1.67,
          D_PLUS: 1.33,
          D: 1.00,
          D_MINUS: 0.67,
          F: 0.00,

          CREDIT: 0.00,
          NO_CREDIT: 0.00,

          Z: 0.00,
          X: 0.00,
          I: 0.00,
          Q_DROP: 0.00,
          WITHDRAWAL: 0.00,
          OBLIT: 0.00
         }

LETTER_GRADES = [
                 A,
                 A_MINUS,
                 B_PLUS,
                 B,
                 B_MINUS,
                 C_PLUS,
                 C,
                 C_MINUS,
                 D_PLUS,
                 D,
                 D_MINUS,
                 F
                ]

MIN_GRADE_REQUIRED = (('', '--'),
                      ('CR', 'CR'),
                      ('D-', 'D-'),
                      ('D', 'D'),
                      ('D+', 'D+'),
                      ('C-', 'C-'),
                      ('C', 'C'),
                      ('C+', 'C+'),
                      ('B-', 'B-'),
                      ('B', 'B'),
                      ('B+', 'B+'),
                      ('A-', 'A-'),
                      ('A', 'A'),
                      ('A+', 'A+'),
                      ('CR', 'CR'),
                      )

FINAL_GRADES = (('', '--'),
                ('A+', 'A+'),
                ('A', 'A'),
                ('A-', 'A-'),
                ('B+', 'B+'),
                ('B', 'B'),
                ('B-', 'B-'),
                ('C+', 'C+'),
                ('C', 'C'),
                ('C-', 'C-'),
                ('D+', 'D+'),
                ('D', 'D'),                                                                                                                               
                ('D-', 'D-'),
                ('F', 'F'),
                ('CR', 'CR'),
                ('NC', 'NC'),
                ('Z', 'Z'),                                                                                                                               
                ('X', 'X'),
                ('I', 'I'),
                ('Q', 'Q'),                                                                                                                               
                ('W', 'W'),
                ('O', 'O')
                )


YES_NO = (('', '--'),
          ('N', 'No'),
          ('Y', 'Yes'),
          )


def evaluate_for_countable_hrs(min_required, pf_counts, grade=False):
    """Decide if this course is eligible to be counted towards degree hours."""
    
    # if there's no grade at all, it doesn't count.
    if not grade:
        return False
    
    # If a class grade is marked as NC, those hours are never
    # going to be countable.
    if grade == NO_CREDIT:
        return False

    # If a class grade is CR, they count as long as the
    # advisor said that Pass/Fail counts
    if grade == CREDIT:
        if pf_counts == 'Y':
            return True
        else:
            return False

    try:
        grade_value = GRADES[grade]
        min_required_value = GRADES[min_required]
    except KeyError:     # these grades don't exist
        logger.error('Tried to evaluate grades: ' + str(grade) + ' ' + str(min_required))
        return False

    if min_required == CREDIT:
        return grade_value > 0

    # for all other grades, the grade must rank
    # equal to or higher than the min required grade.    
    return grade_value >= min_required_value


def render_sp_error_page(request, error_msg=False):
    """Renders a generic page with a generic error message unless a message
    is provided."""
    if not error_msg:
        error_msg = 'An error has occurred. Please contact Athletic Student Services.'
    messages.error(request, error_msg)
    return HttpResponseRedirect(reverse('sp_error'))


def ccyys_to_display(ccyys):
    """Converts a year-semester to readable text. If a bogus
    CCYYS is provided it returns it as is."""
    try:
        ccyys = str(ccyys)
    except TypeError:
        return ccyys

    try:
        semester = ccyys[4:]
        year_ccyy = ccyys[:4]
    except IndexError:
        return ccyys

    if semester == SPRING:
        return 'Spring {0}'.format(year_ccyy)
    elif semester == SUMMER:
        return 'Summer {0}'.format(year_ccyy)
    elif semester == FALL:
        return 'Fall {0}'.format(year_ccyy)
    else:
        return ccyys


class FatalError(Exception):
    """Custom exception for handing 'X' errors
    from Natural. Yoinked from the FIS broker code."""
    def __init__(self, pda, request):
        super(FatalError, self).__init__(pda.recv.return_msg)
        self.pda = pda
        self.request = request
        
        
def make_broker_call(request, pda):
    """Deals with all of the generic broker call code."""
    pda.send.webtoken = request.META['HTTP_TOKEN']
    
    try:
        pda.call_broker_once(service=request.META['HTTP_SERVICE'])
    except UTBrokerError as exception:
        messages.error(request, str(exception))
        raise exception
         
    if pda.recv.return_code:
        error_msg = "%s (%s)" % (pda.recv.return_msg, pda.recv.return_code)
        messages.error(request, error_msg)
    if pda.recv.return_code.startswith('X'):
        raise FatalError(pda, request)
    
    # if we got here, we have no fatal errors
    return pda


def get_last_day(request, ccyys):
    """Returns last class day for a given semester from mainframe."""
    nrdpaec5 = Nrdpaec5()               
    nrdpaec5.send.ccyys = ccyys
    try:
        nrdpaec5 = make_broker_call(request, nrdpaec5)
    except (UTBrokerError, FatalError) as exception:
        logger.error('Exception getting last day: ' + str(exception))
        raise exception

    last_day = nrdpaec5.recv.last_day
    last_day_str = str(last_day)   
    last_day_date_object = datetime.datetime.strptime(last_day_str, '%Y%m%d')
    last_day = datetime.datetime.strftime(last_day_date_object, '%B %d, %Y')
    
    return last_day


def get_current_ccyys(request):
    """Returns the current semester as a CCYYS, a year (CCYY) and a semester
    (S). Uses session storage as necessary to avoid unnecessary broker
    calls."""
    # if it already exist in session, don't make
    # broker call again
    if request.session.get(CURRENT_CCYYS):
        return (request.session[CURRENT_CCYYS],
                request.session[CURRENT_YEAR],
                request.session[CURRENT_SEMESTER])

    # wasn't in session, so we make broker call.                
    nrdpaec4 = Nrdpaec4()               
    try:
        nrdpaec4 = make_broker_call(request, nrdpaec4)
    except (UTBrokerError, FatalError) as exception:
        logger.error('Exception getting current ccyys: ' + str(exception))
        raise exception

    current_ccyys = nrdpaec4.recv.current_ccyys   
    current_ccyy = nrdpaec4.recv.current_ccyy 
    current_s = nrdpaec4.recv.current_s 
    
    # add to session
    request.session[CURRENT_CCYYS] = str(current_ccyys)
    request.session[CURRENT_YEAR] = str(current_ccyy)
    request.session[CURRENT_SEMESTER] = str(current_s)
    request.session.set_expiry(TIMEOUT)
    
    return current_ccyys, current_ccyy, current_s


def get_previous_ccyys(request):
    """Returns the previous semester as a CCYYS,
    a year (CCYY) and a semester (S). """
    
    # make broker call
    nrdpaec4 = Nrdpaec4()               
    try:
        nrdpaec4 = make_broker_call(request, nrdpaec4)
    except (UTBrokerError, FatalError) as exception:
        logger.error('Exception getting prev ccyys: ' + str(exception))
        raise exception

    previous_ccyys = nrdpaec4.recv.previous_ccyys   
    previous_ccyy = nrdpaec4.recv.previous_ccyy 
    previous_s = nrdpaec4.recv.previous_s 
    
    return previous_ccyys, previous_ccyy, previous_s


def decimal_default(obj):
    """This is used to serialize the Decimal type 
    correctly as json."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def page_to_queryset(request, queryset):
    """Returns the next queryset based on user's paging request. This
    is the out-of-the-box paging code from the Django Docs."""

    paginator = Paginator(queryset, DEFAULT_PAGINATION_AMT)
    page = request.GET.get('page')

    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, return first page.
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return last page of results.
        queryset = paginator.page(paginator.num_pages)
    return queryset


def get_academic_year_range(current_ccyys):
    """Given a ccyys, it returns the academic year display.
    Example: 20199 returns 2019-2020, 20176 returns 2017-2018."""

    academic_year_format = "{0} - {1}"

    try:
        semester = str(current_ccyys)[4:5]
        ccyy = str(current_ccyys)[:4]
    except IndexError:
        return current_ccyys

    if semester == SPRING:
        begin_ccyys = int(ccyy) - 1
        return academic_year_format.format(begin_ccyys, ccyy)
    elif semester == SUMMER or semester == FALL:
        end_ccyys = int(ccyy) + 1
        return academic_year_format.format(ccyy, end_ccyys)
