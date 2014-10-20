# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings  # noqa
from appconf import AppConf


class CosinnusEventConf(AppConf):
    # identifier for token label used for the event-feed token in cosinnus_profile.settings 
    TOKEN_EVENT_FEED = 'event_feed'
    