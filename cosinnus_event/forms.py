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

from cosinnus_event.models import Event, Suggestion, Vote, Comment
from cosinnus.forms.attached_object import FormAttachableMixin


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

