from cosinnus.api.views import PublicTaggableObjectFilterMixin
from cosinnus_event.models import Event
from cosinnus_event.api.serializers import EventListSerializer, EventRetrieveSerializer

from rest_framework.viewsets import ModelViewSet


class EventSerializerViewSet(PublicTaggableObjectFilterMixin,
                             ModelViewSet):
    queryset = Event.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(public=True, state=Event.STATE_SCHEDULED)

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        if self.action == 'retrieve':
            return EventRetrieveSerializer
        return EventRetrieveSerializer
