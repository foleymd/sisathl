import logging
from itertools import chain
from copy import deepcopy

from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.db.models import Max
from django.forms.models import modelformset_factory
from django.forms.widgets import Textarea, TextInput
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.contenttypes.models import ContentType

from utbroker.errors import UTBrokerError

from sisathl.sas.utils.authorization import *
from sisathl.sas.utils.constants import *
from sisathl.sas.utils.utils import (render_sp_error_page, ccyys_to_display, get_current_ccyys,
                                     get_last_day, make_broker_call,
                                     FatalError, page_to_queryset)
from sisathl.sas.utils.get_form import get_form, get_form_ccyys
from sisathl.sas.extra.ferpa.ut_ferpa_decorator import FERPACheck
from sisathl.sas.sp.models import (CcyysAdmin,
                                   Athlete,
                                   AthleteCcyys,
                                   AthleteCcyysAdmin,
                                   AthleteCcyysSport,
                                   AthleteMajor,
                                   Course,
                                   AdditionalCourse,
                                   FinalCourse,
                                   User,
                                   SpdFormLog,
                                   CourseLog,
                                   AdditionalCourseLog,
                                   PercentDegree,
                                   Comments,
                                   School,
                                   Major)
from sisathl.sas.sp.forms import (MajorForm,
                                  CourseForm,
                                  AdditionalCourseForm,
                                  AddUserForm,
                                  UpdateUserForm,
                                  PercentForm,
                                  CommentForm,
                                  AddCommentForm,
                                  ContactForm,
                                  CcyysAdminForm,
                                  CustomForm,
                                  )

from sisathl.sas.sp.functions.sp_functions import (inbox_download, render_inbox_error_page,
                                                   search_by_sport_code,
                                                   sort_student_majors, DEFAULT_SORT,
                                                   DEFAULT_DIRECTION)
from sisathl.sas.sp.pdas.nrdpaec1 import Nrdpaec1
from sisathl.sas.sp.pdas.nrdpaec2 import Nrdpaec2
from sisathl.sas.sp.pdas.nrdpaec6 import Nrdpaec6


logger = logging.getLogger(__name__)


@authorization
def index(request):
    """Eligibility Certification Home. Displays open and close dates for the
    system, for informational purposes only.
    """
    context = {}

    # make broker call to get current ccyys
    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception as exception:
        return render_sp_error_page(request, str(exception))

    if 'create_submitted' in request.GET:
        return redirect('create_forms_a', ccyys=current_ccyys)

    try:
        context['ccyys_admin'] = CcyysAdmin.objects.get(ccyys=current_ccyys)
    except CcyysAdmin.DoesNotExist:
        pass

    # In discussion with Jason and Chau, we decided to return the current
    # ccyys and the previous two.
    context['ccyys_admin_all'] = CcyysAdmin.objects.filter(ccyys__lte=current_ccyys).reverse()[:3]
    context['current_ccyy'] = current_ccyy
    context['current_s'] = current_s
    context['user_type'] = request.session[USER_TYPE]
    context['YEARS'] = YEARS
    context['SPORTS'] = AthleteCcyysSport.SPORTS
    return render(request, "index.html", context, context_instance=RequestContext(request))


@authorization
def create_forms(request):
    """Load student data from mainframe """

    # athletics only!
    if not request.session[USER_TYPE] == User.ATHLETICS:
        return render_sp_error_page(request, AUTH_ERROR_MSG)

    context = {}

    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception as exception:
        return render_sp_error_page(request, str(exception))

    try:
        ccyys_admin = CcyysAdmin.objects.get(ccyys=current_ccyys)
    except CcyysAdmin.DoesNotExist:
        messages.warning(request, 'You must first create a semester record before loading forms.')
        return redirect('ccyys_admin')



    nrdpaec1 = Nrdpaec1()

    if 'form_submitted' in request.GET and not ccyys_admin.forms_loaded:
        context['form_submitted'] = True

        # make broker call to generate forms
        try:
            nrdpaec1 = make_broker_call(request, nrdpaec1)
        except (UTBrokerError, FatalError) as exception:
            logger.error('Exception generating forms: {0}'.format(str(exception)))
            return render_sp_error_page(request, str(exception))

        if nrdpaec1.recv.return_code:
            logger.error('Exception generating forms: {0}'.format(str(nrdpaec1.recv.return_code)))
            return render_sp_error_page(request, str(nrdpaec1.recv.return_code))

        # success!
        ccyys_admin.forms_loaded = True
        ccyys_admin.save()
        success_message = 'Jobs '

        for job_number in nrdpaec1.recv.job_numbers:
            success_message += str(job_number) + ' '
        success_message += 'successfully submitted.'
        messages.success(request, success_message)

    context['nrdpaec1'] = nrdpaec1
    context['user_type'] = request.session[USER_TYPE]
    context['ccyys_admin'] = CcyysAdmin.objects.get(ccyys=current_ccyys)

    return render(request, "create_forms.html", context)


