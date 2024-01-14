from rest_framework import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r"clients", views.ClientViewSet, basename="client")
router.register(r"mailings", views.MailingViewSet, basename="mailing")

urlpatterns = [
    path("", include(router.urls)),
]
