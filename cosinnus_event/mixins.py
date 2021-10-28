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
    
    def get_bbb_room_type(self):
        """ Returns the type of preset this room is from `BBB_ROOM_TYPE_CHOICES`,
            to match extra parameters for join/create events.
            See `BBB_ROOM_TYPE_EXTRA_CREATE_PARAMETERS`, `BBB_ROOM_TYPE_EXTRA_JOIN_PARAMETERS`  """
        return settings.BBB_ROOM_TYPE_DEFAULT
    
    def get_max_participants(self):
        """ Returns the number of participants allowed in the room
            @param return: a number between 0-999. """
        return settings.COSINNUS_CONFERENCE_COFFEETABLES_MAX_PARTICIPANTS_DEFAULT
    
    def get_presentation_url(self):
        """ Stub for the presentation URL used in create calls """ 
        return None
    
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
                from cosinnus.models.bbb_room import BBBRoom
                bbb_room = BBBRoom.create(
                    name=event.title,
                    meeting_id=f'{portal.slug}-{event.group.id}-{event.id}',
                    presentation_url=event.get_presentation_url(),
                    source_object=event,
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
            bbb_room.name = self.title
            bbb_room.presentation_url = self.get_presentation_url()
            bbb_room.save()
    
    def sync_bbb_members(self):
        """ Completely re-syncs all users for this room 
            TODO: properly refactor for the fitting `self.group` param """
        if self.media_tag.bbb_room:
            bbb_room = self.media_tag.bbb_room
            with transaction.atomic():
                bbb_room.remove_all_users()
                bbb_room.join_group_members(self.group)
    
    def get_admin_change_url(self):
        """ Stub that all inheriting objects should implement.
            Returns the django admin edit page for this object. """
        return None
    
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