@FERPACheck
@authorization
def inbox(request, ccyys=None, eid=None, sport_code=None):
    """Form inbox. Lists forms available for user and allows sorting and searching
    of those forms."""

    user_college = request.session[USER_COLLEGE]
    context = {}

    # look in GET to see if a sort was specified
    sort_key = request.GET.get('sort', DEFAULT_SORT)
    sort_direction = request.GET.get('direction', DEFAULT_DIRECTION)

    # see if there are search variables in the GET, or session.
    # Session comes last, because if there's anything in the GET,
    # that's a new search and we want to prioritize that.
    if 'form_ccyy' in request.GET and 'form_s' in request.GET:
        ccyys = "{0}{1}".format(request.GET['form_ccyy'], request.GET['form_s'])
    else:  # check if we got one but not the other
        if ('form_ccyy' in request.GET and 'form_s' not in request.GET) or \
        ('form_ccyy' not in request.GET and 'form_s' in request.GET):
            return render_inbox_error_page(request, ccyys)

    eid = request.GET.get('eid', False)
    sport_code = request.GET.get('sport_code', False)

    if not ccyys and not eid and not sport_code:  # check the session
        ccyys = ccyys or request.session.get('ccyys', False)
        eid = eid or request.session.get('eid', False)
        sport_code = sport_code or request.session.get('sport_code', False)

    if not ccyys and not eid and not sport_code:  # we STILL have nothing
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
        ccyys = current_ccyys

    if ccyys:
        ccyys = int(ccyys)

        try:
            ccyys_admin = CcyysAdmin.objects.get(ccyys=ccyys)
            inbox_title = ccyys_admin.display_ccyys
        except CcyysAdmin.DoesNotExist:
            inbox_title = ccyys

        if sport_code:
            inbox_title = "{0} and {1}".format(inbox_title,
                                               AthleteCcyysSport.SPORTS[sport_code])

            student_majors = search_by_sport_code(sport_code)
            student_majors = student_majors.filter(athlete_ccyys_admin__athlete_ccyys__ccyys=ccyys)
        else:
            student_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__ccyys=ccyys)

    elif eid:
        try:
            athlete = Athlete.objects.get(eid=eid)
        except Athlete.DoesNotExist:
            return render_inbox_error_page(request, eid)
        inbox_title = athlete.name
        student_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__athlete__eid=eid)

    else:  # sport_code
        try:
            inbox_title = AthleteCcyysSport.SPORTS[sport_code]
        except KeyError:  # sport doesn't exist
            return render_inbox_error_page(request, sport_code)
        student_majors = search_by_sport_code(sport_code)

    if request.session[USER_TYPE] == User.DEAN:
        student_majors = student_majors.filter(school__code=user_college)

    if not student_majors:
        return render_inbox_error_page(request, str(inbox_title))

    # add last update info the query results
    student_majors = student_majors.annotate(last_update=Max('athlete_ccyys_admin__spdformlog__update_datetime'))

    # sort and page
    student_majors, next_sort_direction = sort_student_majors(student_majors, sort_key, sort_direction)
    student_majors = page_to_queryset(request, student_majors)

    if 'csv' in request.GET.get('export', ''):
        return inbox_download(student_majors)

    # store the search values so that user can return to this page.
    request.session['ccyys'] = ccyys
    request.session['eid'] = eid
    request.session['sport_code'] = sport_code
    context['ccyys'] = ccyys
    context['eid'] = eid
    context['sport_code'] = sport_code

    context['student_majors'] = student_majors
    context['user_type'] = request.session[USER_TYPE]
    context['YEARS'] = YEARS  # to populate drop down
    context['SPORTS'] = AthleteCcyysSport.SPORTS  # to populate dropdown
    context['inbox_title'] = inbox_title
    context['this_url'] = request.get_full_path()
    context['sort'] = sort_key
    context['direction'] = sort_direction
    context['sort_direction'] = next_sort_direction
    context['instructions_tag'] = "inbox"

    return render(request, 'inbox.html', context, context_instance=RequestContext(request))


