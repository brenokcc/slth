import time
from django.apps import apps
from django.conf import settings
from django.core.management.commands.test import Command


class Command(Command):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--preview", action="store_true", help="Preview")
    
    def handle(self, *args, **options):
        seconds = 10 if settings.DEBUG else 60
        preview = options.get("preview")
        try:
            while True:
                print('Checking whatsapp notifications...')
                apps.get_model("slth", "whatsappnotification").objects.send(preview)
                print('Checking email notifications...')
                apps.get_model("slth", "email").objects.send(preview)
                print('Checking push notifications...')
                apps.get_model("slth", "pushnotification").objects.send(preview)
                print('Checking jobs...')
                apps.get_model("slth", "job").objects.execute(preview)
                print(f'Sleeping for {seconds} seconds...')
                time.sleep(seconds)
        except KeyboardInterrupt:
            pass
