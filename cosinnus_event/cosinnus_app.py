# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def register():
    # Import here to prevent import side effects
    from django.utils.translation import ugettext_lazy as _

    from cosinnus.core.registries import (app_registry,
        attached_object_registry, url_registry)

    from cosinnus_event.urls import (cosinnus_group_patterns,
        cosinnus_root_patterns)

    app_registry.register('cosinnus_event', 'event', _('Events'))
    attached_object_registry.register('cosinnus_event.Event',
                             'cosinnus_event.utils.renderer.EventRenderer')
    url_registry.register('cosinnus_event', cosinnus_root_patterns,
        cosinnus_group_patterns)
