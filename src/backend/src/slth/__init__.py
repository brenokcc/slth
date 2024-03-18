
import warnings
from django.apps import apps
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django.db.models import manager, Q, CharField, ForeignKey, DecimalField, OneToOneField, ManyToManyField, TextField, CASCADE
from django.db.models.aggregates import Sum, Avg
from django.db.models.base import ModelBase
from .queryset import QuerySet
from functools import reduce
from django.utils.translation import gettext_lazy as _

warnings.filterwarnings('ignore', module='urllib3')

ENDPOINTS = {}
PROXIED_MODELS = []


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


class BaseManager(manager.BaseManager):
    def get_queryset(self):
        return super().get_queryset()

    def all(self):
        return self.get_queryset().all()

    def __call__(self, model):
        return apps.get_model(model)


class Manager(BaseManager.from_queryset(QuerySet)):
    pass


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


class CharField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 255)
        super().__init__(*args, **kwargs)


class ForeignKey(ForeignKey):
    def __init__(self, to, on_delete=None, **kwargs):
        self.pick = kwargs.pop('pick', False)
        self.addable = kwargs.pop('addable', False)
        super().__init__(to, on_delete or CASCADE, **kwargs)


class ManyToManyField(ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        self.addable = kwargs.pop('addable', False)
        super().__init__(*args, **kwargs)

class OneToManyField(ManyToManyField):

    def formfield(self, *args, **kwargs):
        from . import forms
        kwargs.update(form_class=forms.OneToManyField)
        return super().formfield(*args, model=self.related_model, **kwargs)


class OneToOneField(OneToOneField):

    def formfield(self, *args, **kwargs):
        from . import forms
        kwargs.update(form_class=forms.OneToOneField)
        return super().formfield(*args, model=self.related_model, **kwargs)


class DecimalField(DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['decimal_places'] = kwargs.pop('decimal_places', 2)
        kwargs['max_digits'] = kwargs.pop('max_digits', 9)
        super().__init__(*args, **kwargs)


class TextField(TextField):
    def __init__(self, *args, **kwargs):
        self.formatted= kwargs.pop('formatted', False)
        super().__init__(*args, **kwargs)


ModelBase.__new__ = __new__
models.QuerySet = QuerySet
models.Manager = Manager
models.CharField = CharField
models.ForeignKey = ForeignKey
models.OneToOneField = OneToOneField
models.OneToManyField = OneToManyField
models.ManyToManyField = ManyToManyField
models.DecimalField = DecimalField
models.TextField = TextField
