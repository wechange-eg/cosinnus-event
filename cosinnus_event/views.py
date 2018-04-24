# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import DeleteView, UpdateView, CreateView
from django.views.generic.list import ListView
from django.utils.timezone import now
from django import forms

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
    EventNoFieldForm, CommentForm
from cosinnus_event.models import Event, Suggestion, Vote, upcoming_event_filter,\
    past_event_filter, Comment, EventAttendance
from django.shortcuts import get_object_or_404
from cosinnus.views.mixins.filters import CosinnusFilterMixin
from cosinnus_event.filters import EventFilter
from cosinnus.utils.urls import group_aware_reverse
from cosinnus.utils.permissions import check_object_read_access
from cosinnus.core.decorators.views import require_user_token_access, dispatch_group_access, get_group_for_request
from django.contrib.sites.models import get_current_site
from cosinnus.utils.functions import unique_aware_slugify
from django.views.decorators.csrf import csrf_protect
from django.http.response import HttpResponseBadRequest, JsonResponse
from annoying.functions import get_object_or_None
from cosinnus.views.mixins.reflected_objects import ReflectedObjectSelectMixin,\
    MixReflectedObjectsMixin, ReflectedObjectRedirectNoticeMixin

import logging
from django.contrib.contenttypes.models import ContentType
from cosinnus.models.tagged import BaseTaggableObjectReflection
from django.utils.encoding import force_text
from django.core.exceptions import ValidationError
logger = logging.getLogger('cosinnus')

class EventIndexView(RequireReadMixin, RedirectView):

    def get_redirect_url(self, **kwargs):
        return group_aware_reverse('cosinnus:event:list', kwargs={'group': self.group})

index_view = EventIndexView.as_view()


