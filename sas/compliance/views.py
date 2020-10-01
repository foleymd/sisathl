import logging

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from utbroker.errors import UTBrokerError

from sisathl.sas.compliance.pdas.nrdpaec7 import Nrdpaec7
from sisathl.sas.compliance.functions.authorization import *
from sisathl.sas.compliance.functions.qualtrics import QualtricsRequest
from sisathl.sas.compliance.models import Year, Survey
from sisathl.sas.compliance.functions.compliance_functions import render_error_page, \
    get_academic_year_object, get_fall_ccyys
from sisathl.sas.utils.utils import get_current_ccyys, get_academic_year_range, \
    make_broker_call, FatalError


@authorization
def admin(request):
    """Main list of administrative functions for the compliance forms
    """

    if request.session[COMPLIANCE_LVL] != COMPLIANCE_ADMIN:
        logging.error('Attempt to login to admin site by {0}'.format(request.META['HTTP_UTLOGIN_EID']))
        return render_error_page(request)

    try:
        year = get_academic_year_object(request)
    except Exception as exception:
        return render_error_page(request, str(exception))

    panel_loaded = True if year else False
    if year:
        fall_ccyys = year.fall_ccyys
        academic_year = year.academic_year_display
    else:
        try:
            current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
        except Exception as exception:
            return render_error_page(request, str(exception))
        fall_ccyys = get_fall_ccyys(current_ccyys)
        academic_year = get_academic_year_range(current_ccyys)

    context = {'fall_ccyys': fall_ccyys,
               'academic_year': academic_year,
               'panel_loaded': panel_loaded,
               }
    return render(request, "admin.html", context, context_instance=RequestContext(request))


@authorization
def create_panel(request):
    """Pulls student information from mainframe and send data to Qualtrics to create a panel.
    """

    if request.session[COMPLIANCE_LVL] != COMPLIANCE_ADMIN:
        return render_error_page(request)

    try:
        fall_ccyys = request.GET['fall_ccyys']
    except KeyError:
        return render_error_page(request, 'No academic year provided. Please contact an analyst.')

    try:
        year = Year.objects.get(fall_ccyys=fall_ccyys)
    except Year.DoesNotExist:  # create it
        if settings.PYPE_SERVICE != 'PROD':
            panel_name = "{0} {1} Athletes for compliance forms".format(settings.PYPE_SERVICE, get_academic_year_range(fall_ccyys))
        else:
            panel_name = "{0} Athletes for compliance forms".format(get_academic_year_range(fall_ccyys))
        qualtrics_request = QualtricsRequest()
        panel_id = qualtrics_request.create_panel(panel_name)
        year = Year.objects.create(fall_ccyys=fall_ccyys,
                                   panel_id=panel_id,
                                   panel_name=panel_name)

    nrdpaec7 = Nrdpaec7()               
    nrdpaec7.send.fall_ccyys = fall_ccyys
    nrdpaec7.send.year_pk = year.pk
    error_msg = ''

    try:
        make_broker_call(request, nrdpaec7)
    except (UTBrokerError, FatalError) as exception:
        error_msg = 'Exception submitting job: {0}'.format(str(exception))
        logging.error(error_msg)

    if nrdpaec7.recv.return_code:
        error_msg = "%s (%s)" % (nrdpaec7.recv.return_msg, nrdpaec7.recv.return_code)

    if error_msg:
        messages.error(request, error_msg)
    else:
        success_message = 'The batch job to load the students has been successfully submitted. ' \
                          'The name of your new or updated panel is: {0}'.format(year.panel_name)
        user = request.META['HTTP_UTLOGIN_EID']  # TODO: update to use actual admin stuff
        logging.info('{0} submitted job numbers {1} to create panel {2}'.format(user, nrdpaec7.recv.job_nbr, year.panel_name))
        messages.success(request, success_message)

    return HttpResponseRedirect(reverse('admin'))


@authorization
def student(request):
    """Main list of forms available to a student
    """

    if not request.session.get(COMPLIANCE_LVL, False):
        return render_error_page(request)

    context = {}

    try:
        year = get_academic_year_object(request)
    except Exception as exception:
        return render_error_page(request, str(exception))

    if year:
        context['fall_ccyys'] = year.fall_ccyys
        context['academic_year'] = year.academic_year_display

    qualtrics_request = QualtricsRequest()
    surveys = Survey.objects.filter(year=year)
    for survey in surveys:
        survey_name = qualtrics_request.get_survey_name(survey.survey_id)
        survey.name = survey_name
        survey_link = qualtrics_request.get_survey_link(survey.survey_id)
        survey.link = survey_link
    context['surveys'] = surveys

    return render(request, "student.html", context, context_instance=RequestContext(request))
