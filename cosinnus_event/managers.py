# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now

from taggit.models import TaggedItem
from django.contrib.auth.models import AnonymousUser


class EventManager(models.Manager):
    
    def public(self):
        from cosinnus.utils.permissions import filter_tagged_object_queryset_for_user
        return filter_tagged_object_queryset_for_user(self.get_queryset(), AnonymousUser())

    def all_upcoming(self):
        from cosinnus_event.models import upcoming_event_filter
        return upcoming_event_filter(self.get_queryset())

    def public_upcoming(self):
        from cosinnus_event.models import upcoming_event_filter
        return upcoming_event_filter(self.public())
    
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
