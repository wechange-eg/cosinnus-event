# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from builtins import object
import datetime

from django.urls import reverse
from django.db import models, transaction
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
from cosinnus_event.managers import EventQuerySet
from cosinnus.models import BaseTaggableObjectModel
from cosinnus.utils.permissions import filter_tagged_object_queryset_for_user,\
    check_object_read_access
from cosinnus.utils.urls import group_aware_reverse
from cosinnus_event import cosinnus_notifications
from django.contrib.auth import get_user_model
from cosinnus.utils.files import _get_avatar_filename
from cosinnus.models.group import CosinnusPortal
from cosinnus.views.mixins.reflected_objects import MixReflectedObjectsMixin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from cosinnus.models.tagged import LikeableObjectMixin
from uuid import uuid1
import time
from django.core.validators import MaxValueValidator, MinValueValidator
from cosinnus.models.conference import CosinnusConferenceRoom
from django.core.exceptions import ImproperlyConfigured
from threading import Thread
import logging

logger = logging.getLogger('cosinnus')


def localize(value, format):
    if (not format) or ("FORMAT" in format):
        return date_format(localtime(value), format)
    else:
        return dateformat.format(localtime(value), format)

def get_event_image_filename(instance, filename):
    return _get_avatar_filename(instance, filename, 'images', 'events')

