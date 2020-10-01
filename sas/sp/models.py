import datetime
import logging
from itertools import chain
from decimal import Decimal

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from sisathl.sas.utils.utils import ccyys_to_display, evaluate_for_countable_hrs
from sisathl.sas.utils.ted import TEDConnection

logger = logging.getLogger(__name__)


class School(models.Model):
    """This table is explicitly schools that have majors"""
    code = models.CharField(max_length=1, null=False, unique=True, db_index=True)
    name = models.CharField(max_length=240, null=False)
    begin_ccyys = models.IntegerField()
    end_ccyys = models.IntegerField()

    def __unicode__(self):
        return self.name


class Major(models.Model):
    """All the possible majors students can have and relevant info."""
    school = models.ForeignKey('School')
    code = models.CharField(max_length=5, null=False, db_index=True)
    short_desc = models.CharField(max_length=16)
    long_desc = models.CharField(max_length=54, null=False)
    full_title = models.CharField(max_length=100)
    begin_ccyys = models.IntegerField()
    end_ccyys = models.IntegerField()

    class Meta:
        unique_together = (('school', 'code'),)

    def __unicode__(self):
        return str(self.school.code) + str(self.code)


class User(models.Model):
    """Users allowed to access system. Instead of being deleted,
    users can be deactivated to prevent future access to the system."""
    ATHLETICS = 'A'
    DEAN = 'D'
    REGISTRAR = 'R'

    USER_TYPES = ((ATHLETICS, 'Athletic Student Services'),
                  (DEAN, 'College'),
                  (REGISTRAR, 'Registrar Staff'))

    uin = models.CharField(max_length=16,
                           unique=True, verbose_name="UIN")
    eid = models.CharField(max_length=8,
                           unique=True, verbose_name="EID")
    name = models.CharField(max_length=50, verbose_name="name")
    type = models.CharField(max_length=1,
                            choices=USER_TYPES,
                            default=ATHLETICS, verbose_name="type")
    school = models.ForeignKey("School",
                               blank=True,
                               null=True,
                               default=None)
    active = models.BooleanField(default=True, verbose_name="active")
    email = models.EmailField(default='', verbose_name="email")

    def __unicode__(self):
        return self.eid

    def is_admin(self):
        """Returns if user should have access to the administrative
        functions of the site, such as the interface to add new users."""
        if (self.type == self.ATHLETICS or self.type == self.REGISTRAR) and self.active:
            return True

    def save(self, *args, **kwargs):

        if not self.uin and not self.name:

            # connect to TED to get UIN and name
            ted_conn = TEDConnection(eid=settings.TED_SERVICE_EID, password=settings.TED_SERVICE_PASSWORD)
            # request user
            attrs = ['utexasEduPersonUin', 'displayName', 'mail']
            user = ted_conn.get_by_eid(self.eid, attrs=attrs)

            # save the user's uin, name, and email. They are actually
            # lists and we're taking the first value.
            self.uin = user['utexasEduPersonUin'][0]
            self.name = user['displayName'][0]
            self.email = user['mail'][0]

        super(User, self).save(*args, **kwargs)

    class Meta:
        db_tablespace = 'regs_spform_data'


class CcyysAdmin(models.Model):
    """Used for specifying open and close dates for different
    users to view forms."""
    ccyys = models.IntegerField(validators=[MaxValueValidator(99999), MinValueValidator(0)])
    athletics_open_date = models.DateField(default=datetime.date(9999, 12, 31))
    athletics_close_date = models.DateField(default=datetime.date(9999, 12, 31))
    dean_open_date = models.DateField(default=datetime.date(9999, 12, 31))
    dean_close_date = models.DateField(default=datetime.date(9999, 12, 31))
    reg_open_date = models.DateField(default=datetime.date(9999, 12, 31))
    reg_close_date = models.DateField(default=datetime.date(9999, 12, 31))
    forms_loaded = models.BooleanField(default=False)

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['ccyys']

    def is_open(self, user_type):
        """Checks a user's type and compares it against the open/close
        dates to see if user has access."""
        if user_type == User.ATHLETICS and (
                        self.athletics_open_date <= datetime.date.today() <= self.athletics_close_date):
            return True
        if user_type == User.DEAN and (
                        self.dean_open_date <= datetime.date.today() <= self.dean_close_date):
            return True
        if user_type == User.REGISTRAR and (
                        self.reg_open_date <= datetime.date.today() <= self.reg_close_date):
            return True
        return False

    @property
    def display_ccyys(self):
        return ccyys_to_display(self.ccyys)

    def __unicode__(self):
        return 'Admin dates for ' + str(self.ccyys)


