# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def register():
    # Import here to prevent import side effects
    from django.utils.translation import ugettext_lazy as _
    from django.utils.translation import pgettext_lazy

    from cosinnus.core.registries import (app_registry,
        attached_object_registry, url_registry, widget_registry)

    app_registry.register('cosinnus_event', 'event', _('Events'), deactivatable=True)
    attached_object_registry.register('cosinnus_event.Event',
                             'cosinnus_event.utils.renderer.EventRenderer')
    url_registry.register_urlconf('cosinnus_event', 'cosinnus_event.urls')
    widget_registry.register('event', 'cosinnus_event.dashboard.UpcomingEvents')
    
    # makemessages replacement protection
    name = pgettext_lazy("the_app", "event")