@python_2_unicode_compatible
class Event(LikeableObjectMixin, BaseTaggableObjectModel):

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

    objects = EventQuerySet.as_manager()
    
    timeline_template = 'cosinnus_event/v2/dashboard/timeline_item.html'

    class Meta(BaseTaggableObjectModel.Meta):
        ordering = ['from_date', 'to_date', 'title']
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
    
    def get_icon(self):
        """ Returns the font-awesome icon specific to this object type """
        if self.state == 2:
            return 'fa-calendar-check-o'
        else:
            return 'fa-calendar'
    
    def save(self, created_from_doodle=False, *args, **kwargs):
        created = bool(self.pk) == False
        super(Event, self).save(*args, **kwargs)

        if created:
            # event/doodle was created or
            # event went from being a doodle to being a real event, so fire event created
            session_id = uuid1().int
            audience = get_user_model().objects.filter(id__in=self.group.members).exclude(id=self.creator.pk)
            group_followers_except_creator_ids = [pk for pk in self.group.get_followed_user_ids() if not pk in [self.creator_id]]
            group_followers_except_creator = get_user_model().objects.filter(id__in=group_followers_except_creator_ids)
            if self.state == Event.STATE_SCHEDULED:
                # followers for the group
                cosinnus_notifications.followed_group_event_created.send(sender=self, user=self.creator, obj=self, audience=group_followers_except_creator, session_id=session_id)
                # regular members
                cosinnus_notifications.event_created.send(sender=self, user=self.creator, obj=self, audience=audience, session_id=session_id, end_session=True)
            else:
                # followers for the group
                cosinnus_notifications.followed_group_doodle_created.send(sender=self, user=self.creator, obj=self, audience=group_followers_except_creator, session_id=session_id)
                # regular members
                cosinnus_notifications.doodle_created.send(sender=self, user=self.creator, obj=self, audience=audience, session_id=session_id, end_session=True)
            
        # create a "going" attendance for the event's creator
        if settings.COSINNUS_EVENT_MARK_CREATOR_AS_GOING and created and self.state == Event.STATE_SCHEDULED:
            EventAttendance.objects.get_or_create(event=self, user=self.creator, defaults={'state':EventAttendance.ATTENDANCE_GOING})
        
        self.__state = self.state

    def get_absolute_url(self):
        kwargs = {'group': self.group, 'slug': self.slug}
        if self.state == Event.STATE_VOTING_OPEN:
            return group_aware_reverse('cosinnus:event:doodle-vote', kwargs=kwargs)
        elif self.state == Event.STATE_ARCHIVED_DOODLE:
            return group_aware_reverse('cosinnus:event:doodle-archived', kwargs=kwargs)
        return group_aware_reverse('cosinnus:event:event-detail', kwargs=kwargs)
    
    def get_edit_url(self):
        kwargs = {'group': self.group, 'slug': self.slug}
        if self.state == Event.STATE_VOTING_OPEN or self.state == Event.STATE_ARCHIVED_DOODLE:
            return group_aware_reverse('cosinnus:event:doodle-edit', kwargs=kwargs)
        return group_aware_reverse('cosinnus:event:event-edit', kwargs=kwargs)
    
    def get_delete_url(self):
        kwargs = {'group': self.group, 'slug': self.slug}
        if self.state == Event.STATE_VOTING_OPEN or self.state == Event.STATE_ARCHIVED_DOODLE:
            return group_aware_reverse('cosinnus:event:doodle-delete', kwargs=kwargs)
        return group_aware_reverse('cosinnus:event:event-delete', kwargs=kwargs)
    
    def is_user_attending(self, user):
        """ For notifications, statecheck if a user is attending this event """
        return self.attendances.filter(user=user, state__in=[EventAttendance.ATTENDANCE_GOING, EventAttendance.ATTENDANCE_MAYBE_GOING]).count() >= 1
    
    def special_alert_check(self, user):
        """ Can override checking whether this user wants this alert """
        return self.is_user_attending(user)
    
    @property
    def sort_key(self):
        """ Overriding this sort key so re-ordering won't happen for widgets using events 
            (because all event querysets are already well-sorted.) """
        return 0
    
    @property
    def stream_sort_key(self):
        """ Sort key for activity streams returns the created date instead of the event date """
        return self.created
            

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
    
    def get_humanized_event_time_html(self):
        return mark_safe(render_to_string('cosinnus_event/common/humanized_event_time.html', {'event': self})).strip()

    def get_period(self):
        if self.single_day:
            return localize(self.from_date, "d.m.Y")
        else:
            return "%s - %s" % (localize(self.from_date, "d.m."), localize(self.to_date, "d.m.Y"))
    
    @classmethod
    def get_current(self, group, user, include_sub_projects=False):
        """ Returns a queryset of the current upcoming events """
        groups = [group]
        if include_sub_projects:
            groups = groups + list(group.get_children())
        
        qs = Event.objects.filter(group__in=groups).filter(state__in=[Event.STATE_SCHEDULED, Event.STATE_VOTING_OPEN])
        
        if not include_sub_projects:
            # mix in reflected objects, not needed if we are sub-grouping anyways
            for onegroup in groups:
                if "%s.%s" % (self._meta.app_label, self._meta.model_name) in settings.COSINNUS_REFLECTABLE_OBJECTS:
                    mixin = MixReflectedObjectsMixin()
                    qs = mixin.mix_queryset(qs, self._meta.model, onegroup)
        if user:
            qs = filter_tagged_object_queryset_for_user(qs, user)
        return upcoming_event_filter(qs).distinct()
    
    @classmethod
    def get_current_for_portal(self):
        """ Returns a queryset of the current upcoming events in this portal """
        qs = Event.objects.filter(group__portal=CosinnusPortal.get_current()).filter(state__in=[Event.STATE_SCHEDULED])
        return upcoming_event_filter(qs)
    
    @property
    def is_same_day(self):
        if not self.from_date or not self.to_date:
            return True
        return localtime(self.from_date).date() == localtime(self.to_date).date()
    
    @property
    def is_same_time(self):
        if not self.from_date or not self.to_date:
            return True
        return self.from_date.time() == self.to_date.time()
    
    @property
    def is_all_day(self):
        if not self.from_date or not self.to_date:
            return False
        return (localize(self.from_date, "H:i") == '00:00') and (localize(self.to_date, "H:i") == '23:59')
    
    def get_voters_pks(self):
        """ Gets the pks of all Users that have voted for this event.
            Returns an empty list if nobody has voted or the event isn't a doodle. """
        return self.suggestions.all().values_list('votes__voter__id', flat=True).distinct()
    
    def get_suggestions_hash(self):
        """ Returns a hashable string containing all suggestions with their time.
            Useful to compare equality of suggestions for two doodles. """
        return ','.join([str(time.mktime(dt.timetuple())) for dt in self.suggestions.all().values_list('from_date', flat=True)])

    def get_comment_post_url(self):
        return group_aware_reverse('cosinnus:event:comment', kwargs={'group': self.group, 'event_slug': self.slug})
    
    def get_attendants_count(self):
        all_attendants = EventAttendance.objects.filter(event=self)
        attendants_going = all_attendants.filter(state=EventAttendance.ATTENDANCE_GOING)
        return attendants_going.count()
    

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

    class Meta(object):
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
    

    class Meta(object):
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
    
    class Meta(object):
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
    event = models.ForeignKey(Event, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField(_('Text'))

    class Meta(object):
        ordering = ['created_on']
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return 'Comment on “%(event)s” by %(creator)s' % {
            'event': self.event.title,
            'creator': self.creator.get_full_name(),
        }
    
    def get_icon(self):
        """ Returns the font-awesome icon specific to this object type """
        return 'fa-comment'
    
    @property
    def parent(self):
        """ Returns the parent object of this comment """
        return self.event
    
    def get_notification_hash_id(self):
        """ Overrides the item hashing for notification alert hashing, so that
            he parent item is considered as "the same" item, instead of this comment """
        return self.parent.id

    def get_absolute_url(self):
        if self.pk:
            return '%s#comment-%d' % (self.event.get_absolute_url(), self.pk)
        return self.event.get_absolute_url()
    
    def get_edit_url(self):
        return group_aware_reverse('cosinnus:event:comment-update', kwargs={'group': self.event.group, 'pk': self.pk})

    def get_delete_url(self):
        return group_aware_reverse('cosinnus:event:comment-delete', kwargs={'group': self.event.group, 'pk': self.pk})
    
    def is_user_following(self, user):
        """ Delegates to parent object """
        return self.event.is_user_following(user)
    
    def save(self, *args, **kwargs):
        created = bool(self.pk) == False
        super(Comment, self).save(*args, **kwargs)
        
        already_messaged_user_pks = []
        if created:
            session_id = uuid1().int
            # comment was created, message event creator
            if not self.event.creator == self.creator:
                cosinnus_notifications.event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=[self.event.creator], session_id=session_id)
                already_messaged_user_pks += [self.event.creator_id]
                
            # message all followers of the event
            followers_except_creator = [pk for pk in self.event.get_followed_user_ids() if not pk in [self.creator_id, self.event.creator_id]]
            cosinnus_notifications.following_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=followers_except_creator), session_id=session_id)
            
            # message votees (except comment creator and event creator) if voting is still open
            if self.event.state == Event.STATE_VOTING_OPEN:
                votees_except_creator = [pk for pk in self.event.get_voters_pks() if not pk in [self.creator_id, self.event.creator_id]]
                cosinnus_notifications.voted_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=votees_except_creator), session_id=session_id)
                already_messaged_user_pks += votees_except_creator
                    
                
            # message all attending persons (GOING and MAYBE_GOING)
            if self.event.state == Event.STATE_SCHEDULED:
                attendees_except_creator = [attendance.user.pk for attendance in self.event.attendances.all() \
                            if (attendance.state in [EventAttendance.ATTENDANCE_GOING, EventAttendance.ATTENDANCE_MAYBE_GOING])\
                                and not attendance.user.pk in [self.creator_id, self.event.creator_id]]
                cosinnus_notifications.attending_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=get_user_model().objects.filter(id__in=attendees_except_creator), session_id=session_id)
                already_messaged_user_pks += attendees_except_creator
                
            # message all taggees (except comment creator)
            if self.event.media_tag and self.event.media_tag.persons:
                tagged_users_without_self = self.event.media_tag.persons.exclude(id__in=already_messaged_user_pks+[self.creator.id])
                cosinnus_notifications.tagged_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=list(tagged_users_without_self), session_id=session_id)
            
            # end notification session
            cosinnus_notifications.tagged_event_comment_posted.send(sender=self, user=self.creator, obj=self, audience=[], session_id=session_id, end_session=True)
            
            
    @property
    def group(self):
        """ Needed by the notifications system """
        return self.event.group
    
    def grant_extra_read_permissions(self, user):
        """ Comments inherit their visibility from their commented on parent """
        return check_object_read_access(self.event, user)


