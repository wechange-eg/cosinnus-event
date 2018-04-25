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
    
    def get_image_field_for_background(self, obj):
        return obj.attached_image.file if obj.attached_image else None
    
    def prepare_description(self, obj):
        return obj.note
