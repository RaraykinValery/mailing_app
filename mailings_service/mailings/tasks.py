import json

from celery import shared_task
from celery_singleton import Singleton
from django.db.models.query_utils import Q
from django.conf import settings
from django.utils import timezone
import requests
from requests.exceptions import Timeout, ConnectionError

from mailings_service.celery import app


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
        start_date__lt=now, stop_date__gt=now)

    for mailing in active_mailings:
        start_mailing.delay(mailing_id=mailing.id)


@shared_task(base=Singleton)
def start_mailing(mailing_id):
    from mailings.models import Client, Mailing

    mailing = Mailing.objects.get(pk=mailing_id)

    clients_to_send = (
        Client.objects
        .filter(Q(operator_code=mailing.filter) | Q(tag=mailing.filter))
    )

    print(clients_to_send)

    for client in clients_to_send:
        send_client_message.delay(mailing_id=mailing.id, client_id=client.id)


@shared_task(base=Singleton)
def send_client_message(mailing_id, client_id):
    from mailings.models import Client, Message, Mailing, MessageStatus

    mailing = Mailing.objects.filter(id=mailing_id).first()
    client = Client.objects.filter(id=client_id).first()

    if mailing and client:
        message = Message.objects.filter(
            mailing_id=mailing_id, client_id=client_id).first()

        if not message:
            message = Message.objects.create(
                status=MessageStatus.PENDING, mailing=mailing, client=client)
        else:
            if message.status == MessageStatus.DELIVERED:
                return

        request_data = {
            "id": message.id,
            "phone": int(client.phone_number),
            "text": mailing.text,
        }

        print("Sending message: ", request_data)

        try:
            response = requests.post(
                (
                    f"http://{settings.SENDER_HOST}:{settings.SENDER_PORT}"
                    f"/v1/send/{message.id}"
                ),
                data=json.dumps(request_data),
                headers={
                    "Content-Type": "application/json",
                    # "Authorization": f"Bearer {TOKEN}",
                },
                timeout=9
            )
        except ConnectionError:
            print("Connection could not be established")
            message.status = MessageStatus.ERROR
            message.save()
            return
        except Timeout:
            print("Timeout for the request has been reached")
            message.status = MessageStatus.ERROR
            message.save()
            return

        if response.status_code == 200:
            response_data = response.json()

            if (isinstance(response_data, dict)
                    and 'code' in response_data
                    and 'message' in response_data):

                response_code = response_data.get("code")
                response_message = response_data.get("message")

                print(f"code: {response_code}, message: {response_message}")

                if response_code == 0 and response_message == "OK":
                    message.status = MessageStatus.DELIVERED
                else:
                    message.status = MessageStatus.ERROR

                message.save()

            else:
                print('Invalid data format received')
                message.status = MessageStatus.ERROR
        else:
            print(f'Request failed with status code {response.status_code}')
            message.status = MessageStatus.ERROR

        message.save()
