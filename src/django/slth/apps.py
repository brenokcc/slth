import os
import time
from datetime import datetime
from django.conf import settings
from django.apps import AppConfig
from django.utils import autoreload
from django.apps import apps
import threading
from . import THREADS




class Thread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            # print('.')
            apps.get_model("slth", "email").objects.send()
            apps.get_model("slth", "pushnotification").objects.send()
            apps.get_model("slth", "job").objects.execute()
            for i in range(0, 10):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
    
    def stop(self):
        print("Stopping e-mail thread...")
        self._stop_event.set()


class AppConfig(AppConfig):
    name = 'slth'

    def ready(self):
        settings.SLOTH = True
        if os.environ.get("RUN_MAIN"):
            print('Starting sloth thread...')
            thread = Thread()
            thread.start()
            THREADS.append(thread)
