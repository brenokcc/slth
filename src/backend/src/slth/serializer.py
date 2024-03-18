import json
import types
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.utils.text import slugify
from django.db import models


def serialize(obj, primitive=False):
    if obj is None:
        return None
    elif isinstance(obj, dict):
        return obj
    elif isinstance(obj, date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, datetime):
        return obj.strftime('%d/%m/%Y %H:%M:%S')
    elif isinstance(obj, list):
        return [serialize(obj) for obj in obj]
    elif isinstance(obj, Model):
        return str(obj) if primitive else dict(pk=obj.pk, str=str(obj))
    elif isinstance(obj, QuerySet) or isinstance(obj, Manager):
        if primitive:
            return [str(obj) for obj in obj.filter()]
        else:
            return [dict(pk=item.pk, str=str(item)) for item in obj.filter()]
    return str(obj)

def getfield(obj, name_or_names, request=None, size=100):
    fields = []
    if isinstance(name_or_names, str):
        value = getattr(obj, name_or_names) if obj else None
        fields.append(dict(type='field', name=name_or_names, value=serialize(value, primitive=True), size=size))
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name) if obj else None
        field = dict(type='field', name=name_or_names.name, value=serialize(value, primitive=True), size=size)
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
        self.data = dict(type='instance', title=str(obj), actions=[], data=[])
    
    def fields(self, *names):
        for name in names:
            if not self.only or name in self.only:
                self.data['data'].extend(getfield(self.obj, name, self.request))
        return self
    
    def queryset(self, name):
        if not self.only or name in self.only:
            attr = getattr(self.obj, name)
            if type(attr) == types.MethodType:
                value = attr()
                title = name
            else:
                value = attr
                title = getattr(type(self.obj), name).field.verbose_name
            data = value.title(title).attrname(name).contextualize(self.request).serialize(debug=False)
            self.data['data'].append(data)
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

    def fieldset(self, title, names, attr=None):
        if not self.only or slugify(title) in self.only:
            actions=[]
            fields=[]
            obj = getattr(self.obj, attr) if attr else self.obj
            for name in names:
                fields.extend(getfield(obj, name, self.request))
            self.data['data'].append(
                dict(type='fieldset', title=title, slug=slugify(title), actions=actions, data=fields)
            )
        return self
    
    def serialize(self, debug=False):
        if not self.data['data']:
            self.fields(*[field.name for field in type(self.obj)._meta.fields])
            for m2m in type(self.obj)._meta.many_to_many:
                self.queryset(m2m.name)
        if debug:
            print(json.dumps(self.data, indent=2, ensure_ascii=False))
        return self.data
