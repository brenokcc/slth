import traceback
import time
import datetime
from django.apps import apps
from threading import Thread
from django.db import connection
from django.core.cache import cache
from uuid import uuid1


class Task:

    def __init__(self):
        self.total = 0
        self.partial = 0
        self.progress = 0
        self.error = None
        self.file_path = None
        self.key = uuid1().hex
        self.save()
        self.sleep(1)

    def save(self):
        cache.set(self.key, dict(progress=self.progress, error=self.error, file_path=self.file_path), timeout=30)

    def next(self):
        self.partial += 1
        self.progress = int(self.partial / self.total * 100) if self.total else 0
        if self.progress == 100:
            self.progress = 99
        self.save()

    def iterate(self, iterable):
        self.total = len(iterable)
        for obj in iterable:
            self.next()
            yield obj

    def run(self):
        raise NotImplemented()

    def sleep(self, secs=1):
        time.sleep(secs)

    def objects(self, model):
        return apps.get_model(model).objects


class TaskRunner(Thread):

    def __init__(self, task, *args, **kwargs):
        self.task = task
        super().__init__(*args, **kwargs)

    def run(self):
        try:
            self.task.file_path = self.task.run()
            self.task.progress = 100
            self.task.save()
        except Exception as e:
            traceback.print_exc()
            try:
                from sentry_sdk import capture_exception
                capture_exception(e)
            except Exception:
                pass
            self.task.error = 'Ocorreu um erro: {}'.format(str(e))
            self.task.save()
        finally:
            connection.close()
