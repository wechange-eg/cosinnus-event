# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from haystack import indexes

from cosinnus.utils.search import BaseTaggableObjectIndex

from cosinnus_event.models import Event


class EventIndex(BaseTaggableObjectIndex, indexes.Indexable):

    def get_model(self):
        return Event

