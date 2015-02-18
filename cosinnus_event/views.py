# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic.list import ListView
from django.utils.timezone import now

from extra_views import (CreateWithInlinesView, FormSetView, InlineFormSet,
    UpdateWithInlinesView)

from django_ical.views import ICalFeed

from cosinnus.views.export import CSVExportView
from cosinnus.views.mixins.group import (RequireReadMixin, RequireWriteMixin,
    GroupFormKwargsMixin, FilterGroupMixin)
from cosinnus.views.mixins.user import UserFormKwargsMixin

from cosinnus.views.attached_object import AttachableViewMixin

from cosinnus_event.conf import settings
from cosinnus_event.forms import EventForm, SuggestionForm, VoteForm,\
    EventNoFieldForm
from cosinnus_event.models import Event, Suggestion, Vote, upcoming_event_filter,\
    past_event_filter
from django.shortcuts import get_object_or_404
from cosinnus.views.mixins.filters import CosinnusFilterMixin
from cosinnus_event.filters import EventFilter
from cosinnus.utils.urls import group_aware_reverse
from cosinnus.utils.permissions import filter_tagged_object_queryset_for_user
from cosinnus.core.decorators.views import require_read_access,\
    require_user_token_access
from django.contrib.sites.models import Site, get_current_site


class EventIndexView(RequireReadMixin, RedirectView):

    def get_redirect_url(self, **kwargs):
        return group_aware_reverse('cosinnus:event:list', kwargs={'group': self.group.slug})

index_view = EventIndexView.as_view()


class EventListView(RequireReadMixin, FilterGroupMixin, CosinnusFilterMixin, ListView):

    model = Event
    filterset_class = EventFilter
    event_view = 'upcoming'
    
    def get_queryset(self):
        """ In the calendar we only show scheduled events """
        qs = super(EventListView, self).get_queryset()
        qs = qs.filter(state=Event.STATE_SCHEDULED)
        qs = upcoming_event_filter(qs)
        self.queryset = qs
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        doodle_count = super(EventListView, self).get_queryset().filter(state=Event.STATE_VOTING_OPEN).count()

        context.update({
            'future_events': self.queryset,
            'doodle_count': doodle_count,
            'event_view': self.event_view,
        })
        return context

list_view = EventListView.as_view()


class PastEventListView(EventListView):

    template_name = 'cosinnus_event/event_list_detailed_past.html'
    event_view = 'past'
    
    def get_queryset(self):
        """ In the calendar we only show scheduled events """
        qs = super(EventListView, self).get_queryset()
        qs = qs.filter(state=Event.STATE_SCHEDULED)
        qs = past_event_filter(qs).reverse()
        self.queryset = qs
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(PastEventListView, self).get_context_data(**kwargs)
        context['past_events'] = context.pop('future_events')
        return context
    
past_events_list_view = PastEventListView.as_view()


class DoodleListView(EventListView):
    template_name = 'cosinnus_event/doodle_list.html'

    def get_queryset(self):
        """In the doodle list we only show events with open votings"""
        qs = super(EventListView, self).get_queryset() # not this views, but event views parent!!!
        qs = qs.filter(state=Event.STATE_VOTING_OPEN)
        return qs

doodle_list_view = DoodleListView.as_view()


class DetailedEventListView(EventListView):
    template_name = 'cosinnus_event/event_list_detailed.html'
    
detailed_list_view = DetailedEventListView.as_view()

class SuggestionInlineView(InlineFormSet):
    extra = 1
    form_class = SuggestionForm
    model = Suggestion


class EntryFormMixin(RequireWriteMixin, FilterGroupMixin, GroupFormKwargsMixin,
                     UserFormKwargsMixin):
    form_class = EventForm
    model = Event
    message_success = _('Event "%(title)s" was edited successfully.')
    message_error = _('Event "%(title)s" could not be edited.')

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
            urlname = 'cosinnus:event:event-detail'
        else:
            urlname = 'cosinnus:event:list'
        return group_aware_reverse(urlname, kwargs=kwargs)

    def forms_valid(self, form, inlines):
        ret = super(EntryFormMixin, self).forms_valid(form, inlines)
        messages.success(self.request,
            self.message_success % {'title': self.object.title})
        return ret

    def forms_invalid(self, form, inlines):
        ret = super(EntryFormMixin, self).forms_invalid(form, inlines)
        if self.object:
            messages.error(self.request,
                self.message_error % {'title': self.object.title})
        return ret