class Athlete(models.Model):
    """Each record represents one student athlete."""
    uin = models.CharField(max_length=16)
    ncaa_id = models.CharField(max_length=10)
    sri = models.IntegerField(validators=[MaxValueValidator(999999999), MinValueValidator(0)])
    eid = models.CharField(max_length=8)
    name = models.CharField(max_length=25)

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['name']

    def __unicode__(self):
        return self.eid

    def save(self, *args, **kwargs):
        """Custom save function to look up the name and uin from TED."""
        if not self.uin and not self.name:

            # connect to TED to get UIN and name
            ted_conn = TEDConnection(eid=settings.TED_SERVICE_EID, password=settings.TED_SERVICE_PASSWORD)
            # request user
            attrs = ['utexasEduPersonUin', 'utexasEduPersonSortName', ]
            user = ted_conn.get_by_eid(self.eid, attrs=attrs)
            # These are actually lists and we're taking the first value.
            self.uin = user['utexasEduPersonUin'][0]
            self.name = user['utexasEduPersonSortName'][0]

        super(Athlete, self).save(*args, **kwargs)


class AthleteCcyys(models.Model):
    """Each record represents one semester for one student athlete."""
    athlete = models.ForeignKey('Athlete')
    ccyys = models.IntegerField(validators=[MaxValueValidator(99999), MinValueValidator(0)])
    num_ft_semesters = models.IntegerField(validators=[MaxValueValidator(30), MinValueValidator(0)], blank=True, null=True)

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['ccyys', 'athlete']

    @property
    def squads(self):
        """Returns a list of a student's squads for a given
        CCYYS in the form (squad_code, squad_display_name)"""
        result_list = []
        squads = AthleteCcyysSport.objects.filter(athlete_ccyys=self)
        for squad in squads:
            result_list.append((squad.sport, squad.sport_description))
        return sorted(list(set(result_list)))

    @property
    def display_ccyys(self):
        return ccyys_to_display(self.ccyys)

    def __unicode__(self):
        return self.athlete.eid + ' ' + str(self.ccyys)


class ActiveFormManager(models.Manager):
    """This manager only returns items with a True value
    in their 'active' field."""
    def get_queryset(self):
        return super(ActiveFormManager, self).get_queryset().filter(active=True)