@FERPACheck
@authorization
def student_details(request, major_id=''):
    """Renders and controls one spd form / athlete_ccyys_admin."""

    def _render_success_page(request):
        """Provides a success message and renders page after all of the various
        operations on this page are performed."""
        messages.success(request, 'The form has been saved and routed to the appropriate user.')
        return redirect('inbox')

    context = {}

    # user data
    user_type = request.session[USER_TYPE]
    user_college = request.session[USER_COLLEGE]

    if settings.PYPE_SERVICE != 'PROD':
        del request.session[USER_TYPE]  # resets user_type for testing purposes

    # athlete data from db. If major_id is blank, it will be caught by
    # the exception. An error can occur from a user manually adjusting url.
    try:
        major = AthleteMajor.objects.get(pk=major_id)
    except AthleteMajor.DoesNotExist:
        logger.error('Could not find major_id {0}.'.format(str(major_id)))
        return render_sp_error_page(request, 'No student found. Try your inbox!')

    athlete = Athlete.objects.get(pk=major.athlete_ccyys_admin.athlete_ccyys.athlete.id)
    athlete_ccyys = AthleteCcyys.objects.get(pk=major.athlete_ccyys_admin.athlete_ccyys.id)
    athlete_ccyys_admin = AthleteCcyysAdmin.objects.get(pk=major.athlete_ccyys_admin.id)
    ccyys = athlete_ccyys.ccyys
    athlete_ccyys_sport = AthleteCcyysSport.objects.filter(athlete_ccyys_id=major.athlete_ccyys_admin.athlete_ccyys.id)
    form_type_name = AthleteCcyysAdmin.SPD
    form_id = athlete_ccyys_admin.id
    user = User.objects.get(eid=request.session[USER_EID])
    users_turn = athlete_ccyys_admin.users_turn(user)
    routed_to_dean = athlete_ccyys_admin.routed_to_dean_by
    approved_by_reg = athlete_ccyys_admin.approved_by_reg

    if user_type == User.DEAN or (users_turn is False) or (user_type == User.ATHLETICS
    and athlete_ccyys_admin.routed_to_dean_by) or athlete_ccyys_admin.approved_by_reg:
        extra_num = 0
        addl_extra_num = 0
        can_delete = False
    else:
        extra_num = 1
        addl_extra_num = 2
        can_delete = True

    fields = ('course_category',
             'course_number',
             'unique',
             'credit_hours',
             'countable',
             'min_grade_required',
             'pass_fail_accepted',
             'grade')

    course_formset = modelformset_factory(Course, form=CourseForm,
                                          fields=fields,
                                          extra=extra_num,
                                          can_delete=can_delete,
                                          )

    additional_course_formset = modelformset_factory(AdditionalCourse, form=AdditionalCourseForm,
                                                     fields=fields,
                                                     extra=addl_extra_num,
                                                     can_delete=can_delete,
                                                     )

    # pda info--broker call gets current classes for a student prior to the final cert
    # These classes correspond to the 'current coursework on record' and reflect
    # the actual classes/grades on the mainframe. We might have forms for
    # athlete who aren't students (prospectives, etc). If we don't have an
    # SRI, we don't attempt to go to mainframe for classes.
    if major.athlete_ccyys_admin.athlete_ccyys.athlete.sri and not request.is_ajax():
        nrdpaec2 = Nrdpaec2()
        nrdpaec2.send.sri = major.athlete_ccyys_admin.athlete_ccyys.athlete.sri
        nrdpaec2.send.ccyys = ccyys
        try:
            nrdpaec2 = make_broker_call(request, nrdpaec2)
            classes = nrdpaec2.recv.classes[:int(10)]
        except (UTBrokerError, FatalError) as exception:
            logger.error('Exception calling NRNPAEC2: {0}'.format(str(exception)))
            return render_sp_error_page(request, str(exception))
    else:
        classes = []

    final_classes = FinalCourse.objects.filter(athlete_ccyys=athlete_ccyys)

    for each_class in chain(classes, final_classes):          # taking care of leading zeroes
        each_class.unique = each_class.unique.zfill(5)

    major_form = MajorForm(data=request.POST or None, instance=major,
                           user_type=user_type, users_turn=users_turn, ccyys=ccyys,
                           routed_to_dean=routed_to_dean, approved_by_reg=approved_by_reg,)

    if request.is_ajax():
        template_name = 'major_form.html'
    else:
        template_name = 'spd_form.html'

        course_formset = course_formset(data=request.POST or None, prefix='cou',
                                        queryset=Course.objects.filter(major_id=major_id))
        additional_course_formset = additional_course_formset(data=request.POST or None,
                                                              prefix='adl', queryset=AdditionalCourse.objects.filter(major_id=major_id))

        all_formsets = chain(course_formset, additional_course_formset)

        for form in all_formsets:

            if not users_turn or (user_type == User.ATHLETICS and athlete_ccyys_admin.routed_to_dean_by) \
            or user_type == User.DEAN or athlete_ccyys_admin.approved_by_reg:
                form.fields['course_category'].widget.attrs['readonly'] = 'readonly'
                form.fields['course_number'].widget.attrs['readonly'] = 'readonly'
                form.fields['unique'].widget.attrs['readonly'] = 'readonly'
                form.fields['credit_hours'].widget.attrs['readonly'] = 'readonly'

            if not users_turn or user_type == User.ATHLETICS or athlete_ccyys_admin.approved_by_reg \
            or (user_type == User.DEAN and (athlete_ccyys_admin.approved_by_dean or not athlete_ccyys_admin.routed_to_dean_by)):
                form.fields['countable'].widget = TextInput(attrs={'readonly': 'readonly'})
                form.fields['min_grade_required'].widget = TextInput(attrs={'readonly': 'readonly'})
                form.fields['pass_fail_accepted'].widget = TextInput(attrs={'readonly': 'readonly'})

            if not users_turn or user_type != User.REGISTRAR or athlete_ccyys_admin.approved_by_reg:
                form.fields['grade'].widget = TextInput(attrs={'readonly': 'readonly'})

    # load up all of our variables into the context
    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception as exception:
        return render_sp_error_page(request, str(exception))
    try:
        context['last_day'] = get_last_day(request, ccyys=athlete_ccyys.ccyys)
    except Exception:
        pass
    try:
        context['nrdpaec2'] = nrdpaec2
        context['has_coursework'] = True
    except UnboundLocalError:
        pass

    context['YEARS'] = YEARS
    context['SPORTS'] = AthleteCcyysSport.SPORTS
    context['user_type'] = user_type
    context['user_college'] = user_college
    context['athlete'] = athlete
    context['athlete_ccyys'] = athlete_ccyys
    context['athlete_ccyys_sport'] = athlete_ccyys_sport
    context['athlete_ccyys_admin'] = athlete_ccyys_admin
    context['school'] = major.school
    context['major'] = major
    context['major_desc'] = "{0} {1}".format(major.major_code, major.major_name)
    context['additional_course_formset'] = additional_course_formset
    context['major_form'] = major_form
    context['course_formset'] = course_formset
    context['classes'] = classes  # actual classes from mainframe
    context['final_classes'] = final_classes  # finalized classes at end of semester
    context['users_turn'] = users_turn
    context['advance_recipient'] = athlete_ccyys_admin.advance_recipient
    context['return_recipient'] = athlete_ccyys_admin.return_recipient
    context['form_id'] = form_id
    context['form_type_name'] = form_type_name
    context['signature_info'] = athlete_ccyys_admin.signature_info
    context['current_ccyys'] = current_ccyys
    context['current_ccyys_int'] = int(current_ccyys)
    context['this_url'] = request.get_full_path()
    context['instructions_tag'] = 'spd'

    # the following block occurs after a user has submitted the form
    if not request.is_ajax() and request.method == 'POST':
        # all three forms (major, course, and addtl courses) need to be  valid to perform an action like save/sign/return
        if major_form.is_valid() and course_formset.is_valid() and additional_course_formset.is_valid():

            if major_form.has_changed():
                athlete_ccyys_admins = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys)

                for admin in athlete_ccyys_admins:
                    # get the major for the associated admin so that we can check the major code against the input
                    athlete_major = AthleteMajor.objects.get(athlete_ccyys_admin_id=admin.id)

                    # note that the below check includes catalog year!!!!! so student can have multiple forms with the same major but different catalogs
                    if athlete_major.major_code == major_form.cleaned_data.get('major_code') \
                    and athlete_major.school == major_form.cleaned_data.get('school') \
                    and athlete_major.catalog_begin == major_form.cleaned_data.get('catalog_begin') \
                    and athlete_major.minor == major_form.cleaned_data.get('minor'):

                        messages.error(request, 'Student/semester/major/minor/catalog combination already exists.')
                        return render(request, template_name, context, context_instance=RequestContext(request))

            all_formsets = chain(course_formset, additional_course_formset)
            all_formset_forms = chain(course_formset.forms, additional_course_formset.forms)

            for course in all_formsets:
                # don't allow blank grades on certification
                if 'sign' in request.POST and user_type == User.REGISTRAR and \
                course.cleaned_data.get('grade') == '' and course.cleaned_data.get('course_category'):
                    messages.error(request, 'Grades are required for all coursework before certification can be completed.')
                    return render(request, template_name, context, context_instance=RequestContext(request))
                # don't allow college users to complete form without filling out Countable field for all courses
                if 'sign' in request.POST and user_type == User.DEAN and \
                course.cleaned_data.get('countable') == ''  and course.cleaned_data.get('course_category'):
                    messages.error(request, 'The Countable field must be completed for all courses before signing form.' )
                    return render(request, template_name, context, context_instance=RequestContext(request))

            for course in all_formset_forms: # save each changed course. the final formset.save saves new additions.
                if course.has_changed():
                    course_form = course.save(commit=False)
                    if course.cleaned_data['grade'] == '':  # but do allow blank grades on *save*
                        course_form.grade = course.cleaned_data['grade']
                    if course.cleaned_data['countable'] == 'N': # clear out dependent answers
                        course_form.min_grade_required = None
                        course_form.pass_fail_accepted = None
                    if course.cleaned_data['countable'] == '':  # but do allow blank countables on *save*
                        course_form.countable = course.cleaned_data['countable']
                    course_form.major_id = major_id
                    course_form.save()
                course.major_id = major_id
            course_formset.save()
            additional_course_formset.save()

            saved_major = major_form.save(commit=False)
            saved_major.save(updater=request.session[USER_EID])

            if 'sign' in request.POST:
                athlete_ccyys_admin.advance_routing(user)
                return _render_success_page(request)
            if 'return' in request.POST:
                messages.warning(request, 'An explanation is required for why the form is being returned.')
                return redirect('comment_required', form_type_name=form_type_name, form_id=form_id, action=RETURNING_FORM)

            return redirect('student_details', major_id=major_id)

    return render(request, template_name, context, context_instance=RequestContext(request))


