from datetime import datetime

from rest_framework import serializers

from cosinnus_event.models import Event


class EventListSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.URLField(source='get_absolute_url', read_only=True)
    timestamp = serializers.DateTimeField(source='last_modified')

    class Meta(object):
        model = Event
        fields = ('id', 'timestamp')


class EventRetrieveSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.URLField(source='get_absolute_url', read_only=True)
    timestamp = serializers.DateTimeField(source='last_modified')
    orgId = serializers.SerializerMethodField()
    iCal = serializers.SerializerMethodField()

    class Meta(object):
        model = Event
        fields = ('id', 'timestamp', 'orgId', 'iCal')

    def get_orgId(self, obj):
        return obj.group.get_absolute_url()

    def get_iCal(self, obj):
        ical = "BEGIN:VEVENT\n"
        ical += "UID:%s\n" % obj.get_absolute_url()
        creator = obj.creator
        ical += 'ORGANIZER;CN="%s":MAILTO:%s\n' % (creator.get_full_name(), creator.email)
        ical += "LOCATION:%s\n" % obj.location
        ical += "SUMMARY:%s\n" % obj.note
        ical += "CATEGORIES:%s\n" % obj.media_tag.get_topics()
        ical += "DESCRIPTION:%s\n" % ""
        ical += "DTSTART:%s\n" % obj.from_date.strftime('%Y%m%dT%H%m%sZ')
        ical += "DTEND:%s\n" % obj.to_date.strftime('%Y%m%dT%H%m%sZ')
        ical += "DTSTAMP:%s\n" % obj.created.strftime('%Y%m%dT%H%m%sZ')
        ical += "END:VEVENT\n"
        return ical
