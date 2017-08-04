# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.dispatch as dispatch
from django.utils.translation import ugettext_lazy as _

""" Cosinnus:Notifications configuration etherpad. 
    See http://git.sinnwerkstatt.com/cosinnus/cosinnus-core/wikis/cosinnus-notifications-guidelines.
"""


""" Signal definitions """
event_created = dispatch.Signal(providing_args=["user", "obj", "audience"])
doodle_created = dispatch.Signal(providing_args=["user", "obj", "audience"])
event_comment_posted = dispatch.Signal(providing_args=["user", "obj", "audience"])
tagged_event_comment_posted = dispatch.Signal(providing_args=["user", "obj", "audience"])
voted_event_comment_posted = dispatch.Signal(providing_args=["user", "obj", "audience"])
attending_event_comment_posted = dispatch.Signal(providing_args=["user", "obj", "audience"])


""" Notification definitions.
    These will be picked up by cosinnus_notfications automatically, as long as the 
    variable 'notifications' is present in the module '<app_name>/cosinnus_notifications.py'.
    
    Both the mail and subject template will be provided with the following context items:
        :receiver django.auth.User who receives the notification mail
        :sender django.auth.User whose action caused the notification to trigger
        :receiver_name Convenience, full name of the receiver
        :sender_name Convenience, full name of the sender
        :object The object that was created/changed/modified and which the notification is about.
        :object_url The url of the object, if defined by get_absolute_url()
        :object_name The title of the object (only available if it is a BaseTaggableObject)
        :group_name The name of the group the object is housed in (only available if it is a BaseTaggableObject)
        :site_name Current django site's name
        :domain_url The complete base domain needed to prefix URLs. (eg: 'http://sinnwerkstatt.com')
        :notification_settings_url The URL to the cosinnus notification settings page.
        :site Current django site
        :protocol Current portocol, 'http' or 'https'
        
    
""" 
notifications = {
    'event_created': {
        'label': _('A user created a new event'), 
        'mail_template': 'cosinnus_event/notifications/event_created.txt',
        'subject_template': 'cosinnus_event/notifications/event_created_subject.txt',
        'signals': [event_created],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('New event by %(sender_name)s'),
        'notification_text': _('%(sender_name)s created a new event'),
        'subject_text': _('A new event: "%(object_name)s" was announced in %(team_name)s.'),
        'data_attributes': {
            'object_name': 'title', 
            'object_url': 'get_absolute_url', 
            'object_text': 'note',
            'image_url': 'attached_image.static_image_url_thumbnail',
            'event_meta': 'from_date',
        },
    },  
    'doodle_created': {
        'label': _('A user created a new event poll'), 
        'mail_template': 'cosinnus_event/notifications/doodle_created.txt',
        'subject_template': 'cosinnus_event/notifications/doodle_created_subject.txt',
        'signals': [doodle_created],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('New event poll by %(sender_name)s'),
        'notification_text': _('%(sender_name)s created a new event poll'),
        'subject_text': _('A new event poll: "%(object_name)s" was created in %(team_name)s.'),
        'data_attributes': {
            'object_name': 'title', 
            'object_url': 'get_absolute_url', 
            'object_text': 'note',
            'image_url': 'attached_image.static_image_url_thumbnail',
        },
    },  
    'event_comment_posted': {
        'label': _('A user commented on one of your events'), 
        'mail_template': 'cosinnus_event/notifications/event_comment_posted.html',
        'subject_template': 'cosinnus_event/notifications/event_comment_posted_subject.txt',
        'signals': [event_comment_posted],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('%(sender_name)s commented on your event'),
        'subject_text': _('%(sender_name)s commented on one of your events'),
        'sub_event_text': _('%(sender_name)s'),
        'data_attributes': {
            'object_name': 'event.title', 
            'object_url': 'get_absolute_url', 
            'image_url': 'event.creator.cosinnus_profile.get_avatar_thumbnail_url', # note: receiver avatar, not creator's!
            'sub_image_url': 'creator.cosinnus_profile.get_avatar_thumbnail_url', # the comment creators
            'sub_object_text': 'text',
        },
    },    
    'tagged_event_comment_posted': {
        'label': _('A user commented on a event you were tagged in'), 
        'mail_template': 'cosinnus_event/notifications/tagged_event_comment_posted.html',
        'subject_template': 'cosinnus_event/notifications/tagged_event_comment_posted_subject.txt',
        'signals': [tagged_event_comment_posted],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('%(sender_name)s commented on an event you were tagged in'),
        'subject_text': _('%(sender_name)s commented on an event you were tagged in in %(team_name)s'),
        'sub_event_text': _('%(sender_name)s'),
        'data_attributes': {
            'object_name': 'event.title', 
            'object_url': 'get_absolute_url', 
            'image_url': 'event.creator.cosinnus_profile.get_avatar_thumbnail_url', # note: receiver avatar, not creator's!
            'sub_image_url': 'creator.cosinnus_profile.get_avatar_thumbnail_url', # the comment creators
            'sub_object_text': 'text',
        },
    },  
    'voted_event_comment_posted': {
        'label': _('A user commented on an event you voted in'), 
        'mail_template': 'cosinnus_event/notifications/voted_event_comment_posted.html',
        'subject_template': 'cosinnus_event/notifications/voted_event_comment_posted_subject.txt',
        'signals': [voted_event_comment_posted],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('%(sender_name)s commented on an event you voted in'),
        'subject_text': _('%(sender_name)s commented on an event you voted in in %(team_name)s'),
        'sub_event_text': _('%(sender_name)s'),
        'data_attributes': {
            'object_name': 'event.title', 
            'object_url': 'get_absolute_url', 
            'image_url': 'event.creator.cosinnus_profile.get_avatar_thumbnail_url', # note: receiver avatar, not creator's!
            'sub_image_url': 'creator.cosinnus_profile.get_avatar_thumbnail_url', # the comment creators
            'sub_object_text': 'text',
        },
    },   
    'attending_event_comment_posted': {
        'label': _('A user commented on an event you are attending'), 
        'mail_template': 'cosinnus_event/notifications/attending_event_comment_posted.html',
        'subject_template': 'cosinnus_event/notifications/attending_event_comment_posted_subject.txt',
        'signals': [attending_event_comment_posted],
        'default': True,
        
        'is_html': True,
        'snippet_type': 'event',
        'event_text': _('%(sender_name)s commented on an event you are attending'),
        'subject_text': _('%(sender_name)s commented on an event you are attending in %(team_name)s'),
        'sub_event_text': _('%(sender_name)s'),
        'data_attributes': {
            'object_name': 'event.title', 
            'object_url': 'get_absolute_url', 
            'image_url': 'event.creator.cosinnus_profile.get_avatar_thumbnail_url', # note: receiver avatar, not creator's!
            'sub_image_url': 'creator.cosinnus_profile.get_avatar_thumbnail_url', # the comment creators
            'sub_object_text': 'text',
        },
    },   
}
