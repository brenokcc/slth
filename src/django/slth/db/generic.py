# -*- coding: utf-8 -*-
import datetime
import json
from decimal import Decimal

from django.apps import apps
from django.db.models import *
from django.db.models.query_utils import DeferredAttribute


class GenericModelWrapper(object):
    def __init__(self, obj):
        self._wrapped_obj = obj

    def __getattr__(self, attr):
        if attr == 'prepare_database_save':
            raise AttributeError()
        return getattr(self._wrapped_obj, attr)

    def __setattr__(self, attr, value):
        if attr == '_wrapped_obj':
            super().__setattr__(attr, value)
        elif self._wrapped_obj is not None:
            self._wrapped_obj.__setattr__(attr, value._wrapped_obj)

    def __str__(self):
        return self._wrapped_obj.__str__()

    def __repr__(self):
        return self._wrapped_obj.__repr__()


class GenericValue(object):
    def __init__(self, value):
        self.value = value

    def get_value(self):
        if isinstance(self.value, str) and '::' in self.value:
            value_type, value = self.value.split('::')
            if '.' in value_type:
                self.value = apps.get_model(value_type).objects.get(pk=value)
            elif value_type == 'str':
                self.value = value
            elif value_type == 'int':
                self.value = int(value)
            elif value_type == 'Decimal':
                self.value = Decimal(value)
            elif value_type in ('date', 'datetime'):
                self.value = datetime.datetime.strptime(value[0:10], '%Y-%m-%d')
            elif value_type == 'float':
                self.value = float(value)
            elif value_type == 'bool':
                self.value = value == 'True'
            elif value_type == 'list':
                self.value = json.loads(value)
        return self.value

    def dumps(self):
        value = self.value
        if value is not None:
            if isinstance(value, Model):
                value = GenericModelWrapper(value)
            if isinstance(value, GenericModelWrapper):
                return '{}.{}::{}'.format(
                    value._meta.app_label, value._meta.model_name, value.pk
                )
            if hasattr(value, 'model'):
                value = list(value.values_list('pk', flat=True))
            if isinstance(value, list):
                value = json.dumps(value)
            return '{}::{}'.format(type(value).__name__, value)
        return None


class GenericFieldDescriptor(DeferredAttribute):
    def __get__(self, instance, cls=None):
        obj = super().__get__(instance, cls=cls)
        if isinstance(obj.value, Model):
            return GenericModelWrapper(obj.value)
        return obj.get_value()

    def __set__(self, instance, value):
        instance.__dict__[self.field.attname] = GenericValue(value)


class GenericField(CharField):
    descriptor_class = GenericFieldDescriptor

    def __init__(self, *args, max_length=255, null=True, **kwargs):
        super().__init__(*args, max_length=max_length, null=null, **kwargs)

    def get_prep_value(self, value):
        if value is not None:
            if isinstance(value, GenericValue):
                value = value.dumps()
            else:
                value = GenericValue(value).dumps()
        return value