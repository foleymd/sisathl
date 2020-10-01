from django import forms
from django.core.validators import RegexValidator
from django.forms import ModelForm
from django.core.mail import send_mail
from django.conf import settings
from django.forms.widgets import TextInput, HiddenInput

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import InlineField

from sisathl.sas.sp.models import (AthleteCcyysSport,
                                   AthleteMajor,
                                   Course,
                                   AdditionalCourse,
                                   User,
                                   PercentDegree,
                                   Comments,
                                   CcyysAdmin,
                                   School,
                                   Major)

from sisathl.sas.utils.utils import MIN_GRADE_REQUIRED, FINAL_GRADES, YES_NO
from sisathl.sas.utils.constants import CATALOG_YEARS, SEMESTER_CHOICES, \
    YEAR_CHOICES
from sisathl.sas.utils.ted import TEDConnection


# Checks that a given ccyys is valid YYYYS format, with S being a semester, and
# the year being between 1000 and 2999.
ccyys_validator = RegexValidator(regex='^[12]\d\d\d[269]$',
                                 message='Invalid year and/or semester.',)

catalog_year_validator = RegexValidator(regex='^[12]\d\d\d$',
                                 message='Invalid year.',)


class CustomForm(forms.Form):
    """Used to generate a one-off spd and a one off percent form for a
    student. Can be used when business rules don't dictate that a student
    have one auto generated at the beginning of the semester. Allows users
    to select which form they want to create, but both will be created;
    non-selected form will just be marked inactive."""

    custom_form_sports = []
    for sport_code, sport in AthleteCcyysSport.SPORTS.iteritems():
        if sport_code != AthleteCcyysSport.MENS_TRACK and sport_code != AthleteCcyysSport.WOMENS_TRACK and sport_code != AthleteCcyysSport.WOMENS_ROW_ALL:
            custom_form_sports.append((sport_code, sport))

    eid = forms.CharField(max_length=8, label="Athlete EID")
    name = forms.CharField()
    ccyy = forms.ChoiceField(label="Year", choices=YEAR_CHOICES)
    semester = forms.ChoiceField(label="Semester", choices=SEMESTER_CHOICES)
    num_ft_semesters = forms.IntegerField(label="Number of Full Time Semesters", required=False)
    school = forms.ChoiceField(label="School")
    major = forms.ChoiceField(label="Major", required=False)
    minor = forms.CharField(label="Minor", max_length=25, required=False)
    catalog_begin = forms.ChoiceField(label="Catalog begin",
                                      choices=CATALOG_YEARS,
                                      required=False,
                                      validators=[catalog_year_validator, ])
    # catalog_end = forms.ChoiceField(label="Catalog end",
    #                                choices=CATALOG_YEARS,
    #                                required=False,
    #                                validators=[catalog_year_validator,])
    sport_1 = forms.CharField(max_length=25, label="Sport 1")
    sport_2 = forms.CharField(max_length=25, label="Sport 2", required=False)
    sport_3 = forms.CharField(max_length=25, label="Sport 3", required=False)
    spd_form = forms.BooleanField(label="Create Satisfactory Progress form",
                                  required=False)
    percent_form = forms.BooleanField(label="Create Percentage of Degree form", required=False)

    def __init__(self, ccyys, *args, **kwargs):
        super(CustomForm, self).__init__(*args, **kwargs)
        # create crispy form helper
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.form_method = 'POST'
        self.helper.form_action = 'custom_form'
        self.helper.error_text_inline = True
        self.helper.layout = Layout(InlineField('eid',
                                                'name',
                                                'ccyy',
                                                'semester',
                                                'sport_1',
                                                'sport_2',
                                                'sport_3',
                                                'num_ft_semesters',
                                                'school',
                                                'major',
                                                'minor',
                                                'catalog_begin',
                                                'spd_form',
                                                'percent_form',
                                                ))
        # gets the list of valid school choices for the given CCYYS
        schools = School.objects.filter(begin_ccyys__lte=ccyys).filter(
            end_ccyys__gte=ccyys)
        # If we've already gone through once with the form, (even if it's
        # via ajax) we will have some data. If we have a school picked,
        # then we can figure out the valid major choices. If no school is
        # picked, use the majors from the first school.
        if 'school' in self.data:
            majors = Major.objects.filter(school=self.data['school']).filter(begin_ccyys__lte=ccyys).filter(end_ccyys__gte=ccyys)
        else:
            majors = Major.objects.filter(school=schools[0]).filter(begin_ccyys__lte=ccyys).filter(end_ccyys__gte=ccyys)
        # choice fields have to be in format [(code, display),]
        major_choices = [(major.code, str(major.code) + " " + major.long_desc) for major in majors]
        self.fields['major'] = forms.ChoiceField(choices=major_choices, required=False)
        self.fields['school'] = forms.ChoiceField(choices=[(s.id, s.name)
                                                           for s in schools])

        self.fields['eid'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['name'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['ccyy'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['semester'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['num_ft_semesters'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['sport_1'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['sport_2'].widget = TextInput(attrs={'readonly': 'readonly'})
        self.fields['sport_3'].widget = TextInput(attrs={'readonly': 'readonly'})


class MajorForm(forms.ModelForm):
    """Used on the spd page to allow updating of the AthleteMajor"""
    catalog_begin = forms.ChoiceField(label="Catalog begin",
                                      choices=CATALOG_YEARS,
                                      required=False,
                                      validators=[catalog_year_validator, ])
    catalog_end = forms.CharField(label="Catalog end",
                                  widget=TextInput(attrs={'readonly': 'readonly'}),
                                  required=False,)
    major_code = forms.ChoiceField(label="Major", required=False)

    def clean(self):
        form_data = self.cleaned_data

        return form_data

    class Meta:
        model = AthleteMajor
        exclude = ('athlete', 'athleteCcyys', 'athleteCcyysAdmin')
        fields = (
            'school', 'major_code', 'minor', 'catalog_begin',
            'catalog_end')

    def __init__(self, user_type, users_turn, ccyys, routed_to_dean,
                 approved_by_reg, *args, **kwargs):
        super(MajorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-majorForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(InlineField('school',
                                                'major_code',
                                                'minor',
                                                'catalog_begin',
                                                'catalog_end'))

        # gets the list of valid school choices for the given CCYYS
        schools = School.objects.filter(begin_ccyys__lte=ccyys).filter(
            end_ccyys__gte=ccyys)
        # If we've already gone through once with the form, (even if it's
        # via ajax) we will have some data. If we have a school picked,
        # then we can figure out the valid major choices. If no school is
        # picked, use the majors from the student's current college.
        if 'school' in self.data:
            majors = Major.objects.filter(school=self.data['school']).filter(begin_ccyys__lte=ccyys).filter(end_ccyys__gte=ccyys)
        else:
            majors = Major.objects.filter(school=self.instance.school).filter(begin_ccyys__lte=ccyys).filter(end_ccyys__gte=ccyys)
        # choice fields have to be in format [(code, display),]
        major_choices = [(major.code, str(major.code) + " " + major.long_desc) for major in majors]
        self.fields['major_code'] = forms.ChoiceField(choices=major_choices, required=False)
        self.fields['school'].queryset = schools
        self.fields['school'].label = 'College'
        self.fields['school'].requires = True
        self.fields['major_code'].label = 'Major'
        self.fields['minor'].required = False
        self.fields['catalog_begin'].required = False
        self.fields['catalog_end'].required = False

        if not users_turn or user_type == 'D' or (user_type == 'A' and routed_to_dean) or approved_by_reg:

            self.fields['school'].widget = HiddenInput()
            self.fields['major_code'].widget = HiddenInput()
            self.fields['catalog_begin'].widget = TextInput(attrs={'readonly': 'readonly'})
            self.fields['minor'].widget.attrs['readonly'] = 'readonly'


class CourseForm(forms.ModelForm):
    """Used on the spd page to allow updating of student courses"""

    course_category = forms.CharField(label="Field of Study", max_length=3,
                                      required=False)
    course_number = forms.CharField(label="Course Number", max_length=6,
                                    required=False)
    unique = forms.CharField(label="Unique", max_length=5, required=False)
    credit_hours = forms.IntegerField(label="Credit Hours", required=False,
                                      widget=forms.NumberInput(attrs={'max': 9, 'min': 0}))
    countable = forms.ChoiceField(label="Countable", choices=YES_NO,
                                  required=False, widget=forms.Select(attrs={'class': 'countable'}))
    min_grade_required = forms.ChoiceField(label="Min. Grade Required",
                                           choices=MIN_GRADE_REQUIRED,
                                           required=False)
    pass_fail_accepted = forms.ChoiceField(label="Pass/Fail Accepted",
                                           choices=YES_NO, required=False)
    grade = forms.ChoiceField(label="Grade", choices=FINAL_GRADES,
                              required=False)

    def clean(self):
        cleaned_data = super(CourseForm, self).clean()

        if cleaned_data.get("DELETE"): # we don't need to clean the data if we're just deleting it
            return cleaned_data

        course_category = cleaned_data.get("course_category", False)
        course_number = cleaned_data.get("course_number", False)
        unique = cleaned_data.get("unique", False)
        credit_hours = cleaned_data.get("credit_hours", False)
        countable = cleaned_data.get("countable", False)
        min_grade_required = cleaned_data.get("min_grade_required", False)
        pass_fail_accepted = cleaned_data.get("pass_fail_accepted", False)
        grade = cleaned_data.get("grade", False)

        if not course_category and not course_number and not unique and not credit_hours and not countable \
        and not min_grade_required and not pass_fail_accepted and not grade:
            self.cleaned_data['DELETE'] = True

        else:
            print unique
            if countable == 'Y' and (not min_grade_required or not pass_fail_accepted):
                self._errors['countable'] = ["Min grade required or pass/fail accepted missing."]

            if not course_category:
                self._errors['course_category'] = ["Field of study cannot be blank."]

            if not course_category.isupper():
                self._errors['course_category'] = ["Use upper case for all fields of study."]

            if not course_number:
                self._errors['course_number'] = ["Course number cannot be blank."]

            if course_number.islower():
                self._errors['course_number'] = ["Use upper case for all course numbers."]

            if not unique:
                self._errors['unique'] = ["Unique number cannot be blank."]

            # if unique:
            #     try:
            #         int(unique)
            #     except ValueError:
            #         self._errors['unique'] = ["Course unique must be a number."]

            if credit_hours == 0:   # zero is ok
                pass
            elif not credit_hours:  # blank is not
                self._errors['credit_hours'] = ["Credit hours cannot be blank."]



    class Meta:
        model = Course
        exclude = ('athlete', 'athleteCcyys', 'athleteCcyysAdmin', 'major')
        fields = ('course_category', 'course_number', 'unique', 'credit_hours',
                  'countable', 'min_grade_required', 'pass_fail_accepted',
                  'grade')
        user_type = None


class AdditionalCourseForm(CourseForm):
    """Used on the spd page to allow adding/updating of student courses.
     These are specifically the transfer, CBE etc courses."""
    class Meta:
        model = AdditionalCourse
        exclude = ('athlete', 'athleteCcyys', 'athleteCcyysAdmin', 'major')
        fields = ('course_category', 'course_number', 'unique', 'credit_hours',
                  'countable', 'min_grade_required', 'pass_fail_accepted',
                  'grade')
        user_type = None


class PercentForm(forms.ModelForm):
    """On the percent form page, allows updating of PercentDegree"""

    class Meta:
        model = PercentDegree
        exclude = ('created_by', 'routed_to_dean_by', 'approved_by_dean',
                   'routed_to_reg_by', 'approved_by_reg')
        fields = ('projected_countable_hours',
                  'total_hours_required',
                  'projected_percentage',
                  # The following fields were in the original design, but were removed at the request of the users.
                  # Keeping just in case we want them later.
                  # 'final_countable_hours',
                  # final_percentage'
                  )

    def __init__(self, user_type, users_turn, routed_to_dean, approved_by_reg, *args, **kwargs):
        super(PercentForm, self).__init__(*args,
                                          **kwargs)  # must be before fields are marked as read only
        self.helper = FormHelper()
        self.helper.form_id = 'id-percentDegreeForm'
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.form_method = 'POST'
        self.helper.form_action = ''
        self.helper.error_text_inline = True
        self.helper.layout = Layout(InlineField('projected_countable_hours',
                                                'total_hours_required',
                                                'projected_percentage',
                                                # The following fields were in the original design, but were removed at the request of the users.
                                                # Keeping just in case we want them later.
                                                # 'final_countable_hours',
                                                # 'final_percentage'
                                                ))

        self.fields['projected_percentage'].widget.attrs['readonly'] = 'readonly'

        if not users_turn or (user_type == 'A' and routed_to_dean) or (user_type == 'R' and approved_by_reg):
            self.fields['projected_countable_hours'].widget.attrs['readonly'] = 'readonly'
            self.fields['total_hours_required'].widget.attrs['readonly'] = 'readonly'


class AddUserForm(forms.ModelForm):
    """Allows admin to add or reactive new users of the site."""

    def __init__(self, current_ccyys, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.fields['school'].queryset = School.objects.filter(begin_ccyys__lte=current_ccyys).filter(end_ccyys__gte=current_ccyys)

    def clean_eid(self):
        """Calls TED to check that the EID provided is valid and the user has all the
        info we will need to properly store them."""

        ted_conn = TEDConnection(eid=settings.TED_SERVICE_EID, password=settings.TED_SERVICE_PASSWORD)
        attrs = ['utexasEduPersonUin', 'utexasEduPersonAffCode', 'mail']
        try:
            user = ted_conn.get_by_eid(self.cleaned_data['eid'], attrs=attrs)
        except Exception:
            raise forms.ValidationError("Invalid EID entered.")

        # we want to make sure person is current staff
        if '0SFCU' not in user['utexasEduPersonAffCode'] and '0FCCU' not in user['utexasEduPersonAffCode']:
            raise forms.ValidationError("This EID does not belong to a current staff member.")

        # and has a valid email
        try:
            user['mail'][0]
        except KeyError:
            raise forms.ValidationError("This person does not have an email on file. Please have them correct their staff contact information and try again.")

        return self.cleaned_data['eid']

    def clean(self):
        form_data = self.cleaned_data
        # if a user is from a school or college, the college field must be filled.
        # Meanwhile, non-college level users cannot have a college selected.
        if form_data['type'] == User.DEAN and not form_data['school']:
            self._errors['school'] = ["No school or college was specified."]
        if form_data['type'] != User.DEAN and form_data['school']:
            self._errors['school'] = ["No school should be selected for this type."]
        return form_data

    class Meta:
        model = User
        fields = ['eid', 'type', 'school', ]


class UpdateUserForm(forms.ModelForm):
    """Allows updates to User model."""

    def clean(self):
        form_data = self.cleaned_data

        # if a user is from a college, the school field must be filled.
        # Meanwhile, non-college level users, cannot have a school selected.
        if form_data['type'] == User.DEAN and not form_data['school']:
            self._errors['school'] = ["No school or school was specified."]
        if form_data['type'] != User.DEAN and form_data['school']:
            self._errors['school'] = [
                "No school should be selected for this type."]
        return form_data

    class Meta:
        model = User
        fields = ['eid', 'name', 'type', 'school', 'active']
        widgets = {
            'eid': forms.TextInput(attrs={'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'readonly': 'readonly'}),
        }


class AddCommentForm(forms.ModelForm):
    """Allows a user to add a comment record describing changes they've
    made or questions. """

    class Meta:
        model = Comments
        fields = ('comments',)
        widgets = {'comments': forms.Textarea(attrs={'rows': 5,
                                                     'cols': 200,
                                                     'maxlength': 250,
                                                     },
                                              )}


class CommentForm(forms.ModelForm):
    """Allows users to edit the comments. A comment
    should be editable until they send the form to another user.
    A user should never be able to edit other people's comments."""

    user_name = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'size': 25}))
    timestamp = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = Comments
        fields = ('comments',)

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)

        # is this form editable or not?
        self.editable = self.instance.editable
        self.in_editing_mode = False

        # initialize the user name and timestamp fields.
        # Timestamp cannot be a normal field because Django
        # does not allow auto_now fields in forms.
        self.initial['user_name'] = self.instance.user.name
        self.fields['user_name'].initial = self.instance.user.name
        timestamp = self.instance.timestamp.strftime('%m/%d/%Y %H:%M')
        self.initial['timestamp'] = timestamp
        self.fields['timestamp'].initial = timestamp

        # if not editable, make fields pretty text only
        rows = (len(self.instance.comments) / 30) + 1
        self.fields['comments'].widget = forms.Textarea(attrs={'rows': rows,
                                                               'cols': 40,
                                                               'readonly': 'readonly'})


class CommentFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(CommentFormsetHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_method = 'post'
        self.layout = Layout()
        self.helper.form_class = 'form-inline'
        self.render_required_fields = True,
        self.helper.form_tag = False


class ContactForm(forms.Form):
    """Allow users to send an email to a group of people. They can pick from a
    user type, and it would go to all people of that type. The exception is
    colleges. Rather than send a message to EVERY college, the form lists
    each current college separately and the message only goes to users from
    that college."""

    # rather than using the user codes, I'm hardcoding in values here. This
    # is to prevent there from being confusion between a school with a code
    # R or A and either Athletics or the Registrar's office or future users.
    MAIL_USER_TYPES = {'ATH': User.ATHLETICS, 'REG': User.REGISTRAR}
    recipients = [('ATH', 'Athletic Student Services'),
                  ('REG', 'Registrar\'s Office')]

    recipient = forms.ChoiceField(choices=recipients,
                                  widget=forms.Select(
                                      attrs={'class': 'form-control', }))
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control',
                                     'rows': 5,
                                     'cols': 200, }))

    def __init__(self, *args, **kwargs):
        ccyys = kwargs.pop('ccyys')
        super(ContactForm, self).__init__(*args, **kwargs)
        schools = School.objects.filter(begin_ccyys__lte=ccyys).filter(end_ccyys__gte=ccyys)
        school_choices = [(school.code, school.name) for school in schools]
        self.recipients.extend(school_choices)
        self.fields['recipient'] = forms.ChoiceField(choices=self.recipients,
                                                     widget=forms.Select(attrs={'class': 'form-control', }))

    def send_email(self, sender):
        sender_email = sender.email
        recipient = self.cleaned_data['recipient']
        if recipient in self.MAIL_USER_TYPES:
            email_recipients = User.objects.filter(type=self.MAIL_USER_TYPES[recipient])
        else:
            email_recipients = User.objects.filter(type=User.DEAN).filter(school__code=recipient)
        email_recipients = [recipient.email for recipient in email_recipients]
        if settings.PYPE_SERVICE != 'PROD':
            email_recipients = [settings.ADMINS[0][1]]

        message = self.cleaned_data['message']

        subject = 'You have been sent a message from %s regarding athletic forms.' % sender.name

        send_mail(subject, message, sender_email,
                  email_recipients, fail_silently=False)


class CcyysAdminForm(ModelForm):
    """Allows Athletic Student Service users to adjust the open/close dates
    for each type of user."""

    ccyys = forms.CharField(widget=forms.HiddenInput())
    athletics_open_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Athletics Open Date")
    athletics_close_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Athletics Close Date")
    dean_open_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Colleges Open Date")
    dean_close_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Colleges Close Date")
    reg_open_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Registrar Open Date")
    reg_close_date = forms.DateField(
        widget=forms.widgets.DateInput(format="%m-%d-%Y"),
        input_formats=['%m-%d-%Y', '%Y-%m-%d'],
        label="Registrar Close Date")

    class Meta:
        model = CcyysAdmin
        fields = [
            'ccyys',
            'athletics_open_date',
            'athletics_close_date',
            'dean_open_date',
            'dean_close_date',
            'reg_open_date',
            'reg_close_date',
        ]
