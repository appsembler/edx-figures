
from collections import defaultdict
from datetime import datetime

from pytz import UTC

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_noop

from django_countries.fields import CountryField

from course_modes.models import CourseMode

from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

class UserProfile(models.Model):
    '''
    The production model is student.models.UserProfile
    '''
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='profile')
    name = models.CharField(blank=True, max_length=255, db_index=True)
    country = CountryField(blank=True, null=True)

    # Optional demographic data we started capturing from Fall 2012
    this_year = datetime.now(UTC).year
    VALID_YEARS = range(this_year, this_year - 120, -1)
    year_of_birth = models.IntegerField(blank=True, null=True, db_index=True)

    GENDER_CHOICES = (
        ('m', ugettext_noop('Male')),
        ('f', ugettext_noop('Female')),
        # Translators: 'Other' refers to the student's gender
        ('o', ugettext_noop('Other/Prefer Not to Say'))
    )
    gender = models.CharField(
        blank=True, null=True, max_length=6, db_index=True, choices=GENDER_CHOICES
    )

    # [03/21/2013] removed these, but leaving comment since there'll still be
    # p_se and p_oth in the existing data in db.
    # ('p_se', 'Doctorate in science or engineering'),
    # ('p_oth', 'Doctorate in another field'),
    LEVEL_OF_EDUCATION_CHOICES = (
        ('p', ugettext_noop('Doctorate')),
        ('m', ugettext_noop("Master's or professional degree")),
        ('b', ugettext_noop("Bachelor's degree")),
        ('a', ugettext_noop("Associate degree")),
        ('hs', ugettext_noop("Secondary/high school")),
        ('jhs', ugettext_noop("Junior secondary/junior high/middle school")),
        ('el', ugettext_noop("Elementary/primary school")),
        # Translators: 'None' refers to the student's level of education
        ('none', ugettext_noop("No formal education")),
        # Translators: 'Other' refers to the student's level of education
        ('other', ugettext_noop("Other education"))
    )
    level_of_education = models.CharField(
        blank=True, null=True, max_length=6, db_index=True,
        choices=LEVEL_OF_EDUCATION_CHOICES
    )

    profile_image_uploaded_at = models.DateTimeField(null=True, blank=True)

    @property
    def has_profile_image(self):
        """
        Convenience method that returns a boolean indicating whether or not
        this user has uploaded a profile image.
        """
        return self.profile_image_uploaded_at is not None


class CourseEnrollmentManager(models.Manager):
    def enrollment_counts(self, course_id):

        query = super(CourseEnrollmentManager, self).get_queryset().filter(
                      course_id=course_id, is_active=True).values(
                      'mode').order_by().annotate(models.Count('mode'))
        total = 0
        enroll_dict = defaultdict(int)
        for item in query:
            enroll_dict[item['mode']] = item['mode__count']
            total += item['mode__count']
        enroll_dict['total'] = total
        return enroll_dict


class CourseEnrollment(models.Model):
    '''
    The production model is student.models.CourseEnrollment

    The purpose of this mock is to provide the model needed to
    retrieve:
    * The learners enrolled in a course
    * When a learner enrolled
    * If the learner is active
    '''

    MODEL_TAGS = ['course', 'is_active', 'mode']

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    course = models.ForeignKey(
        CourseOverview,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )

    @property
    def course_id(self):
        return self._course_id

    @course_id.setter
    def course_id(self, value):
        if isinstance(value, basestring):
            self._course_id = CourseKey.from_string(value)
        else:
            self._course_id = value

    # NOTE: We do not want to enable `auto_now_add` because we need the factory
    # to set the created date
    created = models.DateTimeField(null=True)

    # If is_active is False, then the student is not considered to be enrolled
    # in the course (is_enrolled() will return False)
    is_active = models.BooleanField(default=True)

    # Represents the modes that are possible. We'll update this later with a
    # list of possible values.
    mode = models.CharField(default=CourseMode.DEFAULT_MODE_SLUG, max_length=100)

    objects = CourseEnrollmentManager()

    # # cache key format e.g enrollment.<username>.<course_key>.mode = 'honor'
    # COURSE_ENROLLMENT_CACHE_KEY = u"enrollment.{}.{}.mode"  # TODO Can this be removed?  It doesn't seem to be used.

    # MODE_CACHE_NAMESPACE = u'CourseEnrollment.mode_and_active'

    class Meta(object):
        unique_together = (('user', 'course'),)
        ordering = ('user', 'course')

    def __init__(self, *args, **kwargs):
        super(CourseEnrollment, self).__init__(*args, **kwargs)

        # Private variable for storing course_overview to minimize calls to the database.
        # When the property .course_overview is accessed for the first time, this variable will be set.
        self._course_overview = None


class CourseAccessRole(models.Model):
    user = models.ForeignKey(User)
    # blank org is for global group based roles such as course creator (may be deprecated)
    org = models.CharField(max_length=64, db_index=True, blank=True)
    # blank course_id implies org wide role
    course_id = CourseKeyField(max_length=255, db_index=True, blank=True)
    role = models.CharField(max_length=64, db_index=True)

    class Meta(object):
        unique_together = ('user', 'org', 'course_id', 'role')

    @property
    def _key(self):
        """
        convenience function to make eq overrides easier and clearer. arbitrary decision
        that role is primary, followed by org, course, and then user
        """
        return (self.role, self.org, self.course_id, self.user_id)

    def __eq__(self, other):
        """
        Overriding eq b/c the django impl relies on the primary key which requires fetch. sometimes we
        just want to compare roles w/o doing another fetch.
        """
        return type(self) == type(other) and self._key == other._key  # pylint: disable=protected-access

    def __hash__(self):
        return hash(self._key)

    def __lt__(self, other):
        """
        Lexigraphic sort
        """
        return self._key < other._key  # pylint: disable=protected-access

    def __unicode__(self):
        return "[CourseAccessRole] user: {}   role: {}   org: {}   course: {}".format(self.user.username, self.role, self.org, self.course_id)
