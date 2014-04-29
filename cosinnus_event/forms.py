# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.widgets import HiddenInput, RadioSelect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cosinnus.forms.group import GroupKwargModelFormMixin
from cosinnus.forms.tagged import get_form
from cosinnus.forms.user import UserKwargModelFormMixin
from cosinnus.forms.widgets import DateTimeL10nPicker

from cosinnus_event.models import Event, Suggestion
from cosinnus.forms.attached_object import FormAttachable


class _EventForm(GroupKwargModelFormMixin, UserKwargModelFormMixin,
                 FormAttachable):

    class Meta:
        model = Event
        fields = ('title', 'suggestion', 'note', 'tags', 'location', 'street',
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


class SuggestionForm(forms.ModelForm):

    class Meta:
        model = Suggestion
        fields = ('from_date', 'to_date',)
        widgets = {
            'from_date': DateTimeL10nPicker(),
            'to_date': DateTimeL10nPicker(),
        }


class VoteForm(forms.Form):
    YES_NO = (
        (1, _('Yes')),
        (0, _('No')),
    )
    suggestion = forms.IntegerField(required=True, widget=HiddenInput)
    vote = forms.ChoiceField(choices=YES_NO, required=True, widget=RadioSelect)

    def get_label(self):
        pk = self.initial.get('suggestion', None)
        if pk:
            return force_text(Suggestion.objects.get(pk=pk))
        return ''
