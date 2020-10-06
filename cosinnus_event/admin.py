# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from cosinnus_event.models import Event, Suggestion, Vote, ConferenceEvent
from cosinnus.admin import BaseTaggableAdminMixin


class VoteInlineAdmin(admin.TabularInline):
    extra = 0
    list_display = ('from_date', 'to_date', 'event')
    model = Vote


class SuggestionAdmin(admin.ModelAdmin):
    inlines = (VoteInlineAdmin,)
    list_display = ('from_date', 'to_date', 'event', 'count')
    list_filter = ('event__state', 'event__creator', 'event__group',)
    readonly_fields = ('event', 'count')

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            # we create a new suggestion and the user should be able to select
            # an event.
            return [x for x in self.readonly_fields if x != 'event']
        return super(SuggestionAdmin, self).get_readonly_fields(request, obj)


class SuggestionInlineAdmin(admin.TabularInline):
    extra = 0
    list_display = ('from_date', 'to_date', 'event', 'count')
    model = Suggestion
    readonly_fields = ('count',)

admin.site.register(Suggestion, SuggestionAdmin)


class EventAdmin(BaseTaggableAdminMixin, admin.ModelAdmin):
    inlines = BaseTaggableAdminMixin.inlines + [SuggestionInlineAdmin,]
    list_display = BaseTaggableAdminMixin.list_display + ['from_date', 'to_date', 'group', 'state']
    list_filter = BaseTaggableAdminMixin.list_filter + ['state', ]

admin.site.register(Event, EventAdmin)


class ConferenceEventAdmin(BaseTaggableAdminMixin, admin.ModelAdmin):
    list_display = BaseTaggableAdminMixin.list_display + ['type', 'room', 'from_date', 'to_date', 'group', 'state']
    list_filter = BaseTaggableAdminMixin.list_filter + ['type', ]

admin.site.register(ConferenceEvent, ConferenceEventAdmin)