class RoutingForm(models.Model):
    """An abstract class that represents a 'form'
    with routing information."""

    # Django uses a unique id for each form type. The two following
    # functions return that. However, this changes when the db is 
    # reloaded. Thus I sometimes use the variable form_type_name,
    # which is either SPD or PERCENT (below) so that we can refer
    # to them across db loads. The get_form function uses those.
    def SPD_FORM_TYPE(self):
        return ContentType.objects.get(model="athleteccyysadmin").id

    def PERCENT_FORM_TYPE(self):
        return ContentType.objects.get(model="percentdegree").id

    SPD = 'SPD'
    PERCENT = 'PERCENT_DEGREE'

    # the constants used by these forms
    CREATED = "Form created"
    ROUTED_TO_DEAN = "Needs college attention"
    APPROVED_BY_DEAN = "Approved by college"
    ROUTED_TO_REG = "Requires Registrar approval"
    APPROVED_BY_REG = "Complete"
    INACTIVE = "Form Inactive"

    # the order in which the form is routed
    routing_pattern = [CREATED,
                       ROUTED_TO_DEAN,
                       APPROVED_BY_DEAN,
                       ROUTED_TO_REG,
                       APPROVED_BY_REG]

    ROUTING_FIELDS = {CREATED: 'created_by',
                      ROUTED_TO_DEAN: 'routed_to_dean_by',
                      APPROVED_BY_DEAN: 'approved_by_dean',
                      ROUTED_TO_REG: 'routed_to_reg_by',
                      APPROVED_BY_REG: 'approved_by_reg'
                      }

    DATE_FIELDS    = {CREATED: 'created_by_date',
                      ROUTED_TO_DEAN: 'routed_to_dean_by_date',
                      APPROVED_BY_DEAN: 'approved_by_dean_date',
                      ROUTED_TO_REG: 'routed_to_reg_by_date',
                      APPROVED_BY_REG: 'approved_by_reg_date'
                      }

    # these represent who should have access to a
    # form in a given stage.
    user_for_step = {CREATED: [User.ATHLETICS],
                     ROUTED_TO_DEAN: [User.DEAN],
                     APPROVED_BY_DEAN: [User.ATHLETICS],
                     ROUTED_TO_REG: [User.REGISTRAR],
                     APPROVED_BY_REG: [User.REGISTRAR],
                     INACTIVE: [],
                     }

    created_by = models.CharField(max_length=8, null=True, blank=True)
    created_by_date = models.DateTimeField(null=True, blank=True)
    routed_to_dean_by = models.CharField(max_length=8, null=True, blank=True)
    routed_to_dean_by_date = models.DateTimeField(null=True, blank=True)
    approved_by_dean = models.CharField(max_length=8, null=True, blank=True)
    approved_by_dean_date = models.DateTimeField(null=True, blank=True)
    routed_to_reg_by = models.CharField(max_length=8, null=True, blank=True)
    routed_to_reg_by_date = models.DateTimeField(null=True, blank=True)
    approved_by_reg = models.CharField(max_length=8, null=True, blank=True)
    approved_by_reg_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveFormManager()

    @property
    def status(self):
        """ Based on which routing fields are filled, returns a
        verbose status for display.

        Changing the order of these conditions will change the
        functionality so beware!!! """

        if not self.active:
            return self.INACTIVE
        if self.approved_by_reg:
            return self.APPROVED_BY_REG
        if self.routed_to_reg_by:
            return self.ROUTED_TO_REG
        if self.approved_by_dean:
            return self.APPROVED_BY_DEAN
        if self.routed_to_dean_by:
            return self.ROUTED_TO_DEAN
        if self.created_by:
            return self.CREATED
        return self.INACTIVE

    def users_turn(self, user):
        """A Boolean indicating if the user should have access to the form
        during this phase."""

        # if form is inactive, only Athletics has access
        if user.type == User.ATHLETICS and not self.active:
            return False

        # next check to see if user is a valid type depending on the stage
        # form is in.
        form_status = self.status
        valid_types = self.user_for_step[form_status]
        if user.type not in valid_types:
            return False

        # if the user is in a college, they can only alter students
        # that are in their college
        if user.type == User.DEAN:
            if ContentType.objects.get_for_model(self).id == self.SPD_FORM_TYPE():
                student_college = AthleteMajor.objects.get(athlete_ccyys_admin=self).school.code
            else:
                student_college = self.major.school.code
            if user.school.code != student_college:
                return False

        return True

    @property
    def signature_info(self):
        """Returns a dictionary of all people who interacted with the
        form and when, formatted for display."""
        try:
            created_by_user = User.objects.get(eid=self.created_by).name
        except User.DoesNotExist:
            created_by_user = ''
        try:
            routed_to_dean_by_user = User.objects.get(eid=self.routed_to_dean_by).name
        except User.DoesNotExist:
            routed_to_dean_by_user = ''
        try:
            approved_by_dean_user = User.objects.get(eid=self.approved_by_dean).name
        except User.DoesNotExist:
            approved_by_dean_user = ''
        try:
            routed_to_reg_user = User.objects.get(eid=self.routed_to_reg_by).name
        except User.DoesNotExist:
            routed_to_reg_user = ''
        try:
            approved_by_reg_user = User.objects.get(eid=self.approved_by_reg).name
        except User.DoesNotExist:
            approved_by_reg_user = ''

        return {
                'created_by': created_by_user,
                'created_by_date': self.created_by_date,
                'routed_to_dean_by': routed_to_dean_by_user,
                'routed_to_dean_by_date': self.routed_to_dean_by_date,
                'approved_by_dean': approved_by_dean_user,
                'approved_by_dean_date': self.approved_by_dean_date,
                'routed_to_reg_by': routed_to_reg_user,
                'routed_to_reg_by_date': self.routed_to_reg_by_date,
                'approved_by_reg': approved_by_reg_user,
                'approved_by_reg_date': self.approved_by_reg_date,
               }

    @property
    def advance_recipient(self):
        """Gives the display name of the next recipient
        if the form is signed and forwarded on."""

        if self.status == self.APPROVED_BY_REG:
            return None

        routing_index = self.routing_pattern.index(self.status)

        new_routing_index = routing_index + 1

        try:
            new_status = self.routing_pattern[new_routing_index]
        except IndexError:
            return None

        user = self.user_for_step[new_status][0]
        return dict(User.USER_TYPES)[user]

    @property
    def return_recipient(self):
        """Gives the display name of the next recipient
        if the form is returned to the previous user set."""

        if self.status == self.CREATED:
            return None
        routing_index = self.routing_pattern.index(self.status)

        new_routing_index = routing_index - 1

        try:
            new_status = self.routing_pattern[new_routing_index]
        except IndexError:
            return None
        user = self.user_for_step[new_status][0]
        return dict(User.USER_TYPES)[user]

    def freeze_comments(self):
        """Makes all comments associated with form uneditable."""

        # make the comments uneditable
        form_type = ContentType.objects.get_for_model(self)
        comments = Comments.objects.filter(form_id=self.id, form_type=form_type)
        for comment in comments:
            comment.editable = False
            comment.save()

    def send_email(self, comment, form_type_name):
        """Notifies users by email that they have a form
        to attend to."""
        # get school
        if ContentType.objects.get_for_model(self).id == self.SPD_FORM_TYPE():
            student_college = AthleteMajor.objects.get(athlete_ccyys_admin=self).school.code
        else:
            student_college = self.major.school.code
            
        # get recipients
        email_recipient_types = self.user_for_step[self.status]
        email_recipients = User.objects.filter(
            type__in=email_recipient_types).filter(school__code=student_college).filter(active=True)
        email_recipients = [recipient.email for recipient in email_recipients]
        
        # if it's not in production, send the email to admins instead
        if settings.PYPE_SERVICE != 'PROD':
            email_recipients = [settings.ADMINS[0][1]]
        
        # generate email content
        if form_type_name == self.SPD:
            form_name = 'Satisfactory Progress To Degree'
            athlete_name = self.athlete_ccyys.athlete.name
        else:
            form_name = 'Percent of Degree'
            athlete = Athlete.objects.get(pk=self.major.athlete_ccyys_admin.athlete_ccyys.athlete.id)  
            athlete_name = athlete.name
                  
        subject = 'ACTION REQUIRED: %s form for %s needs your attention' % (form_name, athlete_name)
        
        message = '''The %s form for %s has been returned to you with the following comment: "%s"
                   ''' % (form_name, athlete_name, comment.comments)
                   
        send_mail(subject, message, settings.ADMINS[0][1],
                  email_recipients, fail_silently=False)

    def advance_routing(self, user):
        """Determines where in the routing a form is and
        then advances it to the next station."""

        routing_index = self.routing_pattern.index(self.status)

        new_routing_index = routing_index + 1

        try:
            new_status = self.routing_pattern[new_routing_index]
        except IndexError:  # we've gone too far!
            return self

        # set the field
        setattr(self, self.ROUTING_FIELDS[new_status], user.eid)
        setattr(self, self.DATE_FIELDS[new_status], datetime.datetime.now())
        self.save()
        self.freeze_comments()

        return self

    def return_form(self, comment, form_type):
        """Determines where in the routing a form is and
        then moves it one stage back."""
        routing_index = self.routing_pattern.index(self.status)

        status_to_remove = self.routing_pattern[routing_index]

        # set the field
        setattr(self, self.ROUTING_FIELDS[status_to_remove], None)
        setattr(self, self.DATE_FIELDS[status_to_remove], None)
        self.save()
        self.freeze_comments()
        self.send_email(comment, form_type)

        return self

    class Meta:
        abstract = True


