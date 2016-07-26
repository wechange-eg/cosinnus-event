# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now

from taggit.models import TaggedItem


class EventManager(models.Manager):
    def public(self):
        # Django 1.5: get_query_set, 1.7: get_queryset
        qs = getattr(self, 'get_queryset', self.get_query_set)()
        return qs.filter(public=True, state=self.model.STATE_SCHEDULED)

    def upcoming(self, count):
        return self.public().filter(to_date__gte=now()).order_by("from_date").all()[:count]
    
    def archived(self):
        qs = getattr(self, 'get_queryset', self.get_query_set)()
        return qs.filter(state=self.model.STATE_ARCHIVED_DOODLE)
    
    def tags(self):
        event_type = ContentType.objects.get(app_label="cosinnus_event", model="event")

        tag_names = []
        for ti in TaggedItem.objects.filter(content_type_id=event_type):
            if ti.tag.name not in tag_names:
                tag_names.append(ti.tag.name)

        return tag_names
