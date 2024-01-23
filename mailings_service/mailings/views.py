from rest_framework import viewsets

from rest_framework.response import Response
from rest_framework.decorators import action

from mailings.serializers import (
    ClientSerializer,
    MailingSerializer,
    MessageSerializer
)
from mailings.models import (
    Client,
    Mailing,
    Message,
)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    @action(detail=True, methods=['get'])
    def messages(self, request, pk):
        mailing_messages = Message.objects.filter(mailing=pk)
        serializer = MessageSerializer(mailing_messages, many=True)
        return Response(serializer.data)
