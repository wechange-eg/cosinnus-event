# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os.path import join
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import dateformat
from django.utils.encoding import python_2_unicode_compatible
from django.utils.formats import date_format
from django.utils.timezone import localtime, now
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.db.models import Q

from osm_field.fields import OSMField
from cosinnus.models import BaseTaggableObjectModel

from cosinnus_event.conf import settings
from cosinnus_event.managers import EventManager
from django.utils.functional import cached_property
from cosinnus.utils.permissions import get_tagged_object_filter_for_user


def localize(value, format):
    if (not format) or ("FORMAT" in format):
        return date_format(localtime(value), format)
    else:
        return dateformat.format(localtime(value), format)


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

    STATE_CHOICES = (
        (STATE_SCHEDULED, _('Scheduled')),
        (STATE_VOTING_OPEN, _('Voting open')),
        (STATE_CANCELED, _('Canceled')),
    )

    from_date = models.DateTimeField(
        _('Start'), default=None, blank=True, null=True, editable=True)

    to_date = models.DateTimeField(
        _('End'), default=None, blank=True, null=True, editable=True)

    state = models.PositiveIntegerField(
        _('State'),
        choices=STATE_CHOICES,
        default=STATE_VOTING_OPEN,
        editable=False,
    )

    note = models.TextField(_('Note'), blank=True, null=True)

    suggestion = models.ForeignKey(
        'Suggestion',
        verbose_name=_('Event date'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_name',
    )

    location = OSMField(_('Location'), blank=True, null=True, geo_blank=True, geo_null=True)

    street = models.CharField(_('Street'), blank=True, max_length=50, null=True)

    zipcode = models.PositiveIntegerField(_('ZIP code'), blank=True, null=True)

    city = models.CharField(_('City'), blank=True, max_length=50, null=True)

    public = models.BooleanField(_('Is public (on website)'), default=False)

    image = models.ImageField(
        _('Image'),
        upload_to=join('cosinnus_events', 'images'),
        blank=True,
        null=True)

    url = models.URLField(_('URL'), blank=True, null=True)

    objects = EventManager()

    class Meta(BaseTaggableObjectModel.Meta):
        ordering = ['from_date', 'to_date']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

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
        else:
            readable = _('%(event)s (pending)') % {'event': self.title}
        return readable

    def get_absolute_url(self):
        kwargs = {'group': self.group.slug, 'slug': self.slug}
        if self.state == Event.STATE_VOTING_OPEN:
            return reverse('cosinnus:event:doodle-vote', kwargs=kwargs)
        return reverse('cosinnus:event:event-detail', kwargs=kwargs)

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
        qs = Event.objects.filter(group=group)
        if user:
            q = get_tagged_object_filter_for_user(user)
            qs = qs.filter(q)
        return upcoming_event_filter(qs)
        

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


@receiver(post_delete, sender=Vote)
def post_vote_delete(sender, **kwargs):
    try:
        kwargs['instance'].suggestion.update_vote_count()
    except Suggestion.DoesNotExist:
        pass


@receiver(post_save, sender=Vote)
def post_vote_save(sender, **kwargs):
    kwargs['instance'].suggestion.update_vote_count()

   
def upcoming_event_filter(queryset):
    """ Filters a queryset of events for events that begin in the future, or have an end date in the future """
    return queryset.exclude(to_date__lte=now()).exclude(Q(to_date__isnull=True) & Q(from_date__lte=now()))


import django
if django.VERSION[:2] < (1, 7):
    from cosinnus_event import cosinnus_app
    cosinnus_app.register()