class AthleteCcyysAdmin(RoutingForm):
    """Each record represents one spd form."""

    athlete_ccyys = models.ForeignKey('AthleteCcyys')
    total_countable_degree_hours = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        db_tablespace = 'regs_spform_data'

    def __unicode__(self):
        return 'Admin for ' + str(self.athlete_ccyys)

    @property
    def display_ccyys(self):
        return ccyys_to_display(self.athlete_ccyys.ccyys)

    @property
    def total_possible_countable_degree_hours(self):

        total_possible_countable_degree_hours = 0

        courses = Course.objects.filter(major__athlete_ccyys_admin=self)
        additional_courses = AdditionalCourse.objects.filter(major__athlete_ccyys_admin=self)
        course_list = list(chain(courses, additional_courses))  # combine

        for course in course_list:
            total_possible_countable_degree_hours += course.credit_hours

        return total_possible_countable_degree_hours

    @property
    def total_projected_degree_hours(self):

        total_projected_degree_hours = 0

        courses = Course.objects.filter(major__athlete_ccyys_admin=self)
        additional_courses = AdditionalCourse.objects.filter(major__athlete_ccyys_admin=self)
        course_list = list(chain(courses, additional_courses))  # combine

        for course in course_list:
            if course.countable == 'Y':
                total_projected_degree_hours += course.credit_hours

        return total_projected_degree_hours


