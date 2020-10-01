from collections import OrderedDict

from django.shortcuts import render_to_response, render
from django.conf import settings
from django.template import RequestContext

from utbroker.errors import UTBrokerError
from utdirect.templates import UTDirectContext

from sisathl.sas.portal.pdas.nrdpcp50 import Nrdpcp50
from sisathl.sas.compliance.functions.qualtrics import QualtricsRequest
from sisathl.sas.compliance.models import Survey
from sisathl.sas.compliance.functions.compliance_functions import render_error_page, \
    get_academic_year_object

# *************************************************************************** #
# Fill defaults for UTDirect API
# *************************************************************************** #

defaults = {'document_title': "Student Athlete System",
            'window_title': "Student Athlete System",
            'css_file': [settings.STATIC_URL + 'portal/portal.css'],
            'api_key': '8B54A49X54',
            'content_item_name': "Submission",
            }


def portal(request):
    """Checks appropriate security and renders page of compliance related
    links."""
    nrdpcp50 = Nrdpcp50()
    nrdpcp50.send.webtoken = request.META['HTTP_TOKEN']
    nrdpcp50.send.ip_address = request.META['REMOTE_ADDR']

    # **************************************************************************** #
    #                Broker Call
    # **************************************************************************** #

    try:
        nrdpcp50.call_broker_once(service=request.META['HTTP_SERVICE'])

    except UTBrokerError, error_info:
        exception_msg = str(error_info)
        return render_to_response('error.html', UTDirectContext(request,
                                                                {
                                                                    'exception_msg': exception_msg},
                                                                defaults=defaults,
                                                                document_title='Broker Error', ))

    # **************************************************************************** #
    #                Display
    # **************************************************************************** #
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
        survey_link = qualtrics_request.get_survey_link(survey.survey_id)
        context['survey_link'] = survey_link
        break  # only want first one for this page

    # this is all used for debug
    pda_send_dict = OrderedDict()
    pda_recv_dict = OrderedDict()
    for field in nrdpcp50.send:
        pda_send_dict[field] = getattr(nrdpcp50.send, field)
    for field in nrdpcp50.recv:
        pda_recv_dict[field] = getattr(nrdpcp50.recv, field)

    context['recv'] = nrdpcp50.recv
    context['send'] = nrdpcp50.send
    context['user'] = 'student'
    context['show_med_link'] = settings.SHOW_MED_LINK
    return render(request, "portal.html", context, context_instance=RequestContext(request))
