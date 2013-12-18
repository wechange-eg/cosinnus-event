# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from cosinnus.models import CosinnusGroup
from cosinnus_event.models import Event


class EventManagerTest(TestCase):

    def setUp(self):
        super(EventManagerTest, self).setUp()
        self.group = CosinnusGroup.objects.create(name='testgroup')
        self.admin = User.objects.create_superuser(
            username='admin', email=None, password=None)
        self.event = Event.objects.create(group=self.group,
            created_by=self.admin, public=True, state=Event.STATE_SCHEDULED,
            title='testevent')

    def test_tags(self):
        """
        Should have tags
        """
        tags = ['foo', 'bar']
        for tag in tags:
            self.event.tags.add(tag)
        self.assertEqual(Event.objects.tags(), tags)

    def test_public(self):
        """
        Should have public event if event public
        """
        self.event.public = True
        self.event.save()
        self.assertEqual(self.event, Event.objects.public()[0])

    def test_public_non_public_event(self):
        """
        Should have no public event if event not public
        """
        self.event.public = False
        self.event.save()
        self.assertListEqual([], list(Event.objects.public()))

    def test_public_canceled_event(self):
        """
        Should have no public event if event canceled
        """
        self.event.state = Event.STATE_CANCELED
        self.event.public = True
        self.event.save()
        self.assertListEqual([], list(Event.objects.public()))
