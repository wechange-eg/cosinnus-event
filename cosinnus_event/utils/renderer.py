# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cosinnus.utils.renderer import BaseRenderer


class EventRenderer(BaseRenderer):
    """
    EventRenderer for Cosinnus attached objects
    """
    template = 'cosinnus_event/attached_events.html'

    @classmethod
    def render(cls, context, myobjs):
        return super(EventRenderer, cls).render(context, events=myobjs)