@FERPACheck
@authorization
def percentage_of_degree(request, major_id=False):
    """Allows users to record a student's fulfillment of Percentage of Degree
    requirements."""

    context = {}

    # get user data
    user = User.objects.get(eid=request.session[USER_EID])
    user_type = user.type
    try:
        user_college = user.school.code
    except AttributeError:
        user_college = False

    # get athlete data
    try:
        major = AthleteMajor.objects.get(pk=major_id)
    except AthleteMajor.DoesNotExist:
        # an error can occur from a user manually adjusting url
        logger.error('Could not find major_id {0}.'.format(str(major_id)))
        return render_sp_error_page(request, 'Error accessing student data. Please contact Athletic Student Services.')

    athlete = Athlete.objects.get(pk=major.athlete_ccyys_admin.athlete_ccyys.athlete.id)
    athlete_ccyys = AthleteCcyys.objects.get(pk=major.athlete_ccyys_admin.athlete_ccyys.id)
    ccyys = athlete_ccyys.ccyys
    athlete_ccyys_admin = AthleteCcyysAdmin.objects.get(pk=major.athlete_ccyys_admin.id)
    athlete_ccyys_sport = AthleteCcyysSport.objects.filter(athlete_ccyys_id=major.athlete_ccyys_admin.athlete_ccyys.id)
    percentage = PercentDegree.objects.get(major=major)
    routed_to_dean = percentage.routed_to_dean_by
    approved_by_reg = percentage.approved_by_reg
    form_id = percentage.id
    form_type_name = PercentDegree.PERCENT

    # pda info--broker call gets current classes for a student prior to the final cert
    # These classes correspond to the 'current coursework on record' and reflect
    # the actual classes/grades on the mainframe. We might have forms for
    # athlete who aren't students (prospectives, etc). If we don't have an
    # SRI, we don't attempt to go to mainframe for classes.
    if not request.is_ajax() and major.athlete_ccyys_admin.athlete_ccyys.athlete.sri:
        nrdpaec2 = Nrdpaec2()
        nrdpaec2.send.sri = major.athlete_ccyys_admin.athlete_ccyys.athlete.sri
        nrdpaec2.send.ccyys = ccyys
        try:
            nrdpaec2 = make_broker_call(request, nrdpaec2)
        except (UTBrokerError, FatalError) as exception:
            logger.error('Exception calling NRNPAEC2: {0}'.format(str(exception)))
            return render_sp_error_page(request, str(exception))

    major_form = MajorForm(data=request.POST or None, instance=major,
                           user_type=user_type, users_turn=percentage.users_turn(user), ccyys=ccyys,
                           routed_to_dean=routed_to_dean, approved_by_reg=approved_by_reg)
    percent_form = PercentForm(data=request.POST or None, instance=percentage,
                               user_type=user_type, users_turn=percentage.users_turn(user),
                               routed_to_dean=routed_to_dean, approved_by_reg=approved_by_reg)

    # the following block occurs after a user has submitted the form
    if request.method == 'POST' and not request.is_ajax():
        if major_form.is_valid() and percent_form.is_valid():
            saved_major = major_form.save(commit=False)
            # look up the major name from the major table and fill in for user.
            school = major_form.cleaned_data['school']
            major_code = major_form.cleaned_data['major_code']
            major_rec = Major.objects.get(school=school, code=major_code)
            saved_major.major_name = major_rec.long_desc
            saved_major.save(updater=request.session[USER_EID])

            percentage = percent_form.save()
            major.save(updater=request.session[USER_EID])  # trigger logging

            # one business rule is that if an advisor changes these fields, they are required
            # to leave a comment stating why. When returning a form, a comment is always required.
            if percent_form.has_changed() or 'return' in request.POST:
                if 'sign' in request.POST:
                    messages.warning(request, 'An explanation is required for these changes.')
                    action = ADVANCING_FORM
                elif 'return' in request.POST:
                    messages.warning(request, 'An explanation is required for why the form is being returned.')
                    action = RETURNING_FORM
                else:
                    messages.warning(request, 'An explanation is required for these changes.')
                    action = SAVING_PERCENT
                return redirect('comment_required', form_type_name=PercentDegree.PERCENT, form_id=form_id, action=action)

            if 'sign' in request.POST:  # and nothing has changed
                percentage.advance_routing(user)
                messages.success(request, 'The form has been saved and routed to the appropriate user.')
                return redirect('inbox')
            return redirect('percentage_of_degree', major_id=major.id)

    # make broker call to get current ccyys and last class day for semester
    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception as exception:
        return render_sp_error_page(request, str(exception))

    if request.is_ajax():
        template_name = 'major_form.html'
    else:
        template_name = 'percentage_form.html'

    # load context
    try:
        context['nrdpaec2'] = nrdpaec2
        context['has_coursework'] = True
    except UnboundLocalError:
        pass
    context['user_type'] = user_type
    context['user_college'] = user_college
    context['athlete'] = athlete
    context['athlete_ccyys'] = athlete_ccyys
    context['ccyy'] = str(ccyys)[:4]
    context['semester'] = str(ccyys)[4:5]
    context['athlete_ccyys_sport'] = athlete_ccyys_sport
    context['athlete_ccyys_admin'] = athlete_ccyys_admin
    context['school'] = major.school
    context['major'] = major
    context['major_desc'] = "{0} {1}".format(major.major_code, major.major_name)
    context['major_form'] = major_form
    context['percentage'] = percentage
    context['percent_form'] = percent_form
    context['users_turn'] = percentage.users_turn(user)
    context['advance_recipient'] = percentage.advance_recipient
    context['return_recipient'] = percentage.return_recipient
    context['signature_info'] = percentage.signature_info
    context['form_id'] = form_id
    context['form_type_name'] = form_type_name
    context['current_ccyys'] = current_ccyys
    context['current_ccyys_int'] = int(current_ccyys)
    context['this_url'] = request.get_full_path()
    context['instructions_tag'] = 'pd'
    return render(request, template_name, context, context_instance=RequestContext(request))