class AthleteMajor(models.Model):
    """Each record represents the major that corresponds to the form.
    Each form has one athlete/major combo, but an athlete can have
    multiple forms/majors per semester."""

    athlete_ccyys_admin = models.ForeignKey('AthleteCcyysAdmin')
    school = models.ForeignKey('School')
    # college_name = models.CharField(max_length=16)
    major_code = models.CharField(max_length=5)
    major_name = models.CharField(max_length=240)
    minor = models.CharField(max_length=25)
    catalog_begin = models.CharField(max_length=4, blank=True)
    catalog_end = models.CharField(max_length=4, blank=True)
    first_or_second = models.CharField(max_length=1, default='1')
    grades_saved = models.BooleanField(default=False)  # I don't think this is actually used
    final_college_code = models.CharField(max_length=1, default='')
    final_college_name = models.CharField(max_length=240, default='')
    final_major_code = models.CharField(max_length=5, default='')
    final_major_name = models.CharField(max_length=54, default='')
    final_catalog_begin = models.CharField(max_length=4, blank=True)
    final_catalog_end = models.CharField(max_length=4, blank=True)

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['athlete_ccyys_admin__athlete_ccyys__athlete', 'major_name']
        unique_together = ['school', 'major_code', 'minor', 'catalog_begin', 'athlete_ccyys_admin']

    def __unicode__(self):
        return str(self.athlete_ccyys_admin) + ' ' + str(self.major_code)

    @property
    def percent_degree(self):
        try:
            return PercentDegree.objects.get(major=self)
        except PercentDegree.DoesNotExist:
            return None

    def save(self, updater, *args, **kwargs):
        # figure out what the correct major name is based on the code.
        # This isn't set up as a ForeignKey to major (which would simplify this)
        # because the original intent was that they could type in any kind
        # of thing into the major box, even if it was gibberish.
        major = Major.objects.get(school=self.school, code=self.major_code)
        self.major_name = major.long_desc

        # per Shan 9/18/2015, we should add 2 to the begin catalog to
        # calculate end catalog.
        try:
            self.catalog_end = int(self.catalog_begin) + 2
        except ValueError:
            pass  # if there isn't one loaded yet
        # call original save method
        super(AthleteMajor, self).save(*args, **kwargs)

        courses = Course.objects.filter(major=self)
        additional_courses = AdditionalCourse.objects.filter(major=self)
        try:
            percent_degree = PercentDegree.objects.get(major=self)
        except PercentDegree.DoesNotExist:
            percent_degree = False

        # have the changes propagate to the log
        if self.athlete_ccyys_admin.active:
            log_record = SpdFormLog(updater=updater,
                                    spd_form=self.athlete_ccyys_admin,
                                    school_code=self.school.code,
                                    school_name=self.school.name,
                                    major_code=self.major_code,
                                    major_name=self.major_name,
                                    minor=self.minor,
                                    catalog_begin=self.catalog_begin,
                                    catalog_end=self.catalog_end,
                                    )
        else:
                log_record = SpdFormLog(updater=updater,
                                        spd_form=self.athlete_ccyys_admin,
                                        )
        # percent degree depends on the major existing, so when a major
        # record is first created, percent degree won't exist yet.
        if percent_degree:
            log_record.percent_degree = percent_degree
            if percent_degree.active:
                log_record.projected_countable_hours = percent_degree.projected_countable_hours
                log_record.total_hours_required = percent_degree.total_hours_required
                log_record.projected_percentage = percent_degree.projected_percentage
                log_record.final_countable_hours = percent_degree.final_countable_hours
                log_record.final_percentage = percent_degree.final_percentage
        log_record.save()
        if self.athlete_ccyys_admin.active:
            for course in courses:
                CourseLog.objects.create(spd_form_log=log_record,
                                         course_category=course.course_category,
                                         course_number=course.course_number,
                                         unique=course.unique,
                                         course_type=course.course_type,
                                         credit_hours=course.credit_hours,
                                         countable=course.countable,
                                         min_grade_required=course.min_grade_required,
                                         pass_fail_accepted=course.pass_fail_accepted,
                                         grade=course.grade,
                                         )
            for course in additional_courses:
                AdditionalCourseLog.objects.create(spd_form_log=log_record,
                                                   course_category=course.course_category,
                                                   course_number=course.course_number,
                                                   unique=course.unique,
                                                   course_type=course.course_type,
                                                   credit_hours=course.credit_hours,
                                                   countable=course.countable,
                                                   min_grade_required=course.min_grade_required,
                                                   pass_fail_accepted=course.pass_fail_accepted,
                                                   grade=course.grade,
                                                   )


