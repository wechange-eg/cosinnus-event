# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os.path import join
import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import dateformat
from django.utils.encoding import python_2_unicode_compatible
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.timezone import localtime, now
from django.utils.translation import ugettext_lazy as _, pgettext_lazy, pgettext_lazy as p_

from osm_field.fields import OSMField, LatitudeField, LongitudeField

from cosinnus_event.conf import settings
from cosinnus_event.managers import EventManager
from cosinnus.models import BaseTaggableObjectModel
from cosinnus.utils.permissions import filter_tagged_object_queryset_for_user,\
    check_object_read_access
from cosinnus.utils.urls import group_aware_reverse
from cosinnus_event import cosinnus_notifications
from django.contrib.auth import get_user_model
from cosinnus.utils.files import _get_avatar_filename
from cosinnus.models.group import CosinnusPortal
from cosinnus.views.mixins.reflected_objects import MixReflectedObjectsMixin


def localize(value, format):
    if (not format) or ("FORMAT" in format):
        return date_format(localtime(value), format)
    else:
        return dateformat.format(localtime(value), format)

def get_event_image_filename(instance, filename):
    return _get_avatar_filename(instance, filename, 'images', 'events')

@python_2_unicode_compatible
class Event(BaseTaggableObjectModel):

    SORT_FIELDS_ALIASES = [
        ('title', 'title'),
        ('from_date', 'from_date'),
        ('to_date', 'to_date'),
        ('city', 'city'),
        ('state', 'state'),
    ]

    STATE_SCHEDULED = 1
    STATE_VOTING_OPEN = 2
    STATE_CANCELED = 3
    STATE_ARCHIVED_DOODLE = 4

    STATE_CHOICES = (
        (STATE_SCHEDULED, _('Scheduled')),
        (STATE_VOTING_OPEN, _('Voting open')),
        (STATE_CANCELED, _('Canceled')),
        (STATE_ARCHIVED_DOODLE, _('Archived Event Poll')),
    )

    from_date = models.DateTimeField(
        _('Start'), default=None, blank=True, null=True, editable=True)

    to_date = models.DateTimeField(
        _('End'), default=None, blank=True, null=True, editable=True)

    state = models.PositiveIntegerField(
        _('State'),
        choices=STATE_CHOICES,
        default=STATE_VOTING_OPEN,
    )
    __state = None # pre-save purpose

    note = models.TextField(_('Note'), blank=True, null=True)

    suggestion = models.ForeignKey(
        'Suggestion',
        verbose_name=_('Event date'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_name',
    )

    location = OSMField(_('Location'), blank=True, null=True)
    location_lat = LatitudeField(_('Latitude'), blank=True, null=True)
    location_lon = LongitudeField(_('Longitude'), blank=True, null=True)

    street = models.CharField(_('Street'), blank=True, max_length=50, null=True)

    zipcode = models.PositiveIntegerField(_('ZIP code'), blank=True, null=True)

    city = models.CharField(_('City'), blank=True, max_length=50, null=True)

    public = models.BooleanField(_('Is public (on website)'), default=False)

    image = models.ImageField(
        _('Image'),
        upload_to=get_event_image_filename,
        blank=True,
        null=True)

    url = models.URLField(_('URL'), blank=True, null=True)
    
    original_doodle = models.OneToOneField("self", verbose_name=_('Original Event Poll'),
        related_name='scheduled_event', null=True, blank=True, on_delete=models.SET_NULL)

    objects = EventManager()

    class Meta(BaseTaggableObjectModel.Meta):
        ordering = ['from_date', 'to_date']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        
    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.__state = self.state

    def __str__(self):
        if self.state == Event.STATE_SCHEDULED:
            if self.single_day:
                readable = _('%(event)s (%(date)s - %(end)s)') % {
                    'event': self.title,
                    'date': localize(self.from_date, 'd. F Y h:i'),
                    'end': localize(self.to_date, 'h:i'),
                }
            else:
                readable = _('%(event)s (%(from)s - %(to)s)') % {
                    'event': self.title,
                    'from': localize(self.from_date, 'd. F Y h:i'),
                    'to': localize(self.to_date, 'd. F Y h:i'),
                }
        elif self.state == Event.STATE_CANCELED:
            readable = _('%(event)s (canceled)') % {'event': self.title}
        elif self.state == Event.STATE_VOTING_OPEN:
            readable = _('%(event)s (pending)') % {'event': self.title}
        else:
            readable = _('%(event)s (archived)') % {'event': self.title}
            
        return readable
    
    def save(self, created_from_doodle=False, *args, **kwargs):
        created = bool(self.pk) == False
        super(Event, self).save(*args, **kwargs)

        if created and not created_from_doodle:
            # event/doodle was created
            if self.state == Event.STATE_SCHEDULED:
                cosinnus_notifications.event_created.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=self.group.members).exclude(id=self.creator.pk))
            else:
                cosinnus_notifications.doodle_created.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=self.group.members).exclude(id=self.creator.pk))
        if created and created_from_doodle:
            # event went from being a doodle to being a real event, so fire event created
            cosinnus_notifications.event_created.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=self.group.members).exclude(id=self.creator.pk))
            
        # create a "going" attendance for the event's creator
        if created and self.state == Event.STATE_SCHEDULED:
            EventAttendance.objects.get_or_create(event=self, user=self.creator, defaults={'state':EventAttendance.ATTENDANCE_GOING})
        
        self.__state = self.state

    def get_absolute_url(self):
        kwargs = {'group': self.group, 'slug': self.slug}
        if self.state == Event.STATE_VOTING_OPEN:
            return group_aware_reverse('cosinnus:event:doodle-vote', kwargs=kwargs)
        elif self.state == Event.STATE_ARCHIVED_DOODLE:
            return group_aware_reverse('cosinnus:event:doodle-archived', kwargs=kwargs)
        return group_aware_reverse('cosinnus:event:event-detail', kwargs=kwargs)
    
    @property
    def sort_key(self):
            
        """ Using ``self.from_date`` as sort key if this event is scheduled and the date is set, 
            otherwise super().
            Overwritten from BaseTaggableObjectModel:
            The main property on which this object model is sorted. """
        if self.state == self.STATE_SCHEDULED and self.from_date:
            return self.from_date
        return super(Event, self).sort_key
            

    def set_suggestion(self, sugg=None, update_fields=['from_date', 'to_date', 'state', 'suggestion']):
        if sugg is None:
            # No suggestion selected or remove selection
            self.from_date = None
            self.to_date = None
            self.state = Event.STATE_VOTING_OPEN
            self.suggestion = None
        elif sugg.event.pk == self.pk:
            # Make sure to not assign a suggestion belonging to another event.
            self.from_date = sugg.from_date
            self.to_date = sugg.to_date
            self.state = Event.STATE_SCHEDULED
            self.suggestion = sugg
        else:
            return
        self.save(update_fields=update_fields)

    @property
    def single_day(self):
        return localtime(self.from_date).date() == localtime(self.to_date).date()

    def get_period(self):
        if self.single_day:
            return localize(self.from_date, "d.m.Y")
        else:
            return "%s - %s" % (localize(self.from_date, "d.m."), localize(self.to_date, "d.m.Y"))
    
    @classmethod
    def get_current(self, group, user):
        """ Returns a queryset of the current upcoming events """
        qs = Event.objects.filter(group=group).filter(state__in=[Event.STATE_SCHEDULED, Event.STATE_VOTING_OPEN])
        # mix in reflected objects
        if "%s.%s" % (self._meta.app_label, self._meta.model_name) in settings.COSINNUS_REFLECTABLE_OBJECTS:
            mixin = MixReflectedObjectsMixin()
            qs = mixin.mix_queryset(qs, self._meta.model, group)
        if user:
            qs = filter_tagged_object_queryset_for_user(qs, user)
        return upcoming_event_filter(qs)
    
    @classmethod
    def get_current_for_portal(self):
        """ Returns a queryset of the current upcoming events in this portal """
        qs = Event.objects.filter(group__portal=CosinnusPortal.get_current()).filter(state__in=[Event.STATE_SCHEDULED])
        return upcoming_event_filter(qs)
    
    @property
    def is_same_day(self):
        return localtime(self.from_date).date() == localtime(self.to_date).date()
    
    @property
    def is_same_time(self):
        return self.from_date.time() == self.to_date.time()
    
    def get_voters_pks(self):
        """ Gets the pks of all Users that have voted for this event.
            Returns an empty list if nobody has voted or the event isn't a doodle. """
        return self.suggestions.all().values_list('votes__voter__id', flat=True).distinct()
    
    