@ensure_csrf_cookie
def comments(request):
    """Manages the updates of comments from the form pages
    via Ajax. It relies on different action constants being sent
    back, as well as form_id and form_type. In some cases it returns
    a URL for redirection, in other cases it returns a template
    to render."""

    # constants
    DELETE = 'd'
    EDIT = 'e'
    ADD = 'a'
    SAVE_CHANGES = 's'

    # check that it is being called by ajax. We don't want people getting here by
    # manually altering a URL.
    if request.is_ajax():
        context = {}

        # the information on what form and which type is loaded into the
        # template by the other views, and we pull it via javascript.
        form_type_name = request.GET.get('form_type_name', False) or request.POST.get('form_type_name', False)
        form_id = request.GET.get('form_id', False) or request.POST.get('form_id', False)
        try:
            user = User.objects.get(eid=request.session[USER_EID])
        except KeyError:
            return render_sp_error_page(request, 'Your session has timed out. Please log in again.')
        try:
            action = request.POST['action']
        except KeyError:
            action = False

        # get the form object the comments are attached to-
        # form in this case meaning either the SPD or PoD form.
        try:
            form = get_form(form_type_name, form_id)
        except ObjectDoesNotExist:
            return render_to_response('ajax_error.html', {})

        form_type = ContentType.objects.get_for_model(form)
        comments = Comments.objects.filter(form_id=form_id, form_type=form_type)
        comment_formset = modelformset_factory(Comments,
                                               form=CommentForm,
                                               extra=0,)

        if action == ADD:
            add_comment_form = AddCommentForm({'comments': request.POST['comment']})
            if add_comment_form.is_valid():
                    # associate it with the correct form and user
                    new_comment = add_comment_form.save(commit=False)
                    new_comment.user = user
                    new_comment.form_object = form
                    new_comment.save()
                    # load up a new blank for the page
                    add_comment_form = AddCommentForm()
        else:
            # load a blank comment form if we're not processing one.
            add_comment_form = AddCommentForm()
        # the edit and delete actions
        if action == DELETE:
            comment = Comments.objects.get(pk=request.POST['comment_id'])
            comment.delete()
        if action == SAVE_CHANGES:
            comment = Comments.objects.get(pk=request.POST['comment_id'])
            comment.comments = request.POST['comment']
            comment.save()
        if action == EDIT:
            # find the comment we want and make it editable.
            comment_formset = comment_formset(queryset=comments)
            for c_form in comment_formset:
                if c_form.instance.id == int(request.POST['comment_id']):
                    c_form.in_editing_mode = True
                    c_form.fields['comments'].widget = Textarea(attrs={'rows': 7,
                                                                       'cols': 40,
                                                                       'maxlength': 250, })
        else:
            form_type = ContentType.objects.get_for_model(form)
            comments = Comments.objects.filter(form_id=form_id, form_type=form_type)
            comment_formset = comment_formset(queryset=comments)
            # users can only edit/delete their own comments
            for c_form in comment_formset:
                if c_form.instance.user != user:
                    c_form.editable = False

        context['comment_formset'] = comment_formset
        context['add_comment_form'] = add_comment_form
        context['users_turn'] = form.users_turn(user)
        return render(request, 'comments.html', context)
    else:
        logger.error('Comment page not accessed via ajax?!')
        return render_sp_error_page(request)


@authorization
def comment_required(request, form_type_name, form_id, action):
    """Certain actions prompt for the user to add a comment. This view
    loads the 'add a comment' page and saves the comment."""

    if action not in FORM_ACTIONS:
        logger.error('Invalid action for comment required: {0}'.format(str(action)))
        return render_sp_error_page(request)

    try:
        form = get_form(form_type_name, form_id)
    except ObjectDoesNotExist:
        return render_sp_error_page(request)

    user = User.objects.get(eid=request.session[USER_EID])
    users_turn = form.users_turn(user)
    if not users_turn:
        return render_sp_error_page(request)

    add_comment_form = AddCommentForm(request.POST or None)
    if add_comment_form.is_valid():
            # associate it with the correct form and user
            new_comment = add_comment_form.save(commit=False)
            new_comment.user = user
            new_comment.form_object = form
            new_comment.save()

            if action == RETURNING_FORM:
                form.return_form(new_comment, form_type_name)
                messages.success(request, 'The form has successfully been routed and a notification email has been sent')
            elif action == ADVANCING_FORM:
                form.advance_routing(user)
                messages.success(request, 'The form has successfully been saved and routed.')
            else:
                messages.success(request, 'The form has successfully been '
                                          'saved.')
            if form_type_name == PercentDegree.PERCENT:
                return redirect('percentage_of_degree', form.major.id)
            else:
                major = AthleteMajor.objects.get(athlete_ccyys_admin=form)
                return redirect('student_details', major.id)

    # show previous comments
    comment_formset = modelformset_factory(Comments,
                                         form=CommentForm,
                                         extra=0,)

    form_type = ContentType.objects.get_for_model(form)
    comments = Comments.objects.filter(form_id=form_id, form_type=form_type)
    comment_formset = comment_formset(queryset=comments)
    for c_form in comment_formset:
        c_form.editable = False

    context = {'add_comment_form': add_comment_form,
               'comment_formset': comment_formset,
               'users_turn': users_turn,
               'user_type': request.session[USER_TYPE]
               }
    return render(request, 'comment_required.html', context)


@authorization
def user_admin(request):
    """Admin page to manage users."""

    def _render_success_page(request):
        """Provides a success message and renders page after all of the various
        operations on this page are performed."""
        messages.success(request, 'The users have been successfully updated.')
        return HttpResponseRedirect(reverse('user_admin'))

    # check admin auth
    if not request.session[IS_ADMIN]:
        return render_sp_error_page(request, AUTH_ERROR_MSG)

    # make broker call to get the current semester. This will be used
    # to know which schools/colleges are valid.
    try:
        current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
    except Exception as exception:
        return render_sp_error_page(request, str(exception))

    # Get the list of all users and allow pagination of update forms
    user_list = User.objects.filter(active=True).order_by('type', 'school__name')

    # filter by searches
    search_eid = request.GET.get('search_eid', None)
    search_school = request.GET.get('search_school', None)
    if 'search_eid' in request.GET:
        user_list = user_list.filter(eid=search_eid)
    if 'search_school' in request.GET:
        user_list = user_list.filter(school__code=search_school)

    objects = page_to_queryset(request, user_list)
    page_query = user_list.filter(id__in=[obj.id for obj in objects])

    # when updating a user
    user_formset = modelformset_factory(User, form=UpdateUserForm, extra=0)
    schools = School.objects.filter(begin_ccyys__lte=current_ccyys).filter(end_ccyys__gte=current_ccyys)
    if 'update_user' in request.POST:
        update_forms = user_formset(request.POST, request.FILES)
        if update_forms.is_valid():
            update_forms.save()
            # clear out the session type so that if the user has changed
            # their own status (used by analysts testing) it forces
            # a new auth check.
            del request.session[USER_TYPE]
            return _render_success_page(request)
    else:
        update_forms = user_formset(queryset=page_query)
        for form in update_forms:
            form.fields["school"].queryset = schools

    # adding a user
    if 'add_user' in request.POST:
        # check to see if user already exists. If so, we will activate
        # them instead of adding them.
        try:
            user_to_activate = User.objects.get(eid=request.POST['eid'])
            if user_to_activate.active:
                messages.error(request, 'This user is already active.')
                add_user_form = AddUserForm(current_ccyys)
            else:
                data = deepcopy(request.POST)
                data['name'] = user_to_activate.name
                update_form = UpdateUserForm(instance=user_to_activate,
                                             data=data)
                if update_form.is_valid():
                    update_form.save()
                    user_to_activate.active = True
                    user_to_activate.save()
                    return _render_success_page(request)
                else:
                    add_user_form = AddUserForm(current_ccyys, data=request.POST)
                    messages.error(request, "Please correct errors within "
                                            "the form and resubmit.")
        except User.DoesNotExist:
            add_user_form = AddUserForm(current_ccyys, data=request.POST)
            if add_user_form.is_valid():
                add_user_form.save()
                return _render_success_page(request)
    else:
        # else they haven't submitted a form yet, so we show them a blank
        add_user_form = AddUserForm(current_ccyys)

    school_choices = [(school.code, school.name) for school in schools]
    context = {
               'add_user_form': add_user_form,
               'update_forms': update_forms,
               'user_types': User.USER_TYPES,
               'objects': objects,
               'user_type': request.session[USER_TYPE],
               'DEBUG': settings.DEBUG,
               'instructions_tag': 'users',
               'school_choices': school_choices,
               'search_eid': search_eid,
               'search_school': search_school,
              }
    return render(request, "user_admin.html", context, context_instance=RequestContext(request))


