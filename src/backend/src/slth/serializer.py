import re
import json
import types
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.db import models
from django.utils.text import slugify
from .exceptions import JsonResponseException


def to_snake_case(name):
    return slugify(name).replace('-', '_')


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
    def __init__(self, obj=None, request=None, serializer=None, type='instance', title=None):
        self.path = serializer.path.copy() if serializer else []
        self.obj = obj
        self.request = request
        self.metadata = []
        self.serializer:Serializer = serializer
        self.type = type
        if title:
            self.title = title
            self.path.append(to_snake_case(title))
        else:
            self.title = str(obj)
        
    def fields(self, *names):
        self.metadata.append(('fields', dict(names=names)))
        return self
    
    def fieldset(self, title, names=(), attr=None, section=None, list=None, group=None):
        self.metadata.append(('fieldset', dict(title=title, names=names, attr=attr, section=section, list=list, group=group)))
        return self
        
    def queryset(self, name, section=None, list=None, group=None):
        self.metadata.append(('queryset', dict(name=name, section=section, list=list, group=group)))
        return self
    
    def endpoint(self, title, cls, section=None, list=None, group=None):
        self.metadata.append(('endpoint', dict(title=title, cls=cls, section=section, list=list, group=group)))
        return self
    
    def section(self, title):
        return Serializer(obj=self.obj, request=self.request, serializer=self, type='section', title=title)
    
    def group(self, title):
        return Serializer(obj=self.obj, request=self.request, serializer=self, type='group', title=title)

    def parent(self):
        self.serializer.metadata.append(('serializer', dict(serializer=self)))
        return self.serializer
    
    def serialize(self, debug=False):
        try:
            return self.to_dict(debug=debug)
        except JsonResponseException as e:
            if self.serializer:
                raise e
            if debug:
                print(json.dumps(e.data, indent=2, ensure_ascii=False))
            return e.data

    def to_dict(self, debug=False):
        path = [f'&only={token}' if i else f'?only={token}' for i, token in enumerate(self.path)]
        only = self.request.GET.getlist('only') if self.request else ()

        if not self.metadata:
            self.fields(*[field.name for field in type(self.obj)._meta.fields])
            for m2m in type(self.obj)._meta.many_to_many:
                self.queryset(m2m.name)
        
        items = []
        output = None
        for key, metadata in self.metadata:
            data = None
            if key == 'fields':
                data = []
                for name in metadata['names']:
                    if not only or name in only:
                        data.append(getfield(self.obj, name, self.request))
                if only and only[-1] == name: raise JsonResponseException(data)
            elif key == 'fieldset':
                title = metadata['title']
                names = metadata['names']
                attr = metadata['attr']
                if not only or to_snake_case(title) in only:
                    actions=[]
                    fields=[]
                    obj = getattr(self.obj, attr) if attr else self.obj
                    for name in names:
                        fields.append(getfield(obj, name, self.request))
                    url = ''.join(path)
                    url += f'&only={to_snake_case(title)}' if url else f'?only={to_snake_case(title)}'
                    data = dict(type='fieldset', title=title, key=to_snake_case(title), url=url, actions=actions, data=fields)
                    if only and only[-1] == to_snake_case(title): raise JsonResponseException(data)
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
                    data['url'] = '{}&{}'.format(''.join(path)[1:], data['url'][1:]) if data['url'] else ''.join(path)
                    if only and only[-1] == name: raise JsonResponseException(data)
            elif key == 'endpoint':
                title = metadata['title']
                cls = metadata['cls']
                if not only or to_snake_case(title) in only:
                    endpoint = cls(self.request, self.obj)
                    if endpoint.check_permission():
                        data = serialize(endpoint.get())
                    data = dict(type='fieldset', slug=to_snake_case(title), title=title, actions=[], data=data)
            elif key == 'serializer':
                serializer = metadata['serializer']
                if not only or to_snake_case(serializer.title) in only:
                    data = serializer.to_dict()
            if data:
                items.extend(data) if key == 'fields' else items.append(data)
        
        output = dict(type=self.type, title=self.title, url=''.join(path), actions=[], data=items)
        if debug:
            print(json.dumps(output, indent=2, ensure_ascii=False))
        return output
