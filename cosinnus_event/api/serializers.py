from datetime import datetime

import pytz
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


class EventGoodDBSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.URLField(source='get_absolute_url', read_only=True)
    description = serializers.CharField(source='note')
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    allDayEvent = serializers.BooleanField(source='is_all_day')
    createdAt = serializers.SerializerMethodField()
    createdBy = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta(object):
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'allDayEvent', 'createdAt', 'createdBy', 'coordinates',
                  'address', 'contact', 'tags')

    def _get_unixtime(self, datetime_obj):
        epoch = datetime(1970, 1, 1, tzinfo=pytz.UTC)
        return int((datetime_obj - epoch).total_seconds())

    def get_start(self, obj):
        return self._get_unixtime(obj.from_date)

    def get_end(self, obj):
        return self._get_unixtime(obj.to_date)

    def get_createdAt(self, obj):
        return self._get_unixtime(obj.created)

    def get_createdBy(self, obj):
        return obj.creator.email if obj.creator else None

    def get_coordinates(self, obj):
        if hasattr(obj, 'media_tag'):
            media_tag = obj.media_tag
            return {
                'lat': media_tag.location_lat,
                'lng': media_tag.location_lon,
            }
        return {}

    def get_address(self, obj):
        return {}
        # {
        #     'street': self.street,
        #     'zip': self.zipcode,
        #     'city': self.city,
        #     'country': None,
        # }

    def get_contact(self, obj):
        contact = {}
        user = obj.creator
        if user.email:
            contact['email'] = [user.email]
        if obj.url:
            contact['websites'] = [obj.url]
        return contact

    def get_tags(self, obj):
        tags = []
        if hasattr(obj, 'media_tag'):
            tags = obj.media_tag.tags
        return tags
