# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

from cosinnus.models import CosinnusGroup
from cosinnus_event.forms import EventForm
from cosinnus_event.models import Event, Suggestion


class EventFormTest(TestCase):

    def setUp(self):
        super(EventFormTest, self).setUp()
        self.group = CosinnusGroup.objects.create(name='testgroup')
        self.credential = 'admin'
        self.admin = User.objects.create_superuser(
            username=self.credential, email=None, password=self.credential)
        self.event = Event.objects.create(group=self.group,
            created_by=self.admin, public=True, title='testevent')

    def test_has_suggestion(self):
        """
        Should have suggestion field in form if instance given
        """
        form = EventForm(instance=self.event)
        Suggestion.objects.create(
            event=self.event, from_date=now(), to_date=now())
        self.assertIn('suggestion', form.fields)
        num_suggestion = len(form.fields['suggestion'].queryset)
        self.assertEqual(num_suggestion, 1)

    def test_has_no_suggestion(self):
        """
        Should have no suggestion field in form if no instance given
        """
        form = EventForm()
        self.assertNotIn('suggestion', form.fields)
