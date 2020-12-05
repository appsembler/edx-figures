
from __future__ import absolute_import
from datetime import datetime
import pytest
from django.utils.timezone import utc
from six.moves import range
from tests.helpers import organizations_support_sites

from tests.factories import (
    CourseEnrollmentFactory,
    CourseOverviewFactory,
    OrganizationFactory,
    OrganizationCourseFactory,
    StudentModuleFactory,
    SiteFactory,
    UserFactory,
)

if organizations_support_sites():
    from tests.factories import UserOrganizationMappingFactory

    def map_users_to_org(org, users):
        [UserOrganizationMappingFactory(user=user,
                                        organization=org) for user in users]


@pytest.fixture
@pytest.mark.django_db
def sm_test_data(db):
    """
    WIP StudentModule test data to test MAU
    """
    year_for = 2019
    month_for = 10
    created_date = datetime(year_for, month_for, 1).replace(tzinfo=utc)
    modified_date = datetime(year_for, month_for, 10).replace(tzinfo=utc)
    course_overviews = [CourseOverviewFactory() for i in range(3)]
    site = SiteFactory()

    sm = []
    for co in course_overviews:
        sm += [StudentModuleFactory(course_id=co.id,
                                    created=created_date,
                                    modified=modified_date) for co in course_overviews]

    if organizations_support_sites():
        org = OrganizationFactory(sites=[site])
        for co in course_overviews:
            OrganizationCourseFactory(organization=org, course_id=str(co.id))
        for rec in sm:
            UserOrganizationMappingFactory(user=rec.student, organization=org)
    else:
        org = OrganizationFactory()

    return dict(site=site,
                organization=org,
                course_overviews=course_overviews,
                student_modules=sm,
                year_for=year_for,
                month_for=month_for)


@pytest.mark.django_db
def make_site_data(num_users=3, num_courses=2, create_enrollments=True):

    site = SiteFactory()
    if organizations_support_sites():
        org = OrganizationFactory(sites=[site])
    else:
        org = OrganizationFactory()
    courses = [CourseOverviewFactory() for i in range(num_courses)]
    users = [UserFactory() for i in range(num_users)]
    enrollments = []

    users = [UserFactory() for i in range(num_users)]
    if create_enrollments:
        enrollments = []
        for i, user in enumerate(users):
            # Create increasing number of enrollments for each user, maximum to one less
            # than the number of courses
            for j in range(i):
                enrollments.append(
                    CourseEnrollmentFactory(course=courses[j-1], user=user)
                )

    if organizations_support_sites():
        for course in courses:
            OrganizationCourseFactory(organization=org,
                                      course_id=str(course.id))

        # Set up user mappings
        map_users_to_org(org, users)

    data = dict(
        site=site,
        org=org,
        courses=courses,
        users=users,
    )
    if create_enrollments:
        data['enrollments'] = enrollments
    return data


@pytest.fixture
@pytest.mark.django_db
def lm_test_data(db, settings):
    """Learner Metrics Test Data

    user0 not enrolled in any courses
    user1 enrolled in 1 course
    user2 enrolled in 2 courses

    """
    if organizations_support_sites():
        settings.FEATURES['FIGURES_IS_MULTISITE'] = True

    our_site_data = make_site_data()
    other_site_data = make_site_data()
    return dict(us=our_site_data, them=other_site_data)
