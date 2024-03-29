from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models import Count
import pytz

from mailings.tasks import start_mailing


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

    def total_messages(self):
        return self.message_set.count()

    def messages_by_status(self):
        return self.message_set.values("status").annotate(
            messages_count=Count("id")
        )

    def __str__(self):
        return (
            f"{self.id} | "
            f"{self.start_date.strftime('%m.%d|%H:%M')}"
            f"-{self.stop_date.strftime('%m.%d|%H:%M')}, "
            f"{self.filter}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        now = timezone.localtime()

        if self.start_date <= now and self.stop_date > now:
            start_mailing.delay(mailing_id=self.id)


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

    def __str__(self):
        return f"{self.phone_number}"

    def save(self, *args, **kwargs):
        self.operator_code = self.phone_number[1:4]
        super().save(*args, **kwargs)


class MessageStatus(models.TextChoices):
    PENDING = "Pending"
    DELIVERED = "Delivered"
    ERROR = "Error"


class Message(models.Model):
    creation_date = models.DateTimeField(
        "Дата и время создания сообщения",
        auto_now_add=True,
        editable=False
    )
    status = models.CharField("Статус отправки",
                              choices=MessageStatus.choices,
                              max_length=10)
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

    def __str__(self):
        return (
            f"{self.id}, "
            f"{self.client.phone_number} "
            f"({self.mailing.filter}"
            f", {self.status})"
        )