@python_2_unicode_compatible
class Suggestion(models.Model):
    from_date = models.DateTimeField(
        _('Start'), default=None, blank=False, null=False)

    to_date = models.DateTimeField(
        _('End'), default=None, blank=False, null=False)

    event = models.ForeignKey(
        Event,
        verbose_name=_('Event'),
        on_delete=models.CASCADE,
        related_name='suggestions',
    )

    count = models.PositiveIntegerField(
        pgettext_lazy('the subject', 'Votes'), default=0, editable=False)

    class Meta:
        ordering = ['event', '-count']
        unique_together = ('event', 'from_date', 'to_date')
        verbose_name = _('Suggestion')
        verbose_name_plural = _('Suggestions')

    def __str__(self):
        if self.single_day:
            if self.from_date == self.to_date:
                return '%(date)s' % {
                    'date': localize(self.from_date, 'd. F Y H:i'),
                }
            return '%(date)s - %(end)s' % {
                'date': localize(self.from_date, 'd. F Y H:i'),
                'end': localize(self.to_date, 'H:i'),
            }
        return '%(from)s - %(to)s' % {
            'from': localize(self.from_date, 'd. F Y H:i'),
            'to': localize(self.to_date, 'd. F Y H:i'),
        }

    def get_absolute_url(self):
        return self.event.get_absolute_url()

    def update_vote_count(self, count=None):
        self.count = self.votes.count()
        self.save(update_fields=['count'])

    @property
    def single_day(self):
        return localtime(self.from_date).date() == localtime(self.to_date).date()
    
    @cached_property
    def sorted_votes(self):
        return self.votes.order_by('voter__first_name', 'voter__last_name')

