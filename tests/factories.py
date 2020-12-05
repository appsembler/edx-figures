'''Helpers to generate model instances for testing.

Defines model factories for Figures, edX platform, and other models that we
need to create for our tests.

Uses Factory Boy: https://factoryboy.readthedocs.io/en/latest/

'''

from __future__ import absolute_import
import datetime
from dateutil.relativedelta import relativedelta
from django.utils.timezone import utc

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)
from openedx.core.djangoapps.course_groups.models import (
    CourseUserGroup,
    CohortMembership,
)

from figures.compat import StudentModule, CourseKeyField, GeneratedCertificate

from student.models import CourseAccessRole, CourseEnrollment, UserProfile
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership

import organizations

from figures.helpers import as_course_key
from figures.models import (
    CourseDailyMetrics,
    CourseMauMetrics,
    CourseMonthlyActiveUser,
    LearnerCourseGradeMetrics,
    SiteDailyMetrics,
    SiteMonthlyMetrics,
    SiteMauMetrics,
)

from tests.helpers import (
    organizations_support_sites,
    OPENEDX_RELEASE,
    GINKGO,
)
import six


COURSE_ID_STR_TEMPLATE = 'course-v1:StarFleetAcademy+SFA{}+2161'


class SiteFactory(DjangoModelFactory):
    class Meta:
        model = Site
    domain = factory.Sequence(lambda n: 'site-{}.example.com'.format(n))
    name = factory.Sequence(lambda n: 'Site {}'.format(n))


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    # User full name
    name = factory.Sequence(lambda n: 'User Name{}'.format(n))
    country = 'US'
    gender = 'o'
    year_of_birth = fuzzy.FuzzyInteger(1950,2000)
    level_of_education = fuzzy.FuzzyChoice(
        ['p','m','b','a','hs','jh','el','none', 'other',]
        )
    profile_image_uploaded_at = fuzzy.FuzzyDateTime(datetime.datetime(
        2018,0o4,0o1, tzinfo=factory.compat.UTC))


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user{}'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'password')
    email = factory.LazyAttribute(lambda a: '{0}@example.com'.format(a.username))
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 4, 1, tzinfo=factory.compat.UTC))

    # TODO: Figure out if this can be a SubFactory and the advantages
    profile = factory.RelatedFactory(UserProfileFactory, 'user')

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for team in extracted:
                self.teams.add(team)


if organizations_support_sites():
    class OrganizationFactory(DjangoModelFactory):
        class Meta:
            model = organizations.models.Organization

        name = factory.Sequence(u'organization name {}'.format)
        short_name = factory.Sequence(u'name{}'.format)
        description = factory.Sequence(u'description{}'.format)
        logo = None
        active = True

        # Appsembler fork specific:
        @factory.post_generation
        def sites(self, create, extracted, **kwargs):
            if not create:
                return
            if extracted:
                for site in extracted:
                    self.sites.add(site)
else:
    class OrganizationFactory(DjangoModelFactory):
        class Meta:
            model = organizations.models.Organization

        name = factory.Sequence(u'organization name {}'.format)
        short_name = factory.Sequence(u'name{}'.format)
        description = factory.Sequence(u'description{}'.format)
        logo = None
        active = True


class OrganizationCourseFactory(DjangoModelFactory):
    class Meta:
        model = organizations.models.OrganizationCourse

    course_id = factory.Sequence(lambda n: COURSE_ID_STR_TEMPLATE.format(n))
    organization = factory.SubFactory(OrganizationFactory)
    active = True


if organizations_support_sites():
    class UserOrganizationMappingFactory(factory.DjangoModelFactory):
        class Meta(object):
            model = organizations.models.UserOrganizationMapping

        user = factory.SubFactory(UserFactory)
        organization = factory.SubFactory(OrganizationFactory)
        is_active = True
        is_amc_admin = False


class CourseOverviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = CourseOverview

    # Only define the fields that we will retrieve
    id = factory.Sequence(lambda n: as_course_key(
        COURSE_ID_STR_TEMPLATE.format(n)))
    display_name = factory.Sequence(lambda n: 'SFA Course {}'.format(n))
    org = 'StarFleetAcademy'

    if not OPENEDX_RELEASE == GINKGO:
        version = CourseOverview.VERSION
    display_org_with_default = factory.LazyAttribute(lambda o: o.org)
    created = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 2, 1, tzinfo=factory.compat.UTC))
    enrollment_start = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 3, 1, tzinfo=factory.compat.UTC))
    enrollment_end = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 3, 15, tzinfo=factory.compat.UTC))
    start = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 4, 1, tzinfo=factory.compat.UTC))
    end = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 6, 1, tzinfo=factory.compat.UTC))
    self_paced = False


class CourseTeamFactory(DjangoModelFactory):
    class Meta:
        model = CourseTeam

    name = factory.Sequence(lambda n: "CourseTeam #%s" % n)


class CourseTeamMembershipFactory(DjangoModelFactory):
    class Meta:
        model = CourseTeamMembership


class GeneratedCertificateFactory(DjangoModelFactory):
    class Meta:
        model = GeneratedCertificate

    user = factory.SubFactory(
        UserFactory,
    )
    course_id = factory.Sequence(lambda n: COURSE_ID_STR_TEMPLATE.format(n))
    created_date = factory.Sequence(lambda n:
        (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc))


class StudentModuleFactory(DjangoModelFactory):
    class Meta:
        model = StudentModule

    student = factory.SubFactory(
        UserFactory,
    )
    course_id = factory.Sequence(lambda n: as_course_key(
        COURSE_ID_STR_TEMPLATE.format(n)))
    created = fuzzy.FuzzyDateTime(datetime.datetime(
        2018,2,2, tzinfo=factory.compat.UTC))
    modified = fuzzy.FuzzyDateTime(datetime.datetime(
        2018,2,2, tzinfo=factory.compat.UTC))


