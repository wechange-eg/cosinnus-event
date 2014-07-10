# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url


cosinnus_group_patterns = patterns('cosinnus_event.views',
    url(r'^$', 'index_view', name='index'),
    url(r'^calendar/$', 'list_view', name='list'),
    url(r'^calendar/(?P<tag>[^/]+)/$', 'list_view', name='list-filtered'),
    url(r'^export/$', 'export_view', name='export'),

    url(r'^doodle/list/$', 'doodle_list_view',  name='doodle-list'),
    url(r'^doodle/add/$',
        'doodle_add_view',
        {'form_view': 'add'},
        name='doodle-add'),
    url(r'^doodle/(?P<slug>[^/]+)$',
        'doodle_vote_view',
        {'form_view': 'vote'},
        name='doodle-vote'),
    url(r'^doodle/(?P<slug>[^/]+)/edit/$',
        'doodle_edit_view',
        {'form_view': 'edit'},
        name='doodle-edit'),
    url(r'^doodle/(?P<slug>[^/]+)/delete/$',
        'doodle_delete_view',
        {'form_view': 'delete'},
        name='doodle-delete'),

    url(r'^list/$', 'detailed_list_view', name='list_detailed'),
    url(r'^add/$', 'entry_add_view',  {'form_view': 'add'},  name='event-add'),
    url(r'^(?P<slug>[^/]+)/$',
        'entry_detail_view',
        {'form_view': 'edit'},
        name='event-detail'),
    url(r'^(?P<slug>[^/]+)/edit/$',
        'entry_edit_view',
        {'form_view': 'edit'},
        name='event-edit'),
    url(r'^(?P<slug>[^/]+)/delete/$',
        'entry_delete_view',
        {'form_view': 'delete'},
        name='event-delete'),
)


cosinnus_root_patterns = patterns(None)
urlpatterns = cosinnus_group_patterns + cosinnus_root_patterns