class CourseInfoForm(models.Model):
    """An abstract class that represents a course. In an ideal world,
    we would have the time to go back and combine the Course and
    Additional Course models. This is a stop gap."""

    YES = 'Y'
    NO = 'N'

    YES_NO = (
              (YES, 'Yes'),
              (NO, 'No'),
             )

    major = models.ForeignKey('AthleteMajor')
    course_category = models.CharField(max_length=3)
    course_number = models.CharField(max_length=6)
    unique = models.CharField(max_length=5)
    course_type = models.CharField(max_length=3)
    credit_hours = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)], default=0, null=True)
    countable = models.CharField(max_length=1, choices=YES_NO,)
    min_grade_required = models.CharField(max_length=2)
    pass_fail_accepted = models.CharField(max_length=1)
    grade = models.CharField(max_length=2)

    class Meta:
        db_tablespace = 'regs_spform_data'
        abstract = True

    def __unicode__(self):
        return str(self.major) + ' ' + self.unique

    def save(self, *args, **kwargs):
        # call original save method
        super(CourseInfoForm, self).save(*args, **kwargs)
        # update total countable hours
        athlete_ccyys_admin = self.major.athlete_ccyys_admin
        courses = Course.objects.filter(major=self.major)
        additional_courses = AdditionalCourse.objects.filter(major=self.major)
        course_list = list(chain(courses, additional_courses))  # combine
        total_credit = 0
        for course in course_list:
            if not course.countable == 'Y' or not course.grade:
                continue  # just skip this course!
            countable = evaluate_for_countable_hrs(course.min_grade_required, course.pass_fail_accepted, course.grade)
            if countable:
                total_credit += course.credit_hours
        athlete_ccyys_admin.total_countable_degree_hours = total_credit
        athlete_ccyys_admin.save()


class Course(CourseInfoForm):
    """Represents a course taken at UT."""
    pass


class AdditionalCourse(CourseInfoForm):
    """Each record represents a user added CBE, Transfer, etc. course."""
    pass


class FinalCourse(models.Model):
    """Each row represents a course a student had on record for the semester at grade processing."""

    athlete_ccyys = models.ForeignKey('AthleteCcyys')
    course_category = models.CharField(max_length=3)
    course_number = models.CharField(max_length=6)
    unique = models.CharField(max_length=5)
    credit_hours = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])

    class Meta:
        db_tablespace = 'regs_spform_data'

    # def __unicode__(self):
    #     return str(self.athlete_ccyys) + ' ' + self.unique