class DoodleFormMixin(EntryFormMixin):
    inlines = [SuggestionInlineView]
    template_name = "cosinnus_event/doodle_form.html"
    message_success = _('Unscheduled event "%(title)s" was edited successfully.')
    message_error = _('Unscheduled event "%(title)s" could not be edited.')

    def get_success_url(self):
        kwargs = {'group': self.group.slug}
        # no self.object if get_queryset from add/edit view returns empty
        if hasattr(self, 'object'):
            kwargs['slug'] = self.object.slug
            urlname = 'cosinnus:event:doodle-vote'
        else:
            urlname = 'cosinnus:event:doodle-list'
        return group_aware_reverse(urlname, kwargs=kwargs)



class EntryAddView(EntryFormMixin, AttachableViewMixin, CreateWithInlinesView):
    message_success = _('Event "%(title)s" was added successfully.')
    message_error = _('Event "%(title)s" could not be added.')
    
    def forms_valid(self, form, inlines):
        form.instance.creator = self.request.user
        
        # events are created as scheduled.
        # doodle events would be created as STATE_VOTING_OPEN.
        form.instance.state = Event.STATE_SCHEDULED
        return super(EntryAddView, self).forms_valid(form, inlines)
    
entry_add_view = EntryAddView.as_view()


class DoodleAddView(DoodleFormMixin, AttachableViewMixin, CreateWithInlinesView):
    message_success = _('Unscheduled event "%(title)s" was added successfully.')
    message_error = _('Unscheduled event "%(title)s" could not be added.')

    def forms_valid(self, form, inlines):
        form.instance.creator = self.request.user
        form.instance.state = Event.STATE_VOTING_OPEN  # be explicit

        ret = super(DoodleAddView, self).forms_valid(form, inlines)

        # Check for non or a single suggestion and set it and inform the user
        num_suggs = self.object.suggestions.count()
        if num_suggs == 0:
            messages.info(self.request,
                _('You should define at least one date suggestion.'))
        return ret

doodle_add_view = DoodleAddView.as_view()


class EntryEditView(EntryFormMixin, AttachableViewMixin, UpdateWithInlinesView):
    pass

entry_edit_view = EntryEditView.as_view()


class DoodleEditView(DoodleFormMixin, AttachableViewMixin, UpdateWithInlinesView):

    #def forms_invalid(self, form, inlines):
    #    import ipdb; ipdb.set_trace()

    def forms_valid(self, form, inlines):
        # Save the suggestions first so we can directly
        # access the amount of suggestions afterwards
        for formset in inlines:
            formset.save()

        suggestion = form.cleaned_data.get('suggestion')
        if not suggestion:
            num_suggs = form.instance.suggestions.count()
            if num_suggs == 0:
                suggestion = None
                messages.info(self.request,
                    _('You should define at least one date suggestion.'))
        # update_fields=None leads to saving the complete model, we
        # don't need to call obj.self here
        # INFO: set_suggestion saves the instance
        form.instance.set_suggestion(suggestion, update_fields=None)

        return super(DoodleEditView, self).forms_valid(form, inlines)

doodle_edit_view = DoodleEditView.as_view()



class EntryDeleteView(EntryFormMixin, DeleteView):
    message_success = _('Event "%(title)s" was deleted successfully.')
    message_error = _('Event "%(title)s" could not be deleted.')

    def get_success_url(self):
        return group_aware_reverse('cosinnus:event:list', kwargs={'group': self.group.slug})

entry_delete_view = EntryDeleteView.as_view()


class DoodleDeleteView(EntryFormMixin, DeleteView):
    message_success = _('Unscheduled event "%(title)s" was deleted successfully.')
    message_error = _('Unscheduled event "%(title)s" could not be deleted.')

    def get_success_url(self):
        return group_aware_reverse('cosinnus:event:doodle-list', kwargs={'group': self.group.slug})

