
import warnings
from django.apps import apps
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django.db.models import manager, Q, CharField, ForeignKey, DecimalField, OneToOneField, ManyToManyField, TextField, CASCADE
from django.db.models.aggregates import Sum, Avg
from django.db.models.base import ModelBase
from .statistics import Statistics
from functools import reduce
from datetime import datetime
import operator
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


class QuerySet(models.QuerySet):

    def __init__(self, *args, **kwargs):
        self.metadata = {}
        super().__init__(*args, **kwargs)

    def counter(self, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).count(x=x, y=y) if x else super().count()

    def sum(self, z, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).sum(z, x=x, y=y) if x else super().aggregate(sum=Sum(z))['sum'] or 0

    def _clone(self):
        qs = super()._clone()
        for k, v in self.metadata.items():
            v = self.metadata[k]
            if isinstance(v, list):
                qs.metadata[k] = list(v)
            elif isinstance(v, dict):
                qs.metadata[k] = dict(v)
            else:
                qs.metadata[k] = v
        return qs

    def fields(self, *names):
        if 'fields' not in self.metadata:
            self.metadata['fields'] = ('id',) + names
        return self

    def search(self, *names):
        if 'search' not in self.metadata:
            self.metadata['search'] = [name if '__' in name else '{}__icontains'.format(name) for name in names]
        return self

    def filters(self, *names):
        if 'filters' not in self.metadata:
            self.metadata['filters'] = names
        return self

    def actions(self, *names):
        if 'actions' not in self.metadata:
            self.metadata['actions'] = names
        return self

    def subsets(self, *names):
        if 'subsets' not in self.metadata:
            self.metadata['subsets'] = names
        return self

    def title(self, name):
        self.metadata['title'] = name
        return self

    def contextualize(self, request, metadata=None):
        if metadata:
            self.metadata.update(**metadata)
        filters = self.metadata.get('filters', ())
        for lookup in filters:
            if lookup.endswith('userrole'):
                from api.models import Role
                rolename = request.GET.get('userrole')
                if rolename:
                    self = self.filter(
                        **{'{}__in'.format(lookup[0:-10]):
                        Role.objects.filter(name=rolename).values_list('username', flat=True)}
                    )
            elif lookup in request.GET:
                self = self.apply_filter(lookup, request.GET[lookup])
        search = self.metadata.get('search', ())
        if search and 'q' in request.GET:
            self = self.apply_search(request.GET['q'], search)
        return self

    def apply_filter(self, lookup, value):
        booleans = dict(true=True, false=False, null=None)
        if len(value) == 10 and '-' in value:
            value = datetime.strptime(value, '%Y-%m-%d');
        if value in booleans:
            value = booleans[value]
        return self.filter(**{lookup: value}) if value != '' else self

    def apply_search(self, term, lookups=None):
        if lookups is None:
            lookups = [f'{field.name}__icontains' for field in self.model._meta.get_fields()
                       if isinstance(field, CharField)] or []
        if lookups:
            terms = term.split(' ') if term else []
            conditions = []
            for term in terms:
                queries = [
                    Q(**{lookup: term})
                    for lookup in lookups
                ]
                conditions.append(reduce(operator.or_, queries))

            return self.filter(reduce(operator.and_, conditions)) if conditions else self
        return self


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
