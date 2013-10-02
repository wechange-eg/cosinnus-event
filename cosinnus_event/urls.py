# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from cosinnus_event.views import (EventCreateView, EventDeleteView,
    EventDetailView, EventIndexView, EventListView, EventUpdateView,
    VoteFormView)


urlpatterns = patterns('',
    url(r'^list/$',
        EventListView.as_view(),
        name='sinn_event-entry-list'),

    url(r'^list/(?P<tag>[^/]+)/$',
        EventListView.as_view(),
        name='sinn_event-entry-list-filtered'),

    url(r'^create/$',
        EventCreateView.as_view(),
        {'form_view': 'create'},
        name='sinn_event-entry-create'),

    url(r'^entry/(?P<event>[^/]+)/$',
        EventDetailView.as_view(),
        name='sinn_event-entry-detail'),

    url(r'^entry/(?P<event>[^/]+)/delete/$',
        EventDeleteView.as_view(),
        {'form_view': 'delete'},
        name='sinn_event-entry-delete'),

    url(r'^entry/(?P<event>[^/]+)/update/$',
        EventUpdateView.as_view(),
        {'form_view': 'update'},
        name='sinn_event-entry-update'),

    url(r'^entry/(?P<event>[^/]+)/vote/$',
        VoteFormView.as_view(),
        {'form_view': 'vote'},
        name='sinn_event-entry-vote'),

    url(r'^$',
        EventIndexView.as_view(),
        name='sinn_event-entry-index'),
)
