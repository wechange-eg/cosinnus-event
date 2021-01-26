# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from cosinnus.core import signals
from cosinnus.models.bbb_room import BBBRoom
from django.dispatch.dispatcher import receiver
from cosinnus_event.models import Event
from threading import Thread
from cosinnus.models.group import MEMBER_STATUS, MEMBERSHIP_ADMIN
from django.db.models.signals import post_save
from annoying.functions import get_object_or_None
from cosinnus.models.group_extra import CosinnusConference


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


print(f'>>>>>> LOAD HOOOKS')
@receiver(post_save, sender=CosinnusConference)
def sync_hidden_conference_proxy_event(sender, instance, created, **kwargs):
    """ For conferences that have a from_date and to_date set, create and keep in sync a single 
        event with state=`STATE_HIDDEN_GROUP_PROXY`, that has the same name and datetime as the 
        conference itself. This event can be used in all normal views and querysets to display
        and handle the conference as proxy. Set related_groups in the conference to have
        the conference's proxy-event be displayed as one of those related_group's own event. """
    TODO: group from_date to_date nullt display on form reload!
        
    print(f'>> go prox')
    if instance.pk and instance.group_is_conference:
        print(f'>> checky')
        proxy_event = get_object_or_None(Event, group=instance, state=Event.STATE_HIDDEN_GROUP_PROXY)
        if proxy_event:
            if instance.from_date is None or instance.to_date is None:
                proxy_event.delete()
                print(f'>> deleted proxy event')
                return
        elif instance.from_date is not None and instance.to_date is not None:
            # only create proxy events for conferences with from_date and to_date set
            proxy_event = Event(
                group=instance,
                state=Event.STATE_HIDDEN_GROUP_PROXY,
                creator=None
            )
        # sync and save if proxy event and group differ in key attributes
        sync_attributes = [('name', 'title'), ('from_date', 'from_date'), ('to_date', 'to_date')]
        if proxy_event and any(getattr(proxy_event, attr[1]) != getattr(instance, attr[0]) for attr in sync_attributes):
            for attr in sync_attributes:
                setattr(proxy_event, attr[1], getattr(instance, attr[0]))
            print(f'>> saved proxy event')
            proxy_event.save()

