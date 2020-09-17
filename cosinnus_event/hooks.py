# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from cosinnus.core import signals
from cosinnus.models.bbb_room import BBBRoom
from django.dispatch.dispatcher import receiver
from cosinnus_event.models import Event
from threading import Thread


def update_bbb_room_memberships(group_membership, deleted):
    """ Apply membership permission changes to BBBRoom of all events in this group  """
    events_in_group = Event.objects.filter(group=group_membership.group).exclude(media_tag__bbb_room=None)
    bbb_room_ids = events_in_group.values_list('media_tag__bbb_room_id', flat=True)
    rooms = BBBRoom.objects.filter(id__in=bbb_room_ids)
    for room in rooms:
        if deleted:
            room.remove_user(group_membership.user)
        else:
            room.join_user(group_membership.user, group_membership.status)


@receiver(signals.group_membership_has_changed)
def group_membership_has_changed_sub(sender, instance, deleted, **kwargs):
    """ Called after a CosinusGroupMembership is changed, to threaded apply membership permission
        changes to BBBRoom of all events in this group """
    
    class CreateBBBRoomUpdateThread(Thread):
        def run(self):
            update_bbb_room_memberships(instance, deleted)
    CreateBBBRoomUpdateThread().start()













