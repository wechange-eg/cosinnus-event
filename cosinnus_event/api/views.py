from datetime import datetime

from django.db.models import Q
from rest_framework import viewsets

from cosinnus.api.views import PublicTaggableObjectFilterMixin, CosinnusFilterQuerySetMixin
from cosinnus_event.models import Event
from cosinnus_event.api.serializers import EventListSerializer, EventRetrieveSerializer


class EventViewSet(CosinnusFilterQuerySetMixin,
                   PublicTaggableObjectFilterMixin,
                   viewsets.ReadOnlyModelViewSet):

    queryset = Event.objects.all()
    FILTER_CONDITION_MAP = {
        'upcoming': {
            'true': [Q(from_date__gte=datetime.now())]
        }
    }
    FILTER_DEFAULT_ORDER = ['from_date', ]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(state=Event.STATE_SCHEDULED)

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        if self.action == 'retrieve':
            return EventRetrieveSerializer
        return EventRetrieveSerializer