doodle_delete_view = DoodleDeleteView.as_view()



class EntryDetailView(RequireReadMixin, FilterGroupMixin, DetailView):

    model = Event

    def get_context_data(self, **kwargs):
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        height = getattr(settings, 'GEOPOSITION_MAP_WIDGET_HEIGHT', 200)
        context.update({
            'map_widget_height': height,
        })
        return context

entry_detail_view = EntryDetailView.as_view()


class DoodleVoteView(RequireReadMixin, FilterGroupMixin, SingleObjectMixin,
        FormSetView):

    message_success = _('Your votes were saved successfully.')
    message_error = _('Your votes could not be saved.')

    extra = 0
    form_class = VoteForm
    model = Event
    template_name = 'cosinnus_event/doodle_vote.html'
    
    def post(self, request, *args, **kwargs):
        if self.get_object().state != Event.STATE_VOTING_OPEN:
            messages.error(request, _('This is event is already scheduled. You cannot vote for it any more.'))
            return HttpResponseRedirect(request.path)
        return super(DoodleVoteView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DoodleVoteView, self).get_context_data(**kwargs)
        
        # we group formsets, votes and suggestions by days (as in a day there might be more than one suggestion)
        # the absolute order inside the two lists when traversing the suggestions (iterated over days), 
        # is guaranteed to be sorted by date and time ascending, as is the user-grouped list of votes
        formset_forms_grouped = []
        vote_counts_grouped = []
        suggestions_list_grouped = []
        votes_user_grouped = defaultdict(list) # these are grouped by user, and sorted by suggestion, not day!
        for day, suggestions in sorted(self.suggestions_grouped.items(), key=lambda item: item[1][0].from_date):
            formset_forms_grouped_l = []
            vote_counts_grouped_l = []
            suggestions_list_grouped_l = []
            
            for suggestion in suggestions:
                suggestions_list_grouped_l.append(suggestion)
                # group the vote formsets in the same order we grouped the suggestions
                for form in context['formset'].forms:
                    if suggestion.pk == form.initial.get('suggestion', -1):
                        formset_forms_grouped_l.append(form)
                # create a grouped total count for all the votes
                # use sorted_votes here, it's cached
                # format: [no_votes, maybe_votes, yes_notes, is_most_overall_votes]
                counts = [0, 0, 0, False]
                for vote in suggestion.sorted_votes:
                    counts[vote.choice] += 1
                    votes_user_grouped[vote.voter.username].append(vote)
                vote_counts_grouped_l.append(counts)
            
            formset_forms_grouped.append(formset_forms_grouped_l)
            vote_counts_grouped.append(vote_counts_grouped_l)
            suggestions_list_grouped.append(suggestions_list_grouped_l)
        
        # determine and set the winning vote count of suggestions (if there are votes)
        try:
            max_vote_count = max([max([vote[2] for vote in votes]) for votes in vote_counts_grouped])
            for votes in vote_counts_grouped:
                for vote in votes:
                    if vote[2] == max_vote_count:
                        vote[3] = True
        except ValueError:
            pass
        
        context.update({
            'object': self.object,
            'suggestions': self.suggestions,
            'suggestions_grouped': suggestions_list_grouped,
            'formset_forms_grouped': formset_forms_grouped,
            'vote_counts_grouped': vote_counts_grouped,
            'votes_user_grouped': dict(votes_user_grouped),
        })
        return context

    def get_initial(self):
        self.object = self.get_object()
        self.suggestions = self.object.suggestions.order_by('from_date',
                                                            'to_date').all()
        
        self.suggestions_grouped = defaultdict(list)
        for suggestion in self.suggestions:
            self.suggestions_grouped[suggestion.from_date.date().isoformat()].append(suggestion)
                                                                    
        self.max_num = self.suggestions.count()
        self.initial = []
        for suggestion in self.suggestions:
            vote = None
            if self.request.user.is_authenticated():
                try:
                    vote = suggestion.votes.filter(voter=self.request.user).get()
                except Vote.DoesNotExist:
                    pass
            self.initial.append({
                'suggestion': suggestion.pk,
                'choice': vote.choice if vote else Vote.VOTE_NO,
            })
        return self.initial

    def get_success_url(self):
        kwargs = {'group': self.group.slug, 'slug': self.object.slug}
        return group_aware_reverse('cosinnus:event:doodle-vote', kwargs=kwargs)

    def formset_valid(self, formset):
        for form in formset:
            cd = form.cleaned_data
            suggestion = int(cd.get('suggestion'))
            choice = int(cd.get('choice', 0))
            if suggestion:
                vote, _created = Vote.objects.get_or_create(suggestion_id=suggestion,
                                           voter=self.request.user)
                vote.choice = choice
                vote.save()
        
        ret = super(DoodleVoteView, self).formset_valid(formset)
        messages.success(self.request, self.message_success )
        return ret
    
    def formset_invalid(self, formset):
        ret = super(DoodleVoteView, self).formset_invalid(formset)
        if self.object:
            messages.error(self.request, self.message_error)
        return ret


