'''
First cut - ETL all in one for each data sink

Then pull out the steps so we can have a formal, flexible, and scalable pipeline system




'''

#from figures.pipeline import Job


# These are needed for the extractors
import datetime
from django.utils.timezone import utc

from certificates.models import GeneratedCertificate
from courseware.models import StudentModule
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment


from figures.helpers import as_course_key, as_date, next_day, prev_day
from figures.metrics import LearnerCourseGrades
from figures.models import CourseDailyMetrics
from figures.serializers import CourseIndexSerializer

# TODO: Move extractors to figures.pipeline.extract module

# The extractors work locally on the LMS
# Future: add a remote mode to pull data via REST API


# Extraction helper methods


def get_course_enrollments(course_id, date_for):
    return CourseEnrollment.objects.filter(
        course_id=as_course_key(course_id),
        created__lt=next_day(date_for),
    )


def get_num_enrolled_in_exclude_admins(course_id, date_for):
    '''
    Copied over from CourseEnrollmentManager.num_enrolled_in_exclude_admins method
    and modified to filter on date LT

    '''
    from student.roles import CourseCcxCoachRole, CourseInstructorRole, CourseStaffRole
    course_locator = course_id

    if getattr(course_id, 'ccx', None):
        course_locator = course_id.to_course_locator()

    staff = CourseStaffRole(course_locator).users_with_role()
    admins = CourseInstructorRole(course_locator).users_with_role()
    coaches = CourseCcxCoachRole(course_locator).users_with_role()

    return CourseEnrollment.objects.filter(
        course_id=course_id,
        is_active=1,
        created__lt=next_day(date_for),
    ).exclude(user__in=staff).exclude(user__in=admins).exclude(user__in=coaches).count()

def get_active_learners_today(course_id, date_for):
    '''Get StudentModules given a course id and date

    '''
    return StudentModule.objects.filter(
        course_id=as_course_key(course_id),
        modified=as_date(date_for))

def get_average_progress(course_id, date_for, course_enrollments):
    '''

    '''
    progress = []

    for ce in course_enrollments:
        lcg = LearnerCourseGrades(user_id=ce.user.id,course_id=course_id)
        print('learner: {}, pct={}'.format(lcg.learner.username, lcg.course_grade.percent))
        progress.append(lcg.progress_percent())

    if len(progress):
        average_progress = float(sum(progress))/float(len(progress))
    else:
        average_progress = 0.0

    return average_progress


def get_days_to_complete(course_id, date_for):
    '''Return a dict with a list of days to complete and errors

    NOTE: This is a work in progress, as it has issues to resolve:
    * It returns the delta in days, so working in ints
    * This means if a learner starts at midnight and finished just before midnight, then 0 days will be given

    NOTE: This has limited scaling. We ought to test it with
    1k, 10k, 100k cert records

    TODO: change to use start_date, end_date with defaults that
    start_date is open and end_date is today

    TODO: Consider collecting the total seconds rather than days
    This will improve accuracy, but may actually not be that important
    TODO: Analyze the error based on number of completions

    When we have to support scale, we can look into optimization
    techinques.
    '''
    certificates = GeneratedCertificate.objects.filter(
        course_id=as_course_key(course_id),
        created_date__lte=as_date(date_for))

    days = []
    errors = []
    for cert in certificates:
        ce = CourseEnrollment.objects.filter(
            course_id=as_course_key(course_id),
            user=cert.user)
        # How do we want to handle multiples?
        if ce.count() > 1:
            errors.append(
                dict(msg='Multiple CE records',
                     course_id=course_id,
                     user_id=cert.user.id,
                    ))

        print('start date = {}, cert_date = {}'.format(
            ce[0].created, cert.created_date))
        days.append((cert.created_date - ce[0].created).days)
    return dict(days=days, errors=errors)

def calc_average_days_to_complete(days):
    rec_count = len(days)
    if rec_count:
        return float(sum(days))/float(rec_count)
    else:
        return 0.0

def get_average_days_to_complete(course_id, date_for):

    days_to_complete = get_days_to_complete(course_id, date_for)
    # TODO: Track any errors in getting days to complete
    # This is in days_to_complete['errors']
    average_days_to_complete = calc_average_days_to_complete(
        days_to_complete['days'])
    return average_days_to_complete


def get_num_learners_completed(course_id, date_for):
    certificates = GeneratedCertificate.objects.filter(
        course_id=as_course_key(course_id))
    return certificates.count()