@python_2_unicode_compatible
class ConferenceEvent(Event):
    
    TYPE_LOBBY_CHECKIN = 0
    TYPE_STAGE_EVENT = 1
    TYPE_WORKSHOP = 2
    TYPE_DISCUSSION = 3
    TYPE_COFFEE_TABLE = 4
    
    TYPE_CHOICES = (
        (TYPE_LOBBY_CHECKIN, _('Lobby Check-in Event')),
        (TYPE_STAGE_EVENT, _('Stage Stream')),
        (TYPE_WORKSHOP, _('Workshop')),
        (TYPE_DISCUSSION, _('Discussion')),
        (TYPE_COFFEE_TABLE, _('Coffee Table')),
    )
    
    CONFERENCE_EVENT_TYPE_BY_ROOM_TYPE = {
        CosinnusConferenceRoom.TYPE_LOBBY: TYPE_LOBBY_CHECKIN,
        CosinnusConferenceRoom.TYPE_STAGE: TYPE_STAGE_EVENT,
        CosinnusConferenceRoom.TYPE_WORKSHOPS: TYPE_WORKSHOP,
        CosinnusConferenceRoom.TYPE_DISCUSSIONS: TYPE_DISCUSSION,
        CosinnusConferenceRoom.TYPE_COFFEE_TABLES: TYPE_COFFEE_TABLE,
    }
    
    # rooms of these types will initialize a corresponding `BBBRoom` in the media_tag
    BBB_ROOM_TYPES = (
        TYPE_WORKSHOP,
        TYPE_COFFEE_TABLE,
        TYPE_DISCUSSION,
    )
    # which event types will lead to which type of BBBRoom to be created.
    # see settings BBB_ROOM_TYPE_CHOICES and BBB_ROOM_TYPE_EXTRA_JOIN_PARAMETERS.
    # (settings.BBB_ROOM_TYPE_DEFAULT is default if event type is not in this map)
    BBB_ROOM_ROOM_TYPE_MAP = {
        TYPE_COFFEE_TABLE: 1, # 'active' preset
    }

    TIMELESS_TYPES = (
        TYPE_COFFEE_TABLE,
    )
    
    # the room this conference event is in. 
    # the conference event type will be set according to the room type of this room
    room = models.ForeignKey('cosinnus.CosinnusConferenceRoom', verbose_name=_('Room'),
        related_name='events', on_delete=models.CASCADE)
    
    # may not be changed after creation!
    type = models.PositiveSmallIntegerField(_('Conference Event Type'), blank=False,
        default=TYPE_WORKSHOP, choices=TYPE_CHOICES)

    # list of presenters/moderators that should be     
    presenters = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        verbose_name=_('Presenters'), related_name='+',
        help_text='A list of users that will be displayed as presenters and become BBB moderators in attached rooms')
    
    # Type: Workshop, Discussion
    is_break = models.BooleanField(_('Is a Break'),
        help_text='If an event is a break, no rooms will be created for it, and it will be displayed differently',
        default=False)
    
    # Type: Coffee-Tables
    max_participants = models.PositiveSmallIntegerField(_('Maximum Event Participants'),
        blank=False, default=settings.COSINNUS_CONFERENCE_COFFEETABLES_MAX_PARTICIPANTS_DEFAULT,
        validators=[MinValueValidator(2), MaxValueValidator(512)])

    class Meta(BaseTaggableObjectModel.Meta):
        ordering = ['from_date', 'to_date', 'title']
        verbose_name = _('Conference Event')
        verbose_name_plural = _('Conference Events')
        unique_together = None

    def __init__(self, *args, **kwargs):
        super(ConferenceEvent, self).__init__(*args, **kwargs)

    def __str__(self):
        readable = _('%(event)s %(type)s') % {'event': self.title, 'type': self.type}
        return readable

    def save(self, *args, **kwargs):
        created = bool(self.pk) == False
        if created:
            self.type = self.CONFERENCE_EVENT_TYPE_BY_ROOM_TYPE.get(self.room.type, None)
            if self.type is None:
                raise ImproperlyConfigured('Conference Event type not found for room type "%s"' % self.room.type)
        
        # important: super(Event), not ConferenceEvent, because we don't want to inherit the notifiers
        super(Event, self).save(*args, **kwargs)

        # create a "going" attendance for the event's creator
        if settings.COSINNUS_EVENT_MARK_CREATOR_AS_GOING and created and self.state == ConferenceEvent.STATE_SCHEDULED:
            EventAttendance.objects.get_or_create(event=self, user=self.creator, defaults={'state':EventAttendance.ATTENDANCE_GOING})
        
        if self.can_have_bbb_room():
            # we do not create a bbb room on the server yet, that only happens
            # once  `get_bbb_room_url()` is called
            try:
                self.sync_bbb_members()
            except Exception as e:
                logger.exception(e)
    
    def can_have_bbb_room(self):
        """ Check if this event may have a BBB room """
        return self.type in self.BBB_ROOM_TYPES and not self.is_break
        
    def check_and_create_bbb_room(self, threaded=True):
        """ Can be safely called at any time to create a BBB room for this event
            if it doesn't have one yet.
            @return True if a room needed to be created, False if none was created """
        # if event is of the right type and has no BBB room yet,
        if self.can_have_bbb_room() and not self.media_tag.bbb_room:
            # start a thread and create a BBB Room
            event = self
            portal = CosinnusPortal.get_current()
            
            def create_room():
                max_participants = None
                if event.type == event.TYPE_COFFEE_TABLE and event.max_participants:
                    max_participants = event.max_participants
                # determine BBBRoom type from event type
                room_type = event.BBB_ROOM_ROOM_TYPE_MAP.get(event.type, settings.BBB_ROOM_TYPE_DEFAULT)
                    
                from cosinnus.models.bbb_room import BBBRoom
                bbb_room = BBBRoom.create(
                    name=event.title,
                    meeting_id=f'{portal.slug}-{event.group.id}-{event.id}',
                    max_participants=max_participants,
                    room_type=room_type,
                )
                event.media_tag.bbb_room = bbb_room
                event.media_tag.save()
                # sync all bb users
                event.sync_bbb_members()
            
            if threaded:
                class CreateBBBRoomThread(Thread):
                    def run(self):
                        create_room()
                CreateBBBRoomThread().start()
            else:
                create_room()
            return True
        return False
    
    def sync_bbb_members(self):
        """ Completely re-syncs all users for this room """
        if self.media_tag.bbb_room:
            bbb_room = self.media_tag.bbb_room
            with transaction.atomic():
                bbb_room.remove_all_users()
                bbb_room.join_group_members(self.group)
                # creator and presenters are moderators in addition to the group admins
                bbb_room.join_user(self.creator, as_moderator=True)
                for user in self.presenters.all():
                    bbb_room.join_user(user, as_moderator=True)
                    
    
    def get_absolute_url(self):
        return group_aware_reverse('cosinnus:conference:room-event', kwargs={'group': self.group, 'slug': self.room.slug, 'event_id': self.id}).replace('%23/', '#/')
    
    def get_bbb_room_url(self):
        if not self.can_have_bbb_room():
            return None
        if self.can_have_bbb_room() and not self.media_tag.bbb_room:
            self.check_and_create_bbb_room(threaded=True)
            # redirect to a temporary URL that refreshes
            return reverse('cosinnus:bbb-room-queue', kwargs={'mt_id': self.media_tag.id})
        return self.media_tag.bbb_room.get_absolute_url()
    
    def get_edit_url(self):
        return group_aware_reverse('cosinnus:event:conference-event-edit', kwargs={'group': self.group, 'room_slug': self.room.slug, 'slug': self.slug})
    
    def get_delete_url(self):
        return group_aware_reverse('cosinnus:event:conference-event-delete', kwargs={'group': self.group, 'room_slug': self.room.slug, 'slug': self.slug})
    
    def get_type_verbose(self):
        return dict(self.TYPE_CHOICES).get(self.type, '(unknown type)')


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


def annotate_attendants_count(qs):
    """ Utility function to annotate the number of GOING attendants for 
        an Event QS. """
    return qs.annotate(
            attendants_count=models.Count(
                models.Case(
                    models.When(attendances__state=EventAttendance.ATTENDANCE_GOING, then=1),
                        default=0, output_field=models.IntegerField()
                )
            )
        )
    
