from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from sisathl.sas.compliance.models import Year
from sisathl.sas.utils.constants import SPRING
from sisathl.sas.utils.utils import get_current_ccyys


def render_error_page(request, error_msg=False):
    """Renders a generic page with a generic error message unless a message
    is provided."""
    if not error_msg:
        error_msg = 'An error has occurred. Please contact Athletic Compliance.'
    messages.error(request, error_msg)
    return HttpResponseRedirect(reverse('compliance_error'))


def get_fall_ccyys(ccyys):
    ccyys = str(ccyys)
    try:
        year = ccyys[:4]
        semester = ccyys[4:5]
    except IndexError:
        return False

    if semester == SPRING:
        fall_ccyys = int("{0}9".format(int(year) - 1))
    else:
        fall_ccyys = int("{0}9".format(year))

    return fall_ccyys


def get_academic_year_object(request):
    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception:
        return False

    fall_ccyys = get_fall_ccyys(current_ccyys)

    try:
        year = Year.objects.get(fall_ccyys=fall_ccyys)
    except Year.DoesNotExist:
        return False

    return year