@python_2_unicode_compatible
class Vote(models.Model):
    
    VOTE_YES = 2
    VOTE_MAYBE = 1
    VOTE_NO = 0
    
    VOTE_CHOICES = (
        (VOTE_YES, _('Yes')),
        (VOTE_MAYBE, _('Maybe')),
        (VOTE_NO, _('No')),     
    )
    
    suggestion = models.ForeignKey(
        Suggestion,
        verbose_name=_('Suggestion'),
        on_delete=models.CASCADE,
        related_name='votes',
    )

    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Voter'),
        on_delete=models.CASCADE,
        related_name='votes',
    )
    
    choice = models.PositiveSmallIntegerField(_('Vote'), blank=False, null=False,
        default=VOTE_NO, choices=VOTE_CHOICES)
    

    class Meta:
        unique_together = ('suggestion', 'voter')
        verbose_name = pgettext_lazy('the subject', 'Vote')
        verbose_name_plural = pgettext_lazy('the subject', 'Votes')

    def __str__(self):
        return 'Vote for %(event)s: %(from)s - %(to)s' % {
            'event': self.suggestion.event.title,
            'from': localize(self.suggestion.from_date, 'd. F Y h:i'),
            'to': localize(self.suggestion.to_date, 'd. F Y h:i'),
        }

    def get_absolute_url(self):
        return self.suggestion.event.get_absolute_url()