class AthleteCcyysSport(models.Model):
    """Matches athletes to the sports they are playing in a given semester.
    Also referred to as their squad."""

    # There is a business need to unofficially group the different track
    # sports. The ability to search by track was requested by athletics and
    # certifications. This maps the different track fields to the fake track
    # 'MTK'/'WTK' in the SPORTS array.
    # same goes for rowing and the fake 'WRO' code.
    MENS_TRACK = 'MTK'
    WOMENS_TRACK = 'WTK'
    MENS_INDOOR_TRACK = 'MTI'
    WOMENS_INDOOR_TRACK = 'WTI'
    MENS_OUTDOOR_TRACK = 'MTO'
    WOMENS_OUTDOOR_TRACK = 'WTO'
    MENS_CROSS_COUNTRY = 'MCC'
    WOMENS_CROSS_COUNTRY = 'WCC'
    MENS_TRACK_CODES = [MENS_INDOOR_TRACK, MENS_OUTDOOR_TRACK, MENS_CROSS_COUNTRY]
    WOMENS_TRACK_CODES = [WOMENS_INDOOR_TRACK, WOMENS_OUTDOOR_TRACK, WOMENS_CROSS_COUNTRY]
    
    WOMENS_ROW_ALL = 'WRO'
    WOMENS_NOVICE_ROW = 'WUS'
    WOMENS_ROWING = 'WCR'
    WOMENS_ROW_ALL_CODES = [WOMENS_NOVICE_ROW, WOMENS_ROWING] 

    SPORTS = {'MBA': 'Men\'s Baseball',
              'MBB': 'Men\'s Basketball',
              'MCC': 'Men\'s Cross Country ',
              'MFB': 'Men\'s Football',
              'MGO': 'Men\'s Golf',
              'MSW': 'Men\'s Swim/Diving',
              'MTE': 'Men\'s Tennis',
              'MTI': 'Men\'s Track, Indoor',
              'MTO': 'Men\'s Track, Outdoor',
              'WMA': 'Women\'s Athletics',
              'WBB': 'Women\'s Basketball',
              'WCC': 'Women\'s C. Country',
              'WU2': 'Women\'s Diving',
              'WGO': 'Women\'s Golf ',
              'WUS': 'Women\'s Novice Row',
              'WCR': 'Women\'s Rowing',
              'WSO': 'Women\'s Soccer',
              'WSB': 'Women\'s Softball',
              'WSW': 'Women\'s Swim/Diving',
              'WTE': 'Women\'s Tennis',
              'WTI': 'Women\'s Track/Indoor',
              'WTO': 'Women\'s Track/Outdr',
              'WVB': 'Women\'s Volleyball',
              WOMENS_TRACK: 'Women\'s Track -- All',
              MENS_TRACK: 'Men\'s Track -- All',
              WOMENS_ROW_ALL: 'Women\'s Rowing -- All',
              }

    athlete_ccyys = models.ForeignKey('AthleteCcyys')
    sport = models.CharField(max_length=3)
    sport_description = models.CharField(max_length=60, blank=True)

    class Meta:
        db_tablespace = 'regs_spform_data'
        unique_together = (('athlete_ccyys', 'sport'),)

    def __unicode__(self):
        return str(self.athlete_ccyys) + ' ' + self.sport_description

    def save(self, *args, **kwargs):
        # fills the description value
        if not self.sport_description:
            try:
                self.sport_description = self.SPORTS[self.sport]
            except KeyError:
                logger.error('No description for sport ' + str(self.sport))
        # call original save method
        super(AthleteCcyysSport, self).save(*args, **kwargs)


class Comments(models.Model):
    """Allows users to store notes for other users to view."""

    """This model users Generic relations with ContentType, which
    is a little weird if you haven't used them before. I recommend
    reading the docs before messing with it. Basically, the form
    object might be a PercentDegree or it might be an AthleteCcyysAdmin,
    so we have to make Comments able to work with either."""
    form_type = models.ForeignKey(ContentType)
    form_id = models.PositiveIntegerField()
    form_object = GenericForeignKey('form_type', 'form_id')
    comments = models.CharField(max_length=250)
    user = models.ForeignKey('User')
    timestamp = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=True)  # editable until form is advanced or returned

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['-timestamp']

    def __unicode__(self):
        return 'Comment ' + str(self.id)


