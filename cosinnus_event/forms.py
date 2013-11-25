# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, RadioSelect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

#from cosinnus.utils.forms import (BootstrapDateTimeWidget,
#    BaseBootstrapSelectWidget, BootstrapTagWidget)

from cosinnus_event.models import Event, Suggestion


class EventForm(ModelForm):

    class Meta:
        model = Event
        fields = ('title', 'suggestion', 'note', 'tags', 'location', 'street',
                  'zipcode', 'city', 'public', 'image', 'url')
#        widgets = {
#            'suggestion': BaseBootstrapSelectWidget(
#                append=mark_safe('<i class="icon-calendar"></i>')),
#            'tags': BootstrapTagWidget(),
#        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['suggestion'].queryset = Suggestion.objects.filter(
                event=instance)
        else:
            del self.fields['suggestion']

class SuggestionForm(forms.ModelForm):

    class Meta:
        model = Suggestion
#        widgets = {
#            'from_date': BootstrapDateTimeWidget(format="%d.%m.%Y %H:%M"),
#            'to_date': BootstrapDateTimeWidget(format="%d.%m.%Y %H:%M"),
#        }


class VoteForm(forms.Form):
    YES_NO = (
        (1, _(u'Yes')),
        (0, _(u'No')),
    )
    suggestion = forms.IntegerField(required=True, widget=HiddenInput)
    vote = forms.ChoiceField(choices=YES_NO, required=True, widget=RadioSelect)

    def get_label(self):
        pk = self.initial.get('suggestion', None)
        if pk:
            return unicode(Suggestion.objects.get(pk=pk))
        return ''