@authorization
def log(request):
    """Allows users to see changes to the spd_form"""

    # Parse through the request to see what type of records
    # the user wants. They can either search by student or
    # ccyys; neither defaults to current ccyys.
    if 'student' in request.GET:
        try:
            student = Athlete.objects.get(eid=request.GET['student'])
        except Athlete.DoesNotExist:
            return render_sp_error_page(request, 'Student with eid {0} does not exist.'.format(request.GET['student']))
        display_title = student.name
    elif 'form_ccyy' in request.GET:
        ccyys = request.GET['form_ccyy'] + request.GET['form_s']
        display_title = ccyys_to_display(ccyys)
    else:
        # default to current ccyys
        try:
            ccyys, current_ccyy, current_s = get_current_ccyys(request)
        except Exception as exception:
            return render_sp_error_page(request, str(exception))
        display_title = ccyys_to_display(ccyys)

    # find either the student or ccyys records.
    log_records = []

    if 'student' in request.GET:
        logs = SpdFormLog.objects.filter(spd_form__athlete_ccyys__athlete=student)
    elif 'updater' in request.GET:
        logs = SpdFormLog.objects.filter(updater=request.GET['updater'])
    else:  # CCYYS
        logs = SpdFormLog.objects.filter(spd_form__athlete_ccyys__ccyys=ccyys)

    for log in logs:
        try:
            log.updater = User.objects.get(eid=log.updater).name
        except User.DoesNotExist:
            pass  # continue using whatever raw value is here.

        log_records.append({
                            'id': log.id,
                            'ccyys': ccyys_to_display(log.ccyys),
                            'student': log.student.eid,
                            'student_name': log.student.name,
                            'date': log.update_datetime,
                            'updated_by': log.updater,
                           })

    # django pagination machinations
    log_records = page_to_queryset(request, log_records)

    context = {
               'display_title': display_title,
               'log_records': log_records,
               'user_type': request.session[USER_TYPE],
               'YEARS': YEARS,
              }
    return render(request, "log.html", context)


def log_record(request):
    """Returns one before/after log record."""

    def _unpack_courses(courses, dict_to_add_to):
            """Takes a queryset of courses and unpacks them by field
            into a dictionary. Returns the dictionary."""

            dict_to_add_to['courses'] = []

            for course in courses:
                course_dict = {
                             'course_category': course.course_category,
                             'course_number': course.course_number,
                             'unique': str(course.unique).zfill(5),
                             'credit_hours': course.credit_hours,
                             'min_grade_required': course.min_grade_required,
                             'pass_fail_accepted': course.pass_fail_accepted,
                             'grade': course.grade,
                            }
                # convert booleans to Y. Not showing false as 'N' because false could
                # also mean that it was never filled in.
                if course.countable:
                    course_dict['countable'] = 'Y'
                else:
                    course_dict['countable'] = ''
                if course.pass_fail_accepted:
                    course_dict['pass_fail_accepted'] = 'Y'
                else:
                    course_dict['pass_fail_accepted'] = ''
                dict_to_add_to['courses'].append(course_dict)

            return dict_to_add_to

    try:
        record_id = request.GET['record_id']
        record = SpdFormLog.objects.get(pk=record_id)
    except KeyError:
        logger.error('Could not find log record with id {0}.'.format(request.GET.get('record_id', '')))
        messages.error(request, 'There was a problem retrieving the log record.')
        return redirect('log')

# get all log records corresponding to this entry and put into a dictionary
    courses = CourseLog.objects.filter(spd_form_log=record)
    additional_courses = AdditionalCourseLog.objects.filter(spd_form_log=record)
    record_courses = list(chain(courses, additional_courses))

    after = {
             'school_code': record.school_code,
             'school_name': record.school_name,
             'major_code': record.major_code,
             'major_name': record.major_name,
             'minor': record.minor,
             'catalog_begin': record.catalog_begin,
             'catalog_end': record.catalog_end,
             'projected_countable_hours': record.projected_countable_hours,
             'total_hours_required': record.total_hours_required,
             'projected_percentage': record.projected_percentage,
             'final_countable_hours': record.final_countable_hours,
             'final_percentage': record.final_percentage,
            }
    after = _unpack_courses(record_courses, after)

    # find previous record and all log records corresponding to it.
    previous_record = record.previous_record
    courses = CourseLog.objects.filter(spd_form_log=previous_record)
    additional_courses = AdditionalCourseLog.objects.filter(spd_form_log=previous_record)
    previous_record_courses = list(chain(courses, additional_courses))

    if previous_record:
        before = {
                 'school_code': previous_record.school_code,
                 'school_name': previous_record.school_name,
                 'major_code': previous_record.major_code,
                 'major_name': previous_record.major_name,
                 'minor': previous_record.minor,
                 'catalog_begin': previous_record.catalog_begin,
                 'catalog_end': previous_record.catalog_end,
                 'projected_countable_hours': previous_record.projected_countable_hours,
                 'total_hours_required': previous_record.total_hours_required,
                 'projected_percentage': previous_record.projected_percentage,
                 'final_countable_hours': previous_record.final_countable_hours,
                 'final_percentage': previous_record.final_percentage,
                }
        before = _unpack_courses(previous_record_courses, before)
    else:
        before = {
                 'school_code': '',
                 'school_name': '',
                 'major_code': '',
                 'major_name': '',
                 'minor': '',
                 'catalog_begin': '',
                 'catalog_end': '',
                 'projected_countable_hours': '',
                 'total_hours_required': '',
                 'projected_percentage': '',
                 'final_countable_hours': '',
                 'final_percentage': '',
                 'courses': {},
                }
    context = {'after': after,
               'before': before,
               'name': record.spd_form.athlete_ccyys.athlete.name,
               'eid': record.spd_form.athlete_ccyys.athlete.eid,
               }

    return render(request, 'log_record.html', context,
                  context_instance=RequestContext(request))


