'''Helpers to generate model instances for testing.

Defines model factories for edX Figures, edX platform, and other models that we
need to create for our tests.

Uses Factory Boy: https://factoryboy.readthedocs.io/en/latest/

'''

import datetime

from django.contrib.auth import get_user_model
#from django_countries.fields import CountryField
import factory
from factory.django import DjangoModelFactory

from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

from student.models import CourseEnrollment, UserProfile
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership

from edx_figures.models import CourseDailyMetrics, SiteDailyMetrics

COURSE_ID_STR_TEMPLATE = 'course-v1:StarFleetAcademy+SFA{}+2161'


class CourseOverviewFactory(DjangoModelFactory):
    class Meta:
        model = CourseOverview

    # Only define the fields that we will retrieve
    id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    display_name = factory.Sequence(lambda n: 'SFA Course {}'.format(n))
    org = 'StarFleetAcademy'
    number = '2161'
    display_org_with_default = factory.LazyAttribute(lambda o: o.org)


class CourseTeamFactory(DjangoModelFactory):
    class Meta:
        model = CourseTeam

    name = factory.Sequence(lambda n: "CourseTeam #%s" % n)


class CourseTeamMembershipFactory(DjangoModelFactory):
    class Meta:
        model = CourseTeamMembership


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    # User full name
    name = factory.Sequence(lambda n: 'User Name{}'.format(n))
    country = 'US'


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user{}'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'password')
    is_active = True
    is_staff = False

    # TODO: Figure out if this can be a SubFactory and the advantages
    profile = factory.RelatedFactory(UserProfileFactory, 'user')

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for team in extracted:
                self.teams.add(team)


class CourseEnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = CourseEnrollment

    user = factory.SubFactory(
        UserFactory,
    )
    course_id = factory.Sequence(lambda n: COURSE_ID_STR_TEMPLATE.format(n))
    created = factory.Sequence(lambda n:
        datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n))


##
## edX Figures model factories
##

class CourseDailyMetricsFactory(DjangoModelFactory):
    class Meta:
        model = CourseDailyMetrics
    date_for = factory.Sequence(lambda n:
        datetime.date(2018, 1, 1) + datetime.timedelta(days=n))
    course_id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    enrollment_count = factory.Sequence(lambda n: n)
    active_learners_today = factory.Sequence(lambda n: n)
    average_progress = 0.50
    average_days_to_complete = 10
    num_learners_completed = 5


class SiteDailyMetricsFactory(DjangoModelFactory):
    class Meta:
        model = SiteDailyMetrics
    date_for = factory.Sequence(lambda n:
        datetime.date(2018, 1, 1) + datetime.timedelta(days=n))
    cumulative_active_user_count = factory.Sequence(lambda n: n)
    total_user_count = factory.Sequence(lambda n: n)
    course_count = factory.Sequence(lambda n: n)
    total_enrollment_count = factory.Sequence(lambda n: n)
    #site = factory.RelatedFactory(SiteFactory, 'site')
