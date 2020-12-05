"""Figures signals module

Prototype receiver to test notifications on `StudentModule` save.

* Notifications are logged to the log files
* Figures CourseMonthlyActiveUser records are created

"""
import logging
import crum
from django.db.models.signals import post_save
from django.dispatch import receiver

from figures.compat import StudentModule
from figures.log import log_exec_time
from figures.models import CourseMonthlyActiveUser
from figures.sites import get_site_for_course

logger = logging.getLogger(__name__)


def log_student_module_event(request_host, site, event_type, instance):
    """Debug logging Django signal StudentModule save event
    """
    msg = 'Figures.signals event - '
    msg += 'request_host:"{request_host}", site[{site_id}]:"{site}"\n'
    msg += '  StudentModule.{event_type}:{timestamp}, {user}, {course_id}'

    logger.info(msg.format(request_host=request_host,
                           site_id=site.id,
                           site=site.domain,
                           event_type=event_type,
                           timestamp=instance.created,
                           user=instance.student.username,
                           course_id=instance.course_id))


@receiver(post_save, sender=StudentModule)
def track_student_module_save(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Record a StudentModule record save to Figures MAU tracking

    When a StudentModule record is created or modified, this function should
    get called.

    We add a new CourseMonthlyActiveUser record if one does not already exist
    We then log this event to the logs for debugging in staging

    Since the StudentModule does not have a reference to the site, we need to
    get the site from the current request, if it exists
    example kwargs:
    ```
    {
      'update_fields': None, 'raw': False,
      'signal': <django.db.models.signals.ModelSignal object at 0x102d84650>,
      'using': 'default',
      'created': True
    }
    ```
    """
    site = None
    request_host = None
    request = crum.get_current_request()
    if request:
        request_host = request.get_host()
        if hasattr(request, 'site'):
            site = request.site

    if not site:
        with log_exec_time('Time to get site for course {}'.format(instance.course_id)):
            site = get_site_for_course(instance.course_id)

    CourseMonthlyActiveUser.objects.add_mau(site_id=site.id,
                                            course_id=instance.course_id,
                                            user_id=instance.student.id)
    log_student_module_event(request_host, site, 'saved', instance)