class ContactView(SuccessMessageMixin, FormView):
    """Provides a form for a user to send an email to a group of users.
    Sorry that this is a CBV when the others are functions. I wanted to practice
    with CBV on a simple item."""

    template_name = 'contact.html'
    form_class = ContactForm
    success_message = 'Your message has been sent.'
    success_url = reverse_lazy('contact')

    @method_decorator(authorization)
    def dispatch(self, *args, **kwargs):
        return super(ContactView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        sender = User.objects.get(eid=self.request.session[USER_EID])
        form.send_email(sender)
        return super(ContactView, self).form_valid(form)

    def get_form_kwargs(self):
        """Give the form the current ccyys so it can populate it with
        current schools to choose from."""
        try:
            current_ccyys, current_ccyy, current_s = get_current_ccyys(self.request)
            ccyys = current_ccyys
        except Exception as exception:
            return render_sp_error_page(self.request, str(exception))

        kwargs = super(ContactView, self).get_form_kwargs()
        kwargs.update({'ccyys': ccyys})
        return kwargs


@authorization
def custom_form(request):
    """Used to generate a one-off spd and a one off percent form for a
    student. Can be used when business rules don't dictate that a student
    have one auto generated at the beginning of the semester. Allows users
    to select which form they want to create, but both will be created;
    non-selected form will just be marked inactive.

    The form has two steps. First a user has a page where they can select a
    user by eid and the semester, then on the second page they can choose
    major, etc. If they come to the page with an eid and ccyys in the
    request, they go straight to the second page."""

    # Athletics only
    if not request.session[USER_TYPE] == User.ATHLETICS:
        return render_sp_error_page(request, AUTH_ERROR_MSG)

    context = {}

    # user data
    user_type = request.session[USER_TYPE]
    users_turn = True

    context['user_type'] = user_type
    context['users_turn'] = users_turn

    if request.is_ajax():
        template_name = 'custom_form.html'
    else:
        template_name = 'custom_form_base.html'

    # first time through
    if 'eid_ccyys_submit' not in request.GET and not request.POST:

        context['first_time_through'] = True
        context['YEARS'] = YEARS

        return render(request, template_name, context, context_instance=RequestContext(request))

    eid = request.GET.get('eid') or request.POST.get('eid')
    semester = request.GET.get('semester') or request.POST.get('semester')
    ccyy = request.GET.get('ccyy') or request.POST.get('ccyy')

    if not eid or not semester or not ccyy:
        messages.error(request, 'EID, semester, and year are all required.')
        return redirect('custom_form')

    ccyys = ccyy + semester

    nrdpaec6 = Nrdpaec6()
    nrdpaec6.send.eid = eid
    nrdpaec6.send.ccyys = ccyys

    try:
        nrdpaec6.call_broker_once(service=request.META['HTTP_SERVICE'])
    except (UTBrokerError, FatalError) as exception:
        logger.error('Exception calling NRNPAEC6: ' + str(exception))
        return render_sp_error_page(request, str(exception))

    if nrdpaec6.recv.return_code:
        messages.error(request, nrdpaec6.recv.return_msg)
        return redirect('custom_form')

    sport_1 = nrdpaec6.recv.sport_1
    sport_2 = nrdpaec6.recv.sport_2
    sport_3 = nrdpaec6.recv.sport_3

    # if eid and ccyys have been entered
    if 'eid_ccyys_submit' in request.GET:
        initial_data = {'eid': nrdpaec6.recv.eid,
                        'name': nrdpaec6.recv.name,
                        'ccyy': ccyys[:4],
                        'semester': ccyys[4:5],
                        'num_ft_semesters': nrdpaec6.recv.num_ft_semesters,
                        'sport_1': sport_1,
                        'sport_2': sport_2,
                        'sport_3': sport_3,
                        }
        if 'additional' in request.GET:
            initial_data['percent_form'] = True
        form = CustomForm(ccyys=ccyys,
                          initial=initial_data)

    # if all data has been entered
    if request.POST:

        form = CustomForm(ccyys=ccyys, data=(request.POST or None))

        if not request.is_ajax() and form.is_valid():
            form_data = form.cleaned_data
            eid = form_data['eid']

        # check to see if athlete already exists; if not, create
            try:
                athlete = Athlete.objects.get(eid=form_data['eid'])
            except Athlete.DoesNotExist:
                athlete = Athlete.objects.create(eid=form_data['eid'],
                                                 uin=nrdpaec6.recv.uin,
                                                 sri=nrdpaec6.recv.sri,
                                                 ncaa_id=nrdpaec6.recv.ncaa_id,
                                                 name=nrdpaec6.recv.name,
                                                 )

            athlete_ccyys, created = AthleteCcyys.objects.get_or_create(athlete=athlete,
                                                                    ccyys=ccyys,
                                                                    num_ft_semesters=nrdpaec6.recv.num_ft_semesters)

#         link the student's sports to the athlete_ccyys
            if sport_1:
                sport_1, created = AthleteCcyysSport.objects.get_or_create(athlete_ccyys=athlete_ccyys, sport=sport_1)
            if sport_2:
                sport_2, created = AthleteCcyysSport.objects.get_or_create(athlete_ccyys=athlete_ccyys, sport=sport_2)
            if sport_3:
                sport_3, created = AthleteCcyysSport.objects.get_or_create(athlete_ccyys=athlete_ccyys, sport=sport_3)

            # first we need the school/major form data to check if one has already been created
            school = School.objects.get(id=form_data['school'])
            major = Major.objects.get(code=form_data['major'],
                                  school=school)

            catalog_begin = form_data['catalog_begin']
            minor = form_data['minor']

        # run through the admins and majors to see if it already exists
            athlete_ccyys_admin = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys)

            for admin in athlete_ccyys_admin:
                # get the major for the associated admin so that we can check the major code agains tthe input
                athlete_major = AthleteMajor.objects.get(athlete_ccyys_admin_id=admin.id)

                # note that the below check includes catalog year!!!!! so student can have multiple forms with the same major but different catalogs
                if athlete_major.major_code == major.code and athlete_major.school == school \
                and athlete_major.catalog_begin == catalog_begin and athlete_major.minor == minor:

                    messages.error(request, 'Student/semester/major/minor/catalog combination already exists.')

                    context['form'] = form
                    context['eid '] = eid
                    context['ccyys'] = ccyys

                    return render(request, template_name, context, context_instance=RequestContext(request))
