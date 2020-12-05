"""Figures signals module

Experimental receiver to test notifications on `StudentModule` save.

"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from courseware.models import StudentModule  # pylint: disable=import-error


logger = logging.getLogger(__name__)


def log_student_module_event(event_type, instance):
    msg = 'StudentModule.{event_type}:{timestamp}, {user}, {course_id}'.format(
            event_type=event_type,
            timestamp=instance.created,
            user=instance.student.username,
            course_id=instance.course_id)
    logger.info(msg)


@receiver(post_save, sender=StudentModule)
def track_student_module_save(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Spike function to test this Django Signals receiever on staging

    When a StudentModule record is created or modified, this function should
    get called. We're first logging the event to the default logger.
    We can then grep for events in the logs

    example kwargs:
    {
      'update_fields': None, 'raw': False,
      'signal': <django.db.models.signals.ModelSignal object at 0x102d84650>,
      'using': 'default',
      'created': True
    }
    """
    log_student_module_event('saved', instance)
