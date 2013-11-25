# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from cosinnus_event.views import (
    EventAddView, EventDeleteView, EventView, EventIndexView,
    EventListView, EventEditView, VoteFormView)


cosinnus_group_patterns = patterns('',
    url(r'^$',
        EventIndexView.as_view(),
        name='index'),

    url(r'^list/$',
        EventListView.as_view(),
        name='list'),

    url(r'^list/(?P<tag>[^/]+)/$',
        EventListView.as_view(),
        name='list-filtered'),

    url(r'^add/$',
        EventAddView.as_view(),
        {'form_view': 'add'},
        name='add'),

    url(r'^(?P<slug>[^/]+)/$',
        EventView.as_view(),
        name='entry'),

    url(r'^(?P<slug>[^/]+)/delete/$',
        EventDeleteView.as_view(),
        {'form_view': 'delete'},
        name='entry-delete'),

    url(r'^(?P<slug>[^/]+)/edit/$',
        EventEditView.as_view(),
        {'form_view': 'edit'},
        name='entry-edit'),

    url(r'^(?P<slug>[^/]+)/vote/$',
        VoteFormView.as_view(),
        {'form_view': 'vote'},
        name='entry-vote'),
)


cosinnus_root_patterns = patterns(None)
urlpatterns = cosinnus_group_patterns + cosinnus_root_patterns
