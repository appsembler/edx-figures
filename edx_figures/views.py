'''

'''
from django.contrib.auth import get_user_model
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response

# Directly including edx-platform objects for early development
# Follow-on, we'll likely consolidate edx-platform model imports to an adapter
from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)
from student.models import CourseEnrollment, UserProfile

from .filters import (
    CourseDailyMetricsFilter,
    CourseEnrollmentFilter,
    CourseOverviewFilter,
    SiteDailyMetricsFilter,
    UserFilter,
)
from .models import CourseDailyMetrics, SiteDailyMetrics
from .serializers import (
    CourseDailyMetricsSerializer,
    CourseEnrollmentSerializer,
    CourseIndexSerializer,
    SiteDailyMetricsSerializer,
    UserIndexSerializer,
)


##
## UI Template rendering views
##

def edx_figures_home(request):
    '''Renders the JavaScript SPA dashboard


    TODO: Should we make this a view class?

    '''

    # Placeholder context vars just to illustrate returning API hosts to the
    # client. This one uses a protocol relative url
    context = {
        'edx_figures_api_url': '//api.foo.com',
    }
    return render(request, 'edx_figures/index.html', context)


##
## Views for data in edX platform
##

# We're going straight to the model so that we ensure we
# are getting the behavior we want.

#@view_auth_classes(is_authenticated=True)
class CoursesIndexView(ListAPIView):
    '''Provides a list of courses with abbreviated details

    Uses edx_figures.filters.CourseOverviewFilter to select subsets of
    CourseOverview objects

    We want to be able to filter on
    - org: exact and search
    - name: exact and search
    - description search
    - enrollment start
    - enrollment end
    - start
    - end

    '''
    model = CourseOverview
    queryset = CourseOverview.objects.all()
    pagination_class = None
    serializer_class = CourseIndexSerializer

    filter_backends = (DjangoFilterBackend, )
    filter_class = CourseOverviewFilter

    def get_queryset(self):
        '''

        '''
        queryset = super(CoursesIndexView, self).get_queryset()

        return queryset


# TODO: Add authorization
class UserIndexView(ListAPIView):
    '''Provides a list of users with abbreviated details

    Uses edx_figures.filters.UserFilter to select subsets of User objects
    '''

    model = get_user_model()
    queryset = get_user_model().objects.all()
    pagination_class = None
    serializer_class = UserIndexSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = UserFilter

    def get_queryset(self):
        queryset = super(UserIndexView, self).get_queryset()

        return queryset

# TODO: Change to ReadOnlyModelViewSet
class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    model = CourseEnrollment
    queryset = CourseEnrollment.objects.all()
    pagination_class = None
    serializer_class = CourseEnrollmentSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = CourseEnrollmentFilter

    def get_queryset(self):
        queryset = super(CourseEnrollmentViewSet, self).get_queryset()
        return queryset

    def list(self, request, *args, **kwargs):

        # request.query_params
        # <QueryDict: {u'course_id': [u'"course-v1:Appsembler EdX101 2015_Spring"']}>

        #print('insepect me'); import pdb; pdb.set_trace()

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

##
## Views for edX Figures models
##

class CourseDailyMetricsViewSet(viewsets.ModelViewSet):

    model = CourseDailyMetrics
    queryset = CourseDailyMetrics.objects.all()
    pagination_class = None
    serializer_class = CourseDailyMetricsSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = CourseDailyMetricsFilter

    def get_queryset(self):
        queryset = super(CourseDailyMetricsViewSet, self).get_queryset()
        return queryset


#class SiteDailyMetricsViewSet(CommonAuthMixin, viewsets.ModelViewSet):
class SiteDailyMetricsViewSet(viewsets.ModelViewSet):

    model = SiteDailyMetrics
    queryset = SiteDailyMetrics.objects.all()
    pagination_class = None
    serializer_class = SiteDailyMetricsSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = SiteDailyMetricsFilter

    def get_queryset(self):
        queryset = super(SiteDailyMetricsViewSet, self).get_queryset()
        return queryset

        #return SiteDailyMetricsQuery.get_queryset(self.request.query_params)
