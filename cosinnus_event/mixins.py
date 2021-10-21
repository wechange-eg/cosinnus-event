from threading import Thread
import logging

from django.contrib.contenttypes.fields import GenericRelation
from django.db import transaction
from django.urls import reverse

from cosinnus.models.group import CosinnusPortal
from cosinnus_event.conf import settings
from cosinnus_event.utils.bbb_streaming import trigger_streamer_status_changes

logger = logging.getLogger('cosinnus')

class BBBRoomMixin(object):
    """ 
    Mixin that provides the functionality of BBB video conferences into event models
    """

    conference_settings_assignments = GenericRelation('cosinnus.CosinnusConferenceSettings')

    def save(self, *args, **kwargs):        
        # call previous model
        super().save(*args, **kwargs)
        
        if self.can_have_bbb_room():
            # we do not create a bbb room on the server yet, that only happens
            # once  `get_bbb_room_url()` is called
            try:
                self.sync_bbb_members()
            except Exception as e:
                logger.exception(e)
                
        # save changed properties of the BBBRoom
        self.check_and_sync_bbb_room()
        # trigger any streamer status changes if enabled, so streamers
        # are started/stopped instantly on changes
        trigger_streamer_status_changes(events=[self])

    def can_have_bbb_room(self):
        """ 
        Check if this event may have a BBB room.
        Returns 'False' since is just a plug: add a funktion with the very same name into a model 
        you are going to use the mixin with. See the 'ConferenceEvent' model for details.
        """
        return False
    
    def check_and_create_bbb_room(self, threaded=True):
        """ Can be safely called at any time to create a BBB room for this event
            if it doesn't have one yet.
            @return True if a room needed to be created, False if none was created """
        # if event is of the right type and has no BBB room yet,
        if self.can_have_bbb_room() and not self.media_tag.bbb_room:
            # be absolutely sure that no room has been created right now
            self.media_tag.refresh_from_db()
            if self.media_tag.bbb_room:
                return False
            
            # start a thread and create a BBB Room
            event = self
            portal = CosinnusPortal.get_current()
            
            def create_room():
                max_participants = None
                if event.type in event.BBB_MAX_PARTICIPANT_TYPES and event.max_participants:
                    max_participants = event.max_participants
                # determine BBBRoom type from event type
                room_type = event.BBB_ROOM_ROOM_TYPE_MAP.get(event.type, settings.BBB_ROOM_TYPE_DEFAULT)
                presentation_url = event.presentation_file.url if event.presentation_file else None
                    
                from cosinnus.models.bbb_room import BBBRoom
                bbb_room = BBBRoom.create(
                    name=event.title,
                    meeting_id=f'{portal.slug}-{event.group.id}-{event.id}',
                    max_participants=max_participants,
                    room_type=room_type,
                    presentation_url=presentation_url,
                    source_object=self,
                )
                event.media_tag.bbb_room = bbb_room
                event.media_tag.save()
                # sync all bb users
                event.sync_bbb_members()
            
            if threaded:
                class CreateBBBRoomThread(Thread):
                    def run(self):
                        create_room()
                CreateBBBRoomThread().start()
            else:
                create_room()
            return True
        return False

    def check_and_sync_bbb_room(self):
        """ Will check if there is a BBBRoom attached to this event,
            and if so, sync the settings like participants from this event with it """
        if self.media_tag.bbb_room:
            bbb_room = self.media_tag.bbb_room
            max_participants = None
            if self.type in self.BBB_MAX_PARTICIPANT_TYPES and self.max_participants:
                max_participants = self.max_participants
            # monkeypatch for BBB appearently allowing one less persons to enter a room
            if max_participants is not None and settings.BBB_ROOM_FIX_PARTICIPANT_COUNT_PLUS_ONE:
                max_participants += 1
            # determine BBBRoom type from event type
            room_type = self.BBB_ROOM_ROOM_TYPE_MAP.get(self.type, settings.BBB_ROOM_TYPE_DEFAULT)
            presentation_url = self.presentation_file.url if self.presentation_file else None
            bbb_room.name = self.title
            bbb_room.max_participants = max_participants
            bbb_room.room_type = room_type
            bbb_room.presentation_url = presentation_url
            bbb_room.save()
    
    def sync_bbb_members(self):
        """ Completely re-syncs all users for this room """
        if self.media_tag.bbb_room:
            bbb_room = self.media_tag.bbb_room
            with transaction.atomic():
                bbb_room.remove_all_users()
                bbb_room.join_group_members(self.group)
                # creator and presenters are moderators in addition to the group admins
                bbb_room.join_user(self.creator, as_moderator=True)
                for user in self.presenters.all():
                    bbb_room.join_user(user, as_moderator=True)

    def get_bbb_room_url(self):
        if not self.can_have_bbb_room():
            return None
        if self.can_have_bbb_room() and not self.media_tag.bbb_room:
            self.check_and_create_bbb_room(threaded=True)
            # redirect to a temporary URL that refreshes
            return reverse('cosinnus:bbb-room-queue', kwargs={'mt_id': self.media_tag.id})
        return self.media_tag.bbb_room.get_absolute_url()
    
    def get_bbb_room_queue_api_url(self):
        if not self.can_have_bbb_room():
            return None
        if not settings.COSINNUS_TRIGGER_BBB_ROOM_CREATION_IN_QUEUE:
            # create a room here if mode is on hesitant-creation
            if self.can_have_bbb_room() and not self.media_tag.bbb_room:
                self.check_and_create_bbb_room(threaded=True)
            # redirect to a temporary URL that refreshes
        return reverse('cosinnus:bbb-room-queue-api', kwargs={'mt_id': self.media_tag.id})
