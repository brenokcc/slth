import json
import warnings
from pathlib import Path
from datetime import datetime, date
from django.db import models
from .queryset import QuerySet
from django.db.models import manager
from .serializer import Serializer, serialize
from django.db.models.deletion import Collector
from .factory import FormFactory
import django.db.models.options as options
from django.db.models.base import ModelBase
from django.db.models import Model
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.utils.autoreload import autoreload_started
from django.core import serializers
from django.utils import autoreload
from .threadlocal import tl
from django.apps import apps as django_apps

from decimal import Decimal

warnings.filterwarnings('ignore', module='urllib3')

FILENAME = 'application.yml'
ENDPOINTS = {}
PROXIED_MODELS = []
THREADS = []

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return dict(type='decimal', value=float(obj))
        elif isinstance(obj, datetime):
            return dict(type='datetime', value=obj.isoformat())
        elif isinstance(obj, date):
            return dict(type='date', value=obj.isoformat())
        elif isinstance(obj, QuerySet):
            return dict(type='queryset', value=obj.dump())
        elif isinstance(obj, Model):
            return dict(type='object', model=obj._meta.label.lower(), pk=obj.pk)
        return json.JSONEncoder.default(self, obj)


class JSONDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        type = obj.get('type')
        if type:
            if type == 'decimal':
                return Decimal(obj['value'])
            elif type == 'datetime':
                return datetime.fromisoformat(obj['value'])
            elif type == 'date':
                return date.fromisoformat(obj['value'])
            elif type == 'queryset':
                return QuerySet.load(obj['value'])
            elif type == 'object':
                return django_apps.get_model(obj['model']).objects.get(pk=obj['pk'])
        return obj


def dumps(data, indent=1, ensure_ascii=False):
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, cls=JSONEncoder)


def loads(data):
    return json.loads(data, cls=JSONDecoder)


class BaseManager(manager.BaseManager):
    def get_queryset(self):
        return super().get_queryset()

    def all(self):
        return self.get_queryset().all()

    def __call__(self, model):
        return django_apps.get_model(model)


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
            roles = django_apps.get_model('api.role').objects.filter(username=obj)
            setattr(self, '_roles', roles)
        return roles

    def getuser(self, username_lookup):
        obj = self
        for attr_name in username_lookup.split('__'):
            obj = getattr(obj, attr_name)
        return django_apps.get_model('auth.user').objects.get(username=obj)
    
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
        backup  = dumps(dict(order=order, objects=serializers.serialize("python", objects)))
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
                    try:
                        b = getattr(self, field.name)
                    except ObjectDoesNotExist:
                        b = None
                    if a != b:
                        diff[field.verbose_name] = (serialize(a), serialize(b))
        else:
            action = 'add'
            for field in self._meta.fields:
                try:
                    b = getattr(self, field.name)
                except ObjectDoesNotExist:
                    b = None
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


original_trigger_reload = autoreload.trigger_reload

def trigger_reload(filename):
    print('Stoping sloth thread....')
    for thread in THREADS:
        thread.stop()
        thread.join()
    print('Thread stopped!')
    original_trigger_reload(filename)

autoreload.trigger_reload = trigger_reload
