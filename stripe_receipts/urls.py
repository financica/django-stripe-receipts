from django.urls import path

from .api import StripeAddKey, StripeSync

urlpatterns = [
    path("add_key", StripeAddKey.as_view()),
    path("sync", StripeSync.as_view()),
]
