import re
import os
import yaml
import warnings
from pathlib import Path
from django.apps import apps
from django.db import models
from .queryset import QuerySet
from django.db.models import manager
from .serializer import Serializer
from .factory import FormFactory
import django.db.models.options as options
from django.db.models.base import ModelBase
from django.core.exceptions import FieldDoesNotExist
from django.utils.autoreload import autoreload_started

warnings.filterwarnings('ignore', module='urllib3')

FILENAME = 'application.yml'
ENDPOINTS = {}
PROXIED_MODELS = []
APPLICATON = None

if APPLICATON is None and os.path.exists(FILENAME):
    with open(FILENAME) as file:
        content = file.read()
        for variable in re.findall(r'\$[a-zA-z0-9_]+', content):
            content = content.replace(variable, os.environ.get(variable[1:], ''))
    APPLICATON = yaml.safe_load(content).get('application')


class BaseManager(manager.BaseManager):
    def get_queryset(self):
        return super().get_queryset()

    def all(self):
        return self.get_queryset().all()

    def __call__(self, model):
        return apps.get_model(model)


class Manager(BaseManager.from_queryset(QuerySet)):
    pass


models.QuerySet = QuerySet
models.Manager = Manager
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + ('icon', 'search_fields'))



class ModelMixin(object):

    @classmethod
    def get_field(cls, lookup):
        model = cls
        attrs = lookup.split('__')
        while attrs:
            attr_name = attrs.pop(0)
            if attrs:  # go deeper
                field = model._meta.get_field(attr_name)
                model = field.related_model
            else:
                try:
                    return model._meta.get_field(attr_name)
                except FieldDoesNotExist:
                    pass
        return None

    def getroles(self, username_lookup='username'):
        roles = getattr(self, '_roles', None)
        if roles is None:
            obj = self
            for attr_name in username_lookup.split('__'):
                obj = getattr(obj, attr_name)
            roles = apps.get_model('api.role').objects.filter(username=obj)
            setattr(self, '_roles', roles)
        return roles

    def getuser(self, username_lookup):
        obj = self
        for attr_name in username_lookup.split('__'):
            obj = getattr(obj, attr_name)
        return apps.get_model('auth.user').objects.get(username=obj)
    
    def serializer(self) -> Serializer:
        return Serializer(self)
    
    def formfactory(self) -> FormFactory:
        return FormFactory(self)


___new___ = ModelBase.__new__


def __new__(mcs, name, bases, attrs, **kwargs):
    if attrs['__module__'] != '__fake__':
        # See .db.models.Manager
        if 'objects' in attrs and isinstance(attrs['objects'], QuerySet):
            queryset_class = attrs['objects']
            attrs.update(objects=BaseManager.from_queryset(type(queryset_class))())
        # Defining the objects Manager using .db.models.QuerySet
        if 'objects' not in attrs and not all(['objects' in dir(cls) for cls in bases]):
            attrs.update(objects=BaseManager.from_queryset(QuerySet)())

    if ModelMixin not in bases:
        bases = bases + (ModelMixin, )
    cls = ___new___(mcs, name, bases, attrs, **kwargs)
    if cls._meta.proxy_for_model:
        PROXIED_MODELS.append(cls._meta.proxy_for_model)
    return cls


ModelBase.__new__ = __new__


def api_watchdog(sender, **kwargs):
    sender.extra_files.add(Path('application.yml'))

autoreload_started.connect(api_watchdog)


def meta(verbose_name=None):
    def decorate(function):
        function.verbose_name = verbose_name
        return function
    return decorate
