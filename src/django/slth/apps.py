from django.conf import settings
from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'slth'

    def ready(self):
        settings.SLOTH = True
