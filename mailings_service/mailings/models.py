import json

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models.query_utils import Q
import pytz
import requests

from mailings.services import start_mailing


TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))


class Mailing(models.Model):
    start_date = models.DateTimeField("Дата начала рассылки")
    stop_date = models.DateTimeField("Дата окончания рассылки")
    text = models.CharField(
        "Текст сообщения",
        max_length=255
    )
    filter = models.CharField(
        "Фильтр свойств клиентов",
        max_length=255
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        now = timezone.localtime()

        if self.start_date <= now and self.stop_date > now:
            start_mailing(mailing=self)


class Client(models.Model):
    phone_regex = RegexValidator(
        regex=r"^7\d{10}$",
        message="Phone number must be entered in the format: '79999999999'",
    )
    phone_number = models.CharField(
        "Номер телефона",
        validators=[phone_regex],
        max_length=11
    )
    operator_code = models.CharField(
        "Код оператора",
        max_length=3,
        editable=False
    )
    tag = models.CharField(
        "Тэг",
        max_length=255,
        blank=True
    )
    timezone = models.CharField(
        "Часовой пояс",
        max_length=32,
        choices=TIMEZONES,
        default="UTS"
    )

    def save(self, *args, **kwargs):
        self.operator_code = self.phone_number[1:4]
        super().save(*args, **kwargs)


class Message(models.Model):
    creation_date = models.DateTimeField(
        "Дата и время создания сообщения",
        auto_now_add=True,
        editable=False
    )
    status = models.IntegerField("Статус отправки")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        blank=False
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        blank=False
    )