#
            # if we haven't yet been rejected for a pre-existing athlete_ccyys_admin, then we want to create one
            athlete_ccyys_admin = AthleteCcyysAdmin.objects.create(athlete_ccyys=athlete_ccyys,
                                                                   total_countable_degree_hours=0,
                                                                   created_by=request.session[USER_EID],
                                                                   created_by_date = datetime.datetime.now(),
                                                                   active=form_data['spd_form'])

            # get major name to store
            athlete_major = AthleteMajor(athlete_ccyys_admin=athlete_ccyys_admin,
                                         school=school,
                                         major_code=major.code,
                                         major_name=major.long_desc,
                                         minor=form_data['minor'],
                                         catalog_begin=form_data['catalog_begin'],
                                         first_or_second='',)

            athlete_major.save(updater=request.session[USER_EID])

            # add classes
            nrdpaec2 = Nrdpaec2()
            nrdpaec2.send.sri = athlete_major.athlete_ccyys_admin.athlete_ccyys.athlete.sri
            nrdpaec2.send.ccyys = ccyys

            try:
                nrdpaec2 = make_broker_call(request, nrdpaec2)
                classes = nrdpaec2.recv.classes[:int(10)]
            except (UTBrokerError, FatalError) as exception:
                logger.error('Exception calling NRNPAEC2: {0}'.format(str(exception)))
                return render_sp_error_page(request, str(exception))

            for item in classes:
                if item.unique:
                    Course.objects.create(major=athlete_major,
                                          course_category=item.dept_abbr,
                                          course_number=item.course_number,
                                          unique=item.unique,
                                          course_type=item.course_type,
                                          credit_hours=item.hours_credit
                                          )
            # get or create percent_degree form
            try:
                PercentDegree.objects.get(major=athlete_major)
            except PercentDegree.DoesNotExist:
                PercentDegree.objects.create(major=athlete_major,
                                         created_by=request.session[USER_EID],
                                         created_by_date = datetime.datetime.now(),
                                         active=form_data['percent_form'])
            messages.success(request, 'Forms successfully created for {0}'.format(athlete.name))
            return redirect('inbox')

    context['form'] = form
    context['eid '] = eid
    context['ccyys'] = ccyys

    return render(request, template_name, context, context_instance=RequestContext(request))


@authorization
def ccyys_admin(request, ccyys_to_edit=False):
    """Admin page to modify system open/close dates."""

    def _render_success_page(request):
        """Provides a success message and renders page after all of the various
        operations on this page are performed."""
        messages.success(request, 'The dates have been successfully updated.')
        return redirect('ccyys_admin')

    # athletic student services only
    if not request.session[USER_TYPE] == User.ATHLETICS:
        return render_sp_error_page(request, AUTH_ERROR_MSG)

    data = request.POST or None
    try:
        ccyys_to_edit = request.GET['form_ccyy'] + request.GET['form_s']
    except KeyError:
        pass

    if not ccyys_to_edit:
        # make broker call to get current ccyys
        try:
            current_ccyys, current_ccyy, current_s = get_current_ccyys(request)
            ccyys_to_edit = current_ccyys
        except Exception as exception:
            return render_sp_error_page(request, str(exception))

    try:
        ccyys = CcyysAdmin.objects.get(ccyys=ccyys_to_edit)
    except CcyysAdmin.DoesNotExist:
        ccyys = None

    if ccyys:
        form = CcyysAdminForm(data, instance=ccyys)
    else:
        initial = {'ccyys': ccyys_to_edit}
        form = CcyysAdminForm(data, initial=initial)
    if form.is_valid():
        form.save()
        return _render_success_page(request)

    context = {
               'form': form,
               'user_type': request.session[USER_TYPE],
               'display_ccyys': ccyys_to_display(ccyys_to_edit),
               'YEARS': YEARS,
              }
    return render(request, "ccyys_admin.html", context, context_instance=RequestContext(request))


class ErrorView(TemplateView):
    """Renders error page."""
    template_name = "sp_error.html"

    def dispatch(self, *args, **kwargs):
        return super(ErrorView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ErrorView, self).get_context_data(**kwargs)
        try:
            context['user_type'] = self.request.session[USER_TYPE]
        except KeyError:  # unauthorized people will have no type
            pass
        context['YEARS'] = YEARS
        context['SPORTS'] = AthleteCcyysSport.SPORTS
        return context


@authorization
def activate(request, form_type_name, form_id, action):
    """Gives user the option to reactivate an inactive or deleted form
    or to inactivate/delete an active one."""

    ACTIVATE = 'A'
    DELETE = 'D'
    VALID_ACTIONS = [ACTIVATE, DELETE]

    # athletics only!
    user_type = request.session[USER_TYPE]
    if not user_type == User.ATHLETICS:
        return render_sp_error_page(request, AUTH_ERROR_MSG)

    #  audit action
    if action not in VALID_ACTIONS:
        return render_sp_error_page(request)

    #  get relevant form
    try:
        form = get_form(form_type_name, form_id)
        form_ccyys = get_form_ccyys(form_type_name, form_id)
    except ObjectDoesNotExist:
        return render_sp_error_page(request)

    if action == ACTIVATE and 'submit' in request.GET:
        if form.active:
            return render_sp_error_page(request, 'This form is already in use.')
        msg = "This form has been successfully reactivated."
        form.active = True
        form.save()
    elif action == DELETE and 'submit' in request.GET:
        if not form.active:
            render_sp_error_page(request, 'This form has already been deleted.')
        msg = "The form has been successfully deactivated."
        form.active = False
        form.save()
    if 'submit' in request.GET:  # By this point it would be a success
        messages.success(request, msg)
        return redirect('inbox')

    # get display info for page
    if form_type_name == AthleteCcyysAdmin.SPD:
        form_type_display = 'Satisfactory Progress Toward Degree'
        athlete_name = form.athlete_ccyys.athlete.name
    else:
        form_type_display = 'Percentage of Degree'
        athlete_name = Athlete.objects.get(pk=form.major.athlete_ccyys_admin.athlete_ccyys.athlete.id).name

    context = {'user_type': user_type,
               'form_type_name': form_type_name,
               'form_id': form_id,
               'form_type_display': form_type_display,
               'athlete_name': athlete_name,
               'form_ccyys': form_ccyys,
               'action': action,
               }

    return render(request, 'activate.html', context)