class EventListView(RequireReadMixin, CosinnusFilterMixin, MixReflectedObjectsMixin, FilterGroupMixin, ListView):

    model = Event
    filterset_class = EventFilter
    event_view = 'upcoming'
    show_past_events = getattr(settings, 'COSINNUS_EVENT_CALENDAR_ALSO_SHOWS_PAST_EVENTS', False)
    
    def get_queryset(self):
        """ In the calendar we only show scheduled events """
        qs = self.get_future_queryset()
        self.queryset = qs
        return qs
    
    def get_base_queryset(self):
        if hasattr(self, 'base_queryset'):
            return self.base_queryset
        self.queryset = None # reset self.queryset to get a base queryset, not an overloaded one
        self.base_queryset = super(EventListView, self).get_queryset()
        return self.base_queryset
        
    def get_future_queryset(self):
        qs = self.get_base_queryset()
        qs = qs.filter(state=Event.STATE_SCHEDULED)
        if not self.show_past_events:
            qs = upcoming_event_filter(qs)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        doodle_count = self.get_base_queryset().filter(state=Event.STATE_VOTING_OPEN).count()
        if not self.show_past_events:
            future_events_count = self.get_future_queryset().count() 
        else:
            future_events_count = upcoming_event_filter(self.get_future_queryset()).count()
        
        context.update({
            'future_events': self.get_queryset(),
            'future_events_count': future_events_count,
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
        qs = self.get_base_queryset()
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
        qs = self.get_base_queryset()
        qs = qs.filter(state=Event.STATE_VOTING_OPEN)
        self.queryset = qs
        return qs

doodle_list_view = DoodleListView.as_view()


class ArchivedDoodlesListView(EventListView):

    template_name = 'cosinnus_event/doodle_list_detailed_archived.html'
    event_view = 'archived'
    
    def get_queryset(self):
        """ In the calendar we only show scheduled events """
        qs = self.get_base_queryset()
        qs = qs.filter(state=Event.STATE_ARCHIVED_DOODLE).order_by('-created')
        self.queryset = qs
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(ArchivedDoodlesListView, self).get_context_data(**kwargs)
        context['archived_doodles'] = context.pop('future_events')
        return context
    
archived_doodles_list_view = ArchivedDoodlesListView.as_view()


class DetailedEventListView(EventListView):
    template_name = 'cosinnus_event/event_list_detailed.html'
    show_past_events = False
    
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
    success_url_list = 'cosinnus:event:list'

    @dispatch_group_access()
    def dispatch(self, request, *args, **kwargs):
        self.form_view = kwargs.get('form_view', None)
        if self.form_view != 'add':
            obj = self.get_object()
            if obj.state == Event.STATE_ARCHIVED_DOODLE and not self.form_view == 'delete':
                messages.warning(request, _('The page you requested is not available for this event at this time.'))
                return HttpResponseRedirect(obj.get_absolute_url())
            if self.form_view == 'delete':
                if obj.state == Event.STATE_VOTING_OPEN:
                    self.success_url_list = 'cosinnus:event:doodle-list'
                elif obj.state == Event.STATE_ARCHIVED_DOODLE:
                    self.success_url_list = 'cosinnus:event:doodle-list-archived'
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
        kwargs = {'group': self.group}
        # no self.object if get_queryset from add/edit view returns empty
        if hasattr(self, 'object'):
            kwargs['slug'] = self.object.slug
            urlname = 'cosinnus:event:event-detail'
        else:
            urlname = self.success_url_list
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
        
        # we need to re-convert the string-date values in our suggestion fields so our hacky form template can read them
        datefield = forms.DateTimeField()
        for inline in inlines:
            data = inline.data
            data._mutable = True
            for key, val in data.items():
                if key.startswith('suggestions-') and key.endswith('_date'):
                    try:
                        data[key] = datefield.to_python(val)
                        data[key] = datefield.to_python(val)
                    except ValidationError:
                        # cannot show errors on the suggestion fields themselves
                        if key.endswith('from_date'):
                            messages.error(self.request, _('One of the event suggestions times could not be understood!'))
        
        try:
            logger.error('Errors in doodle formsets! Errors in extra.', extra={'formset_errors': force_text(inlines[0].errors), 'form_errors': force_text(form.errors),
                    'obj_form_error': form.forms['obj'].errors, 'media_tag_form_error': form.forms['media_tag'].errors})
        except:
            logger.error('Errors in doodle formsets! Double error in inlines.', extra={'formsets': force_text(inlines), 'form_errors': force_text(form.errors),
                    'obj_form_error': form.forms['obj'].errors, 'media_tag_form_error': form.forms['media_tag'].errors})
        return ret


class DoodleFormMixin(EntryFormMixin):
    inlines = [SuggestionInlineView]
    template_name = "cosinnus_event/doodle_form.html"
    message_success = _('Unscheduled event "%(title)s" was edited successfully.')
    message_error = _('Unscheduled event "%(title)s" could not be edited.')

    def get_success_url(self):
        kwargs = {'group': self.group}
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

    def get_context_data(self, *args, **kwargs):
        context = super(DoodleEditView, self).get_context_data(*args, **kwargs)
        context.update({
            'has_active_votes': self.object.suggestions.filter(votes__isnull=False).count() > 0,
        })
        return context
    
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
        urlname = getattr(self, 'success_url_list', 'cosinnus:event:list')
        return group_aware_reverse(urlname, kwargs={'group': self.group})

entry_delete_view = EntryDeleteView.as_view()


class DoodleDeleteView(EntryFormMixin, DeleteView):
    message_success = _('Unscheduled event "%(title)s" was deleted successfully.')
    message_error = _('Unscheduled event "%(title)s" could not be deleted.')

    def get_success_url(self):
        urlname = getattr(self, 'success_url_list', 'cosinnus:event:doodle-list')
        return group_aware_reverse(urlname, kwargs={'group': self.group})

doodle_delete_view = DoodleDeleteView.as_view()



class EntryDetailView(ReflectedObjectRedirectNoticeMixin, ReflectedObjectSelectMixin, 
          RequireReadMixin, FilterGroupMixin, DetailView):

    model = Event

    def get_context_data(self, **kwargs):
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        event = context['object']
        user = self.request.user
        
        user_attendance = None if not user.is_authenticated() else get_object_or_None(EventAttendance, user=user, event=event)
        all_attendants = EventAttendance.objects.filter(event=event)
        attendants_going = all_attendants.filter(state=EventAttendance.ATTENDANCE_GOING)
        attendants_maybe = all_attendants.filter(state=EventAttendance.ATTENDANCE_MAYBE_GOING)
        attendants_not_going = all_attendants.filter(state=EventAttendance.ATTENDANCE_NOT_GOING)

        context.update({
            'user_attendance': user_attendance,
            'attendants_going': attendants_going,
            'attendants_maybe': attendants_maybe,
            'attendants_not_going': attendants_not_going,
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
    form_view = None # (set in urls.py), 'vote' or 'archived' or 'assign'
    
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.state not in (Event.STATE_VOTING_OPEN, Event.STATE_ARCHIVED_DOODLE):
            messages.warning(request, _('The page you requested is not available for this event at this time.'))
            return HttpResponseRedirect(obj.get_absolute_url())
        return super(DoodleVoteView, self).get(request, *args, **kwargs)
    
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
        kwargs = {'group': self.group, 'slug': self.object.slug}
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

"""
class ArchivedDoodleView(DoodleVoteView):

    template_name = 'cosinnus_event/doodle_vote.html'
    form_view = None # (set in urls.py), 'vote' or 'archived' or 'assign'

archived_doodle_view = ArchivedDoodleView.as_view()
"""

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
        old_doodle_pk = event.pk
        
        # give this a new temporary slug so the original one is free again
        event.slug += '-archive'
        unique_aware_slugify(event, 'title', 'slug', group=self.group, force_redo=True)
        event.created = now()
        event.save(update_fields=['slug', 'created'])
        
        # 'clone' media_tag
        new_media_tag = event.media_tag
        new_media_tag.pk = None 
        new_media_tag.save()
        
        event.pk = None # set pk to None to have this become a new event
        event.slug = None # set slug to None so we can re-unique slugify 
        event.media_tag = new_media_tag
        event.from_date = suggestion.from_date
        event.to_date = suggestion.to_date
        event.state = Event.STATE_SCHEDULED
        event.save(created_from_doodle=True)
        
        # re-retrieve old doodle, set it to archived 
        doodle = self.model.objects.get(pk=old_doodle_pk)
        doodle.state = Event.STATE_ARCHIVED_DOODLE
        doodle.save(update_fields=['state'])
        
        # link old doodle to new event. can't do this until now because we wouldn't have had the old pointer correctly
        event.original_doodle = doodle
        event.save(update_fields=['original_doodle'])
        
        messages.success(request, _('The event was created successfully at the specified date.'))
        return HttpResponseRedirect(self.object.get_absolute_url())
    
doodle_complete_view = DoodleCompleteView.as_view()


class EventFeed(ICalFeed):
    """
    A simple event calender feed. Uses a permanent user token for authentication
    (the token is only used for views displaying the user's event-feeds).
    """
    PROTO_PRODUCT_ID = '-//%s//Event//Feed'
    
    product_id = None
    timezone = 'UTC'
    title = _('Events')
    description = _('Upcoming events in')
    
    @require_user_token_access(settings.COSINNUS_EVENT_TOKEN_EVENT_FEED)
    def __call__(self, request, *args, **kwargs):
        site = get_current_site(request)
        
        self.title = '%s - %s' %  (self.group.name, self.title)
        self.description = '%s %s' % (self.description, self.group.name)
        if not self.product_id:
            self.product_id = EventFeed.PROTO_PRODUCT_ID % site.domain
        
        return super(EventFeed, self).__call__(request, *args, **kwargs)
    
    def get_feed(self, obj, request):
        self.request = request
        return super(EventFeed, self).get_feed(obj, request)
    
    def items(self, request):
        qs = Event.get_current(self.group, self.user)
        qs = qs.filter(state=Event.STATE_SCHEDULED, from_date__isnull=False, to_date__isnull=False).order_by('-from_date')
        return qs
    
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        description = item.note
        # add website URL to description if set on event
        if item.url:
            description = description + '\n\n' + item.url if description else item.url 
        return description

    def item_start_datetime(self, item):
        # we're returning a DateTime here. if we wanted to mark a full-day event, we would return a Date
        return item.from_date
    
    def item_end_datetime(self, item):
        # we're returning a DateTime here. if we wanted to mark a full-day event, we would return a Date
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



class CommentCreateView(RequireWriteMixin, FilterGroupMixin, CreateView):

    form_class = CommentForm
    group_field = 'event__group'
    model = Comment
    template_name = 'cosinnus_event/event_detail.html'
    
    message_success = _('Your comment was added successfully.')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.event = self.event
        messages.success(self.request, self.message_success)
        return super(CommentCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CommentCreateView, self).get_context_data(**kwargs)
        # always overwrite object here, because we actually display the event as object, 
        # and not the comment in whose view we are in when form_invalid comes back
        context.update({
            'event': self.event,
            'object': self.event, 
        })
        return context

    def get(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, group=self.group, slug=self.kwargs.get('event_slug'))
        return super(CommentCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, group=self.group, slug=self.kwargs.get('event_slug'))
        self.referer = request.META.get('HTTP_REFERER', self.event.group.get_absolute_url())
        return super(CommentCreateView, self).post(request, *args, **kwargs)
    
    def get_success_url(self):
        # self.referer is set in post() method
        return self.referer

comment_create = CommentCreateView.as_view()


class CommentDeleteView(RequireWriteMixin, FilterGroupMixin, DeleteView):

    group_field = 'event__group'
    model = Comment
    template_name_suffix = '_delete'
    
    message_success = _('Your comment was deleted successfully.')
    
    def get_context_data(self, **kwargs):
        context = super(CommentDeleteView, self).get_context_data(**kwargs)
        context.update({'event': self.object.event})
        return context
    
    def post(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        self.referer = request.META.get('HTTP_REFERER', self.comment.event.group.get_absolute_url())
        return super(CommentDeleteView, self).post(request, *args, **kwargs)

    def get_success_url(self):
        # self.referer is set in post() method
        messages.success(self.request, self.message_success)
        return self.referer

comment_delete = CommentDeleteView.as_view()


class CommentDetailView(SingleObjectMixin, RedirectView):

    model = Comment

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return HttpResponseRedirect(obj.get_absolute_url())

comment_detail = CommentDetailView.as_view()


class CommentUpdateView(RequireWriteMixin, FilterGroupMixin, UpdateView):

    form_class = CommentForm
    group_field = 'event__group'
    model = Comment
    template_name_suffix = '_update'

    def get_context_data(self, **kwargs):
        context = super(CommentUpdateView, self).get_context_data(**kwargs)
        context.update({'event': self.object.event})
        return context
    
    def post(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        self.referer = request.META.get('HTTP_REFERER', self.comment.event.group.get_absolute_url())
        return super(CommentUpdateView, self).post(request, *args, **kwargs)

    def get_success_url(self):
        # self.referer is set in post() method
        return self.referer

comment_update = CommentUpdateView.as_view()


@csrf_protect
def assign_attendance_view(request, group, slug):
    """ Assign attendance for an event. 
        POST param: ``target_state``: Numerical for EventAttendance::ATTENDANCE_STATES.
            Pass '-1' to remove the attending object, i.e. the 'no choice selected' state.  """
    
    if not request.is_ajax():
        return HttpResponseBadRequest("This can only be called via Ajax.")
    user = request.user
    if not user.is_authenticated():
        return HttpResponseBadRequest("This can only be called for logged in users.")
    
    target_state = request.POST.get('target_state', None)
    try:
        target_state = int(target_state)
    except:
        pass
    if target_state != -1 and target_state not in dict(EventAttendance.ATTENDANCE_STATES).keys():
        target_state = None
    
    if target_state is None:
        return HttpResponseBadRequest("Missing or malformed POST parameter: 'target_state'")
    
    group = get_group_for_request(group, request)
    if not group:
        logger.error('No group found when trying to assign attendance to an event!', extra={'group_slug': group, 
            'request': request, 'path': request.path})
        return JsonResponse({'error': 'groupnotfound'})
    
    event = get_object_or_None(Event, slug=slug, group=group)
    if not event:
        logger.error('No event found when trying to assign attendance to an event!', extra={'event_slug': slug, 
            'request': request, 'path': request.path})
        return JsonResponse({'error': 'eventnotfound'})
    
    event = get_object_or_None(Event, slug=slug, group=group)
    if not event.state == Event.STATE_SCHEDULED:
        return JsonResponse({'error': 'eventnotactive'})
    
    if not check_object_read_access(event, user):
        logger.warn('Permission error while assigning attendance for an event!', 
             extra={'user': user, 'request': request, 'path': request.path, 'group_slug': group, 'event_slug': slug})
        return JsonResponse({'error': 'denied'})
    
    result_state = None
    try:
        attendance = get_object_or_None(EventAttendance, event=event, user=user)
        if (attendance is None and target_state == -1) or (attendance is not None and target_state == attendance.state):
            # no action required
            result_state = target_state
        elif attendance is not None and target_state == -1:
            attendance.delete()
            result_state = -1
        elif attendance is not None:
            attendance.state = target_state
            attendance.save(update_fields=['state', 'date'])
            result_state = attendance.state
        else:
            attendance = EventAttendance.objects.create(event=event, user=user, state=target_state)
            result_state = attendance.state
            
    except Exception, e:
        logger.error('Exception while assigning attendance for an event!', 
             extra={'user': user, 'request': request, 'path': request.path, 'group_slug': group, 'event_slug': slug, 'exception': str(e)})
    
    if result_state is not None:
        return JsonResponse({'status': 'ok', 'result_state': result_state})
    
    return JsonResponse({'error': 'statecouldnotbechanged', 'result_state': -1 if attendance is None else attendance.state})
