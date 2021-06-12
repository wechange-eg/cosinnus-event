from cosinnus_conference.bbb_streaming import create_streamer, delete_streamer,\
    start_streamer, stop_streamer
import logging
from cosinnus.apis.bigbluebutton import BigBlueButtonAPI

logger = logging.getLogger('cosinnus')

# key for the streamer id in `event.settings`
SETTINGS_STREAMER_ID = 'streaming_streamer_id'
# key for if the streamer is currently running in `event.settings`
SETTINGS_STREAMER_RUNNING = 'streaming_streamer_running'


def create_streamer_for_event(event):
    """ Creates a streamer using the BBB streaming API for this event. This does
        not start the actual stream yet.
        Only executes if there is not already a streamer ID set. """
    
    if event.settings.get(SETTINGS_STREAMER_ID, None):
        logger.warn('BBB Streaming: Could not create a streamer because one was already created!', extra={
            'event_id': event.id,
            'streamer_id': event.settings.get(SETTINGS_STREAMER_ID),
        })
        return 
    if not event.enable_streaming or not event.stream_url or not event.stream_key:
        logger.error('BBB Streaming: Could not create a streamer for event because streaming was not enabled for it or stream url or key was missing!', extra={
            'event_id': event.id,
        })
        return
    bbb_room = event.media_tag.bbb_room
    if not bbb_room:
        logger.error('BBB Streaming: Could not create a streamer for event because no BBBRoom exists for it!', extra={
            'event_id': event.id,
        })
        return
    stream_url = event.stream_url.strip()
    if not stream_url.endswith('/'):
        stream_url += '/'
    stream_url += event.stream_key
    bbb_api_obj = BigBlueButtonAPI(source_object=event)
    
    streamer_uuid_name = f'Streamer-{event.group.portal.slug}-{event.id}'
    streamer_id = create_streamer(
        name=streamer_uuid_name,
        bbb_url=bbb_api_obj.api_auth_url,
        bbb_secret=bbb_api_obj.api_auth_secret,
        meeting_id=bbb_room.meeting_id,
        stream_url=stream_url
    )
    if streamer_id is not None:
        event.settings[SETTINGS_STREAMER_ID] = streamer_id
        event.save(update_fields=['settings'])


def start_streamer_for_event(event):
    """ Starts the streaming for a previously created streamer (using `create_streamer_for_event`)
        for the BBB streaming API for this event.
        Only executes if there is a streamer ID set but the streamer is not yet running. """
        
    if not event.settings.get(SETTINGS_STREAMER_ID, None):
        logger.warn('BBB Streaming: Could not start a streamer because no streamer id existed!', extra={
            'event_id': event.id,
        })
        return 
    if event.settings.get(SETTINGS_STREAMER_RUNNING, False):
        logger.warn('BBB Streaming: Could not start a streamer because it was already running!', extra={
            'event_id': event.id,
        })
        return 
    ret = start_streamer(event.settings.get(SETTINGS_STREAMER_ID))
    if ret is True:
        event.settings[SETTINGS_STREAMER_RUNNING] = True
        event.save(update_fields=['settings'])


def stop_streamer_for_event(event):
    """ Stops the streaming for a previously started streamer for the BBB streaming API for this event.
        Only executes if there is a streamer ID set and the streamer is running. """
    if not event.settings.get(SETTINGS_STREAMER_ID, None):
        logger.warn('BBB Streaming: Could not stop a streamer because no streamer id existed!', extra={
            'event_id': event.id,
        })
        return 
    if not event.settings.get(SETTINGS_STREAMER_RUNNING, False):
        logger.warn('BBB Streaming: Could not stop a streamer because it was not running!', extra={
            'event_id': event.id,
        })
        return 
    ret = stop_streamer(event.settings.get(SETTINGS_STREAMER_ID))
    if ret is True:
        if SETTINGS_STREAMER_RUNNING in event.settings:
            del event.settings[SETTINGS_STREAMER_RUNNING]
            event.save(update_fields=['settings'])


def delete_streamer_for_event(event):
    """ Deletes a previously created streamer for the BBB streaming API for this event.
        Only executes if there is a streamer ID set. """
    if not event.settings.get(SETTINGS_STREAMER_ID, None):
        logger.warn('BBB Streaming: Could not delete a streamer because no streamer id existed!', extra={
            'event_id': event.id,
        })
        return 
    delete_streamer(event.settings.get(SETTINGS_STREAMER_ID))
    # the return value only telss us that the streamer was deleted successfully. we also delete it from the event if
    # it returns False, because then the streamer was already deleted.
    # all other results produce an Exception anyways
    if SETTINGS_STREAMER_ID in event.settings:
        del event.settings[SETTINGS_STREAMER_ID]
        event.save(update_fields=['settings'])

