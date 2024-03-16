import json
import types
from datetime import date, datetime
from django.apps import apps
from django.db.models import Model, QuerySet, Manager
from django.utils.text import slugify


def serialize(obj):
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, datetime):
        return obj.strftime('%d/%m/%Y %H:%M:%S')
    elif isinstance(obj, list):
        return [serialize(obj) for obj in obj]
    elif isinstance(obj, Model):
        return dict(pk=obj.pk, str=str(obj))
    elif isinstance(obj, QuerySet) or isinstance(obj, Manager):
        return [dict(pk=item.pk, str=str(item)) for item in obj.filter()]
    return str(obj)

def getfield(obj, name_or_names, request=None, size=100):
    fields = []
    if isinstance(name_or_names, str):
        value = getattr(obj, name_or_names)
        fields.append(dict(type='field', name=name_or_names, value=serialize(value), size=size))
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name)
        field = dict(type='field', name=name_or_names.name, value=serialize(value), size=size)
        if value:
            endpoint = name_or_names.endpoint(request, value.id)
            if endpoint.check_permission():
                field.update(url=name_or_names.endpoint.get_api_url(value.id))
        fields.append(field)
    else:
        for name in name_or_names:
            fields.append(getfield(obj, name, size=int(100/len(name_or_names))))
    return fields

class LinkField:
    def __init__(self, name, endpoint):
        self.name = name
        self.endpoint = endpoint

class Serializer:
    def __init__(self, obj, request=None):
        self.obj = obj
        self.request = request
        self.only = request.GET.getlist('only') if request else ()
        if isinstance(obj, Model):
            self.data = dict(type='instance', title=str(obj), actions=[], data=[])
        elif isinstance(self.obj, QuerySet) or isinstance(self.obj, Manager):
            self.obj = self.obj.filter()
            self.data= dict(type='queryset', title=self.obj.model._meta.verbose_name_plural, data={})
    
    def fields(self, *names):
        for name in names:
            self.data['data'].extend(getfield(self.obj, name, self.request))
        return self
    
    def relation(self, name):
        title = name
        if not self.only or slugify(title) in self.only:
            attr = getattr(self.obj, name)
            value = attr() if type(attr) == types.MethodType else attr
            data = serialize(value)
            if isinstance(value, QuerySet) or isinstance(value, Manager):
                data = dict(type='queryset', data=data)
            self.data['data'].append(dict(type='fieldset', slug=slugify(title), title=name, data=data))
        return self
    
    def endpoint(self, title, cls):
        if not self.only or slugify(title) in self.only:
            endpoint = cls(self.request, self.obj)
            if endpoint.check_permission():
                data = serialize(endpoint.get())
            self.data['data'].append(
                dict(type='fieldset', slug=slugify(title), title=title, actions=[], data=data)
            )
        return self

    def fieldset(self, title, names, relation=None):
        if not self.only or slugify(title) in self.only:
            actions=[]
            fields=[]
            obj = getattr(self.obj, relation) if relation else self.obj
            for name in names:
                fields.extend(getfield(obj, name, self.request))
            self.data['data'].append(
                dict(type='fieldset', title=title, slug=slugify(title), actions=actions, data=fields)
            )
        return self
    
    def serialize(self, debug=False):
        if not self.data['data']:
            self.data['data'] = serialize(self.obj)
        if debug:
            json.dumps(self.data, indent=2, ensure_ascii=False)
        return self.data

