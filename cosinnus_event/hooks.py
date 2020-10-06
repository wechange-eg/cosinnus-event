# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from cosinnus.core import signals
from cosinnus.models.bbb_room import BBBRoom
from django.dispatch.dispatcher import receiver
from cosinnus_event.models import Event
from threading import Thread
from cosinnus.models.group import MEMBER_STATUS, MEMBERSHIP_ADMIN


def update_bbb_room_memberships(group_membership, deleted):
    """ Apply membership permission changes to BBBRoom of all events in this group  """
    events_in_group = Event.objects.filter(group=group_membership.group).exclude(media_tag__bbb_room=None)
    for event in events_in_group:
        if not event.media_tag.bbb_room:
            continue
        room = event.media_tag.bbb_room
        if deleted:
            room.remove_user(group_membership.user)
        else:
            if group_membership.status in MEMBER_STATUS:
                as_moderator = bool(
                    group_membership.status==MEMBERSHIP_ADMIN or \
                    group_membership.user == event.creator
                )
                conference_event = event.conferenceevent
                if conference_event:
                    as_moderator = as_moderator or conference_event.presenters.filter(id=group_membership.user.id).count() > 0
                room.join_user(group_membership.user, as_moderator=as_moderator)


@receiver(signals.group_membership_has_changed)
def group_membership_has_changed_sub(sender, instance, deleted, **kwargs):
    """ Called after a CosinusGroupMembership is changed, to threaded apply membership permission
        changes to BBBRoom of all events in this group """
    
    class CreateBBBRoomUpdateThread(Thread):
        def run(self):
            update_bbb_room_memberships(instance, deleted)
    CreateBBBRoomUpdateThread().start()













