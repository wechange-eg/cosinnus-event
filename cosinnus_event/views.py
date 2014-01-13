# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from django.utils.timezone import now

from extra_views import (CreateWithInlinesView, FormSetView, InlineFormSet,
    UpdateWithInlinesView, SortableListMixin)

from cosinnus.views.mixins.group import (RequireReadMixin, RequireWriteMixin,
    FilterGroupMixin)
from cosinnus.views.mixins.tagged import TaggedListMixin


from cosinnus_event.conf import settings
from cosinnus_event.forms import EventForm, SuggestionForm, VoteForm
from cosinnus_event.models import Event, Suggestion, Vote


class EventIndexView(RequireReadMixin, RedirectView):

    def get_redirect_url(self, **kwargs):
        return reverse('cosinnus:event:list', kwargs={'group': self.group.slug})

index_view = EventIndexView.as_view()


class EventListView(RequireReadMixin, FilterGroupMixin, TaggedListMixin,
        SortableListMixin, ListView):

    model = Event

    def get(self, request, *args, **kwargs):
        self.sort_fields_aliases = self.model.SORT_FIELDS_ALIASES
        return super(EventListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        past_events = []
        future_events = []

        for event in context['object_list']:
            if event.to_date and event.to_date < now():
                past_events.append(event)
            else:
                future_events.append(event)
        context.update({
            'past_events': past_events,
            'future_events': future_events
        })
        return context

list_view = EventListView.as_view()


class SuggestionInlineView(InlineFormSet):
    extra = 1
    form_class = SuggestionForm
    model = Suggestion


class EntryFormMixin(object):
    form_class = EventForm
    model = Event
    inlines = [SuggestionInlineView]

    def dispatch(self, request, *args, **kwargs):
        self.form_view = kwargs.get('form_view', None)
        return super(EntryFormMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EntryFormMixin, self).get_context_data(**kwargs)
        tags = Event.objects.tags()
        context.update({
            'tags': tags,
            'form_view': self.form_view,
        })
        return context

    def get_success_url(self):
        kwargs = {'group': self.group.slug}
        # no self.object if get_queryset from add/edit view returns empty
        if hasattr(self, 'object'):
            kwargs['slug'] = self.object.slug
            urlname = 'cosinnus:event:entry-detail'
        else:
            urlname = 'cosinnus:event:list'
        return reverse(urlname, kwargs=kwargs)


class EntryAddView(RequireWriteMixin, FilterGroupMixin, EntryFormMixin,
        CreateWithInlinesView):

    def forms_valid(self, form, inlines):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.group = self.group
        self.object.save()
        form.save_m2m()

        # Save the suggestions
        for formset in inlines:
            formset.save()

        # Check for non or a single suggestion and set it and inform the user
        num_suggs = self.object.suggestions.count()
        if num_suggs == 0:
            messages.info(self.request, _('You should define at least one date suggestion.'))
        elif num_suggs == 1:
            self.object.set_suggestion(self.object.suggestions.get())
            messages.info(self.request, _('Automatically selected the only given date suggestion as event date.'))
        return HttpResponseRedirect(self.get_success_url())

entry_add_view = EntryAddView.as_view()


class EntryEditView(RequireWriteMixin, FilterGroupMixin, EntryFormMixin,
        UpdateWithInlinesView):

    def forms_valid(self, form, inlines):
        # Save the suggestions first so we can directly access the amount of suggestions afterwards
        for formset in inlines:
            formset.save()

        self.object = form.save(commit=False)
        suggestion = form.cleaned_data.get('suggestion')
        if not suggestion:
            num_suggs = self.object.suggestions.count()
            if num_suggs == 0:
                suggestion = None
                messages.info(self.request, _('You should define at least one date suggestion.'))
            elif num_suggs == 1:
                suggestion = self.object.suggestions.get()
                messages.info(self.request, _('Automatically selected the only given date suggestion as event date.'))
        # update_fields=None leads to saving the complete model, we don't need to call obj.self here
        self.object.set_suggestion(suggestion, update_fields=None)
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        qs = super(EntryEditView, self).get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(created_by=self.request.user)

    def get(self, request, *args, **kwargs):
        try:
            return super(EntryEditView, self).get(request, *args, **kwargs)
        except Http404:
            messages.error(request, _('Event does not exist or you are not allowed to modify it.'))
            return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        try:
            return super(EntryEditView, self).post(request, *args, **kwargs)
        except Http404:
            messages.error(request, _('Event does not exist or you are not allowed to modify it.'))
            return HttpResponseRedirect(self.get_success_url())

entry_edit_view = EntryEditView.as_view()


class EntryDeleteView(RequireWriteMixin, FilterGroupMixin, DeleteView):

    model = Event
    pk_url_kwarg = 'event'

    def get_queryset(self):
        qs = super(EntryDeleteView, self).get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(created_by=self.request.user)

    def get_success_url(self):
        return reverse('cosinnus:event:list', kwargs={'group': self.group.slug})

    def get(self, request, *args, **kwargs):
        try:
            return super(EntryDeleteView, self).get(request, *args, **kwargs)
        except Http404:
            messages.error(request, _('Event does not exist or you are not allowed to modify it.'))
            return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        try:
            return super(EntryDeleteView, self).post(request, *args, **kwargs)
        except Http404:
            messages.error(request, _('Event does not exist or you are not allowed to modify it.'))
            return HttpResponseRedirect(self.get_success_url())

entry_delete_view = EntryDeleteView.as_view()


class EntryDetailView(RequireReadMixin, FilterGroupMixin, DetailView):

    model = Event

    def get_context_data(self, **kwargs):
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        context.update({
            'map_widget_height': settings.GEOPOSITION_MAP_WIDGET_HEIGHT,
        })
        return context

entry_detail_view = EntryDetailView.as_view()


class EntryVoteView(RequireWriteMixin, FilterGroupMixin, SingleObjectMixin,
        FormSetView):

    extra = 0
    form_class = VoteForm
    model = Event
    pk_url_kwarg = 'event'
    template_name = 'cosinnus_event/vote_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(EntryVoteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EntryVoteView, self).get_context_data(**kwargs)
        context.update({
            'object': self.object,
            'suggestions': self.suggestions,
        })
        return context

    def get_initial(self):
        self.object = self.get_object()
        self.suggestions = self.object.suggestions.order_by('from_date',
                                                            'to_date').all()
        self.max_num = self.suggestions.count()
        self.initial = []
        for suggestion in self.suggestions:
            vote = suggestion.votes.filter(voter=self.request.user).exists()
            self.initial.append({
                'suggestion': suggestion.pk,
                'vote': 1 if vote else 0,
            })
        return self.initial

    def get_success_url(self):
        kwargs = {'group': self.group.slug, 'slug': self.object.slug}
        return reverse('cosinnus:event:entry-detail', kwargs=kwargs)

    def formset_valid(self, formset):
        for form in formset:
            cd = form.cleaned_data
            suggestion = int(cd.get('suggestion'))
            selection = int(cd.get('vote', 0))
            if selection:
                Vote.objects.get_or_create(suggestion_id=suggestion,
                                           voter=self.request.user)
            else:
                Vote.objects.filter(suggestion_id=suggestion,
                                    voter=self.request.user).delete()
        return super(EntryVoteView, self).formset_valid(formset)

entry_vote_view = EntryVoteView.as_view()