if OPENEDX_RELEASE == GINKGO:
    class CourseEnrollmentFactory(DjangoModelFactory):
        class Meta:
            model = CourseEnrollment

        user = factory.SubFactory(
            UserFactory,
        )
        course_id = factory.SelfAttribute('course_overview.id')
        course_overview = factory.SubFactory(CourseOverviewFactory)
        created = factory.Sequence(lambda n:
            (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc))

else:

    class CourseEnrollmentFactory(DjangoModelFactory):
        class Meta(object):
            model = CourseEnrollment

        user = factory.SubFactory(UserFactory)

        created = factory.Sequence(lambda n:
            (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc))


        @classmethod
        def _create(cls, model_class, *args, **kwargs):
            manager = cls._get_manager(model_class)
            course_kwargs = {}
            for key in kwargs.keys():
                if key.startswith('course__'):
                    course_kwargs[key.split('__')[1]] = kwargs.pop(key)

            if 'course' not in kwargs:
                course_id = kwargs.get('course_id')
                course_overview = None
                if course_id is not None:
                    if isinstance(course_id, six.string_types):
                        course_id = as_course_key(course_id)
                        course_kwargs.setdefault('id', course_id)

                    try:
                        course_overview = CourseOverview.get_from_id(course_id)
                    except CourseOverview.DoesNotExist:
                        pass

                if course_overview is None:
                    course_overview = CourseOverviewFactory(**course_kwargs)
                kwargs['course'] = course_overview

            return manager.create(*args, **kwargs)


class CourseAccessRoleFactory(DjangoModelFactory):
    class Meta:
        model = CourseAccessRole
    user = factory.SubFactory(
        UserFactory,
    )
    course_id = factory.Sequence(lambda n: as_course_key(
        COURSE_ID_STR_TEMPLATE.format(n)))
    role = factory.Iterator(['instructor', 'staff'])


##
## Figures model factories
##

class CourseDailyMetricsFactory(DjangoModelFactory):
    class Meta:
        model = CourseDailyMetrics
    site = factory.SubFactory(SiteFactory)
    date_for = factory.Sequence(lambda n:
        (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc).date())
    course_id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    enrollment_count = factory.Sequence(lambda n: n)
    active_learners_today = factory.Sequence(lambda n: n)
    average_progress = 0.50
    average_days_to_complete = 10
    num_learners_completed = 5


class LearnerCourseGradeMetricsFactory(DjangoModelFactory):
    class Meta:
        model = LearnerCourseGradeMetrics
    site = factory.SubFactory(SiteFactory)
    date_for = factory.Sequence(lambda n:
        (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc).date())
    user = factory.SubFactory(UserFactory)
    course_id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    points_possible = 30.0
    points_earned = 15.0
    sections_worked = 5
    sections_possible = 10


class SiteDailyMetricsFactory(DjangoModelFactory):
    class Meta:
        model = SiteDailyMetrics
    site = factory.SubFactory(SiteFactory)
    date_for = factory.Sequence(lambda n:
        (datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(tzinfo=utc).date())
    cumulative_active_user_count = factory.Sequence(lambda n: n)
    total_user_count = factory.Sequence(lambda n: n)
    course_count = factory.Sequence(lambda n: n)
    total_enrollment_count = factory.Sequence(lambda n: n)
    mau = factory.Sequence(lambda n: n)


class SiteMonthlyMetricsFactory(DjangoModelFactory):
    class Meta:
        model = SiteMonthlyMetrics

    site = factory.SubFactory(SiteFactory)
    month_for = factory.Sequence(lambda n: (
        datetime.date(2020, 6, 1) - relativedelta(months=n)))
    active_user_count = factory.Sequence(lambda n: n)


class CourseMauMetricsFactory(DjangoModelFactory):
    class Meta:
        model = CourseMauMetrics

    site = factory.SubFactory(SiteFactory)
    date_for = factory.Sequence(lambda n: (
        datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(
            tzinfo=utc).date())
    course_id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    mau = factory.Sequence(lambda n: n*10)


class SiteMauMetricsFactory(DjangoModelFactory):
    class Meta:
        model = SiteMauMetrics

    site = factory.SubFactory(SiteFactory)
    date_for = factory.Sequence(lambda n: (
        datetime.datetime(2018, 1, 1) + datetime.timedelta(days=n)).replace(
            tzinfo=utc).date())
    mau = factory.Sequence(lambda n: n*10)


class CourseMonthlyActiveUserFactory(DjangoModelFactory):
    """
    We might not need this
    """
    class Meta:
        model = CourseMonthlyActiveUser
    site = factory.SubFactory(SiteFactory)
    month_for = factory.Sequence(lambda n: (
        datetime.date(2020, 6, 1) - relativedelta(months=n)))
    course_id = factory.Sequence(lambda n:
        'course-v1:StarFleetAcademy+SFA{}+2161'.format(n))
    user = factory.SubFactory(UserFactory)


class CourseUserGroupFactory(DjangoModelFactory):
    class Meta:
        model = CourseUserGroup
    name = factory.Sequence(lambda n: "CourseTeam #%s" % n)
    course_id = factory.Sequence(lambda n: as_course_key(
        COURSE_ID_STR_TEMPLATE.format(n)))
    group_type = CourseUserGroup.COHORT

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.users.add(user)


class CohortMembershipFactory(DjangoModelFactory):
    class Meta:
        model = CohortMembership

    course_user_group = factory.SubFactory(CourseUserGroupFactory)
    user = factory.SubFactory(UserFactory)
    course_id = factory.SelfAttribute('course_user_group.course_id')