# Formal extractor classes

class CourseIndicesExtractor(object):
    '''
    Extract a list of course index dicts
    '''
    def extract(self, **kwargs):
        '''
        TODO: Add filters in the kwargs
        '''

        filter_args = kwargs.get('filters', {})
        queryset = CourseOverview.objects.filter(**filter_args)
        return CourseIndexSerializer(queryset, many=True)


class CourseDailyMetricsExtractor(object):
    '''
    Prototype extractor to get data needed for CourseDailyMetrics

    Next step is to break out the functionality from here to 
    separate extractors so we have more reusability
    BUT, we will then need to find a transform
    '''
    def extract(self, course_id, date_for=None, **kwargs):
        '''
            defaults = dict(
                enrollment_count=data['enrollment_count'],
                active_learners_today=data['active_learners_today'],
                average_progress=data.get('average_progress', None),
                average_days_to_complete=data.get('average_days_to_complete, None'),
                num_learners_completed=data['num_learners_completed'],
            )
        '''

        # Update args if not assigned
        if not date_for:
            #date_for = prev_day(datetime.datetime.now().date())
            date_for = prev_day(
                datetime.datetime.utcnow().replace(tzinfo=utc).date()
                )

        # We can turn this series of calls into a parallel
        # set of calls defined in a ruleset instead of hardcoded here
        # Get querysets and datasets we'll use
        # We do this to reduce calls

        course_enrollments = get_course_enrollments(
            course_id, date_for,)


        
        data = dict(date_for=date_for, course_id=course_id)

        # This is the transform step
        # After we get this working, we can then define them declaratively
        # we can do a lambda for course_enrollments to get the count

        # extract_map = dict(
        #     course_enrollments=get_course_enrollments_count,
        #     active_learners_today=get_active_learners_today
        #     )

        data['enrollment_count'] = course_enrollments.count()

        active_learners_today = get_active_learners_today(
            course_id, date_for,)
        if active_learners_today:
            active_learners_today = active_learners_today.count()
        else:
            active_learners_today = 0

        data['active_learners_today'] = active_learners_today
        data['average_progress'] = get_average_progress(
            course_id, date_for, course_enrollments,)
        data['average_days_to_complete'] = get_average_days_to_complete(
            course_id, date_for,)
        data['num_learners_completed'] = get_num_learners_completed(
            course_id, date_for,)

        return data


class CourseDailyMetricsLoader(object):

    def __init__(self, course_id):
        self.course_id = course_id
        self.extractor = CourseDailyMetricsExtractor()

    def get_data(self, date_for):
        return self.extractor.extract(
            course_id=self.course_id,
            data_for=date_for)

    def load(self, date_for=None, **kwargs):
        '''
        TODO: clean up how we do this. We want to be able to call the loader
        with an existing data set (not having to call the extractor) but we
        need to make sure that the metrics row 'date_for' is the same as
        provided in the data. So before hacking something together, I want to
        think this over some more.
        
        '''
        if not date_for:
            #date_for = prev_day(datetime.datetime.now().date())
            date_for = prev_day(
                datetime.datetime.utcnow().replace(tzinfo=utc).date()
                )

        #
        data = self.get_data(date_for=date_for)

        print('inspect me')
        import pdb; pdb.set_trace()

        course_metrics, created = CourseDailyMetrics.objects.update_or_create(
            course_id=self.course_id,
            date_for=date_for,
            defaults = dict(
                enrollment_count=data['enrollment_count'],
                active_learners_today=data['active_learners_today'],
                average_progress=data['average_progress'],
                average_days_to_complete=data['average_days_to_complete'],
                num_learners_completed=data['num_learners_completed'],
            )
        )
        return (course_metrics, created,)


#class CourseDailyMetricsJob(Job):
class CourseDailyMetricsJob(object):
    def __init__(self):
        pass

    def run(self, *args, **kwargs):
        '''

        '''
        pass


def test_extract(course_id=None):
    if not course_id:
        course_id = CourseOverview.objects.first().id

    print('course_id={}'.format(course_id))
    extractor = CourseDailyMetricsExtractor()
    return extractor.extract(course_id)


def test_load(course_id=None):
    if not course_id:
        course_id = CourseOverview.objects.first().id

    print('course_id={}'.format(course_id))
    return CourseDailyMetricsLoader(course_id).load()