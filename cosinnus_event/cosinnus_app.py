# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from cosinnus_event.utils import renderer

IS_COSINNUS_APP = True
COSINNUS_APP_NAME = 'event'
COSINNUS_APP_LABEL = _('Events')

ATTACHABLE_OBJECT_MODELS = ['cosinnus_event.Event']
ATTACHABLE_OBJECT_RENDERERS = {'cosinnus_event.Event':renderer.EventRenderer}
