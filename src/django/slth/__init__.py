import re
import os
import yaml
import json
import warnings
from pathlib import Path
from datetime import datetime, date
from django.apps import apps
from django.db import models
from .queryset import QuerySet
from django.db.models import manager
from .serializer import Serializer, serialize
from django.db.models.deletion import Collector
from .factory import FormFactory
import django.db.models.options as options
from django.db.models.base import ModelBase
from django.core.exceptions import FieldDoesNotExist
from django.utils.autoreload import autoreload_started
from django.core import serializers
from .threadlocal import tl

from decimal import Decimal

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


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, date):
            return obj.strftime("%d-%m-%Y")
        return json.JSONEncoder.default(self, obj)


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
    
    def pre_save(self):
        pass

    def post_save(self):
        pass

    def safe_delete(self, username=None):
        from .models import Deletion
        order = []
        objects = []
        collector = Collector('default')
        qs = type(self).objects.filter(pk=self.pk)
        collector.collect(qs)
        for instances in collector.data.values():
            for instance in instances:
                if instance.__class__.__name__ not in ['Log'] and instance not in objects:
                    objects.append(instance)
                    if instance.__class__.__name__ not in order:
                        order.append(instance.__class__.__name__)
        for qs in collector.fast_deletes:
            for instance in qs:
                if instance.__class__.__name__ not in ['Log'] and instance not in objects:
                    objects.append(instance)
                    if instance.__class__.__name__ not in order:
                        order.append(instance.__class__.__name__)
        backup  = json.dumps(dict(order=order, objects=serializers.serialize("python", objects)), cls=JSONEncoder)
        instance = '{}.{}:{}'.format(self._meta.app_label, self._meta.model_name, self.pk)
        Deletion.objects.create(username=username, datetime=datetime.now(), instance=instance, backup=backup)
        return self.delete()


def save_decorator(func):
    
    def decorate(self, *args, **kwargs):
        diff = {}
        if self.pk:
            action = 'edit'
            obj = type(self).objects.filter(pk=self.pk).first()
            if obj:
                for field in self._meta.fields:
                    a = getattr(obj, field.name)
                    b = getattr(self, field.name)
                    if a != b:
                        diff[field.verbose_name] = (serialize(a), serialize(b))
        else:
            action = 'add'
            for field in self._meta.fields:
                b = getattr(self, field.name)
                if b is not None:
                    diff[field.verbose_name] = (None, serialize(b))
        func(self, *args, **kwargs)
        if diff:
            model = '{}.{}'.format(self._meta.app_label, self._meta.model_name)
            log = dict(model=model, pk=self.pk, action=action, diff=diff)
            context = getattr(tl, 'context', None)
            if context:
                context['logs'].append(log)

    return decorate


def delete_decorator(func):
    def decorate(self, *args, **kwargs):
        diff = {}
        for field in self._meta.fields:
            a = getattr(self, field.name)
            diff[field.verbose_name] = (a, None)
        log = dict(model='{}.{}'.format(
            self._meta.app_label, self._meta.model_name), action='delete', diff=diff
        )
        context = getattr(tl, 'context', None)
        if context:
            context['logs'].append(log)
        func(self, *args, **kwargs)

    return decorate


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
    if name == 'Model':
        cls.save = save_decorator(cls.save)
        cls.delete = delete_decorator(cls.delete)
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