doodle_vote_view = DoodleVoteView.as_view()


class DoodleCompleteView(RequireWriteMixin, FilterGroupMixin, UpdateView):
    """ Completes a doodle event for a selected suggestion, setting the event to Scheduled. """
    form_class = EventNoFieldForm
    form_view = 'assign'
    model = Event
    
    def get_object(self, queryset=None):
        obj = super(DoodleCompleteView, self).get_object(queryset)
        return obj
    
    def get(self, request, *args, **kwargs):
        # we don't accept GETs on this, just POSTs
        messages.error(request, _('The complete request can only be sent via POST!'))
        return HttpResponseRedirect(self.get_object().get_absolute_url())
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        event = self.object
        
        if self.object.state != Event.STATE_VOTING_OPEN:
            messages.error(request, _('This is event is already scheduled. You cannot vote for it any more.'))
            return HttpResponseRedirect(self.object.get_absolute_url())
        if 'suggestion_id' not in kwargs:
            messages.error(request, _('Event cannot be completed: No date was supplied.'))
            return HttpResponseRedirect(self.object.get_absolute_url())
        
        suggestion = get_object_or_404(Suggestion, pk=kwargs.get('suggestion_id'))
        
        event.from_date = suggestion.from_date
        event.to_date = suggestion.to_date
        event.state = Event.STATE_SCHEDULED
        event.save()
        
        messages.success(request, _('The event was created successfully at the specified date.'))
        return HttpResponseRedirect(self.object.get_absolute_url())
    
doodle_complete_view = DoodleCompleteView.as_view()


class EventFeed(ICalFeed):
    """
    A simple event calender feed. Uses a permanent user token for authentication
    (the token is only used for views displaying the user's event-feeds).
    """
    product_id = '-//%s//Event//Feed'
    timezone = 'UTC'
    title = _('Events')
    description = _('Upcoming events in')
    
    @require_user_token_access(settings.COSINNUS_EVENT_TOKEN_EVENT_FEED)
    def __call__(self, request, *args, **kwargs):
        site = get_current_site(request)
        
        self.title = '%s - %s' %  (self.group.name, self.title)
        self.description = '%s %s' % (self.description, self.group.name)
        self.product_id = self.product_id % site.domain
        
        return super(EventFeed, self).__call__(request, *args, **kwargs)
    
    def get_feed(self, obj, request):
        self.request = request
        return super(EventFeed, self).get_feed(obj, request)
    
    def items(self, request):
        qs = Event.get_current(self.group, self.user)
        qs.filter(state=Event.STATE_SCHEDULED).order_by('-from_date')
        return qs
    
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.note

    def item_start_datetime(self, item):
        return item.from_date
    
    def item_end_datetime(self, item):
        return item.to_date
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_geolocation(self, item):
        mt = item.media_tag
        if mt and mt.location_lat and mt.location_lon:
            return (mt.location_lat, mt.location_lon)
        return None
    

event_ical_feed = EventFeed()


class EventExportView(CSVExportView):
    fields = [
        'from_date',
        'to_date',
        'creator',
        'state',
        'note',
        'location',
        'street',
        'zipcode',
        'city',
        'public',
        'image',
        'url',
    ]
    model = Event
    file_prefix = 'cosinnus_event'

export_view = EventExportView.as_view()