class PercentDegree(RoutingForm):
    """Each record represents one percentage of degree form."""

    major = models.ForeignKey('AthleteMajor')
    projected_countable_hours = models.IntegerField(validators=[MinValueValidator(0)], default=0, null=True)
    total_hours_required = models.IntegerField(validators=[MinValueValidator(0)], default=0, null=True)
    projected_percentage = models.FloatField(default=0, null=True)
    # The following fields were in the original design, but were removed at the request of the users.
    # Keeping just in case we want them later.
    final_countable_hours = models.IntegerField(validators=[MinValueValidator(0)], default=0, null=True)
    final_percentage = models.FloatField(default=0, null=True)

    class Meta:
        db_tablespace = 'regs_spform_data'

    def __unicode__(self):
        return 'Percent form for major ' + str(self.major)

    def save(self, *args, **kwargs):

        if self.projected_countable_hours == 0 or self.total_hours_required == 0:
            self.projected_percentage = 0
        # calculate the projected percentage of degree
        # This is meant to be this way. It looks janky, but we don't round up on percentage.
        # NCAA regulation requires it to be truncated, and this is an easy way to do it.
        elif self.projected_countable_hours != '' and self.total_hours_required != '':
            percentage = (Decimal(self.projected_countable_hours) / Decimal(self.total_hours_required)) * 100
            percentage_split = str(percentage).split('.')
            a = percentage_split[0]
            try:
                b = percentage_split[1]
            except (ValueError, IndexError):     # in the case of an integer
                self.projected_percentage = (Decimal(self.projected_countable_hours) / Decimal(self.total_hours_required)) * 100
            else:
                self.projected_percentage = float(a + '.' + b[0:2])


        # call original save method
        super(PercentDegree, self).save(*args, **kwargs)


class CourseLog(models.Model):
    """ Works with SpdFormLog to record changes to courses."""

    spd_form_log = models.ForeignKey('SpdFormLog')
    course_category = models.CharField(max_length=3)
    course_number = models.CharField(max_length=6)
    unique = models.CharField(max_length=5)
    course_type = models.CharField(max_length=3)
    credit_hours = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)], default=0, null=True)
    countable = models.BooleanField(default=False)
    min_grade_required = models.CharField(max_length=2)
    pass_fail_accepted = models.BooleanField(default=False)
    grade = models.CharField(max_length=12)

    class Meta:
        db_tablespace = 'regs_spform_data'

    def __unicode__(self):
        return 'CourseLog record for ' + str(self.spd_form_log) + ' ' + self.unique


class AdditionalCourseLog(models.Model):
    """ Works with SpdFormLog to record changes to transfer/cbe/etc courses."""

    spd_form_log = models.ForeignKey('SpdFormLog')
    course_category = models.CharField(max_length=3)
    course_number = models.CharField(max_length=6)
    unique = models.CharField(max_length=5)
    course_type = models.CharField(max_length=3)
    credit_hours = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])
    countable = models.BooleanField(default=False)
    min_grade_required = models.CharField(max_length=2)
    pass_fail_accepted = models.BooleanField(default=False)
    grade = models.CharField(max_length=12)

    class Meta:
        db_tablespace = 'regs_spform_data'

    def __unicode__(self):
        return 'AdditionalCourseLog record for ' + str(self.spd_form_log) + ' ' + self.unique


class SpdFormLog(models.Model):
    """Records changes to a given spd form."""

    update_datetime = models.DateTimeField(auto_now_add=True)
    updater = models.CharField(max_length=8, default='Unknown')  # either a user eid or a batch job name
    spd_form = models.ForeignKey('AthleteCcyysAdmin')
    percent_degree = models.ForeignKey("PercentDegree", null=True, blank=True)

    school_code = models.CharField(max_length=1, blank=True)
    school_name = models.CharField(max_length=240, blank=True)
    major_code = models.CharField(max_length=5, blank=True)
    major_name = models.CharField(max_length=54, blank=True)
    minor = models.CharField(max_length=25, blank=True)
    catalog_begin = models.CharField(max_length=4, blank=True)
    catalog_end = models.CharField(max_length=4, blank=True)
    projected_countable_hours = models.IntegerField(validators=[MinValueValidator(0)], null=True)
    total_hours_required = models.IntegerField(validators=[MinValueValidator(0)], null=True)
    projected_percentage = models.FloatField(default=0, null=True)
    final_countable_hours = models.IntegerField(validators=[MinValueValidator(0)], null=True)
    final_percentage = models.FloatField(default=0, null=True)

    @property
    def student(self):
        return self.spd_form.athlete_ccyys.athlete

    @property
    def ccyys(self):
        return self.spd_form.athlete_ccyys.ccyys

    @property
    def previous_record(self):
        try:
            return SpdFormLog.objects.filter(spd_form=self.spd_form).filter(pk__lt=self.id)[:1].get()
        except SpdFormLog.DoesNotExist:
            return False

    class Meta:
        db_tablespace = 'regs_spform_data'
        ordering = ['-pk']

    def __unicode__(self):
        return ('Log record for ' + str(self.spd_form) + ' on ' + str(self.update_datetime) +
                ' by ' + str(self.updater))
