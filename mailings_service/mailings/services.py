import json
import os

from django.db.models.query_utils import Q
import requests


def start_mailing(mailing):
    from mailings.models import Client, Message

    clients_to_send = Client.objects.filter(
        Q(operator_code=mailing.filter) | Q(tag=mailing.filter)
    )

    for client in clients_to_send:
        data = {
            "id": client.id,
            "phone": int(client.phone_number),
            "text": mailing.text,
        }

        print("Sending message: ", data)

        response = requests.post(
            f"http://{os.environ['SENDER_HOST']}:{os.environ['SENDER_PORT']}/",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                # "Authorization": f"Bearer {TOKEN}",
            },
        )

        print(response.content)

        Message.objects.create(
            status=response.status_code, mailing=mailing, client=client
        )
