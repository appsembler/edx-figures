
from datetime import datetime
import pytest
from django.utils.timezone import utc

from tests.factories import (
    CourseOverviewFactory,
    OrganizationFactory,
    OrganizationCourseFactory,
    StudentModuleFactory,
    SiteFactory,
)
from tests.helpers import organizations_support_sites


if organizations_support_sites():
    from tests.factories import UserOrganizationMappingFactory


@pytest.fixture
@pytest.mark.django_db
def sm_test_data(db):
    year_for = 2019
    month_for = 10
    created_date = datetime(year_for, month_for, 1).replace(tzinfo=utc)
    modified_date = datetime(year_for, month_for, 10).replace(tzinfo=utc)
    site = SiteFactory()
    org = OrganizationFactory(sites=[site])
    co = CourseOverviewFactory()
    sm = [StudentModuleFactory(
        course_id=co.id,
        created=created_date,
        modified=modified_date,
        ) for i in range(5)]
    OrganizationCourseFactory(organization=org, course_id=str(co.id))
    if organizations_support_sites():
        for rec in sm:
            UserOrganizationMappingFactory(user=rec.student,
                                           organization=org)
    return dict(
        student_modules=sm,
        organization=org,
        site=site,
        year_for=year_for,
        month_for=month_for
    )
