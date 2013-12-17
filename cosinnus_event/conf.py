# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from appconf import AppConf


class CosinnusEventConf(AppConf):
    DATETIME_PICK_FORMAT = getattr(
        settings, 'COSINNUS_DATETIME_PICK_FORMAT', None) or 'YYYY-MM-DD HH:mm'
