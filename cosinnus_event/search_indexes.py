# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from haystack import indexes

from cosinnus.utils.search import BaseTaggableObjectIndex

from cosinnus_event.models import Event
from django.contrib.staticfiles.templatetags.staticfiles import static


class EventIndex(BaseTaggableObjectIndex, indexes.Indexable):
    
    from_date = indexes.DateTimeField(model_attr='from_date', null=True)
    to_date = indexes.DateTimeField(model_attr='to_date', null=True)
    
    def get_model(self):
        return Event
    
    def prepare_marker_image_url(self, obj):
        return (obj.attached_image and obj.attached_image.static_image_url()) or static('images/event-image-placeholder.png')
    
    def prepare_description(self, obj):
        return obj.note
