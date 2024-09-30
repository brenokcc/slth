import time
from django.apps import apps
from django.core.management.commands.test import Command


class Command(Command):
    def handle(self, *args, **options):
        try:
            while True:
                print('Checking emails...')
                apps.get_model("slth", "email").objects.send()
                print('Checking notifications...')
                apps.get_model("slth", "pushnotification").objects.send()
                print('Checking jobs...')
                apps.get_model("slth", "job").objects.execute()
                print('Sleeping for 10 seconds...')
                time.sleep(10)
        except KeyboardInterrupt:
            pass
