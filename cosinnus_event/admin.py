# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from cosinnus_event.models import Event, Suggestion, Vote


class VoteInlineAdmin(admin.TabularInline):
    extra = 0
    list_display = ('from_date', 'to_date', 'event')
    model = Vote


class SuggestionAdmin(admin.ModelAdmin):
    inlines = (VoteInlineAdmin,)
    list_display = ('from_date', 'to_date', 'event', 'count')
    list_filter = ('event__state', 'event__created_by', 'event__group',)
    readonly_fields = ('event', 'count')

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            # we create a new suggestion and the user should be able to select
            # an event.
            return filter(lambda x: x != 'event', self.readonly_fields)
        return super(SuggestionAdmin, self).get_readonly_fields(request, obj)


class SuggestionInlineAdmin(admin.TabularInline):
    extra = 0
    list_display = ('from_date', 'to_date', 'event', 'count')
    model = Suggestion
    readonly_fields = ('count',)


class EventAdmin(admin.ModelAdmin):
    inlines = (SuggestionInlineAdmin,)
    list_display = ('title', 'from_date', 'to_date', 'created_by', 'group',
                    'state')
    list_filter = ('state', 'created_by', 'group',)
    search_fields = ('title', 'note')


admin.site.register(Event, EventAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
