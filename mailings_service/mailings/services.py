import json

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import requests


def create_or_get_message(mailing, client):
    from mailings.models import Message, MessageStatus

    try:
        message = Message.objects.get(
            mailing_id=mailing.id, client_id=client.id)
    except ObjectDoesNotExist:
        message = Message.objects.create(
            status=MessageStatus.PENDING, mailing=mailing, client=client)

    return message


def send_request(mailing, client, message):
    request_data = {
        "id": message.id,
        "phone": int(client.phone_number),
        "text": mailing.text,
    }

    response = requests.post(
        (
            f"https://{settings.SENDER_HOST}"
            f"/v1/send/{message.id}"
        ),
        data=json.dumps(request_data),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.MAILING_TOKEN}",
        },
        timeout=9
    )
    response.raise_for_status()

    return response.json()
