from datetime import datetime

from rest_framework import serializers

from cosinnus_event.models import Event


class EventListSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.URLField(source='get_absolute_url', read_only=True)
    timestamp = serializers.DateTimeField(source='last_modified')

    class Meta(object):
        model = Event
        fields = ('id', 'title', 'from_date', 'to_date', 'note',
                  'location', 'location_lat', 'location_lon', 'street', 'zipcode', 'city',
                  'timestamp')


class EventRetrieveSerializer(EventListSerializer):
    pass