@python_2_unicode_compatible
class EventAttendance(models.Model):
    """ Model for attendance choices of a User for an Event.
        The choices do not include a "no choice selected" state on purpose,
        as a user not having made a choice is modeled by a missing instance
        of ``EventAttendance`` for that user and event.
     """
    
    ATTENDANCE_NOT_GOING = 0
    ATTENDANCE_MAYBE_GOING = 1
    ATTENDANCE_GOING = 2
    
    ATTENDANCE_STATES = (
        (ATTENDANCE_NOT_GOING, p_('cosinnus_event_attendance', 'not going')),
        (ATTENDANCE_MAYBE_GOING, p_('cosinnus membership status', 'maybe going')),
        (ATTENDANCE_GOING, p_('cosinnus membership status', 'going')),
    )
    
    event = models.ForeignKey(Event, related_name='attendances', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        related_name='cosinnus_event_attendances', on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField(choices=ATTENDANCE_STATES,
        db_index=True, default=ATTENDANCE_NOT_GOING)
    date = models.DateTimeField(auto_now_add=True, editable=False)
    
    class Meta:
        unique_together = ('event', 'user', )
        
    def __str__(self):
        return "Event Attendance <user: %(user)s, event: %(event)s, state: %(state)d>" % {
            'user': self.user.email,
            'event': self.event.slug,
            'state': self.state,
        }
    

@python_2_unicode_compatible
class Comment(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Creator'), on_delete=models.PROTECT, related_name='event_comments')
    created_on = models.DateTimeField(_('Created'), default=now, editable=False)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True, editable=False)
    event = models.ForeignKey(Event, related_name='comments')
    text = models.TextField(_('Text'))

    class Meta:
        ordering = ['created_on']
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return 'Comment on “%(event)s” by %(creator)s' % {
            'event': self.event.title,
            'creator': self.creator.get_full_name(),
        }

    def get_absolute_url(self):
        if self.pk:
            return '%s#comment-%d' % (self.event.get_absolute_url(), self.pk)
        return self.event.get_absolute_url()
    
    def save(self, *args, **kwargs):
        created = bool(self.pk) == False
        super(Comment, self).save(*args, **kwargs)
        
        already_messaged_user_pks = []
        if created:
            # comment was created, message event creator
            if not self.event.creator == self.creator:
                cosinnus_notifications.event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=[self.event.creator])
                already_messaged_user_pks += [self.event.creator_id]
            # message votees (except comment creator and event creator) if voting is still open
            if self.event.state == Event.STATE_VOTING_OPEN:
                votees_except_creator = [pk for pk in self.event.get_voters_pks() if not pk in [self.creator_id, self.event.creator_id]]
                if votees_except_creator:
                    cosinnus_notifications.voted_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=votees_except_creator))
                    already_messaged_user_pks += votees_except_creator
            # message all attending persons (GOING and MAYBE_GOING)
            if self.event.state == Event.STATE_SCHEDULED:
                attendees_except_creator = [attendance.user.pk for attendance in self.event.attendances.all() \
                            if (attendance.state in [EventAttendance.ATTENDANCE_GOING, EventAttendance.ATTENDANCE_MAYBE_GOING])\
                                and not attendance.user.pk in [self.creator_id, self.event.creator_id]]
                if attendees_except_creator:
                    cosinnus_notifications.attending_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=attendees_except_creator))
                    already_messaged_user_pks += attendees_except_creator
                
            # message all taggees (except comment creator)
            if self.event.media_tag and self.event.media_tag.persons:
                tagged_users_without_self = self.event.media_tag.persons.exclude(id__in=already_messaged_user_pks+[self.creator.id])
                if len(tagged_users_without_self) > 0:
                    cosinnus_notifications.tagged_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=list(tagged_users_without_self))
    @property
    def group(self):
        """ Needed by the notifications system """
        return self.event.group
    
    def grant_extra_read_permissions(self, user):
        """ Comments inherit their visibility from their commented on parent """
        return check_object_read_access(self.event, user)

@receiver(post_delete, sender=Vote)
def post_vote_delete(sender, **kwargs):
    try:
        kwargs['instance'].suggestion.update_vote_count()
    except Suggestion.DoesNotExist:
        pass


@receiver(post_save, sender=Vote)
def post_vote_save(sender, **kwargs):
    kwargs['instance'].suggestion.update_vote_count()


def get_past_event_filter_expression():
    """ Returns the filter expression that defines all events that were finished before <now>. """
    _now = now()
    event_horizon = datetime.datetime(_now.year, _now.month, _now.day)
    return Q(to_date__lt=event_horizon) | (Q(to_date__isnull=True) & Q(from_date__lt=event_horizon))
   
def upcoming_event_filter(queryset):
    """ Filters a queryset of events for events that begin in the future, 
    or have an end date in the future. Will always show all events that ended today as well. """
    return queryset.exclude(get_past_event_filter_expression())

def past_event_filter(queryset):
    """ Filters a queryset of events for events that began before today, 
    or have an end date before today. """
    return queryset.filter(get_past_event_filter_expression())


import django
if django.VERSION[:2] < (1, 7):
    from cosinnus_event import cosinnus_app
    cosinnus_app.register()
