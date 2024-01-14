from mailings.serializers import ClientSerializer, MailingSerializer
from mailings.models import Client, Mailing
from rest_framework import viewsets


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer
