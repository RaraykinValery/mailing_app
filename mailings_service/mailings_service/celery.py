import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mailings_service.settings')

app = Celery("mailing_service")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
