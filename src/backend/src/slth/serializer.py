import re
import json
import types
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.db import models


def to_snake_case(name):
    return name if name.islower() else re.sub(r'(?<!^)(?=[A-Z0-9])', '_', name).lower()


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

def getfield(obj, name_or_names, request=None):
    if isinstance(name_or_names, str):
        if obj:
            attr = getattr(obj, name_or_names)
            if type(attr) == types.MethodType:
                value = attr()
                label = getattr(attr, 'verbose_name', name_or_names)
            else:
                value = attr
                label = getattr(type(obj), name_or_names).field.verbose_name
        else:
            value = None
            label = None
        field = dict(type='field', name=name_or_names, label=label, value=serialize(value, primitive=True))
        return field
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name) if obj else None
        field = dict(type='field', name=name_or_names.name, value=serialize(value, primitive=True))
        if value:
            endpoint = name_or_names.endpoint(request, value.id)
            if endpoint.check_permission():
                field.update(url=name_or_names.endpoint.get_api_url(value.id))
        return field
    else:
        fields = []
        for name in name_or_names:
            fields.append(getfield(obj, name))
        return fields

class LinkField:
    def __init__(self, name, endpoint):
        self.name = name
        self.endpoint = endpoint

class Serializer:
    def __init__(self, obj=None, request=None):
        self.obj = obj
        self.request = request
        self.metadata = []
        
    def fields(self, *names):
        self.metadata.append(('fields', dict(names=names)))
        return self
        
    def queryset(self, name):
        self.metadata.append(('queryset', dict(name=name)))
        return self
    
    def endpoint(self, title, cls):
        self.metadata.append(('endpoint', dict(title=title, cls=cls)))
        return self

    def fieldset(self, title, names, attr=None):
        self.metadata.append(('fieldset', dict(title=title, names=names, attr=attr)))
        return self
    
    def serialize(self, debug=False):
        only = self.request.GET.getlist('only') if self.request else ()

        if not self.metadata:
            self.fields(*[field.name for field in type(self.obj)._meta.fields])
            for m2m in type(self.obj)._meta.many_to_many:
                self.queryset(m2m.name)
        
        serialized = dict(type='instance', title=str(self.obj), actions=[], data=[])
        
        for key, metadata in self.metadata:
            if key == 'fields':
                for name in metadata['names']:
                    if not only or name in only:
                        serialized['data'].append(getfield(self.obj, name, self.request))
            elif key == 'queryset':
                name = metadata['name']
                if not only or to_snake_case(name) in only:
                    attr = getattr(self.obj, name)
                    if type(attr) == types.MethodType:
                        value = attr()
                        title = name
                    else:
                        value = attr
                        title = getattr(type(self.obj), name).field.verbose_name
                    data = value.title(title).attrname(name).contextualize(self.request).serialize(debug=False)
                    serialized['data'].append(data)
            elif key == 'endpoint':
                title = metadata['title']
                cls = metadata['cls']
                if not only or to_snake_case(title) in only:
                    endpoint = cls(self.request, self.obj)
                    if endpoint.check_permission():
                        data = serialize(endpoint.get())
                    serialized['data'].append(
                        dict(type='fieldset', slug=to_snake_case(title), title=title, actions=[], data=data)
                    )
            elif key == 'fieldset':
                title = metadata['title']
                names = metadata['names']
                attr = metadata['attr']
                if not only or to_snake_case(title) in only:
                    actions=[]
                    fields=[]
                    obj = getattr(self.obj, attr) if attr else self.obj
                    for i, name in enumerate(names):
                        for field in getfield(obj, name, self.request):
                            fields.append(field)
                    serialized['data'].append(
                        dict(type='fieldset', title=title, key=to_snake_case(title), actions=actions, data=fields)
                    )

        if debug:
            print(json.dumps(serialized, indent=2, ensure_ascii=False))
        return serialized
