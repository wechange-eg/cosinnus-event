# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template.loader import render_to_string


class EventRenderer(object):
    """
    EventRenderer for Cosinnus attached objects
    """

    @staticmethod
    def render_attached_objects(context, events):
        template = "cosinnus_event/attached_events.html"

        context['events'] = events

        return render_to_string(template, context)
