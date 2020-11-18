# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from builtins import object
from django import forms
from django.forms.widgets import HiddenInput, RadioSelect,\
    SplitHiddenDateTimeWidget
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cosinnus.forms.group import GroupKwargModelFormMixin
from cosinnus.forms.tagged import get_form, BaseTaggableObjectForm
from cosinnus.forms.user import UserKwargModelFormMixin
from cosinnus.forms.widgets import SplitHiddenDateWidget

from cosinnus_event.models import Event, Suggestion, Vote, Comment,\
    ConferenceEvent
from cosinnus.forms.attached_object import FormAttachableMixin
from cosinnus.utils.user import get_user_select2_pills
from cosinnus.fields import UserSelect2MultipleChoiceField
from django.urls.base import reverse
from django.core.validators import MaxValueValidator, MinValueValidator


class _EventForm(GroupKwargModelFormMixin, UserKwargModelFormMixin,
                 FormAttachableMixin, BaseTaggableObjectForm):
    
    url = forms.URLField(widget=forms.TextInput, required=False)
    
    from_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='00:00'))
    to_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='23:59'))

    class Meta(object):
        model = Event
        fields = ('title', 'suggestion', 'from_date', 'to_date', 'note', 'street',
                  'zipcode', 'city', 'public', 'image', 'url')
    
    def __init__(self, *args, **kwargs):
        super(_EventForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['suggestion'].queryset = Suggestion.objects.filter(
                event=instance)
        else:
            del self.fields['suggestion']


EventForm = get_form(_EventForm)


class _DoodleForm(_EventForm):
    
    from_date = forms.SplitDateTimeField(required=False)
    to_date = forms.SplitDateTimeField(required=False)

DoodleForm = get_form(_DoodleForm)


class SuggestionForm(forms.ModelForm):

    class Meta(object):
        model = Suggestion
        fields = ('from_date', 'to_date',)
    
    from_date = forms.SplitDateTimeField(required=False, widget=SplitHiddenDateWidget(default_time='00:00'))
    to_date = forms.SplitDateTimeField(required=False, widget=SplitHiddenDateWidget(default_time='00:00'))


class VoteForm(forms.Form):
    suggestion = forms.IntegerField(required=True, widget=HiddenInput)
    choice = forms.ChoiceField(choices=Vote.VOTE_CHOICES, required=True)

    def get_label(self):
        pk = self.initial.get('suggestion', None)
        if pk:
            return force_text(Suggestion.objects.get(pk=pk))
        return ''
    
    
class EventNoFieldForm(forms.ModelForm):

    class Meta(object):
        model = Event
        fields = ()
        
        
class CommentForm(forms.ModelForm):

    class Meta(object):
        model = Comment
        fields = ('text',)


class _ConferenceEventBaseForm(_EventForm):
    
    url = None
    from_date = None
    to_date = None
    
    def __init__(self, *args, **kwargs):
        
        # note: super(_EventForm), not _ConferenceEventBaseForm
        super(_EventForm, self).__init__(*args, **kwargs)
        
        # init select2 presenters field
        if 'presenters' in self.fields:
            data_url = reverse('cosinnus:select2:all-members')
            self.fields['presenters'] = UserSelect2MultipleChoiceField(label=_("Presenters"), help_text='', required=False, data_url=data_url)
          
            if self.instance.pk:
                # choices and initial must be set so pre-existing form fields can be prepopulated
                preresults = get_user_select2_pills(self.instance.presenters.all(), text_only=True)
                self.fields['presenters'].choices = preresults
                self.fields['presenters'].initial = [key for key,__ in preresults]
                self.initial['presenters'] = self.fields['presenters'].initial
        
        # limit the max participants field to those set in the room 
        # Disabled until we can figure out how to keep the kwargs getting passed to the MultiModelForm first
        #self.room = kwargs.pop('room')
        #if 'max_participants' in self.fields:
        #    self.fields['max_participants'].validators = [MinValueValidator(2), MaxValueValidator(self.room.max_coffeetable_participants)]
    
    def after_save(self, obj):
        # again sync the bbb members so m2m changes are taken into account properly
        obj.sync_bbb_members()
    

class _ConferenceEventCoffeeTableForm(_ConferenceEventBaseForm):
    
    class Meta(object):
        model = ConferenceEvent
        fields = ('title', 'note', 'image', 'max_participants', 'presentation_file')

ConferenceEventCoffeeTableForm = get_form(_ConferenceEventCoffeeTableForm)


class _ConferenceEventWorkshopForm(_ConferenceEventBaseForm):
    
    from_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='00:00'))
    to_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='23:59'))
    
    class Meta(object):
        model = ConferenceEvent
        fields = ('title', 'is_break', 'note', 'from_date', 'to_date', 'presenters', 'presentation_file')

ConferenceEventWorkshopForm = get_form(_ConferenceEventWorkshopForm)


class _ConferenceEventDiscussionForm(_ConferenceEventWorkshopForm):
    pass

ConferenceEventDiscussionForm = get_form(_ConferenceEventDiscussionForm)


class _ConferenceEventStageForm(_ConferenceEventBaseForm):
    
    url = forms.URLField(widget=forms.TextInput, required=False)
    
    from_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='00:00'))
    to_date = forms.SplitDateTimeField(widget=SplitHiddenDateWidget(default_time='23:59'))
    
    class Meta(object):
        model = ConferenceEvent
        fields = ('title', 'is_break', 'note', 'from_date', 'to_date', 'presenters', 'url', 'raw_html')

ConferenceEventStageForm = get_form(_ConferenceEventStageForm)


class _ConferenceEventLobbyForm(_ConferenceEventStageForm):
    pass

ConferenceEventLobbyForm = get_form(_ConferenceEventLobbyForm)

