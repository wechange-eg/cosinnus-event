# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from haystack import indexes

from cosinnus.utils.search import BaseTaggableObjectIndex

from cosinnus_event.models import Event


class EventIndex(BaseTaggableObjectIndex, indexes.Indexable):
    
    from_date = indexes.DateTimeField(model_attr='from_date', null=True)
    to_date = indexes.DateTimeField(model_attr='to_date', null=True)
    needs_date_filtering = indexes.BooleanField()
    
    def prepare_needs_date_filtering(self, obj):
        return True
    
    def get_model(self):
        return Event

