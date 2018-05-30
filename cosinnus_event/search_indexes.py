# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from haystack import indexes

from cosinnus.utils.search import BaseTaggableObjectIndex, StoredDataIndexMixin

from cosinnus_event.models import Event, EventAttendance


class EventIndex(BaseTaggableObjectIndex, StoredDataIndexMixin, indexes.Indexable):
    
    from_date = indexes.DateTimeField(model_attr='from_date', null=True)
    to_date = indexes.DateTimeField(model_attr='to_date', null=True)
    event_state = indexes.IntegerField(model_attr='state', null=True)
    humanized_event_time_html = indexes.CharField(stored=True, indexed=False)
    participants = indexes.MultiValueField(stored=True, indexed=False)
    
    def get_model(self):
        return Event
    
    def get_image_field_for_background(self, obj):
        return obj.attached_image.file if obj.attached_image else None
    
    def prepare_description(self, obj):
        return obj.note
    
    def prepare_participant_count(self, obj):
        """ Attendees for events """
        return obj.attendances.filter(state__gt=EventAttendance.ATTENDANCE_NOT_GOING).count()
    
    def prepare_humanized_event_time_html(self, obj):
        return obj.get_humanized_event_time_html()
    
    def prepare_participants(self, obj):
        return list(obj.attendances.filter(state__gt=EventAttendance.ATTENDANCE_NOT_GOING).values_list('user__id', flat=True))
    
    