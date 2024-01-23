from celery import shared_task
from celery_singleton import Singleton
from django.db.models.query_utils import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from requests.exceptions import RequestException

from mailings_service.celery import app
from mailings import services


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        5.0,
        check_mailings.s()
    )


@app.task
def check_mailings():
    from mailings.models import Mailing

    now = timezone.localtime()

    active_mailings = Mailing.objects.filter(
        start_date__lt=now, stop_date__gt=now
    )

    for mailing in active_mailings:
        start_mailing.apply_async((mailing.id,),
                                  expires=mailing.stop_date)


@shared_task(base=Singleton)
def start_mailing(mailing_id):
    from mailings.models import Client, Mailing

    mailing = Mailing.objects.get(pk=mailing_id)

    clients_to_send = (
        Client.objects
        .filter(Q(operator_code=mailing.filter) | Q(tag=mailing.filter))
    )

    for client in clients_to_send:
        send_client_message.apply_async((mailing.id, client.id),
                                        expires=mailing.stop_date)


@shared_task(base=Singleton)
def send_client_message(mailing_id, client_id):
    from mailings.models import Client, Mailing, Message, MessageStatus

    try:
        client = Client.objects.get(id=client_id)
        mailing = Mailing.objects.get(id=mailing_id)
    except ObjectDoesNotExist:
        print(f"Client with id {client.id} "
              f"or mailing with id {mailing.id} object "
              "doesn't exist")
        return

    try:
        message = Message.objects.get(mailing_id=mailing.id,
                                      client_id=client.id)
        if message.status == MessageStatus.DELIVERED:
            return
        print(f"Retry sending message {message.id}")
    except ObjectDoesNotExist:
        message = Message.objects.create(status=MessageStatus.PENDING,
                                         mailing=mailing,
                                         client=client)
        print(f"Created message {message.id}")

    try:
        print(f"Sending message {message.id}")
        response = services.send_request(mailing, client, message)
    except RequestException as e:
        print(f"Request for message {message.id} failed: {e}")
        message.status = MessageStatus.ERROR
        message.save()
        return

    try:
        response_code = response.get("code")
        response_message = response.get("message")
    except (ValueError, KeyError):
        print(f'Invalid data format received for message ({message.id})')
        message.status = MessageStatus.ERROR
        message.save()
        return

    if response_code == 0 and response_message == "OK":
        print(f"Message {message.id} delivered "
              f"with code: {response_code}, "
              f"and message: {response_message}")
        message.status = MessageStatus.DELIVERED
    else:
        print(f"Error in delivering of "
              f"message {message.id} "
              f"with code: {response_code}, "
              f"and message: {response_message}")
        message.status = MessageStatus.ERROR

    message.save()
