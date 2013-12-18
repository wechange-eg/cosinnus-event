# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

from cosinnus.models import CosinnusGroup
from cosinnus_event.models import Event, Suggestion, localize


class EventTest(TestCase):

    def setUp(self):
        super(EventTest, self).setUp()
        self.group = CosinnusGroup.objects.create(name='testgroup')
        self.admin = User.objects.create_superuser(
            username='admin', email=None, password=None)
        dt = now()
        self.event = Event.objects.create(
            group=self.group,
            created_by=self.admin,
            public=True,
            title='testevent',
            from_date=dt,
            to_date=dt,
            state=Event.STATE_SCHEDULED)

    def test_string_repr_scheduled_single_day(self):
        """
        Should have certain string representation if single day event
        """
        expected = '%(event)s (%(date)s - %(end)s)' % {
            'event': self.event.title,
            'date': localize(self.event.from_date, 'd. F Y h:i'),
            'end': localize(self.event.to_date, 'h:i'),
        }
        self.assertEqual(expected, str(self.event))

    def test_string_repr_scheduled_multi_day(self):
        """
        Should have certain string representation if multi day event
        """
        self.event.to_date += timedelta(days=1)
        self.event.save()
        expected = '%(event)s (%(from)s - %(to)s)' % {
            'event': self.event.title,
            'from': localize(self.event.from_date, 'd. F Y h:i'),
            'to': localize(self.event.to_date, 'd. F Y h:i'),
        }
        self.assertEqual(expected, str(self.event))

    def test_string_repr_pending(self):
        """
        Should have certain string representation if pending event
        """
        self.event.state = Event.STATE_VOTING_OPEN
        self.event.save()
        expected = '%(event)s (pending)' % {'event': self.event.title}
        self.assertEqual(expected, str(self.event))

    def test_set_suggestion_none(self):
        """
        Should not set suggestion if none is given to event
        """
        self.event.set_suggestion(sugg=None)
        self.assertEqual(self.event.suggestion, None)

    def test_set_suggestion(self):
        """
        Should set suggestion for an event
        """
        suggestion = Suggestion.objects.create(
            event=self.event, from_date=now(), to_date=now())
        self.event.set_suggestion(sugg=suggestion)
        self.assertEqual(self.event.suggestion, suggestion)

    def test_set_suggestion_other_event(self):
        """
        Should not set suggestion for another event
        """
        event = Event.objects.create(
            group=self.group,
            created_by=self.admin,
            public=True,
            title='testevent')
        suggestion = Suggestion.objects.create(
            event=event, from_date=now(), to_date=now())
        self.event.set_suggestion(sugg=suggestion)
        self.assertEqual(self.event.suggestion, None)

    def test_single_day_same_day(self):
        """
        Should be single day event if from and to date are on the same day
        """
        self.event.from_date = self.event.to_date
        self.event.save()
        self.assertTrue(self.event.single_day)

    def test_single_day_different_day(self):
        """
        Should not be single day event if from and to date are on different days
        """
        self.event.from_date = now()
        self.event.to_date = self.event.from_date + timedelta(days=1)
        self.event.save()
        self.assertFalse(self.event.single_day)

    def test_period_same_day(self):
        """
        Should be from date on same day for period
        """
        self.event.from_date = self.event.to_date
        self.event.save()
        expected = localize(self.event.from_date, 'd.m.Y')
        self.assertEqual(expected, self.event.get_period())

    def test_period_other_day(self):
        """
        Should be certain string on different days for period
        """
        self.event.from_date = now()
        self.event.to_date = self.event.from_date + timedelta(days=1)
        self.event.save()
        expected = '%s - %s' % (localize(self.event.from_date, "d.m."),
            localize(self.event.to_date, "d.m.Y"))
        self.assertEqual(expected, self.event.get_period())
