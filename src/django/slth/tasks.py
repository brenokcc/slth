import time
from django.apps import apps
from threading import Thread
from django.db import connection
from django.core.cache import cache


def __init__(function):
    def wrapper(*args, **kwargs):
        args[0].__initializer__ = (args[1:], kwargs)
        return function(*args, **kwargs)
    return wrapper


class TaskMetaclass(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        if name != 'Task' and '__init__' in attrs:
            attrs['__init__'] = __init__(attrs['__init__'])
        return super().__new__(cls, name, bases, attrs, **kwargs)



class Task(metaclass=TaskMetaclass):

    def __init__(self):
        self.job = None
        self.total = 0
        self.partial = 0
        self.progress = 0
        self.progress2 = 0
        self.error = None
        self.file_path = None

    def iterate(self, iterable):
        if self.total == 0:
            self.total = len(iterable)
        for obj in iterable:
            self.partial += 1
            self.update()
            yield obj
        self.update()

    def update(self):
        key = f'task-{self.job.name}'
        self.progress = int(self.partial / self.total * 100) if self.total else 0
        if self.progress == 0 or self.progress - self.progress2 > 5 or self.progress == 100:
            self.progress2 = self.progress
            data = dict(progress=self.progress, error=self.error, file_path=self.file_path)
            print(f'Caching "{key}": {data}...')
            cache.set(key, data, timeout=10)
        
    def run(self):
        raise NotImplemented()

    def sleep(self, secs=1):
        time.sleep(secs)

    def objects(self, model):
        return apps.get_model(model).objects
